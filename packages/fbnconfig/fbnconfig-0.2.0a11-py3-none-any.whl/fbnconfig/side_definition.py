from __future__ import annotations

from types import SimpleNamespace
from typing import Annotated, Any, Dict, Optional, Sequence

import httpx
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, model_validator

from .property import PropertyKey
from .resource_abc import Ref, Resource, register_resource


@register_resource()
class SideRef(BaseModel, Ref):
    """Used to reference an existing side
    Example
    -------
    >>> from fbnconfig.side_definition import SideRef
    >>> side = SideRef(id="side", scope="scope", side="side")
    """

    id: str = Field(exclude=True)
    scope: str
    side: str

    def attach(self, client):
        scope, side = self.scope, self.side
        try:
            client.get(f"/api/api/transactionconfiguration/sides/{side}", params={"scope": scope})
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Side {self.side} does not exist in scope {self.scope}")
            else:
                raise ex


@register_resource()
class SideResource(BaseModel, Resource):
    """Create a side definition

    Example
    -------
    >>> from fbnconfig.side_definition import SideResource
    >>> side = SideResource(
    >>>     id="side",
    >>>     side="side",
    >>>     scope="scope",
    >>>     security="Txn:LusidInstrumentId",
    >>>     currency = "Txn:TradeCurrency",
    >>>     rate = "Txn:TradeToPortfolioRate",
    >>>     units = "Txn:Units",
    >>>     amount = "Txn:TotalConsideration",
    >>>     notional_amount = "0",
    >>>     current_face = "Txn:TotalConsideration"
    >>> )
    """

    id: str = Field(exclude=True, init=True)
    side: str
    scope: str
    security: str | PropertyKey
    currency: str | PropertyKey
    rate: str | PropertyKey
    units: str | PropertyKey
    amount: str | PropertyKey
    notional_amount: str | PropertyKey
    current_face: str | PropertyKey | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def create(self, client: httpx.Client) -> Optional[Dict[str, Any]]:
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"scope"})
        scope = self.scope
        client.put(
            f"/api/api/transactionconfiguration/sides/{self.side}", json=desired, params={"scope": scope}
        )
        return {"side": self.side, "scope": self.scope}

    def read(self, client: httpx.Client, old_state: SimpleNamespace):
        side = old_state.side
        scope = old_state.scope
        return client.get(
            f"/api/api/transactionconfiguration/sides/{side}", params={"scope": scope}
        ).json()

    def update(self, client: httpx.Client, old_state: SimpleNamespace):
        # Check for scope or name change, must delete and create
        if [old_state.side, old_state.scope] != [self.side, self.scope]:
            self.delete(client, old_state)
            return self.create(client)
        # Has there been a change?
        remote = self.read(client, old_state) or {}
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"scope"})
        effective = remote | desired
        if effective == remote:
            return None
        return self.create(client)

    @staticmethod
    def delete(client: httpx.Client, old_state: SimpleNamespace):
        side, scope = old_state.side, old_state.scope
        client.delete(f"/api/api/transactionconfiguration/sides/{side}/$delete", params={"scope": scope})

    def deps(self) -> Sequence[Resource | Ref]:
        return [
            value
            for value in (
                self.security,
                self.currency,
                self.amount,
                self.rate,
                self.units,
                self.notional_amount,
                self.current_face,
            )
            if isinstance(value, (Resource, Ref))
        ]


def ser_side_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return value.side


def des_side_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


SideKey = Annotated[
    SideResource | SideRef,
    BeforeValidator(des_side_key), PlainSerializer(ser_side_key)
]
