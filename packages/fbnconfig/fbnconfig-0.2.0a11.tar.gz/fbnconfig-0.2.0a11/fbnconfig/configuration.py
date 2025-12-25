from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Dict, Union

import httpx
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, computed_field, model_validator

from .resource_abc import Ref, Resource, register_resource


class SetType(StrEnum):
    PERSONAL = "personal"
    SHARED = "shared"


@register_resource()
class SetRef(BaseModel, Ref):
    """Refer to an existing configuration set"""

    id: str = Field(None, exclude=True, init=True)
    scope: str = Field(exclude=True, init=True)
    code: str = Field(exclude=True, init=True)
    type: SetType

    def attach(self, client):
        # just check it exists
        scope = self.scope
        code = self.code
        set_type = self.type
        try:
            client.get(f"/configuration/api/sets/{set_type}/{scope}/{code}").json()
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Config set {set_type}/{scope}/{code} not found")
            else:
                raise ex


@register_resource()
class SetResource(BaseModel, Resource):
    """Manage a configuration set"""

    id: str = Field(None, exclude=True, init=True)
    scope: str = Field(init=True)
    code: str = Field(init=True)
    description: str
    type: SetType

    @computed_field(alias="id")
    def set_id(self) -> Dict[str, str]:
        return {"scope": self.scope, "code": self.code}

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # Handle API format where id is a nested object with scope/code
        if "id" in data and isinstance(data["id"], dict):
            result = data.copy()
            id = result.pop("id", None)
            result = {"scope": id["scope"], "code": id["code"]} | result
            # If there's a context id, use it
            if info.context and info.context.get("id"):
                result["id"] = info.context.get("id")
            return result
        # Handle context injection for dump/undump
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        scope = self.scope
        code = self.code
        set_type = old_state.type
        return client.get(f"/configuration/api/sets/{set_type}/{scope}/{code}").json()

    def create(self, client: httpx.Client) -> Dict[str, Any]:
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
                                  exclude={"scope", "code"})
        client.request("post", "/configuration/api/sets", json=desired)
        return {"scope": self.scope, "code": self.code, "type": self.type}

    @staticmethod
    def delete(client, old_state):
        set_type = old_state.type
        scope = old_state.scope
        code = old_state.code
        client.request("delete", f"/configuration/api/sets/{set_type}/{scope}/{code}")

    def update(self, client, old_state) -> Dict[str, Any] | None:
        if [old_state.scope, old_state.code, old_state.type] != [self.scope, self.code, self.type]:
            raise RuntimeError("Cannot change the scope, code or type on a config set")
        remote = self.read(client, old_state)
        assert remote is not None
        current = {"description": remote["description"]}
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
                                  exclude={"scope", "code"})
        desired.pop("id")
        desired.pop("type")
        if desired == current:
            return None
        client.put(f"/configuration/api/sets/{self.type}/{self.scope}/{self.code}", json=desired)
        return {"scope": self.scope, "code": self.code, "type": self.type}

    def deps(self):
        return []


def ser_set_key(value, info):
    if info.context and info.context.get("style", "api") == "dump":
        return {"$ref": value.id}
    return {"scope": value.scope, "code": value.code}


def des_set_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


SetKey = Annotated[
    SetResource | SetRef,
    BeforeValidator(des_set_key), PlainSerializer(ser_set_key)
]


@register_resource()
class ItemRef(BaseModel, Ref):
    """Reference an existing configuration item with a set"""

    id: str = Field(None, exclude=True, init=True)
    set: SetKey
    key: str
    ref: str = Field(None, exclude=False, init=False)

    def attach(self, client):
        set_type = self.set.type
        scope = self.set.scope
        code = self.set.code
        key = self.key
        try:
            get = client.get(f"/configuration/api/sets/{set_type}/{scope}/{code}/items/{key}")
            self.ref = get.json()["ref"]
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError("Config item not found")
            else:
                raise ex


class ValueType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    TEXTCOLLECTION = "textCollection"
    NUMBERCOLLECTION = "numberCollection"


@register_resource()
class ItemResource(BaseModel, Resource):
    """Manage a configuration item with a set"""

    id: str = Field(None, exclude=True, init=True)
    set: SetKey
    key: str
    ref: str = Field(None, exclude=False, init=False)
    value: Any
    value_type: ValueType
    is_secret: bool
    description: str
    block_reveal: bool = False

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        set_type = old_state.type
        scope = old_state.scope
        code = old_state.code
        key = old_state.key
        return client.get(f"/configuration/api/sets/{set_type}/{scope}/{code}/items/{key}").json()

    def create(self, client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"set"})
        set_type = self.set.type
        scope = self.set.scope
        code = self.set.code
        post = client.post(f"/configuration/api/sets/{set_type}/{scope}/{code}/items", json=desired)
        match = next((item for item in post.json()["items"] if item["key"] == self.key), None)
        if match is None:
            raise RuntimeError("Something wrong creating config item")
        self.ref = match["ref"]
        return {"scope": scope, "code": code, "type": set_type, "key": self.key}

    @staticmethod
    def delete(client, old_state):
        set_type = old_state.type
        scope = old_state.scope
        code = old_state.code
        key = old_state.key
        client.delete(f"/configuration/api/sets/{set_type}/{scope}/{code}/items/{key}")

    def update(self, client, old_state):
        set_type = self.set.type
        scope = self.set.scope
        code = self.set.code
        key = self.key
        # if the location has changed we remove the old one
        if [old_state.scope, old_state.code, old_state.type] != [scope, code, set_type]:
            self.delete(client, old_state)
            return self.create(client)
        remote = self.read(client, old_state)
        # can't update these using PUT
        if self.is_secret != remote["isSecret"] or self.value_type != remote["valueType"]:
            self.delete(client, old_state)
            return self.create(client)
        self.ref = remote["ref"]
        current = {k: v for k, v in remote.items() if k in ["description", "value", "blockReveal"]}
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"set"})
        desired = {k: v for k, v in desired.items() if k in ["description", "value", "blockReveal"]}
        if desired == current:
            return None
        client.put(f"/configuration/api/sets/{set_type}/{scope}/{code}/items/{key}", json=desired)
        return {"scope": scope, "code": code, "type": set_type, "key": self.key}

    def deps(self):
        return [self.set]


def ser_item_key(value, info):
    if info.context and info.context.get("style", "api") == "dump":
        return {"$ref": value.id}
    return value.ref


def des_item_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


ItemKey = Annotated[
    ItemResource | ItemRef,
    BeforeValidator(des_item_key), PlainSerializer(ser_item_key)
]


@register_resource()
class SystemConfigResource(BaseModel, Resource):
    """Manage a system configuration item

     The default value is used to reset the system configuration value when the resource is deleted

    Example
    -------
        >>> from fbnconfig import Deployment
        >>> from fbnconfig.configuration import SystemConfigResource
        >>> validate_instruments = SystemConfigResource(
        >>>      id="validate-instr",
        >>>      code="TransactionBooking",
        >>>      key="ValidateInstruments",
        >>>      value=True,
        >>>      description="Test from fbnconfig",
        >>>      default_value=False)
        >>> Deployment("myDeployment", [validate_instruments])

    Attributes
    ----------
    id : str
      Resource identifier; this will be used in the log to reference the item resource
    code : str
      Code of the system configuration set; System configurations exist in the 'system' scope
    key: str
        Key of the set to use
    value: Any
        Configuration item value
    default_value: Any
      The value this configuration item will be set to when the resource is deleted
    """

    id: str = Field(None, exclude=True, init=True)
    code: str = Field(init=True)
    key: str
    value: str
    default_value: Any = Field(None, exclude=True, init=True)
    description: str
    block_reveal: bool = False

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        code = old_state.code
        key = old_state.key
        get = client.get(f"/configuration/api/sets/system/{code}/items/{key}")
        return get.json()["values"][0]

    def create(self, client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"code"})
        result = client.put(
            f"/configuration/api/sets/shared/system/{self.code}/items/{self.key}", json=desired
        )
        if result is None:
            raise RuntimeError("Something wrong creating config item")
        return {"code": self.code, "key": self.key, "default_value": self.default_value}

    @staticmethod
    def delete(client, old_state):
        if old_state.default_value is None:
            pass  # can't delete system config, using default values as deleted instead
        else:
            desired = {"value": old_state.default_value}
            client.put(
                f"/configuration/api/sets/shared/system/{old_state.code}/items/{old_state.key}",
                json=desired,
            )

    def update(self, client, old_state) -> Union[None, Dict[str, Any]]:
        code = self.code
        key = self.key

        if self.key != old_state.key or code != old_state.code:
            self.delete(client, old_state)
            return self.create(client)

        remote = self.read(client, old_state)
        current = {k: v for k, v in remote.items() if k in ["description", "value", "blockReveal"]}
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"code"})
        desired = {k: v for k, v in desired.items() if k in ["description", "value", "blockReveal"]}
        if desired == current:
            return None
        client.put(f"/configuration/api/sets/shared/system/{code}/items/{key}", json=desired)
        return {"code": code, "key": self.key, "default_value": self.default_value}

    def deps(self):
        return []
