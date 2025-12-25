from __future__ import annotations

import copy
import json
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Any, Dict, List, Literal, Optional, Sequence, Union

import httpx
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    field_serializer,
    field_validator,
    model_validator,
)

from .resource_abc import CamelAlias, Ref, Resource, register_resource


class ActionId(CamelAlias, BaseModel):
    """ActionId resource used with IdSelector

    Example
    -------
    >>> from fbnconfig.access import ActionId
    >>> ActionId(scope="myscope", activity="execute", entity="Feature")

    -------
    """

    scope: str
    activity: str
    entity: str


class MatchAllSelector(CamelAlias, BaseModel):
    type_name: Literal["matchAllSelectorDefinition"] = Field("matchAllSelectorDefinition", init=False)
    actions: List[ActionId]
    name: Optional[str] = None
    description: Optional[str] = None


class IdSelector(CamelAlias, BaseModel):
    """IdSelector resource used with PolicyResource

    Example
    -------
    >>> from fbnconfig.access import IdSelector, ActionId
    >>> IdSelector(
            name="feature_id_selector",
            description="feature_id_selector",
            identifier={"scope": "myscope", "code": "mycode"},
            actions=[ActionId(scope="myscope", activity="execute", entity="Feature")])
    """
    type_name: Literal["idSelectorDefinition"] = Field("idSelectorDefinition", init=False)
    identifier: Dict[str, str]
    actions: List[ActionId]
    name: Optional[str] = None
    description: Optional[str] = None


class MetadataExpression(CamelAlias, BaseModel):
    metadata_key: str
    operator: str
    text_value: str | None


class MetadataSelector(CamelAlias, BaseModel):
    type_name: Literal["metadataSelectorDefinition"] = Field("metadataSelectorDefinition", init=False)
    actions: List[ActionId]
    name: str | None = None
    description: str | None = None
    expressions: List[MetadataExpression]


class PolicySelector(CamelAlias, BaseModel):
    type_name: Literal["policySelectorDefinition"] = Field("policySelectorDefinition", init=False)
    actions: List[ActionId]
    name: str | None = None
    description: str | None = None
    identity_restriction: Dict[str, str] | None = None
    restriction_selectors: Sequence[Selector] | None = None

    @field_serializer("restriction_selectors", when_used="always")
    def ser_selectors(self, selectors: Any, info):
        if selectors is None:
            return None
        if info.context and info.context.get("style") == "dump":
            # dump mode: serialise them fully
            return selectors
        # convert array of selectors to dict for the api
        return [
            {selector.type_name: selector.model_dump(exclude=["type_name"], by_alias=True)}
            for selector in selectors
        ]

    @field_validator("restriction_selectors", mode="before")
    @classmethod
    def des_selectors(cls, data, info) -> Sequence[Selector] | Dict | None:
        if data is None:
            return None
        style = info.context.get("style", "api") if info.context else "api"
        if style == "api" and isinstance(data, dict):
            data = [value | {"typeName": key} for key, value in data.items()]
        return data


Selector = Annotated[
    IdSelector | MatchAllSelector | MetadataSelector | PolicySelector,
    Field(discriminator="type_name")
]


class WhenSpec(CamelAlias, BaseModel):
    """
    WhenSpec resource used with PolicyResource

    Example
    -------
    >>> from fbnconfig.access import WhenSpec
    >>>WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00")

    Notes
    -------
    When deactivate is not supplied, the policy is valid from time in activate until end of time
    """

    activate: str
    deactivate: Optional[str] = None


class Grant(StrEnum):
    """Type of grant used with PolicyResource

    Available values are: Allow, Deny and Undefined
    """

    ALLOW = "Allow"
    DENY = "Deny"
    UNDEFINED = "Undefined"


@register_resource()
class PolicyRef(BaseModel, Ref):
    id: str = Field(exclude=True, init=True)
    code: str
    scope: str = "default"

    def attach(self, client):
        try:
            client.request("get", f"/access/api/policies/{self.code}", params={"scope": self.scope})
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Policy {self.scope}/{self.code} not found")
            else:
                raise ex


@register_resource()
class PolicyResource(BaseModel, Resource):
    """Manage a policy

    Attributes
    -------
    id: str
        Resource identifier
    """

    id: str = Field(exclude=True)
    code: str
    scope: str = Field("default", init=False, exclude=True)
    description: str
    applications: List[str]
    grant: Grant
    selectors: Sequence[Selector]
    when: WhenSpec

    @field_serializer("selectors", when_used="always")
    def ser_selectors(self, selectors: Any, info):
        if info.context and info.context.get("style") == "dump":
            # dump mode: serialise them fully, no backward compat required
            return selectors
        # else we're in api mode
        # backward compatible for when the user passes in their own dict
        if all([isinstance(selector, dict) for selector in selectors]):
            return selectors
        # new version: when the user passes an array of selector objects
        return [
            {selector.type_name: selector.model_dump(exclude=["type_name"], by_alias=True,
                                                     exclude_none=True)}
            for selector in selectors
        ]

    @field_validator("selectors", mode="before")
    @classmethod
    def des_selectors(cls, data, info) -> Sequence[Selector] | Dict | None:
        if data is None:
            return None
        style = info.context.get("style", "api") if info.context else "api"
        if style == "dump":
            return data
        # in api mode it's [{type: definition}, {type: definition}, ...]
        # we need [definition, definition] with the typeName field inside
        new_selectors = []
        for obj in data:
            if isinstance(obj, dict):
                new_selectors.extend([
                    value | {"typeName": key} for key, value in obj.items()
                ])
            else:
                new_selectors.append(obj)
        return new_selectors

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # promote scope and code to top for api style
        if "id" in data and isinstance(data["id"], dict):
            data = data | data["id"]
            data.pop("id", None)
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        remote = client.request(
            "get", f"/access/api/policies/{self.code}", params={"scope": self.scope}
        ).json()
        remote.pop("id")
        remote.pop("links")
        return remote

    def create(self, client: httpx.Client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        client.request("POST", "/access/api/policies", json=desired)
        return {"id": self.id, "code": self.code}

    def update(self, client: httpx.Client, old_state):
        if old_state.code != self.code:
            raise (RuntimeError("Cannot change the code on a policy"))
        get = self.read(client, old_state)
        remote = copy.deepcopy(get)
        desired = self.model_dump(
            mode="json", exclude_none=True, exclude={"scope", "code"}, by_alias=True
        )
        if (
            desired["when"].get("deactivate", None) is None
        ):  # deactivate is defaulted on the server so not a difference unless we set it
            remote["when"].pop("deactivate")
        if desired == remote:
            return None
        client.request("put", f"/access/api/policies/{self.code}", json=desired)
        return {"id": self.id, "code": self.code}

    @staticmethod
    def delete(client, old_state):
        client.request("DELETE", f"/access/api/policies/{old_state.code}")

    def deps(self):
        return []


def ser_policy_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return {"scope": value.scope, "code": value.code}


def des_policy_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


PolicyKey = Annotated[
    PolicyResource | PolicyRef,
    BeforeValidator(des_policy_key), PlainSerializer(ser_policy_key)
]


@register_resource()
class PolicyCollectionRef(BaseModel, Ref):
    id: str = Field(exclude=True, init=True)
    code: str
    scope: str = "default"

    def attach(self, client):
        try:
            client.get(f"/access/api/policycollections/{self.code}", params={"scope": self.scope})
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"PolicyCollection {self.scope}/{self.code} not found")
            else:
                raise ex


@register_resource()
class PolicyCollectionResource(CamelAlias, BaseModel, Resource):
    id: str = Field(exclude=True)
    # collections can be referenced by scope, but it can't be specified
    scope: str = Field("default", init=False, exclude=True)
    code: str
    description: str | None = None
    policies: Sequence[PolicyKey] = []
    policy_collections: Sequence[PolicyCollectionKey] | None = []
    metadata: Dict[str, List[str]] | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # promote scope and code to top for api style
        if "id" in data and isinstance(data["id"], dict):
            data = data | data["id"]
            data.pop("id", None)
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state) -> Dict[str, Any]:
        scope = old_state.scope
        code = old_state.code
        params = {"scope": scope} if scope is not None else None
        remote = client.get(f"/access/api/policycollections/{code}", params=params).json()
        remote.pop("links")
        remote.pop("id")
        return remote

    def create(self, client) -> Dict[str, Any]:
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        res = client.request("POST", "/access/api/policycollections", json=desired)
        return res.json()["id"]

    def update(self, client, old_state) -> Dict[str, Any] | None:
        if old_state.code != self.code:
            self.delete(client, old_state)
            return self.create(client)
        remote = self.read(client, old_state)
        desired = self.model_dump(mode="json", exclude_none=True, exclude={"code"}, by_alias=True)
        if desired == remote:
            return None
        client.request("put", f"/access/api/policycollections/{self.code}", json=desired)
        return {"code": self.code, "scope": old_state.scope}

    @staticmethod
    def delete(client, old_state):
        client.request("DELETE", f"/access/api/policycollections/{old_state.code}")

    def deps(self) -> List[Resource | Ref]:
        deps: List[Resource | Ref] = []
        for pol in self.policies:
            deps.append(pol)
        if self.policy_collections:
            for col in self.policy_collections:
                deps.append(col)
        return deps


def ser_policycollection_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return {"scope": value.scope, "code": value.code}


def des_policycollection_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


PolicyCollectionKey = Annotated[
    PolicyCollectionResource | PolicyCollectionRef,
    BeforeValidator(des_policycollection_key), PlainSerializer(ser_policycollection_key)
]


# not an fbnconfig Resource despite the name
class PolicyIdRoleResource(CamelAlias, BaseModel):
    """Used to refer to a policy resource in a role resource"""

    policies: Sequence[PolicyKey] | None = []
    policy_collections: Sequence[PolicyCollectionKey] | None = []


class Permission(StrEnum):
    """Permission type used on a role resource"""

    READ = "Read"
    WRITE = "Write"
    EXECUTE = "Execute"
    UPDATE = "Update"


class NonTransitiveSupervisorRoleResource(BaseModel):
    roles: Sequence[RoleKey]


class RoleResourceRequest(BaseModel, CamelAlias):
    non_transitive_supervisor_role_resource: NonTransitiveSupervisorRoleResource | None = None
    policy_id_role_resource: PolicyIdRoleResource | None = None


class RoleRef(BaseModel, Ref):
    """Reference an existing Role"""

    id: str = Field(exclude=True, init=True)
    scope: str = "default"
    code: str

    def attach(self, client):
        try:
            params = {"scope": self.scope}
            client.request("get", f"/access/api/roles/{self.code}", params=params)
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Role {self.scope}/{self.code} not found")
            else:
                raise ex


@register_resource()
class RoleResource(CamelAlias, BaseModel, Resource):
    """Define a role resource"""

    id: str = Field(exclude=True)
    scope: str = Field("default", exclude=True, init=False)
    code: str
    description: str | None = None
    resource: None | RoleResourceRequest = None
    when: WhenSpec
    permission: Permission
    role_hierarchy_index: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # promote scope and code to top for api style
        if "id" in data and isinstance(data["id"], dict):
            data = data | data["id"]
            data.pop("id", None)
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        get = client.request("get", f"/access/api/roles/{old_state.code}")
        remote = get.json()
        remote.pop("id")
        remote.pop("links")
        return remote

    def create(self, client):
        body = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        client.request("POST", "/access/api/roles", json=body)
        return {"id": self.id, "code": self.code}

    def update(self, client: httpx.Client, old_state):
        if old_state.code != self.code:
            raise (RuntimeError("Cannot change the code on a role"))

        remote = self.read(client, old_state)
        desired = self.model_dump(mode="json", exclude={"code"}, exclude_none=True, by_alias=True)
        remote["when"].pop(
            "deactivate"
        )  # deactivate is defaulted on the server so not a difference unless we set it
        remote.pop("roleHierarchyIndex")  # set by the server
        if desired == remote:
            return None
        client.request("put", f"/access/api/roles/{self.code}", json=desired)
        return {"id": self.id, "code": self.code}

    @staticmethod
    def delete(client, old_state):
        client.request("DELETE", f"/access/api/roles/{old_state.code}")

    def deps(self):
        if self.resource is None or self.resource.policy_id_role_resource is None:
            return []
        res = self.resource.policy_id_role_resource
        pol_deps = [v for v in res.policies] if res.policies is not None else []
        col_deps = [v for v in res.policy_collections] if res.policy_collections is not None else []
        return pol_deps + col_deps


@register_resource()
class PolicyTemplateRef(BaseModel, Ref):
    """Reference an existing policy template

    Example
    -------
    >>> from fbnconfig.access import PolicyTemplateRef
    >>> PolicyTemplateRef = PolicyTemplateRef(id="policy_templates", code="code_example")
    """

    id: str = Field(exclude=True, init=True)
    code: str
    scope: str = "default"

    def attach(self, client):
        try:
            params = {"scope": self.scope}
            client.request("get", f"/access/api/policytemplates/{self.code}", params=params)
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Policy Template {self.scope}/{self.code} not found")
            else:
                raise ex


class TemplatedSelector(BaseModel):
    application: str
    tag: str
    selector: Selector

    @field_serializer("selector")
    def ser_selector(self, value: Selector, info) -> Any:
        style = info.context.get("style", "api") if info.context else "api"
        if style == "api":
            serialized = value.model_dump(exclude={"type_name"}, by_alias=True)
            return {
                value.type_name: serialized
            }
        else:
            return value

    @field_validator("selector", mode="before")
    @classmethod
    def des_selectors(cls, data, info) -> Sequence[Selector] | Dict | None:
        if data is None:
            return None
        style = info.context.get("style", "api") if info.context else "api"
        if style == "api" and isinstance(data, dict):
            unpacked = [value | {"typeName": key} for key, value in data.items()]
            data = unpacked[0]  # this is a dict with one element
        return data


@register_resource()
class PolicyTemplateResource(BaseModel, Resource):
    """Define a policy template in LUSID"""

    id: str = Field(exclude=True)
    display_name: str
    scope: str = Field("default", init=False, exclude=True)
    code: str
    description: str
    templated_selectors: List[TemplatedSelector]

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # promote scope and code to top for api style
        if "id" in data and isinstance(data["id"], dict):
            data = data | data["id"]
            data.pop("id", None)
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def __get_content_hash__(self) -> str:
        dump = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        return sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()

    def read(self, client: httpx.Client, old_state) -> None | Dict[str, Any]:
        return client.get(f"/access/api/policytemplates/{old_state.code}").json()

    def create(self, client: httpx.Client) -> Optional[Dict[str, Any]]:
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        response = client.post("/access/api/policytemplates", json=desired).json()
        return {
            "id": self.id,
            "code": self.code,
            "source_version": self.__get_content_hash__(),
            "remote_version": sha256(json.dumps(response, sort_keys=True).encode()).hexdigest(),
        }

    def update(self, client: httpx.Client, old_state) -> Union[None, Dict[str, Any]]:
        if old_state.code != self.code:
            raise (RuntimeError("Cannot change the code on a policy template"))

        source_hash = self.__get_content_hash__()
        remote = self.read(client, old_state)
        remote_hash = sha256(json.dumps(remote, sort_keys=True).encode()).hexdigest()

        if remote_hash == old_state.remote_version and source_hash == old_state.source_version:
            return None

        desired = self.model_dump(mode="json", exclude={"code"}, exclude_none=True, by_alias=True)
        response = client.put(f"/access/api/policytemplates/{self.code}", json=desired).json()
        return {
            "id": self.id,
            "code": self.code,
            "source_version": self.__get_content_hash__(),
            "remote_version": sha256(json.dumps(response, sort_keys=True).encode()).hexdigest(),
        }

    @staticmethod
    def delete(client: httpx.Client, old_state) -> None:
        client.delete(f"/access/api/policytemplates/{old_state.code}")

    def deps(self):
        return []


def ser_role_key(value, info):
    if info.context and info.context.get("style", "api") == "dump":
        return {"$ref": value.id}
    return {"scope": value.scope, "code": value.code}


def des_role_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


RoleKey = Annotated[
    RoleResource | RoleRef,
    BeforeValidator(des_role_key), PlainSerializer(ser_role_key)
]
