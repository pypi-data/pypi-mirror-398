from __future__ import annotations

from enum import StrEnum
from types import SimpleNamespace
from typing import Annotated, Any, Dict, List, TypeVar

import httpx
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    field_serializer,
    field_validator,
    model_validator,
)

from fbnconfig import datatype

from .resource_abc import CamelAlias, Ref, Resource, register_resource

# Converts a Resource or Ref into an embedded
# reference to the Resource for use when dumping
T = TypeVar("T")


def as_reference(v: T) -> Dict | T:
    if isinstance(v, (Resource, Ref)):
        return {"$ref": v.id}
    return v


ResourceId = datatype.ResourceId  # expose property.ResourceId for backwards compatibility


class LifeTime(StrEnum):
    Perpetual = "Perpetual"
    TimeVariant = "TimeVariant"


class Domain(StrEnum):
    Abor = "Abor"
    AborConfiguration = "AborConfiguration"
    AccessMetadata = "AccessMetadata"
    Account = "Account"
    Allocation = "Allocation"
    Analytic = "Analytic"
    Block = "Block"
    Calendar = "Calendar"
    ChartOfAccounts = "ChartOfAccounts"
    Compliance = "Compliance"
    ConfigurationRecipe = "ConfigurationRecipe"
    CustodianAccount = "CustodianAccount"
    CustomEntity = "CustomEntity"
    CutLabelDefinition = "CutLabelDefinition"
    DerivedValuation = "DerivedValuation"
    DiaryEntry = "DiaryEntry"
    Execution = "Execution"
    FundConfiguration = "FundConfiguration"
    Fund = "Fund"
    Holding = "Holding"
    IdentifierDefinition = "IdentifierDefinition"
    Instrument = "Instrument"
    InstrumentEvent = "InstrumentEvent"
    InvestorRecord = "InvestorRecord"
    InvestmentAccount = "InvestmentAccount"
    Leg = "Leg"
    LegalEntity = "LegalEntity"
    MarketData = "MarketData"
    NextBestAction = "NextBestAction"
    NotDefined = "NotDefined"
    Order = "Order"
    OrderInstruction = "OrderInstruction"
    Package = "Package"
    Participation = "Participation"
    Person = "Person"
    Placement = "Placement"
    Portfolio = "Portfolio"
    PortfolioGroup = "PortfolioGroup"
    PropertyDefinition = "PropertyDefinition"
    Reconciliation = "Reconciliation"
    ReferenceHolding = "ReferenceHolding"
    Transaction = "Transaction"
    TransactionConfiguration = "TransactionConfiguration"
    UnitResult = "UnitResult"


class ConstraintStyle(StrEnum):
    Property = "Property"
    Collection = "Collection"
    Identifier = "Identifier"


class CollectionType(StrEnum):
    Set = "Set"
    Array = "Array"


@register_resource()
class DefinitionRef(BaseModel, Ref):
    id: str = Field(exclude=True)
    domain: Domain
    scope: str
    code: str

    def __format__(self, _):
        return f"Properties[{self.domain}/{self.scope}/{self.code}]"

    def attach(self, client):
        domain, scope, code = self.domain, self.scope, self.code
        try:
            client.get(f"/api/api/propertydefinitions/{domain}/{scope}/{code}")
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Property definition {domain}/{scope}/{code} not found")
            else:
                raise ex


class Formula(BaseModel):
    formula: str
    args: Dict

    def __init__(self, formula, **kwargs):
        super().__init__(formula=formula, args=kwargs)

    @classmethod
    def create(cls, formula, **kwargs):
        return Formula(formula, **kwargs)


@register_resource()
class DefinitionResource(CamelAlias, BaseModel, Resource):
    id: str = Field(init=True, exclude=True)
    domain: Domain
    scope: str
    code: str
    display_name: str
    data_type_id: datatype.DataTypeKey
    property_description: str | None = None
    life_time: LifeTime | None = None
    constraint_style: ConstraintStyle | None = None
    collection_type: str | None = None
    derivation_formula: Formula | None = None
    is_filterable: bool | None = None
    remote: Dict[str, Any] | None = Field(None, exclude=True, init=False)

    def __format__(self, _):
        return f"Properties[{self.domain}/{self.scope}/{self.code}]"

    @field_serializer("derivation_formula", when_used="always")
    def ser_formula(self, value: Formula, info) -> str | Dict[str, Any]:
        style = info.context.get("style", "api") if info.context else "api"
        if style == "dump":
            return {
                "formula": value.formula,
                "args": {k: as_reference(v) for k, v in value.args.items()},
            }
        # use str.format to interpolate the values, hits __format__ when
        # arg is another property
        return value.formula.format(**value.args)

    @field_validator("derivation_formula", mode="before")
    @classmethod
    def des_formula(cls, value, info) -> Formula | None:
        if isinstance(value, Formula):
            return value
        args = (
            {
                k: info.context["$refs"][p["$ref"]] if isinstance(p, Dict) and p.get("$ref") else p
                for k, p in value["args"].items()
            }
            if info.context and info.context.get("$refs")
            else value["args"]
        )
        return Formula(value["formula"], **args)

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    @model_validator(mode="after")
    def check_derived_or_plain(self):
        if self.derivation_formula:
            if self.life_time or self.constraint_style or self.collection_type:
                raise RuntimeError("A property must be either derived or plain")
        # if this is not a derived property, then is_filterable cannot be set
        elif self.is_filterable is not None:
            raise RuntimeError(
                "Cannot set 'is_filterable' field, a property must be either derived or plain"
            )
        return self

    def read(self, client, old_state):
        domain = old_state.domain
        scope = old_state.scope
        code = old_state.code
        self.remote = client.get(f"/api/api/propertydefinitions/{domain}/{scope}/{code}").json()
        return self.remote

    def create(self, client: httpx.Client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        derived = self.derivation_formula is not None
        if derived:
            client.post("/api/api/propertydefinitions/derived", json=desired)
        else:
            client.post("/api/api/propertydefinitions", json=desired)
        return {"domain": self.domain, "scope": self.scope, "code": self.code, "derived": derived}

    @staticmethod
    def delete(client, old_state: SimpleNamespace):
        domain, scope, code = old_state.domain, old_state.scope, old_state.code
        client.delete(f"/api/api/propertydefinitions/{domain}/{scope}/{code}")

    def update(self, client, old_state):
        # cannot change identifier or switch derived and non-derived. recreate
        derived = self.derivation_formula is not None
        if [self.domain, self.scope, self.code, derived] != [
            old_state.domain,
            old_state.scope,
            old_state.code,
            old_state.derived,
        ]:
            self.delete(client, old_state)
            return self.create(client)
        self.read(client, old_state)
        remote = self.remote or {}
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        effective = remote | desired
        if effective == remote:
            return None
        # cannot change dataType, collectionType or lifetime need to recreate
        if (
            remote["dataTypeId"] != desired["dataTypeId"]
            or remote.get("collectionType", None) != effective.get("collectionType", None)
            or remote.get("lifeTime", None) != desired.get("lifeTime", None)
            or remote.get("constraintStyle", None) != desired.get("constraintStyle", None)
        ):
            self.delete(client, old_state)
            return self.create(client)
        if derived:
            client.put(
                f"/api/api/propertydefinitions/derived/{self.domain}/{self.scope}/{self.code}",
                json=desired,
            )
        else:
            client.put(
                f"/api/api/propertydefinitions/{self.domain}/{self.scope}/{self.code}", json=desired
            )
        return {"domain": self.domain, "scope": self.scope, "code": self.code, "derived": derived}

    def deps(self):
        res: List[Resource | Ref] = []
        if self.derivation_formula:
            res = [
                value
                for value in self.derivation_formula.args.values()
                if isinstance(value, (DefinitionResource, DefinitionRef))
            ]
        if isinstance(self.data_type_id, (Resource, Ref)):
            res.append(self.data_type_id)
        return res


#
# for use when another object needs to reference a property definition
# normal form is domain/scope/code
#
def ser_property_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return "/".join([value.domain, value.scope, value.code])


def des_property_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


PropertyKey = Annotated[
    DefinitionResource | DefinitionRef,
    BeforeValidator(des_property_key),
    PlainSerializer(ser_property_key),
]


@register_resource()
class DefinitionOverrideResource(DefinitionResource):
    """ a speciial definition for override properties. These get created by
        lusid but can be updated by clients """
    # create requires that the definition already exists
    def create(self, client: httpx.Client):
        domain, scope, code = self.domain, self.scope, self.code
        derived = True if self.derivation_formula else False
        desired_state = SimpleNamespace(domain=domain, scope=scope, code=code, derived=derived)
        # see if it exists already
        preexisting = True
        try:
            self.read(client, desired_state)
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                preexisting = False
            else:
                raise ex
        if preexisting:
            # update will try to read and throw if it doesnt exist
            new_state = self.update(client, desired_state)
            # even if update didn't change anything we still need to return the state
            # because create always does
            if new_state is None:
                return {
                    "domain": domain,
                    "scope": scope,
                    "code": code,
                    "derived": derived,
                    "preexisting": preexisting
                }
            return new_state | {"preexisting": preexisting}
        else:
            # if it does not exist, create it
            new_state = super().create(client)
            return new_state | {"preexisting": preexisting}

    def update(self, client: httpx.Client, old_state: SimpleNamespace):
        # normal update but preserve state.preexisting
        preexisting = getattr(old_state, "preexisting", False)
        new_state = super().update(client, old_state)
        if new_state is None:
            return None
        return new_state | {"preexisting": preexisting}

    # delete does nothing because we don't own the resource we just update it
    @staticmethod
    def delete(client, old_state: SimpleNamespace):
        preexisting = getattr(old_state, "preexisting", False)
        if not preexisting:
            return DefinitionResource.delete(client, old_state)
