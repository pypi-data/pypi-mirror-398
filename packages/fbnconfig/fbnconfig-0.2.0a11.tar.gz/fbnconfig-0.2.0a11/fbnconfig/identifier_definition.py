from __future__ import annotations

import json
from enum import StrEnum
from hashlib import sha256
from typing import Any, Dict, Union

import httpx
from pydantic import BaseModel, Field, model_validator

from fbnconfig.property import LifeTime

from .properties import PropertyValue, PropertyValueDict
from .resource_abc import CamelAlias, Ref, Resource, register_resource

_ = PropertyValue


class SupportedDomain(StrEnum):
    Instrument = "Instrument"
    Person = "Person"
    LegalEntity = "LegalEntity"
    CustomEntity = "CustomEntity"


@register_resource()
class IdentifierDefinitionRef(BaseModel, Ref):
    """
    Reference to an identifier definition resource.

    Example
    ----------
    >>> from fbnconfig import identifier_definition
    >>> ref = identifier_definition.IdentifierDefinitionRef(
    >>>  id="identifier-def-ref",
    >>>  domain="Instrument",
    >>>  identifier_scope="id_scope",
    >>>  identifier_type="id_type")
    """

    id: str = Field(exclude=True)
    domain: SupportedDomain
    identifier_scope: str
    identifier_type: str

    def attach(self, client):
        """Attach to an existing identifier definition resource."""
        scope = self.identifier_scope
        id_type = self.identifier_type
        try:
            client.get(f"/api/api/identifierdefinitions/{self.domain}/{scope}/{id_type}")
        except httpx.HTTPStatusError as ex:
            error_message = f"Identifier Definition {self.domain}/{scope}/{id_type} does not exist"
            if ex.response.status_code == 404:
                raise RuntimeError(error_message)
            else:
                raise ex


@register_resource()
class IdentifierDefinitionResource(CamelAlias, BaseModel, Resource):
    """identifier definition resource"""

    id: str = Field(exclude=True)
    domain: SupportedDomain
    identifier_scope: str
    identifier_type: str
    life_time: LifeTime
    hierarchy_usage: str | None = None
    hierarchy_level: str | None = None
    display_name: str | None = None
    description: str | None = None
    properties: PropertyValueDict | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}

        return data

    def __get_content_hash__(self) -> str:
        dump = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        return sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()

    def read(self, client: httpx.Client, old_state) -> Dict[str, Any]:
        domain = old_state.domain
        scope = old_state.identifier_scope
        id_type = old_state.identifier_type
        response = client.get(f"/api/api/identifierdefinitions/{domain}/{scope}/{id_type}")

        result = response.json()
        # Remove unnecessary fields
        result.pop("href", None)

        return result

    def create(self, client: httpx.Client) -> Dict[str, Any]:
        body = self.model_dump(mode="json", exclude_none=True, by_alias=True)

        response = client.post("/api/api/identifierdefinitions", json=body)
        result = response.json()

        # Remove unnecessary fields
        result.pop("href", None)

        source_version = self.__get_content_hash__()
        remote_version = result["version"]["asAtVersionNumber"]

        return {
            "domain": self.domain,
            "identifier_scope": self.identifier_scope,
            "identifier_type": self.identifier_type,
            "source_version": source_version,
            "remote_version": remote_version
        }

    def update(self, client: httpx.Client, old_state) -> Union[None, Dict[str, Any]]:
        current_identity_tuple = (self.domain, self.identifier_scope, self.identifier_type)
        old_state_tuple = (old_state.domain, old_state.identifier_scope, old_state.identifier_type)

        if current_identity_tuple != old_state_tuple:
            self.delete(client, old_state)
            return self.create(client)

        source_hash = self.__get_content_hash__()
        remote = self.read(client, old_state)
        remote_hash = remote["version"]["asAtVersionNumber"]

        if remote_hash == old_state.remote_version and source_hash == old_state.source_version:
            return None

        #  Exclude fields not needed in put call
        body = self.model_dump(
            mode="json",
            exclude_none=True,
            by_alias=True,
            exclude={"domain", "identifier_scope", "identifier_type"}
        )

        scope = self.identifier_scope
        id_type = self.identifier_type

        response = client.put(
            f"/api/api/identifierdefinitions/{self.domain}/{scope}/{id_type}",
            json=body)
        result = response.json()

        # Remove unnecessary fields
        result.pop("href", None)

        return {
            "domain": self.domain,
            "identifier_scope": self.identifier_scope,
            "identifier_type": self.identifier_type,
            "source_version": source_hash,
            "remote_version": result["version"]["asAtVersionNumber"]
        }

    @staticmethod
    def delete(client: httpx.Client, old_state) -> None:

        domain = old_state.domain
        scope = old_state.identifier_scope
        id_type = old_state.identifier_type
        client.delete(f"/api/api/identifierdefinitions/{domain}/{scope}/{id_type}")

    def deps(self):
        deps = []
        if self.properties is None:
            return deps

        for perp_prop in self.properties:
            deps.append(perp_prop.property_key)

        return deps
