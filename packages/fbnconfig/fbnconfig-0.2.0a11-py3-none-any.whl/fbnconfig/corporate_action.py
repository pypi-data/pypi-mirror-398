import json
import string
from hashlib import sha256
from typing import Any, Dict, List

import httpx
from pydantic import BaseModel, Field, field_validator, model_validator

from .resource_abc import CamelAlias, Resource, register_resource
from .urlfmt import Urlfmt

u: string.Formatter = Urlfmt("/api/api/corporateactionsources")


@register_resource()
class CorporateActionSourceResource(CamelAlias, BaseModel, Resource):
    id: str = Field(init=True, exclude=True)
    scope: str
    code: str
    display_name: str
    description: str | None = None
    instrument_scopes: List[str] | None = None

    @field_validator("instrument_scopes")
    @classmethod
    def validate_instrument_scopes(cls, v):
        if v is not None and len(v) > 1:
            raise ValueError("instrument_scopes can have at most one element")
        return v

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # promote scope and code from id dict if present
        if isinstance(data.get("id"), dict):
            # promote scope and code from id dict
            data = data | data["id"]
            data.pop("id", None)
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client: httpx.Client, old_state):
        filter_query = f"id.scope eq '{old_state.scope}' and id.code eq '{old_state.code}'"
        url = u.format("{base}")
        response = client.get(url, params={"filter": filter_query})
        results = response.json()["values"]
        if not results or len(results) == 0:
            return None
        return results[0]

    def create(self, client: httpx.Client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        client.post(u.format("{base}"), json=desired)
        return {"scope": self.scope, "code": self.code, "content_hash": content_hash}

    @staticmethod
    def delete(client: httpx.Client, old_state):
        scope = old_state.scope
        code = old_state.code
        client.delete(u.format("{base}/{scope}/{code}", scope=scope, code=code))

    def update(self, client: httpx.Client, old_state):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        sorted_desired = json.dumps(desired, sort_keys=True)
        desired_hash = sha256(sorted_desired.encode()).hexdigest()
        if desired_hash == old_state.content_hash:
            return None
        # there is no update on a CAS. Have to start again.
        self.delete(client, old_state)
        return self.create(client)

    def deps(self):
        return []
