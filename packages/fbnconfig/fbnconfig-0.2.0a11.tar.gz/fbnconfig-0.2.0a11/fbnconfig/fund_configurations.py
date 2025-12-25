import json
import string
from enum import StrEnum
from hashlib import sha256
from typing import List, Sequence

from pydantic import BaseModel, Field, field_serializer, model_validator

from . import property
from .properties import PropertyValueInner
from .resource_abc import CamelAlias, Ref, Resource, register_resource
from .urlfmt import Urlfmt

url: string.Formatter = Urlfmt("api/api/fundconfigurations")
CREATE_FUNDCONFIGURATION_URL = ("{base}/{scope}")
FUND_CONFIGURATION_URL = ("{base}/{scope}/{code}")


class PropertyValue(CamelAlias, BaseModel):
    key: property.PropertyKey  # Renamed from property_definition
    value: PropertyValueInner
    effective_from: str | None = None
    effective_until: str | None = None

    @classmethod
    def create(cls, key, label_value=None, metric_value=None,
                    label_set_value=None, effective_from=None, effective_until=None):
        """Convenience method to create PropertyValue with the nested value structure"""
        value_inner = PropertyValueInner(
            label_value=label_value,
            metric_value=metric_value,
            label_set_value=label_set_value
        )
        return cls(
            key=key,
            value=value_inner,
            effective_from=effective_from,
            effective_until=effective_until
        )


class AppliesToEnum(StrEnum):
    Undefined = "Undefined"
    PnLBucket = "PnLBucket"
    Fees = "Fees"


class ExternalFeeComponentFilter(CamelAlias, BaseModel):
    filter_id: str
    filter: str
    applies_to: AppliesToEnum


class ComponentFilter(CamelAlias, BaseModel):
    filter_id: str
    filter: str


@register_resource()
class FundConfigurationResource(BaseModel, Resource):
    id: str = Field(exclude=True)
    scope: str
    # request body
    code: str
    display_name: str | None = None
    description: str | None = None
    dealing_filters: List[ComponentFilter]
    pnl_filters: List[ComponentFilter]
    back_out_filters: List[ComponentFilter]
    external_fee_filters: List[ExternalFeeComponentFilter] | None = None
    properties: List[PropertyValue] | None = None

    @field_serializer("properties", mode="plain")
    def serialize_properties(self, properties, _info):
        if properties is None:
            return None
        return {
            f"FundConfiguration/{pv.key.scope}/{pv.key.code}": pv for pv in properties
        }

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info):
        if not isinstance(data, dict):
            return data

        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        scope, code = old_state.scope, old_state.code
        formatted_url = url.format(FUND_CONFIGURATION_URL, scope=scope, code=code)
        return client.get(formatted_url).json()

    def create(self, client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode("utf-8")).hexdigest()

        scope = desired["scope"]
        code = desired["code"]

        formatted_url = url.format(CREATE_FUNDCONFIGURATION_URL, scope=scope)
        client.post(formatted_url, json=desired)

        return {"scope": scope, "code": code, "content_hash": content_hash}

    def update(self, client, old_state):
        # Currently only some fields can be updated with FundConfiguration
        # So we must delete and recreate a fund configuration if other fields change
        if (self.scope, self.code) != (old_state.scope, old_state.code):
            self.delete(client, old_state)
            return self.create(client)
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        sorted_desired = json.dumps(desired, sort_keys=True)
        desired_hash = sha256(sorted_desired.encode("utf-8")).hexdigest()
        if desired_hash == old_state.content_hash:
            return None
        self.delete(client, old_state)
        return self.create(client)

    @staticmethod
    def delete(client, old_state):
        scope, code = old_state.scope, old_state.code
        formatted_url = url.format(FUND_CONFIGURATION_URL, scope=scope, code=code)
        client.delete(formatted_url)

    def deps(self) -> Sequence[Resource | Ref]:
        property_keys = []
        if self.properties is None:
            return property_keys

        for property_def in self.properties:
            if property_def.key is not None:
                property_keys.append(property_def.key)

        return property_keys
