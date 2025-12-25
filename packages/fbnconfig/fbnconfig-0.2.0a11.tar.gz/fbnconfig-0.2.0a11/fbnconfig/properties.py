
from typing import Annotated, Mapping, Self, Sequence

from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, model_validator

from .coretypes import IsoDateTime
from .property import PropertyKey
from .resource_abc import CamelAlias


class MetricValue(CamelAlias, BaseModel):
    value: float
    unit: str | None = None


# The inner part of a property value for when it is used inside a structure
# that has the property definition
class PropertyValueInner(CamelAlias, BaseModel):
    label_value: str | None = None  # noqa: N815
    metric_value: MetricValue | None = None  # noqa: N815
    label_set_value: Sequence[str] | None = None  # noqa: N815

    @model_validator(mode="after")
    def validate_one_value_exists(self):
        fields = ["label_value", "metric_value", "label_set_value"]
        s = [field for field in fields if getattr(self, field) is not None]
        if len(s) > 1:
            raise KeyError(f"Cannot set {' and '.join(s)}, only one of {' or '.join(fields)} can be set")
        return self


class PropertyValue(CamelAlias, BaseModel):
    property_key: PropertyKey = Field(serialization_alias="propertyKey")
    label_value: str | None = Field(default=None, serialization_alias="labelValue")
    metric_value: MetricValue | None = Field(default=None, serialization_alias="metricValue")
    label_set_value: Sequence[str] | None = Field(default=None, serialization_alias="labelSetValue")
    effective_from: IsoDateTime | None = None
    effective_until: IsoDateTime | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info):
        if not isinstance(data, dict):
            return data
        style = info.context.get("style", "api") if info.context else "api"
        if style == "api" and data.get("value", None):
            return data | data["value"]
        return data

    @model_validator(mode="after")
    def validate_one_value_exists(self) -> Self:
        fields = ["label_value", "metric_value", "label_set_value"]
        s = [field for field in fields if getattr(self, field) is not None]
        if len(s) > 1:
            raise KeyError(f"Cannot set {' and '.join(s)}, only one of {' or '.join(fields)} can be set")

        return self


def ser_properties_as_dict(values: Sequence[PropertyValue], info):
    style = info.context.get("style", "api") if info.context else "api"
    if style == "dump":
        return values
    property_dict = {}
    for prop in values:
        value = {}
        if prop.label_value:
            value["labelValue"] = prop.label_value
        elif prop.metric_value:
            value["metricValue"] = prop.metric_value
        elif prop.label_set_value:
            value["labelSetValue"] = prop.label_set_value
        key = f"{prop.property_key.domain.value}/{prop.property_key.scope}/{prop.property_key.code}"
        property_dict[key] = {"key": key, "value": value}

        if prop.effective_from is not None:
            property_dict[key]["effectiveFrom"] = prop.effective_from

        if prop.effective_until is not None:
            property_dict[key]["effectiveUntil"] = prop.effective_until

    return property_dict


def des_properties_dict(data, info) -> Sequence[PropertyValue] | Mapping | None:
    if not isinstance(data, dict) or data is None:
        return data
    style = info.context.get("style", "api") if info.context else "api"
    if style == "api" and isinstance(data, dict):
        data = [value | {"propertyKey": value["key"]} for value in data.values()]
    return data


PropertyValueDict = Annotated[
    Sequence[PropertyValue],
    BeforeValidator(des_properties_dict), PlainSerializer(ser_properties_as_dict)
]
