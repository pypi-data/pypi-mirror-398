from __future__ import annotations

import json
from hashlib import sha256
from typing import Annotated, Any, Dict, List, Literal, Union, get_args

import httpx
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, computed_field, model_validator

from fbnconfig.configuration import ItemKey
from fbnconfig.identity import UserKey

from .resource_abc import CamelAlias, Ref, Resource, register_resource


class SubscriptionStatus:
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class MatchingPattern(BaseModel, CamelAlias):
    event_type: str
    filter: str | None = None


@register_resource()
class SubscriptionRef(BaseModel, Ref):
    """
    Reference to a subscription resource.

    Example
    ----------
    >>> from fbnconfig import notifications
    >>> notifications.SubscriptionRef(
    ...  id="subscription-ref",
    ...  scope="myScope",
    ...  code="mySubscription")

    Attributes
    ----------
    id : str
         Resource identifier.
    scope : str
        Scope of the subscription.
    code: str
        Code of the subscription.
    """

    id: str = Field(exclude=True)
    scope: str
    code: str

    def attach(self, client):
        """Attach to an existing subscription resource."""
        try:
            client.get(f"/notification/api/subscriptions/{self.scope}/{self.code}")
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Subscription {self.scope}/{self.code} does not exist")
            else:
                raise ex


@register_resource()
class SubscriptionResource(CamelAlias, BaseModel, Resource):
    """Subscription resource"""

    id: str = Field(exclude=True)
    scope: str
    code: str
    display_name: str
    description: str | None = None
    status: str = Field(default=SubscriptionStatus.ACTIVE)
    matching_pattern: MatchingPattern
    use_as_auth: UserKey | None = None

    @computed_field(alias="id")
    def resource_id(self) -> dict[str, str]:
        return {"scope": self.scope, "code": self.code}

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

    def __get_content_hash__(self) -> str:
        dump = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        return sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()

    def read(self, client: httpx.Client, old_state) -> Dict[str, Any]:
        response = client.get(f"/notification/api/subscriptions/{old_state.scope}/{old_state.code}")
        result = response.json()
        # Remove read-only fields
        result.pop("href", None)
        result.pop("createdAt", None)
        result.pop("userIdCreated", None)
        result.pop("modifiedAt", None)
        result.pop("userIdModified", None)
        return result

    def create(self, client: httpx.Client) -> Dict[str, Any]:
        body = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"scope", "code"})

        response = client.post("/notification/api/subscriptions", json=body)
        result = response.json()

        # Remove read-only fields
        result.pop("href", None)
        result.pop("createdAt", None)
        result.pop("userIdCreated", None)
        result.pop("modifiedAt", None)
        result.pop("userIdModified", None)

        # Calculate version hashes - convert to string for hashability
        source_version = self.__get_content_hash__()
        remote_version = sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()

        return {
            "scope": self.scope,
            "code": self.code,
            "source_version": source_version,
            "remote_version": remote_version
        }

    def update(self, client: httpx.Client, old_state) -> Union[None, Dict[str, Any]]:
        if old_state.code != self.code:
            raise (RuntimeError("Cannot change the code on an existing subscription"))

        if old_state.scope != self.scope:
            raise (RuntimeError("Cannot change the scope on an existing subscription"))

        # Check if source version changed - convert to string for hashability
        source_hash = self.__get_content_hash__()
        remote = self.read(client, old_state)
        remote_hash = sha256(json.dumps(remote, sort_keys=True).encode()).hexdigest()

        if remote_hash == old_state.remote_version and source_hash == old_state.source_version:
            return None

        body = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"scope", "code"})

        scope = self.scope
        code = self.code

        response = client.put(f"/notification/api/subscriptions/{scope}/{code}", json=body)
        result = response.json()

        # Remove read-only fields
        result.pop("href", None)
        result.pop("createdAt", None)
        result.pop("userIdCreated", None)
        result.pop("modifiedAt", None)
        result.pop("userIdModified", None)

        return {
            "scope": scope,
            "code": code,
            "source_version": self.__get_content_hash__(),
            "remote_version": sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
        }

    @staticmethod
    def delete(client: httpx.Client, old_state) -> None:
        client.delete(f"/notification/api/subscriptions/{old_state.scope}/{old_state.code}")

    def deps(self) -> List:
        """Dependencies."""
        return [self.use_as_auth] if self.use_as_auth else []


def ser_sub_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return {"scope": value.scope, "code": value.code}


def des_sub_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


SubscriptionKey = Annotated[
    SubscriptionRef | SubscriptionResource,
    BeforeValidator(des_sub_key), PlainSerializer(ser_sub_key)
]


class EmailNotificationType(CamelAlias, BaseModel):
    """Email notification configuration."""
    type: Literal["Email"] = "Email"
    subject: str
    plain_text_body: str | None = Field(default=None)
    html_body: str | None = Field(default=None)
    email_address_to: List[str]
    email_address_cc: List | None = Field(default=None)
    email_address_bcc: List | None = Field(default=None)

    def deps(self) -> List:
        return []


class AmazonSqsNotificationType(CamelAlias, BaseModel):
    """Amazon SQS notification configuration."""
    type: Literal["AmazonSqs"] = "AmazonSqs"
    api_key_ref: ItemKey
    api_secret_ref: ItemKey
    body: str
    queue_url_ref: ItemKey

    def deps(self) -> List:
        return [
            self.api_key_ref,
            self.api_secret_ref,
            self.queue_url_ref]


class AmazonSqsPrincipalAuthNotificationType(CamelAlias, BaseModel):
    type: Literal["AmazonSqsPrincipalAuth"] = "AmazonSqsPrincipalAuth"
    body: str
    queue_url_ref: ItemKey

    def deps(self) -> List:
        return [self.queue_url_ref]


class AzureServiceBusNotificationType(CamelAlias, BaseModel):
    """Azure Service Bus notification configuration."""
    type: Literal["AzureServiceBus"] = "AzureServiceBus"
    body: str
    namespace_ref: ItemKey
    queue_name_ref: ItemKey
    tenant_id_ref: ItemKey
    client_id_ref: ItemKey
    client_secret_ref: ItemKey

    def deps(self) -> List:
        return [
            self.namespace_ref,
            self.queue_name_ref,
            self.tenant_id_ref,
            self.client_id_ref,
            self.client_secret_ref
        ]


class WebhookNotificationType(CamelAlias, BaseModel):
    """Webhook notification configuration."""
    type: Literal["Webhook"] = "Webhook"
    http_method: str
    url: str
    authentication_type: Literal["Lusid", "BasicAuth", "BearerToken", None]
    authentication_configuration_item_paths: Dict[str, ItemKey] | Dict[str, None] | None = None
    content_type: str
    content: Dict[str, Any] | None

    def deps(self) -> List:
        item_paths = self.authentication_configuration_item_paths

        if item_paths is None:
            return []

        # Loops through the item paths and adds any that are ItemKeys
        item_type = get_args(ItemKey)[0]
        item_dependencies = []

        for path in item_paths.values():
            if isinstance(path, item_type):
                item_dependencies.append(path)

        return item_dependencies


class SmsNotificationType(CamelAlias, BaseModel):
    """SMS notification configuration."""
    type: Literal["Sms"] = "Sms"
    body: str
    recipients: list[str] | None

    def deps(self) -> List:
        return []


NotificationTypes = Union[
    EmailNotificationType,
    AmazonSqsNotificationType,
    AmazonSqsPrincipalAuthNotificationType,
    AzureServiceBusNotificationType,
    WebhookNotificationType,
    SmsNotificationType,
]


@register_resource()
class NotificationRef(BaseModel, Ref):
    """
    Reference to a notification

    Example
    ----------
    >>> from fbnconfig import notifications
    >>> subscription = notifications.SubscriptionRef(
    ...  id="subscription-ref",
    ...  scope="myScope",
    ...  code="mySubscription")


    >>> ref = notifications.NotificationRef(
    ...  id="notification-ref",
    ...  subscriptions=subscription
    ...  notification_id="myNotification")
    >>> ref.attach()  # Attach to an existing notification

    """

    id: str = Field(exclude=True)
    subscription: SubscriptionKey
    notification_id: str

    def attach(self, client):
        """Attach to an existing notification resource."""
        try:
            client.get(
                f"/notification/api/subscriptions/{self.subscription.scope}/"
                f"{self.subscription.code}/notifications/{self.notification_id}"
            )
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(
                    f"Notification {self.notification_id} for subscription "
                    f"{self.subscription.scope}/{self.subscription.code} does not exist"
                )
            else:
                raise ex


@register_resource()
class NotificationResource(CamelAlias, BaseModel, Resource):
    """
    Notification resource for managing notifications on subscriptions.
    """

    id: str = Field(exclude=True)
    subscription: SubscriptionKey
    notification_id: str
    display_name: str
    description: str | None = Field(default=None)
    notification_type: NotificationTypes | dict[str, Any]

    def __get_content_hash__(self) -> str:
        dump = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        return sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client: httpx.Client, old_state) -> Dict[str, Any] | None:
        response = client.get(
            f"/notification/api/subscriptions/{old_state.scope}/"
            f"{old_state.code}/notifications/{old_state.notification_id}"
        )
        result = response.json()
        # Remove read-only fields
        result.pop("href", None)
        result.pop("createdAt", None)
        result.pop("userIdCreated", None)
        result.pop("modifiedAt", None)
        result.pop("userIdModified", None)
        return result

    def create(self, client: httpx.Client) -> Dict[str, Any]:
        """POST - Create new notification on subscription."""
        body = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"subscription"})

        response = client.post(
            f"/notification/api/subscriptions/{self.subscription.scope}/"
            f"{self.subscription.code}/notifications",
            json=body
        )
        result = response.json()

        # Remove read-only fields
        result.pop("href", None)
        result.pop("createdAt", None)
        result.pop("userIdCreated", None)
        result.pop("modifiedAt", None)
        result.pop("userIdModified", None)

        # Calculate version hashes - convert to string for hashability
        source_version = self.__get_content_hash__()
        remote_version = sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()

        return {
            "id": self.id,
            "scope": self.subscription.scope,
            "code": self.subscription.code,
            "notification_id": self.notification_id,
            "source_version": source_version,
            "remote_version": remote_version
        }

    def update(self, client: httpx.Client, old_state) -> Dict[str, Any] | None:
        """PUT - Update existing notification."""
        if old_state.code != self.subscription.code:
            raise (RuntimeError("Cannot change the code on a notification"))

        if old_state.scope != self.subscription.scope:
            raise (RuntimeError("Cannot change the scope on a notification"))

        if old_state.notification_id != self.notification_id:
            self.delete(client, old_state)
            return self.create(client)

        source_hash = self.__get_content_hash__()
        remote = self.read(client, old_state)
        remote_hash = sha256(json.dumps(remote, sort_keys=True).encode()).hexdigest()

        if remote_hash == old_state.remote_version and source_hash == old_state.source_version:
            return None

        body = self.model_dump(mode="json", exclude_none=True, by_alias=True)

        response = client.put(
            f"/notification/api/subscriptions/{self.subscription.scope}/"
            f"{self.subscription.code}/notifications/{self.notification_id}",
            json=body
        )

        result = response.json()
        # Remove read-only fields
        result.pop("href", None)
        result.pop("createdAt", None)
        result.pop("userIdCreated", None)
        result.pop("modifiedAt", None)
        result.pop("userIdModified", None)

        return {
            "id": self.id,
            "scope": self.subscription.scope,
            "code": self.subscription.code,
            "notification_id": self.notification_id,
            "source_version": self.__get_content_hash__(),
            "remote_version": sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
        }

    @staticmethod
    def delete(client: httpx.Client, old_state) -> None:
        client.delete(
            f"/notification/api/subscriptions/{old_state.scope}/"
            f"{old_state.code}/notifications/{old_state.notification_id}"
        )

    def deps(self) -> List:
        all_deps = [self.subscription]

        if isinstance(self.notification_type, NotificationTypes):
            all_deps += (self.notification_type.deps())

        return all_deps
