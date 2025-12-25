from __future__ import annotations

from typing import Any, Dict

import httpx
from pydantic import BaseModel, Field, model_validator

from fbnconfig.resource_abc import CamelAlias, Resource, register_resource


@register_resource()
class SequenceResource(CamelAlias, BaseModel, Resource):
    resource_type: str = Field(default="SequenceResource", exclude=True)
    id: str = Field(exclude=True)

    scope: str
    code: str
    increment: int | None = None
    min_value: int | None = None
    max_value: int | None = None
    start: int | None = None
    cycle: bool | None = None
    pattern: str | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Dict[str, Any], info) -> Dict[str, Any]:
        if isinstance(data.get("id"), dict):
            # promote scope and code
            data = data | data.pop("id")
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state) -> Dict[str, Any]:
        return client.request("get", f"/api/api/sequences/{self.scope}/{self.code}").json()

    def create(self, client: httpx.Client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
            exclude={"scope"})
        client.request("POST", f"/api/api/sequences/{self.scope}", json=desired)
        return {"scope": self.scope, "code": self.code}

    def update(self, client: httpx.Client, old_state):
        if [old_state.scope, old_state.code] != [self.scope, self.code]:
            raise (RuntimeError("Cannot change the scope/code on a sequence"))
        remote = self.read(client, old_state)
        desired = self.model_dump(
            mode="json", exclude_none=True, exclude={"scope", "code"}, by_alias=True
        )
        effective = remote | desired
        if effective == remote:
            return None
        raise RuntimeError("Cannot modify a sequence")

    @staticmethod
    def delete(client, old_state):
        raise RuntimeError("Cannot delete a sequence")

    def deps(self):
        return []
