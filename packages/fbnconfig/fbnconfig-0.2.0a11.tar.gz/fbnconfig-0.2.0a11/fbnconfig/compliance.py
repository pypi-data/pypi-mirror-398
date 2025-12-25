import json
from hashlib import sha256
from typing import Annotated, Any, Dict, List, Literal, Mapping, Sequence

import httpx
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    computed_field,
    field_serializer,
    model_validator,
)

from . import property
from .coretypes import ResourceId
from .properties import PropertyValueInner as PropertyValue
from .reference_list import ReferenceListKey
from .resource_abc import CamelAlias, Ref, Resource, register_resource


class ComplianceTemplateParameter(CamelAlias, BaseModel):
    name: str
    description: str
    type: str


class BranchStep(CamelAlias, BaseModel):
    label: str
    parameters: List[ComplianceTemplateParameter]
    complianceStepTypeRequest: Literal["BranchStepRequest"] = Field("BranchStepRequest", init=False)  # noqa: N815


class CheckStep(CamelAlias, BaseModel):
    label: str
    limit_check_parameters: List[ComplianceTemplateParameter]  # noqa: N815
    warning_check_parameters: List[ComplianceTemplateParameter]  # noqa: N815
    complianceStepTypeRequest: Literal["CheckStepRequest"] = Field("CheckStepRequest", init=False)  # noqa: N815


class FilterStep(CamelAlias, BaseModel):
    label: str
    parameters: List[ComplianceTemplateParameter]
    complianceStepTypeRequest: Literal["FilterStepRequest"] = Field("FilterStepRequest", init=False)  # noqa: N815


class GroupByStep(CamelAlias, BaseModel):
    values: list[str]
    parameters: List[ComplianceTemplateParameter]
    complianceStepTypeRequest: Literal["GroupByStepRequest"] = Field("GroupByStepRequest",  # noqa: N815
                                                                         init=False)


class GroupFilterStep(CamelAlias, BaseModel):
    label: str
    limit_check_parameters: List[ComplianceTemplateParameter]  # noqa: N815
    complianceStepTypeRequest: Literal["GroupFilterStepRequest"] = Field("GroupFilterStepRequest",  # noqa: N815
                                                                            init=False)


class PercentCheckStep(CamelAlias, BaseModel):
    label: str
    limit_check_parameters: List[ComplianceTemplateParameter]  # noqa: N815
    warning_check_parameters: List[ComplianceTemplateParameter]  # noqa: N815
    complianceStepTypeRequest: Literal["PercentCheckStepRequest"] = Field("PercentCheckStepRequest",  # noqa: N815
                                                                             init=False)


class RecombineStep(CamelAlias, BaseModel):
    values: list[str]
    parameters: List[ComplianceTemplateParameter]
    complianceStepTypeRequest: Literal["RecombineStepRequest"] = Field("RecombineStepRequest",  # noqa: N815
                                                                             init=False)


StepTypes = Annotated[
    BranchStep | CheckStep | FilterStep | GroupByStep | GroupFilterStep
    | PercentCheckStep | RecombineStep
    , Field(discriminator="complianceStepTypeRequest")]


class ComplianceTemplateVariation(CamelAlias, BaseModel):
    label: str
    description: str
    outcome_description: str | None = None  # noqa: N815
    steps: Sequence[StepTypes]
    referenced_group_label: str | None = None  # noqa: N815


@register_resource()
class ComplianceTemplateResource(CamelAlias, BaseModel, Resource):
    id: str = Field(init=True, exclude=True)
    scope: str
    code: str
    description: str | None = None
    tags: list[str] | None = None
    variations: Sequence[ComplianceTemplateVariation]

    @computed_field(alias="id")
    def _id(self) -> dict[str, str]:
        return {"scope": self.scope, "code": self.code}

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # Handle API response format (id.scope and id.code)
        if isinstance(data.get("id", None), dict):
            data = data | data["id"]
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        scope, code = old_state.scope, old_state.code
        url = f"/api/api/compliance/templates/{scope}/{code}"
        entity = client.get(url).json()
        entity.pop("links", None)
        entity.pop("version", None)
        return entity

    def create(self, client) -> Dict[str, Any]:
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"id", "scope"})
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        client.request("POST", f"/api/api/compliance/templates/{self.scope}", json=desired)
        return {"scope": self.scope, "code": self.code, "content_hash": content_hash}

    def update(self, client, old_state):
        if (self.scope, self.code) != (old_state.scope, old_state.code):
            self.delete(client, old_state)
            return self.create(client)
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"id", "scope"})
        sorted_desired = json.dumps(desired, sort_keys=True)
        desired_hash = sha256(sorted_desired.encode()).hexdigest()
        if desired_hash == old_state.content_hash:
            return None
        client.request("PUT", f"/api/api/compliance/templates/{self.scope}/{self.code}", json=desired)
        return {"scope": self.scope, "code": self.code, "content_hash": desired_hash}

    @staticmethod
    def delete(client, old_state):
        client.request("DELETE", f"/api/api/compliance/templates/{old_state.scope}/{old_state.code}")

    def deps(self) -> List[Resource | Ref]:
        return []


class ComplianceTemplateRef(CamelAlias, BaseModel, Ref):
    id: str
    scope: str
    code: str

    def attach(self, client):
        try:
            url = f"/api/api/compliance/templates/{self.scope}/{self.code}"
            response = client.get(url)
            return response.json()
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                return None
            else:
                raise ex


def ser_template_key(value, info):
    if info.context and info.context.get("style", "api") == "dump":
        return {"$ref": value.id}
    return {"scope": value.scope, "code": value.code}


def des_template_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


ComplianceTemplateKey = Annotated[
    ComplianceTemplateResource | ComplianceTemplateRef,
    BeforeValidator(des_template_key), PlainSerializer(ser_template_key)
]


# Compliance Rule Parameter Classes

class AddressKeyComplianceParameter(CamelAlias, BaseModel):
    value: str
    complianceParameterType: Literal["AddressKeyComplianceParameter"] = Field(  # noqa: N815
        "AddressKeyComplianceParameter", init=False)


class AddressKeyListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["AddressKeyListComplianceParameter"] = Field(  # noqa: N815
        "AddressKeyListComplianceParameter", init=False)


class BoolComplianceParameter(CamelAlias, BaseModel):
    value: bool
    complianceParameterType: Literal["BoolComplianceParameter"] = Field(  # noqa: N815
        "BoolComplianceParameter", init=False)


class BoolListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["BoolListComplianceParameter"] = Field(  # noqa: N815
        "BoolListComplianceParameter", init=False)


class DateTimeComplianceParameter(CamelAlias, BaseModel):
    value: str  # ISO 8601 datetime string
    complianceParameterType: Literal["DateTimeComplianceParameter"] = Field(  # noqa: N815
        "DateTimeComplianceParameter", init=False)


class DateTimeListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["DateTimeListComplianceParameter"] = Field(  # noqa: N815
        "DateTimeListComplianceParameter", init=False)


class DecimalComplianceParameter(CamelAlias, BaseModel):
    value: float
    complianceParameterType: Literal["DecimalComplianceParameter"] = Field(  # noqa: N815
        "DecimalComplianceParameter", init=False)


class DecimalListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["DecimalListComplianceParameter"] = Field(  # noqa: N815
        "DecimalListComplianceParameter", init=False)


class FilterPredicateComplianceParameter(CamelAlias, BaseModel):
    value: str
    complianceParameterType: Literal["FilterPredicateComplianceParameter"] = Field(  # noqa: N815
        "FilterPredicateComplianceParameter", init=False)


class GroupBySelectorComplianceParameter(CamelAlias, BaseModel):
    value: str
    complianceParameterType: Literal["GroupBySelectorComplianceParameter"] = Field(  # noqa: N815
        "GroupBySelectorComplianceParameter", init=False)


class GroupCalculatorComplianceParameter(CamelAlias, BaseModel):
    value: str
    complianceParameterType: Literal["GroupCalculatorComplianceParameter"] = Field(  # noqa: N815
        "GroupCalculatorComplianceParameter", init=False)


class GroupFilterPredicateComplianceParameter(CamelAlias, BaseModel):
    value: str
    complianceParameterType: Literal["GroupFilterPredicateComplianceParameter"] = Field(  # noqa: N815
        "GroupFilterPredicateComplianceParameter", init=False)


class InstrumentListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["InstrumentListComplianceParameter"] = Field(  # noqa: N815
        "InstrumentListComplianceParameter", init=False)


class PortfolioGroupIdComplianceParameter(CamelAlias, BaseModel):
    value: ResourceId
    complianceParameterType: Literal["PortfolioGroupIdComplianceParameter"] = Field(  # noqa: N815
        "PortfolioGroupIdComplianceParameter", init=False)


class PortfolioGroupIdListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["PortfolioGroupIdListComplianceParameter"] = Field(  # noqa: N815
        "PortfolioGroupIdListComplianceParameter", init=False)


class PortfolioIdComplianceParameter(CamelAlias, BaseModel):
    value: ResourceId
    complianceParameterType: Literal["PortfolioIdComplianceParameter"] = Field(  # noqa: N815
        "PortfolioIdComplianceParameter", init=False)


class PortfolioIdListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["PortfolioIdListComplianceParameter"] = Field(  # noqa: N815
        "PortfolioIdListComplianceParameter", init=False)


class PropertyKeyComplianceParameter(CamelAlias, BaseModel):
    value: property.PropertyKey
    complianceParameterType: Literal["PropertyKeyComplianceParameter"] = Field(  # noqa: N815
        "PropertyKeyComplianceParameter", init=False)


class PropertyKeyListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["PropertyKeyListComplianceParameter"] = Field(  # noqa: N815
        "PropertyKeyListComplianceParameter", init=False)


class PropertyListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["PropertyListComplianceParameter"] = Field(  # noqa: N815
        "PropertyListComplianceParameter", init=False)


class StringComplianceParameter(CamelAlias, BaseModel):
    value: str
    complianceParameterType: Literal["StringComplianceParameter"] = Field(  # noqa: N815
        "StringComplianceParameter", init=False)


class StringListComplianceParameter(CamelAlias, BaseModel):
    value: ReferenceListKey
    complianceParameterType: Literal["StringListComplianceParameter"] = Field(  # noqa: N815
        "StringListComplianceParameter", init=False)


# Union type for all compliance parameters
RuleParameterTypes = Annotated[
    AddressKeyComplianceParameter | AddressKeyListComplianceParameter |
    BoolComplianceParameter | BoolListComplianceParameter |
    DateTimeComplianceParameter | DateTimeListComplianceParameter |
    DecimalComplianceParameter | DecimalListComplianceParameter |
    FilterPredicateComplianceParameter |
    GroupBySelectorComplianceParameter | GroupCalculatorComplianceParameter |
    GroupFilterPredicateComplianceParameter |
    PortfolioGroupIdComplianceParameter | PortfolioGroupIdListComplianceParameter |
    PortfolioIdComplianceParameter | PortfolioIdListComplianceParameter |
    PropertyKeyComplianceParameter | PropertyKeyListComplianceParameter |
    PropertyListComplianceParameter |
    StringComplianceParameter | StringListComplianceParameter | GroupBySelectorComplianceParameter
    , Field(discriminator="complianceParameterType")
]


class PropertyListItem(CamelAlias, BaseModel):
    key: property.PropertyKey
    value: PropertyValue

    def propkey(self):
        pd = self.key
        return "/".join([pd.domain.value, pd.scope, pd.code])


@register_resource()
class ComplianceRuleResource(CamelAlias, BaseModel, Resource):
    id: str
    scope: str
    code: str
    name: str
    description: str | None = None
    active: bool
    template_id: ComplianceTemplateKey
    variation: str
    portfolio_group_id: ResourceId  # noqa: N815
    parameters: Mapping[str, RuleParameterTypes] | None = None
    properties: Sequence[PropertyListItem]

    @field_serializer("properties", when_used="always")
    def ser_properties(self, value, info):
        style = info.context.get("style", "api") if info.context else "api"
        if style == "dump":
            # prop list will handle the $refs
            return value
        # In API mode, return the computed field value (dict format)
        return {p.propkey(): p for p in value}

    @computed_field(alias="id")
    def ser_id(self) -> dict[str, str]:
        return {"scope": self.scope, "code": self.code}

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # promote scope and code to top for api style
        if "id" in data and isinstance(data["id"], dict):
            data = data | data["id"]
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        # Handle API response properties format (dict to array)
        if isinstance(data.get("properties", None), dict):
            data = data | {"properties": list(data["properties"].values())}
        return data

    def read(self, client, old_state):
        scope, code = old_state.scope, old_state.code
        url = f"/api/api/compliance/rules/{scope}/{code}"
        entity = client.get(url).json()
        entity.pop("links", None)
        entity.pop("version", None)
        return entity

    def create(self, client) -> Dict[str, Any]:
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
            exclude={"id", "scope", "code"}
        )
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        client.request("POST", "/api/api/compliance/rules", json=desired)
        return {"scope": self.scope, "code": self.code, "content_hash": content_hash}

    def update(self, client, old_state):
        if (self.scope, self.code) != (old_state.scope, old_state.code):
            self.delete(client, old_state)
            return self.create(client)
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
            exclude={"id", "scope", "code"}
        )
        sorted_desired = json.dumps(desired, sort_keys=True)
        desired_hash = sha256(sorted_desired.encode()).hexdigest()
        if desired_hash == old_state.content_hash:
            return None
        client.request("POST", "/api/api/compliance/rules", json=desired)
        return {"scope": self.scope, "code": self.code, "content_hash": desired_hash}

    @staticmethod
    def delete(client, old_state):
        client.request("DELETE", f"/api/api/compliance/rules/{old_state.scope}/{old_state.code}")

    def deps(self) -> List[Resource | Ref]:
        res: List[Resource | Ref] = []
        res.append(self.template_id)
        for p in self.properties:
            res.append(p.key)
        return res


class ComplianceRuleRef(CamelAlias, BaseModel, Ref):
    id: str
    scope: str
    code: str

    def attach(self, client):
        try:
            url = f"/api/api/compliance/rules/{self.scope}/{self.code}"
            response = client.get(url)
            return response.json()
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                return None
            else:
                raise ex
