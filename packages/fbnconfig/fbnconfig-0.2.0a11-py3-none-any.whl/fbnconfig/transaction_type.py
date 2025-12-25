import json
from enum import StrEnum
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Self, Sequence, Union

from httpx import Client as httpxClient
from pydantic import BaseModel, Field, field_serializer, model_validator

from .property import PropertyKey
from .resource_abc import CamelAlias, Ref, Resource, register_resource
from .side_definition import SideKey, SideRef, SideResource


class TransactionTypeAlias(CamelAlias, BaseModel):
    type: str
    description: str
    transaction_class: str = Field(serialization_alias="transactionClass")
    transaction_roles: str = Field(serialization_alias="transactionRoles")
    is_default: Optional[bool] = Field(False, serialization_alias="isDefault")


class MovementOption(StrEnum):
    DirectAdjustment = "DirectAdjustment"
    IncludesTradedInterest = "IncludesTradedInterest"


class MovementType(StrEnum):
    Settlement = "Settlement"
    Traded = "Traded"
    StockMovement = "StockMovement"
    FutureCash = "FutureCash"
    Commitment = "Commitment"
    Receivable = "Receivable"
    CashSettlement = "CashSettlement"
    CashForward = "CashForward"
    CashCommitment = "CashCommitment"
    CashReceivable = "CashReceivable"
    Accrual = "Accrual"
    CashAccrual = "CashAccrual"
    ForwardFx = "ForwardFx"
    CashFxForward = "CashFxForward"
    UnsettledCashTypes = "UnsettledCashTypes"
    # Carry movements - Memo transaction to record carry against an instrument.
    Carry = "Carry"  # Carry that will present as an inflow/outflow.
    CarryAsPnl = "CarryAsPnl"  # Carry that will present as a gain or loss.
    VariationMargin = "VariationMargin"
    Capital = "Capital"
    Fee = "Fee"


class CalculationType(StrEnum):
    TaxAmounts = "TaxAmounts"
    NotionalAmount = "Txn:NotionalAmount"
    GrossConsideration = "Txn:GrossConsideration"
    TradeToPortfolioRate = "Txn:TradeToPortfolioRate"
    ExchangeRate = "Txn:ExchangeRate"
    DeriveTotalConsideration = "DeriveTotalConsideration"
    BondInterest = "Txn:BondInterest"


class TransactionTypeCalculation(CamelAlias, BaseModel):
    type: CalculationType | str
    side: SideKey | None = None
    formula: Optional[str] = None


class MetricValue(CamelAlias, BaseModel):
    value: float
    unit: Optional[str] = None


class PerpetualProperty(CamelAlias, BaseModel):
    property_key: PropertyKey = Field(serialization_alias="propertyKey")
    label_value: Optional[str] = Field(default=None, serialization_alias="labelValue")
    metric_value: Optional[MetricValue] = Field(default=None, serialization_alias="metricValue")
    label_set_value: Optional[List[str]] = Field(default=None, serialization_alias="labelSetValue")

    @model_validator(mode="after")
    def validate_one_value_exists(self) -> Self:
        fields = ["label_value", "metric_value", "label_set_value"]
        s = [field for field in fields if getattr(self, field) is not None]
        if len(s) > 1:
            raise KeyError(f"Cannot set {' and '.join(s)}, only one of {' or '.join(fields)} can be set")

        return self


class TransactionTypePropertyMapping(CamelAlias, BaseModel):
    property_key: PropertyKey = Field(serialization_alias="propertyKey")
    map_from: PropertyKey | None = Field(serialization_alias="mapFrom", default=None)
    set_to: str = Field(serialization_alias="setTo", default=None)


def sort_transaction_type_arrays(obj):  # type: ignore
    if isinstance(obj, dict):
        return {k: sort_transaction_type_arrays(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        if all(isinstance(i, dict) for i in obj):
            return sorted(
                [sort_transaction_type_arrays(i) for i in obj],
                key=lambda x: json.dumps(x, sort_keys=True),
            )
        else:
            return sorted(obj)
    else:
        return obj


def _compare_json_structures(json1, json2) -> bool:
    return sort_transaction_type_arrays(json1) == sort_transaction_type_arrays(json2)


def _normalize_settlement_modes(data: dict) -> dict:
    """
    Normalize settlement modes in movements for comparison.
    Removes default settlementMode values to ensure proper comparison.
    """
    if not isinstance(data, dict):
        return data

    normalized = data.copy()

    # Handle movements array
    if "movements" in normalized and isinstance(normalized["movements"], list):
        normalized_movements = []
        for movement in normalized["movements"]:
            if isinstance(movement, dict):
                movement_copy = movement.copy()
                # Remove settlementMode if it's the default value (None/null or "Internal")
                if movement_copy.get("settlementMode") in [None, "Internal"]:
                    movement_copy.pop("settlementMode", None)
                normalized_movements.append(movement_copy)
            else:
                normalized_movements.append(movement)
        normalized["movements"] = normalized_movements

    return normalized


def serialize_properties(values: List[PerpetualProperty]):
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

    return property_dict


class SettlementMode(StrEnum):
    Internal = "Internal"
    External = "External"


class TransactionTypeMovement(CamelAlias, BaseModel):
    movement_types: MovementType
    side: SideKey
    direction: int
    properties: Optional[List[PerpetualProperty]] = []
    mappings: Optional[List[TransactionTypePropertyMapping]] = []
    name: Optional[str] = None
    movement_options: Optional[List[MovementOption] | str] = []
    settlement_date_override: Optional[str] = None
    condition: Optional[str] = ""
    settlement_mode: SettlementMode | None = None

    @field_serializer("properties", when_used="always")
    def serialize_properties(self, v: List[PerpetualProperty], info):
        style = info.context.get("style", "api") if info.context else "api"
        return v if style == "dump" else serialize_properties(v)


@register_resource()
class TransactionTypeResource(BaseModel, Resource):
    """
    Represents a transaction type
    """

    id: str = Field(exclude=True, init=True)
    scope: str = Field(init=True)
    source: str = Field(init=True)
    aliases: List[TransactionTypeAlias] = Field(min_length=1)
    movements: List[TransactionTypeMovement] = []
    properties: Optional[List[PerpetualProperty]] = []
    calculations: Optional[List[TransactionTypeCalculation]] = []

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def _get_first_alias(self):
        return sorted([alias.type for alias in self.aliases])[0]

    @field_serializer("properties", when_used="always")
    def serialize_properties(self, v: List[PerpetualProperty], info):
        style = info.context.get("style", "api") if info.context else "api"
        return v if style == "dump" else serialize_properties(v)

    def read(self, client: httpxClient, old_state: SimpleNamespace) -> None | Dict[str, Any]:
        transaction_type = old_state.transaction_type
        source = old_state.source
        scope = old_state.scope
        response = client.get(
            f"/api/api/transactionconfiguration/types/{source}/{transaction_type}",
            params={"scope": scope},
        ).json()
        if "links" in response.keys():
            del response["links"]
        return response

    def create(self, client: httpxClient) -> Optional[Dict[str, Any]]:
        desired = self.model_dump(mode="json", exclude_none=True,
                                  by_alias=True, exclude={"scope", "source"})
        client.put(
            f"/api/api/transactionconfiguration/types/{self.source}/{self._get_first_alias()}",
            params={"scope": self.scope},
            json=desired,
        )
        return {"source": self.source, "scope": self.scope, "transaction_type": self._get_first_alias()}

    def update(self, client: httpxClient, old_state) -> Union[None, Dict[str, Any]]:
        if [old_state.transaction_type, old_state.scope, old_state.source] != [
            self._get_first_alias(),
            self.scope,
            self.source,
        ]:
            self.delete(client, old_state)
            return self.create(client)

        remote = self.read(client, old_state) or {}
        desired = self.model_dump(mode="json", exclude_none=True,
                                  by_alias=True, exclude={"scope", "source"})

        # Normalize both remote and desired data before comparison to handle settlementMode defaults
        normalized_remote = _normalize_settlement_modes(remote)
        normalized_desired = _normalize_settlement_modes(desired)

        if _compare_json_structures(normalized_remote, normalized_desired):
            return None
        # create and update are the same on the api
        return self.create(client)

    @staticmethod
    def delete(client: httpxClient, old_state) -> None:
        transaction_type, scope, source = (old_state.transaction_type, old_state.scope, old_state.source)
        client.delete(
            f"/api/api/transactionconfiguration/types/{source}/{transaction_type}",
            params={"scope": scope},
        )

    def deps(self) -> Sequence[Resource | Ref]:
        def add_to_unique(item):
            if item.id not in seen:
                seen.add(item.id)
                unique.append(item)

        seen = set()
        unique = []

        for movement in self.movements or []:
            if isinstance(movement.side, (SideRef, SideResource)):
                add_to_unique(movement.side)
            for p in movement.properties or []:
                add_to_unique(p.property_key)
            for m in movement.mappings or []:
                add_to_unique(m.property_key)
                if m.map_from:
                    add_to_unique(m.map_from)

        for prop in self.properties or []:
            add_to_unique(prop.property_key)

        for calc in self.calculations or []:
            if calc.side is not None:
                add_to_unique(calc.side)

        return unique
