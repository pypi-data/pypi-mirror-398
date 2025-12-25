from __future__ import annotations

from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Any, Dict, Optional, Sequence, Union

from httpx import Client as httpxClient
from pydantic import AliasGenerator, ConfigDict, alias_generators

std_config = ConfigDict(
    populate_by_name=True,
    alias_generator=AliasGenerator(
        serialization_alias=alias_generators.to_camel,
        validation_alias=alias_generators.to_camel,
    )
)

RESOURCE_REGISTRY = {}


def get_resource_type(resource: Resource | Ref) -> str:
    """
    Get the resource name from a resource or ref object.
    """
    resource_type = getattr(resource, "resource_type", None)
    # Use class name if resource_type couldn't be determined
    if not resource_type:
        resource_type = type(resource).__name__

    return resource_type


def register_resource(type_name: str | None = None):
    """
    Decorator to register resource classes.
    Allows lookup of resource classes by their resource_type.
    """

    def decorator(cls):
        # Use class name if resource_type couldn't be determined
        resource_type = type_name if type_name else cls.__name__
        RESOURCE_REGISTRY[resource_type] = {"class": cls}
        cls.resource_type = resource_type
        return cls

    return decorator


def get_resource_class(resource_type: str):
    """
    Get a resource class by its resource_type.
    """
    resource = RESOURCE_REGISTRY.get(resource_type)
    if resource is None:
        raise RuntimeError(f"Resource type '{resource_type}' not found in registry")
    return resource["class"]


class Ref(ABC):
    id: str

    @abstractmethod
    def attach(self, client: httpxClient) -> None:
        pass

    def deps(self):
        return []


class Resource(ABC):
    model_config = std_config

    id: str

    @abstractmethod
    def read(self, client: httpxClient, old_state: SimpleNamespace) -> None | Dict[str, Any]:
        pass

    @abstractmethod
    def create(self, client: httpxClient) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update(self, client: httpxClient, old_state) -> Union[None, Dict[str, Any]]:
        pass

    @staticmethod
    @abstractmethod
    def delete(client: httpxClient, old_state) -> None:
        pass

    @abstractmethod
    def deps(self) -> Sequence["Resource|Ref"]:
        pass


class CamelAlias(ABC):
    model_config = std_config
