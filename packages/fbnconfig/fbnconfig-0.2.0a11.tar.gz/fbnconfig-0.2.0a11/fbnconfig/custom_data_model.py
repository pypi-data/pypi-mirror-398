from __future__ import annotations

import json
import string
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Any, Dict, List

import httpx
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, model_validator

from .coretypes import ResourceId
from .property import PropertyKey
from .resource_abc import CamelAlias, Ref, Resource, register_resource
from .urlfmt import Urlfmt

url: string.Formatter = Urlfmt("api/api/datamodel")
DATA_MODEL_URL_FORMAT = "{base}/{entity_type}"
FULL_DATA_MODEL_URL = DATA_MODEL_URL_FORMAT + "/{scope}/{code}"


class SortOrder(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


class DataModelProperty(CamelAlias, BaseModel):
    property_key: PropertyKey
    required: bool | None


class IdentifierType(CamelAlias, BaseModel):
    identifier_key: str
    required: bool | None


class AttributeAlias(CamelAlias, BaseModel):
    attribute_name: str
    attribute_alias: str


class RecommendedSortBy(CamelAlias, BaseModel):
    attribute_name: str
    sort_order: SortOrder | None


def ser_parent_data_model(value, info):
    """Serialize parent data model reference."""
    if info.context and info.context.get("style", "api") == "dump":
        if isinstance(value, (Resource, Ref)):
            return {"$ref": value.id}
        return value
    if isinstance(value, (CustomDataModelResource, CustomDataModelRef)):
        return {"scope": value.resource_id.scope, "code": value.resource_id.code}
    return value


def des_parent_data_model(value, info):
    """Deserialize parent data model reference."""
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs") and "$ref" in value:
        ref = info.context["$refs"][value["$ref"]]
        return ref
    # Handle ResourceId format
    if "scope" in value and "code" in value:
        return value
    return value


ParentDataModelKey = Annotated[
    "CustomDataModelResource | CustomDataModelRef | ResourceId | None",
    BeforeValidator(des_parent_data_model),
    PlainSerializer(ser_parent_data_model),
]


@register_resource()
class CustomDataModelRef(CamelAlias, BaseModel, Ref):
    """Reference to an existing custom data model.

    Example
    -------
    >>> from fbnconfig.custom_data_model import CustomDataModelRef
    >>> model_ref = CustomDataModelRef(
    ...     id="my_ref",
    ...     entity_type="Instrument",
    ...     resource_id=ResourceId(scope="MyScope", code="MyModel")
    ... )
    """

    id: str = Field(exclude=True)
    entity_type: str
    resource_id: ResourceId

    def attach(self, client: httpx.Client):
        """Verify the custom data model exists."""
        try:
            (
                client.get(
                    url.format(
                        FULL_DATA_MODEL_URL,
                        entity_type=self.entity_type,
                        scope=self.resource_id.scope,
                        code=self.resource_id.code,
                    )
                ),
            )

        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(
                    f"CustomDataModel {self.entity_type}/{self.resource_id.scope}/"
                    f"{self.resource_id.code} not found"
                )
            else:
                raise ex


@register_resource()
class CustomDataModelResource(CamelAlias, BaseModel, Resource):
    """Resource describing a LUSID Custom Data Model.

    Creates a custom data model if it doesn't exist and updates if it has changed.
    Custom data models define validation rules, required properties, and identifiers
    for LUSID entities.

    Example
    -------
    >>> from fbnconfig import custom_data_model, Deployment
    >>> from fbnconfig.coretypes import ResourceId
    >>> model = custom_data_model.CustomDataModelResource(
    ...     id="my_model",
    ...     entity_type="Instrument",
    ...     resource_id=ResourceId(scope="MyScope", code="MyModel"),
    ...     display_name="My Custom Model",
    ...     description="A custom data model for instruments",
    ...     conditions="InstrumentDefinition.InstrumentType eq 'bond'",
    ...     properties=[
    ...         custom_data_model.DataModelProperty(
    ...             property_key="Instrument/MyScope/Rating",
    ...             required=True
    ...         )
    ...     ]
    ... )
    >>> Deployment("my_deployment", [model])

    Attributes
    ----------
    id : str
        Resource identifier; used in the log to reference the custom data model resource
    entity_type : str
        The entity type this model applies to (e.g., "Instrument", "Portfolio")
    resource_id : ResourceId
        The resource identifier containing scope and code
    display_name : str
        The display name for the custom data model
    description : str
        A description of the custom data model
    parent_data_model : ParentDataModelKey, optional
        Reference to a parent data model to inherit from
    conditions : str, optional
        Filter conditions for when this model applies
    properties : List[DataModelProperty], optional
        List of properties required or validated by this model
    identifier_types : List[IdentifierType], optional
        List of identifier types required or validated by this model
    attribute_aliases : List[AttributeAlias], optional
        List of attribute alias mappings
    recommended_sort_by : List[RecommendedSortBy], optional
        Recommended sorting configuration
    """

    id: str = Field(exclude=True)
    entity_type: str = Field(exclude=True)  # Path parameter, not in body
    resource_id: ResourceId = Field(serialization_alias="id")
    display_name: str
    description: str
    parent_data_model: ParentDataModelKey = None
    conditions: str | None = None
    properties: List[DataModelProperty] | None = None
    identifier_types: List[IdentifierType] | None = None
    attribute_aliases: List[AttributeAlias] | None = None
    recommended_sort_by: List[RecommendedSortBy] | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data

        # Handle nested id structure from API response first (for resource_id field)
        has_resource_id_in_data = "id" in data and isinstance(data["id"], dict) and "scope" in data["id"]

        if has_resource_id_in_data:
            # This is the resource_id coming from API
            data["resource_id"] = data.pop("id")

        # Handle id and entity_type from context (for dump/undump)
        # The context "id" is the resource identifier, not the resource_id
        if info.context:
            if info.context.get("id") and "id" not in data:
                # Only set if not already consumed from API data
                data["id"] = info.context.get("id")
            if info.context.get("entity_type"):
                data["entity_type"] = info.context.get("entity_type")

        return data

    def __get_content_hash__(self) -> str:
        dump = self.model_dump(
            mode="json", exclude_none=True, by_alias=True, exclude={"entity_type", "resource_id"}
        )
        return sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()

    def read(self, client: httpx.Client, old_state) -> Dict[str, Any]:
        return client.get(
            url.format(
                FULL_DATA_MODEL_URL,
                entity_type=old_state.entity_type,
                scope=old_state.scope,
                code=old_state.code,
            )
        ).json()

    def create(self, client: httpx.Client):
        desired = self.model_dump(
            mode="json",
            exclude_none=True,
            by_alias=True,
            exclude={"entity_type"},  # entity_type is path param
        )

        remote = client.post(
            url.format(DATA_MODEL_URL_FORMAT, entity_type=self.entity_type), json=desired
        ).json()

        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "scope": self.resource_id.scope,
            "code": self.resource_id.code,
            "source_version": self.__get_content_hash__(),
            "remote_version": f"{remote['version']['asAtVersionNumber']}",
        }

    def update(self, client: httpx.Client, old_state):
        # Check if entity_type/scope/code changed (not allowed)
        if (
            self.entity_type != old_state.entity_type
            or self.resource_id.scope != old_state.scope
            or self.resource_id.code != old_state.code
        ):
            # Delete old and create new
            self.delete(client, old_state)
            return self.create(client)

        remote = self.read(client, old_state) or {}
        remote_version = f"{remote['version']['asAtVersionNumber']}"

        # Build request body (without id/resourceId for update)
        desired = self.model_dump(
            mode="json", exclude_none=True, by_alias=True, exclude={"entity_type", "resource_id"}
        )

        source_version = self.__get_content_hash__()

        # Check if content has changed using both source and remote versions
        if source_version == old_state.source_version and remote_version == old_state.remote_version:
            return None  # No change

        # Update the custom data model
        updated = client.put(
            url.format(
                FULL_DATA_MODEL_URL,
                entity_type=self.entity_type,
                scope=self.resource_id.scope,
                code=self.resource_id.code,
            ),
            json=desired,
        ).json()

        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "scope": self.resource_id.scope,
            "code": self.resource_id.code,
            "source_version": source_version,
            "remote_version": f"{updated['version']['asAtVersionNumber']}",
        }

    @staticmethod
    def delete(client: httpx.Client, old_state):
        client.delete(
            url.format(
                FULL_DATA_MODEL_URL,
                entity_type=old_state.entity_type,
                scope=old_state.scope,
                code=old_state.code,
            )
        )

    def deps(self):
        """Return dependencies."""
        deps = []
        if self.parent_data_model and isinstance(self.parent_data_model, (Resource, Ref)):
            deps.append(self.parent_data_model)
        # Add property_key dependencies from properties
        if self.properties:
            for prop_def in self.properties:
                if isinstance(prop_def.property_key, (Resource, Ref)):
                    deps.append(prop_def.property_key)
        return deps
