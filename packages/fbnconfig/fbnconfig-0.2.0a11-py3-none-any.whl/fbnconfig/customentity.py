from __future__ import annotations

import copy
import json
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Any, ClassVar, Dict, List

import httpx
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    model_serializer,
    model_validator,
)

from . import property  # type: noqa
from .properties import MetricValue, PropertyValue, PropertyValueDict
from .resource_abc import CamelAlias, Ref, Resource, register_resource
from .urlfmt import Urlfmt

# force these to be used so they appear in the customentity namespace
_ = [property, PropertyValue, MetricValue]

# Context key for reference resolution
REFS_CONTEXT_KEY = "$refs"


class CollectionType(StrEnum):
    SINGLE = "Single"
    ARRAY = "Array"


class LifeTime(StrEnum):
    PERPETUAL = "Perpetual"
    TIMEVARIANT = "TimeVariant"


class FieldType(StrEnum):
    STRING = "String"
    BOOLEAN = "Boolean"
    DATE_TIME = "DateTime"
    DECIMAL = "Decimal"


class FieldDefinition(CamelAlias, BaseModel):
    name: str
    lifetime: LifeTime
    type: FieldType
    collection_type: CollectionType = CollectionType.SINGLE
    required: bool
    description: str = ""


# These are optional in the API create and will be given default values. When read is called
# they will not be returned if they have the default value
DEFAULT_FIELD = {"collectionType": "Single", "description": ""}


@register_resource()
class EntityTypeResource(CamelAlias, BaseModel, Resource):
    id: str = Field(exclude=True)
    entity_type_name: str
    display_name: str
    description: str
    field_schema: List[FieldDefinition]

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state) -> Dict[str, Any]:
        entity_type = old_state.entitytype
        return client.request("get", f"/api/api/customentities/entitytypes/{entity_type}").json()

    def create(self, client: httpx.Client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        res = client.request("POST", "/api/api/customentities/entitytypes", json=desired).json()
        return {"entitytype": res["entityType"]}

    def update(self, client: httpx.Client, old_state):
        remote = self.read(client, old_state)
        # enrich remote fields with the default values if not present
        remote["fieldSchema"] = [rem | DEFAULT_FIELD for rem in remote["fieldSchema"]]
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        effective = remote | copy.deepcopy(desired)
        for i in range(0, len(self.field_schema)):
            if i < len(remote["fieldSchema"]):
                eff_field = remote["fieldSchema"][i] | desired["fieldSchema"][i]
                effective["fieldSchema"][i] = eff_field
        if effective == remote:
            return None
        res = client.request(
            "PUT", f"/api/api/customentities/entitytypes/{old_state.entitytype}", json=desired
        ).json()
        return {"entitytype": res["entityType"]}

    @staticmethod
    def delete(client, old_state):
        raise RuntimeError("Cannot delete a custom entity definition")

    def deps(self):
        return []


class EntityTypeRef(CamelAlias, BaseModel, Ref):
    id: str = Field(exclude=True)
    entity_type_name: str

    def attach(self, client):
        entity_type = self.entity_type_name
        try:
            client.get(f"/api/api/customentities/entitytypes/{entity_type}").json()
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Custom Entity Definition {entity_type} does not exist")
            else:
                raise ex


def ser_entitytype_key(value, info):
    if info.context and info.context.get("style", "api") == "dump":
        return {"$ref": value.id}
    return "~" + value.entity_type_name


def des_entitytype_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get(REFS_CONTEXT_KEY):
        ref = info.context[REFS_CONTEXT_KEY][value["$ref"]]
        return ref
    return value


EntityTypeKey = Annotated[
    EntityTypeResource | EntityTypeRef,
    BeforeValidator(des_entitytype_key), PlainSerializer(ser_entitytype_key)
]


class EntityField(CamelAlias, BaseModel):
    effective_from: str | None = None
    effective_to: str | None = None
    name: str
    value: Any


class EntityIdentifier(CamelAlias, BaseModel):
    effective_from: str | None = None
    effective_to: str | None = None
    identifier_type: property.DefinitionRef | property.DefinitionResource
    identifier_value: str

    @model_serializer()
    def ser_model(self, info):
        style = info.context.get("style", "api") if info.context else "api"
        if style == "dump":
            return {
                "identifierType": {"$ref": self.identifier_type.id},
                "identifierValue": self.identifier_value,
            }
        return {
            "identifierScope": self.identifier_type.scope,
            "identifierType": self.identifier_type.code,
            "identifierValue": self.identifier_value
        }

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info):
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get(REFS_CONTEXT_KEY):
            ident_type = data["identifierType"]
            if isinstance(ident_type, dict) and "$ref" in ident_type:
                ref_id = ident_type["$ref"]
                return data | {"identifierType": info.context[REFS_CONTEXT_KEY][ref_id]}
            elif isinstance(ident_type, str):
                return data | {"identifierType": info.context[REFS_CONTEXT_KEY][ident_type]}
        return data


@register_resource()
class EntityResource(CamelAlias, BaseModel, Resource):
    id: str = Field(exclude=True)
    fields: List[EntityField]
    identifiers: List[EntityIdentifier] = Field(min_length=1)
    entity_type: EntityTypeKey
    description: str
    display_name: str
    properties: PropertyValueDict | None = None
    u: ClassVar = Urlfmt("/api/api/customentities")

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info):
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def create(self, client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"entity_type"})
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        i0 = desired["identifiers"][0]
        url = self.u.format("{base}/~{type}", type=self.entity_type.entity_type_name)
        client.post(url, json=desired)
        return {
            "entity_type": self.entity_type.entity_type_name,
            "identifier_scope": i0["identifierScope"],
            "identifier_type": i0["identifierType"],
            "identifier_value": i0["identifierValue"],
            "content_hash": content_hash
        }

    def read(self, client, old_state) -> Dict:
        url = self.u.format("{base}/~{type}/{idtype}/{idvalue}",
            type=old_state.entity_type,
            idtype=old_state.identifier_type,
            idvalue=old_state.identifier_value,
        )
        res = client.get(url, params={"identifierScope": old_state.identifier_scope}).json()
        res.pop("href", None)
        res.pop("version", None)
        res.pop("relationships", None)
        return res

    def update(self, client, old_state):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
                                  exclude={"id", "scope", "entity_type"})
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        if old_state.content_hash == content_hash:
            return None
        # if the type or previously used identifier has changes delete and recreate
        newid = [
            i for i in desired["identifiers"]
             if i["identifierType"] == old_state.identifier_type and
                i["identifierScope"] == old_state.identifier_scope and
                i["identifierValue"] == old_state.identifier_value
        ]
        if len(newid) != 1 or self.entity_type.entity_type_name != old_state.entity_type:
            self.delete(client, old_state)
            return self.create(client)
        url = self.u.format("{base}/~{type}", type=self.entity_type.entity_type_name)
        client.post(url, json=desired)
        i0 = desired["identifiers"][0]
        return {
            "entity_type": self.entity_type.entity_type_name,
            "identifier_scope": i0["identifierScope"],
            "identifier_type": i0["identifierType"],
            "identifier_value": i0["identifierValue"],
            "content_hash": content_hash
        }

    @staticmethod
    def delete(client, old_state):
        url = EntityResource.u.format("{base}/~{type}/{idtype}/{idvalue}",
            type=old_state.entity_type,
            idtype=old_state.identifier_type,
            idvalue=old_state.identifier_value,
        )
        client.delete(url, params={"identifierScope": old_state.identifier_scope})

    def deps(self):
        res = [self.entity_type] + [i.identifier_type for i in self.identifiers]
        if self.properties:
            res.extend([p.property_key for p in self.properties])
        return res
