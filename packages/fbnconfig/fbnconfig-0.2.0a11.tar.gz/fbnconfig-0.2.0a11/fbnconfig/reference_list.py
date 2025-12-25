import json
from hashlib import sha256
from typing import Annotated, Any, Dict, List, Literal

import httpx
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, computed_field, model_validator

from fbnconfig.coretypes import ResourceId

from . import property
from .properties import MetricValue
from .properties import PropertyValueInner as PropertyValue
from .resource_abc import CamelAlias, Ref, Resource, register_resource

_ = MetricValue


class ReferenceListRef(CamelAlias, BaseModel, Ref):
    id: str
    scope: str
    code: str

    def attach(self, client):
        try:
            url = f"/api/api/referencelists/{self.scope}/{self.code}"
            response = client.get(url)
            return response.json()
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                return None
            else:
                raise ex


class AddressKeyList(CamelAlias, BaseModel):
    values: list[str]
    reference_list_type: Literal["AddressKeyList"] = Field("AddressKeyList", init=False)


class DecimalList(CamelAlias, BaseModel):
    values: list[float]
    reference_list_type: Literal["DecimalList"] = Field("DecimalList", init=False)


class FundIdList(CamelAlias, BaseModel):
    values: list[ResourceId]
    reference_list_type: Literal["FundIdList"] = Field("FundIdList", init=False)


class PortfolioGroupIdList(CamelAlias, BaseModel):
    values: list[ResourceId]
    reference_list_type: Literal["PortfolioGroupIdList"] = Field("PortfolioGroupIdList", init=False)


class PortfolioIdList(CamelAlias, BaseModel):
    values: list[ResourceId]
    reference_list_type: Literal["PortfolioIdList"] = Field("PortfolioIdList", init=False)


class InstrumentList(CamelAlias, BaseModel):
    values: list[str]
    reference_list_type: Literal["InstrumentList"] = Field("InstrumentList", init=False)


class StringList(CamelAlias, BaseModel):
    values: list[str]
    reference_list_type: Literal["StringList"] = Field("StringList", init=False)


class PropertyListItem(CamelAlias, BaseModel):
    key: property.PropertyKey
    value: PropertyValue
    effective_from: str | None = None
    effective_until: str | None = None


class PropertyList(CamelAlias, BaseModel):
    values: list[PropertyListItem]
    reference_list_type: Literal["PropertyList"] = Field("PropertyList", init=False)


ReferenceListTypes = Annotated[
    AddressKeyList | DecimalList | FundIdList | PortfolioGroupIdList |
    PortfolioIdList | InstrumentList | StringList | PropertyList,
    Field(discriminator="reference_list_type")
]


@register_resource()
class ReferenceListResource(BaseModel, Resource):
    id: str = Field(exclude=True)
    scope: str
    code: str
    name: str
    description: str | None = None
    tags: list[str] | None = None
    reference_list: ReferenceListTypes

    @computed_field(alias="id")
    def list_id(self) -> dict[str, str]:
        return {"scope": self.scope, "code": self.code}

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if isinstance(data.get("id"), dict):
            # promote scope and code from id dict
            data = data | data["id"]
        if info.context and info.context.get("id"):
            # Handle id from context (for dump/undump)
            # For undump, the id might be a string that needs to be the resource id
            context_id = info.context.get("id")
            data = data | {"id": context_id}
        return data

    def read(self, client, old_state):
        scope, code = old_state.scope, old_state.code
        url = f"/api/api/referencelists/{scope}/{code}"
        entity = client.get(url).json()
        entity.pop("version", None)
        return entity

    def create(self, client) -> Dict[str, Any]:
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
                                  exclude={"id", "scope", "code"})
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        client.request("POST", "/api/api/referencelists", json=desired)
        return {"scope": self.scope, "code": self.code, "content_hash": content_hash}

    def update(self, client, old_state):
        if (self.scope, self.code) != (old_state.scope, old_state.code):
            self.delete(client, old_state)
            return self.create(client)
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True
                                  , exclude={"id", "scope", "code"})
        sorted_desired = json.dumps(desired, sort_keys=True)
        desired_hash = sha256(sorted_desired.encode()).hexdigest()
        if desired_hash == old_state.content_hash:
            return None
        client.request("POST", "/api/api/referencelists", json=desired)
        return {"scope": self.scope, "code": self.code, "content_hash": desired_hash}

    @staticmethod
    def delete(client, old_state):
        client.request("DELETE", f"/api/api/referencelists/{old_state.scope}/{old_state.code}")

    def deps(self) -> List[Resource | Ref]:
        if isinstance(self.reference_list, PropertyList):
            props = {i.key.id: i.key for i in self.reference_list.values}
            return list(props.values())
        return []


def ser_referencelist_key(value, info):
    print("ser_resource_id", value)
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return {"scope": value.scope, "code": value.code}


def des_referencelist_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


ReferenceListKey = Annotated[
    ReferenceListResource | ReferenceListRef,
    BeforeValidator(des_referencelist_key), PlainSerializer(ser_referencelist_key)
]
