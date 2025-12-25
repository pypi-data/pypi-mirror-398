import json
import string
from hashlib import sha256
from typing import Any, Dict, List

import httpx
from pydantic import BaseModel, Field, model_validator

from fbnconfig import property as prop

from .resource_abc import CamelAlias, Resource, register_resource
from .urlfmt import Urlfmt

url: string.Formatter = Urlfmt("api/api/instrumenteventtypes")

TRANSACTION_TEMPLATE_URL_PATTERN = (
    "{base}/{instrumentEventType}/transactiontemplates/{instrumentType}/{scope}"
)


class TransactionCurrencyAndAmount(CamelAlias, BaseModel):
    currency: str | None = None
    amount: str | None = None


class TransactionPriceAndType(CamelAlias, BaseModel):
    price: str | None = None
    type: str | None = None


class TransactionFieldMap(CamelAlias, BaseModel):
    instrument: str
    settlement_date: str
    source: str
    transaction_currency: str
    transaction_date: str
    transaction_id: str
    type: str
    units: str
    transaction_price: TransactionPriceAndType
    exchange_rate: str | None
    total_consideration: TransactionCurrencyAndAmount


class TransactionPropertyMap(CamelAlias, BaseModel):
    property_key: prop.PropertyKey | None
    value: str | None = None


class ComponentTransactions(CamelAlias, BaseModel):
    display_name: str
    condition: str | None = None
    transaction_field_map: TransactionFieldMap
    transaction_property_map: List[TransactionPropertyMap]
    preserve_tax_lot_structure: bool | None = None
    market_open_time_adjustments: str | None = None


@register_resource()
class TransactionTemplateResource(BaseModel, Resource):
    id: str = Field(exclude=True)
    scope: str
    instrument_type: str
    instrument_event_type: str
    description: str
    component_transactions: List[ComponentTransactions]

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client: httpx.Client, old_state):
        scope = old_state.scope
        instrument_event_type = old_state.instrumentEventType
        instrument_type = old_state.instrumentType

        formatted_url = url.format(
            TRANSACTION_TEMPLATE_URL_PATTERN,
            scope=scope,
            instrumentEventType=instrument_event_type,
            instrumentType=instrument_type
        )
        return client.get(formatted_url).json()

    def create(self, client: httpx.Client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        scope = desired["scope"]
        instrument_event_type = desired["instrumentEventType"]
        instrument_type = desired["instrumentType"]
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        formatted_url = url.format(
            TRANSACTION_TEMPLATE_URL_PATTERN,
            scope=scope,
            instrumentEventType=instrument_event_type,
            instrumentType=instrument_type
        )

        client.post(formatted_url, json=desired)

        return {
            "id": self.id,
            "scope": self.scope,
            "instrumentType": self.instrument_type,
            "instrumentEventType": self.instrument_event_type,
            "content_hash": content_hash
        }

    @staticmethod
    def delete(client: httpx.Client, old_state):
        scope = old_state.scope
        instrument_event_type = old_state.instrumentEventType
        instrument_type = old_state.instrumentType

        formatted_url = url.format(
            TRANSACTION_TEMPLATE_URL_PATTERN,
            scope=scope,
            instrumentEventType=instrument_event_type,
            instrumentType=instrument_type
        )
        client.delete(formatted_url)

    def update(self, client: httpx.Client, old_state):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        sorted_desired = json.dumps(desired, sort_keys=True)

        content_hash = sha256(sorted_desired.encode()).hexdigest()

        if (self.scope, self.instrument_type, self.instrument_event_type) != (
            old_state.scope,
            old_state.instrumentType,
            old_state.instrumentEventType
        ):
            self.delete(client, old_state)
            return self.create(client)

        if content_hash == old_state.content_hash:
            return None

        self.delete(client, old_state)
        return self.create(client)

    def deps(self):
        property_keys = []

        for tx in self.component_transactions:
            for prop_map in tx.transaction_property_map:
                if prop_map.property_key is not None:
                    property_keys.append(prop_map.property_key)

        return property_keys
