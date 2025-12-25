from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from types import SimpleNamespace
from typing import Annotated, Any, Dict, Sequence

import httpx
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, model_validator

from .resource_abc import Ref, Resource, register_resource


class Visibility(StrEnum):
    PERSONAL = "personal"
    SHARED = "shared"


class WorkspaceRef(BaseModel, Ref):
    id: str = Field(exclude=True, init=True)
    visibility: Visibility
    name: str

    def attach(self, client):
        try:
            client.request(
                "get", f"/api/api/workspaces/{self.visibility.value}/{self.name}"
            )
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(
                    f"Workspace {self.visibility.value}/{self.name} not found"
                )
            else:
                raise ex


@register_resource()
class WorkspaceResource(BaseModel, Resource):
    """Manage a workspace"""

    id: str = Field(exclude=True)
    visibility: Visibility
    name: str
    description: str

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(
        self, client: httpx.Client, old_state: SimpleNamespace
    ) -> None | Dict[str, Any]:
        workspace_path = f"{old_state.visibility}/{old_state.name}"
        response = client.get(f"/api/api/workspaces/{workspace_path}").json()
        for key in ["links", "version"]:
            response.pop(key, None)
        return response

    def create(self, client: httpx.Client) -> Dict[str, Any]:
        desired = self.model_dump(mode="json", exclude_none=True, exclude={"visibility"}, by_alias=True)
        sorted_json = json.dumps(desired, sort_keys=True)
        content_hash = hashlib.sha256(sorted_json.encode()).hexdigest()
        client.request("POST", f"/api/api/workspaces/{self.visibility.value}", json=desired)
        return {"visibility": self.visibility, "name": self.name, "content_hash": content_hash}

    def update(self, client: httpx.Client, old_state: SimpleNamespace) -> None | Dict[str, Any]:
        if [old_state.visibility, old_state.name] != [self.visibility, self.name]:
            state = self.create(client)
            self.delete(client, old_state)
            return state
        desired = self.model_dump(mode="json", exclude_none=True, exclude={"visibility"}, by_alias=True)
        sorted_json = json.dumps(desired, sort_keys=True)
        content_hash = hashlib.sha256(sorted_json.encode()).hexdigest()
        if content_hash == getattr(old_state, "content_hash", None):
            return None
        client.request("put", f"/api/api/workspaces/{self.visibility.value}/{self.name}", json=desired)
        return {"visibility": self.visibility, "name": self.name, "content_hash": content_hash}

    @staticmethod
    def delete(client, old_state):
        client.request(
            "delete",
            f"/api/api/workspaces/{old_state.visibility}/{old_state.name}",
        )

    def deps(self) -> Sequence[Resource | Ref]:
        return []


def ser_workspace_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return value


def des_workspace_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


WorkspaceKey = Annotated[
    WorkspaceResource | WorkspaceRef,
    BeforeValidator(des_workspace_key), PlainSerializer(ser_workspace_key)
]


class WorkspaceItemRef(BaseModel, Ref):
    id: str = Field(exclude=True)
    workspace: WorkspaceKey
    group: str
    name: str

    def attach(self, client):
        viz = self.workspace.visibility.value
        name = self.workspace.name
        try:
            client.request(
                "get",
                f"/api/api/workspaces/{viz}/{name}/items/{self.group}/{self.name}",
            )
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(
                    f"Workspace item {viz}/{name}/items/{self.group}/{self.name} not found"
                )
            else:
                raise ex


@register_resource()
class WorkspaceItemResource(BaseModel, Resource):
    id: str = Field(exclude=True)
    workspace: WorkspaceKey
    type: str
    group: str
    name: str
    description: str
    content: Dict[Any, Any]
    format: int

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state) -> Dict[str, Any]:
        workspace_path = f"{old_state.visibility}/{old_state.workspace_name}"
        remote = client.request(
            "get",
            f"/api/api/workspaces/{workspace_path}/items/{old_state.group}/{old_state.name}",
        ).json()
        remote.pop("version")
        remote.pop("links")
        return remote

    def create(self, client: httpx.Client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"workspace"})
        sorted_json = json.dumps(desired, sort_keys=True)
        content_hash = hashlib.sha256(sorted_json.encode()).hexdigest()
        workspace_path = f"{self.workspace.visibility.value}/{self.workspace.name}"
        client.request(
            "post", f"/api/api/workspaces/{workspace_path}/items", json=desired
        )
        return {
            "visibility": self.workspace.visibility.value,
            "group": self.group,
            "workspace_name": self.workspace.name,
            "name": self.name,
            "content_hash": content_hash,
        }

    def update(self, client: httpx.Client, old_state):
        wksp = self.workspace
        # if we have moved it to a different workspace
        if [old_state.visibility, old_state.workspace_name] != [
            wksp.visibility, wksp.name]:
            state = self.create(client)
            self.delete(client, old_state)
            return state
        # rename the item within the workspace
        if [old_state.name, old_state.group] != [self.name, self.group]:
            state = self.create(client)
            self.delete(client, old_state)
            return state
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"workspace"})
        sorted_json = json.dumps(desired, sort_keys=True)
        content_hash = hashlib.sha256(sorted_json.encode()).hexdigest()
        if content_hash == getattr(old_state, "content_hash", None):
            return None
        workspace_path = f"{self.workspace.visibility.value}/{self.workspace.name}"
        client.request(
            "put",
            f"/api/api/workspaces/{workspace_path}/items/{self.group}/{self.name}",
            json=desired,
        )
        return {
            "visibility": self.workspace.visibility,
            "workspace_name": self.workspace.name,
            "group": self.group,
            "name": self.name,
            "content_hash": content_hash,
        }

    @staticmethod
    def delete(client, old_state):
        workspace_path = f"{old_state.visibility}/{old_state.workspace_name}"
        client.request(
            "delete",
            f"/api/api/workspaces/{workspace_path}/items/{old_state.group}/{old_state.name}",
        )

    def deps(self):
        return [self.workspace]
