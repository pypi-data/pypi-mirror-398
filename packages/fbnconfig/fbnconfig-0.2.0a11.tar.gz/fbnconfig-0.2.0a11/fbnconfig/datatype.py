from __future__ import annotations

import copy
from enum import StrEnum
from typing import Annotated, Any, Dict, List

import httpx
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, model_validator

from .resource_abc import CamelAlias, Ref, Resource, register_resource


class TypeValueRange(StrEnum):
    OPEN = "Open"
    CLOSED = "Closed"


class ValueType(StrEnum):
    BOOLEAN = "Boolean"
    CODE = "Code"
    CURRENCY = "Currency"
    CURRENCY_AND_AMOUNT = "CurrencyAndAmount"
    CUT_LOCAL_TIME = "CutLocalTime"
    DATE_OR_CUTLABEL = "DateOrCutLabel"
    DATE_TIME = "DateTime"
    DECIMAL = "Decimal"
    ID = "Id"
    INT = "Int"
    LIST = "List"
    MAP = "Map"
    METRIC_VALUE = "MetricValue"
    PERCENTAGE = "Percentage"
    PROPERTY_ARRAY = "PropertyArray"
    RESOURCE_ID = "ResourceId"
    RESULT_VALUE = "ResultValue"
    STRING = "String"
    TRADE_PRICE = "TradePrice"
    UNINDEXED_TEXT = "UnindexedText"
    URI = "Uri"


class FieldValueType(StrEnum):
    STRING = "String"
    DECIMAL = "Decimal"


class Unit(BaseModel, CamelAlias):
    code: str
    display_name: str
    description: str
    details: Any | None = None


class UnitSchema(StrEnum):
    NO_UNITS = "NoUnits"
    BASIC = "Basic"
    ISO4217_CURRENCY = "Iso4217Currency"


class FieldDefinition(BaseModel, CamelAlias):
    key: str
    is_required: bool
    is_unique: bool
    value_type: str | FieldValueType = FieldValueType.STRING


class FieldValue(BaseModel):
    value: str
    fields: Dict[str, str]  # limit to strings because get returns strings


class ReferenceData(BaseModel, CamelAlias):
    field_definitions: List[FieldDefinition]
    values: List[FieldValue]


@register_resource()
class DataTypeRef(BaseModel, Ref):
    id: str = Field(exclude=True)
    scope: str
    code: str

    def attach(self, client):
        scope, code = self.scope, self.code
        try:
            client.get(f"/api/api/datatypes/{scope}/{code}", params={"includeSystem": True})
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Datatype {scope}/{code} not found")
            else:
                raise ex


@register_resource()
class DataTypeResource(CamelAlias, BaseModel, Resource):
    id: str = Field(exclude=True)
    scope: str
    code: str
    type_value_range: TypeValueRange
    display_name: str
    description: str
    value_type: ValueType
    acceptable_values: List[str] | None = None
    unit_schema: UnitSchema = UnitSchema.NO_UNITS
    acceptable_units: List[Unit] | None = None
    reference_data: ReferenceData | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if isinstance(data.get("id", None), dict):
            data = data | data.pop("id")
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state) -> Dict[str, Any]:
        return client.get(f"/api/api/datatypes/{old_state.scope}/{old_state.code}").json()

    def create(self, client: httpx.Client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        client.post("/api/api/datatypes", json=desired)
        return {"scope": self.scope, "code": self.code}

    def update(self, client: httpx.Client, old_state):
        if [self.scope, self.code] != [old_state.scope, old_state.code]:
            raise RuntimeError("Cannot change scope/code on datatype")
        remote = self.read(client, old_state)
        remote.pop("href")
        remote.pop("id")
        remote.pop("links")
        remote.pop("version")
        desired = self.model_dump(
            mode="json", exclude_none=True, exclude={"scope", "code"}, by_alias=True
        )
        effective = remote | copy.deepcopy(desired)
        if "referenceData" in remote and "referenceData" in effective:
            # sort the fields since the api changes the order they come back
            remote["referenceData"]["fieldDefinitions"].sort(key=lambda field: field["key"])
            effective["referenceData"]["fieldDefinitions"].sort(key=lambda field: field["key"])
            # sort the values since the api changes the order they come back
            remote["referenceData"]["values"].sort(key=lambda field: field["value"])
            effective["referenceData"]["values"].sort(key=lambda field: field["value"])
        if "acceptableValues" in remote and "acceptableValues" in effective:
            # sort the acceptableValues since the api changes the order they come back
            remote["acceptableValues"].sort()
            effective["acceptableValues"].sort()
        if effective == remote:
            return None
        # check for illegal modifications
        readonly_fields = ["typeValueRange", "unitSchema", "valueType"]
        modified = [field for field in readonly_fields if effective[field] != remote[field]]
        if len(modified) > 0:
            raise RuntimeError(f"Cannot change readonly fields {modified} on datatype")
        if effective["referenceData"]["fieldDefinitions"] != remote["referenceData"]["fieldDefinitions"]:
            raise RuntimeError(
                "Cannot change readonly fields referenceData.fieldDefinitions on datatype"
            )
        # update reference data values if required
        if effective["referenceData"]["values"] != remote["referenceData"]["values"]:
            client.put(
                f"/api/api/datatypes/{self.scope}/{self.code}/referencedatavalues",
                json=effective["referenceData"]["values"],
            )
        # update core data if required
        effective.pop("referenceData")
        remote.pop("referenceData")
        if effective != remote:
            client.put(f"/api/api/datatypes/{self.scope}/{self.code}", json=desired)
        return {"scope": self.scope, "code": self.code}

    @staticmethod
    def delete(client, old_state):
        client.delete(f"/api/api/datatypes/{old_state.scope}/{old_state.code}")

    def deps(self):
        return []


class ResourceId(BaseModel):
    scope: str
    code: str


def ser_datatype_key(value: ResourceId | DataTypeRef | DataTypeResource, info):
    style = info.context.get("style", "api") if info.context else "api"
    if style == "dump":
        if isinstance(value, (Resource, Ref)):
            return {"$ref": value.id}
        return value
    # uses str.format to interpolate the values for the api request
    return {"scope": value.scope, "code": value.code}


def des_datatype_key(value, info):
    if info.context and info.context.get("$refs"):
        return info.context["$refs"][value["$ref"]]
    return value


# as a special case, we allow system datatypes to be represented as ResourceId
# so users don't have to create refs for them.
DataTypeKey = Annotated[
    ResourceId | DataTypeRef | DataTypeResource,
    BeforeValidator(des_datatype_key), PlainSerializer(ser_datatype_key)
]
