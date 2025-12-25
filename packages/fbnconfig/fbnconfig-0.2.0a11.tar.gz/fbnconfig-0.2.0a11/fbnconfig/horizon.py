import json
import string
from hashlib import sha256
from typing import Annotated, Any, ClassVar, Mapping, Sequence

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    model_serializer,
    model_validator,
)

from .property import PropertyKey
from .resource_abc import CamelAlias, Ref, Resource, register_resource
from .urlfmt import Urlfmt


class Trigger(BaseModel, CamelAlias):
    type: str
    cron_expression: str
    time_zone: str


@register_resource()
class IntegrationInstanceResource(BaseModel, Resource, CamelAlias):
    id: str = Field(exclude=True)
    integration_type: str
    name: str
    description: str
    enabled: bool
    triggers: Sequence[Trigger]
    details: Mapping[str, Any]
    instance_id: str | None = Field(None, exclude=True, init=False)
    u: ClassVar[string.Formatter] = Urlfmt("/horizon/api/integrations/instances")

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Any:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            context_id = info.context.get("id")
            data = data | {"id": context_id}
        return data

    def create(self, client):
        url = self.u.format("{base}")
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        desired_hash = sha256(json.dumps(desired, sort_keys=True).encode()).hexdigest()
        res = client.post(url, json=desired).json()
        self.instance_id = res["id"]
        return {
            "instanceId": res["id"],
            "content_hash": desired_hash
        }

    def read(self, client, old_state):
        instances = client.get(self.u.format("{base}")).json()
        me = next(i for i in instances if i["id"] == old_state.instanceId)
        return me

    def update(self, client, old_state):
        self.instance_id = old_state.instanceId
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        desired_hash = sha256(json.dumps(desired, sort_keys=True).encode()).hexdigest()
        if old_state.content_hash == desired_hash:
            return None
        url = IntegrationInstanceResource.u.format("{base}/{id}", id=old_state.instanceId)
        desired = desired | {"id": old_state.instanceId}
        client.put(url, json=desired)
        return {
            "instanceId": old_state.instanceId,
            "content_hash": desired_hash
        }

    @staticmethod
    def delete(client, old_state):
        client.delete(IntegrationInstanceResource.u.format("{base}/{id}", id=old_state.instanceId))

    def deps(self):
        return []


def ser_instance(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return value.instance_id


def des_instance(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


InstanceKey = Annotated[
    IntegrationInstanceResource,
    BeforeValidator(des_instance), PlainSerializer(ser_instance)
]


class OptionalProp(BaseModel, CamelAlias):
    property: PropertyKey
    display_name_override: str
    description_override: str
    entity_type: str | None = None
    entity_sub_type: Sequence[str] | None = None
    vendor_package: Sequence[str] | None = None


@register_resource()
class OptionalPropsResource(BaseModel, Resource):
    id: str = Field(exclude=True)
    props: Sequence[OptionalProp]
    instance: InstanceKey
    u: ClassVar[string.Formatter] = Urlfmt("/horizon/api/integrations/instances/configuration")

    @model_serializer(mode="wrap")
    def ser_model(self, serializer, info):
        style = info.context.get("style", "api") if info.context else "api"
        if style == "dump":
            return serializer(self)
        res = {}
        # api just wants the props as a dict keyed by property
        for op in self.props:
            data = op.model_dump(mode="json", exclude_none=True, by_alias=True)
            prop_key = data.pop("property", None)
            res[prop_key] = data
        return res

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Any:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            context_id = info.context.get("id")
            data = data | {"id": context_id}
        return data

    def create(self, client):
        url = self.u.format("{base}/{integration}/{instanceId}",
            integration=self.instance.integration_type,
            instanceId=self.instance.instance_id
        )
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        desired_hash = sha256(json.dumps(desired, sort_keys=True).encode()).hexdigest()
        client.put(url, json=desired)
        return {
            "content_hash": desired_hash,
            "integrationType": self.instance.integration_type,
            "instanceId": self.instance.instance_id
        }

    def read(self, client, old_state):
        url = self.u.format("{base}/{integration}/{instanceId}",
            integration=old_state.integrationType,
            instanceId=old_state.instanceId
        )
        return client.get(url).json()

    def update(self, client, old_state):
        old_id = old_state.instanceId
        old_type = old_state.integrationType
        if (self.instance.instance_id, self.instance.integration_type) != (old_id, old_type):
            new_state = self.create(client)
            self.delete(client, old_state)
            return new_state
        url = self.u.format("{base}/{integration}/{instanceId}",
            integration=old_type,
            instanceId=old_id
        )
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        desired_hash = sha256(json.dumps(desired, sort_keys=True).encode()).hexdigest()
        if desired_hash == old_state.content_hash:
            return None
        client.put(url, json=desired)
        return {
            "content_hash": desired_hash,
            "integrationType": self.instance.integration_type,
            "instanceId": self.instance.instance_id
        }

    @staticmethod
    def delete(client, old_state):
        old_id = old_state.instanceId
        old_type = old_state.integrationType
        url = OptionalPropsResource.u.format("{base}/{integration}/{instanceId}",
            integration=old_type,
            instanceId=old_id
        )
        client.put(url, json={})

    def deps(self) -> Sequence[Resource | Ref]:
        instance: Sequence[Resource | Ref] = [self.instance]
        props = [p.property for p in self.props]
        return instance + props
