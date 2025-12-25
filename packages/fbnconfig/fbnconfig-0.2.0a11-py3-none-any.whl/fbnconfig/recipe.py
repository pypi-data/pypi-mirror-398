from __future__ import annotations

import hashlib
import json
from pathlib import PurePath
from types import SimpleNamespace
from typing import Annotated, Any

import httpx
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_serializer,
    model_validator,
)

from .resource_abc import Resource, register_resource


def validate_recipe(v: dict[str, Any]) -> dict[str, Any]:
    if v is None:
        return v
    if isinstance(v, PurePath) and not v.is_absolute():
        raise ValueError("Path should be an absolute path")
    return v


@register_resource()
class RecipeResource(BaseModel, Resource):
    """
    Manage a Recipe resource.

    Attributes:

        id: str
            The unique identifier of this resource.
        scope: str
            The scope of the recipe.
        code: str
            The code of the recipe.
        recipe: dict[str, Any] | PurePath | None
            The recipe definition.
            If a dictionary, it is a recipe as defined in the LUSID API.
            If a PurePath, it is a path to a JSON file containing the recipe.

    Example:

        .. code-block:: python

            from fbnconfig import recipe

            recipe = recipe.RecipeResource(
                scope="my_scope",
                code="my_code",
                recipe={
                    "market": {...},
                }
            )
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(init=True, exclude=True)
    scope: str = Field(init=True, exclude=True)
    code: str = Field(init=True, exclude=True)
    recipe: Annotated[dict[str, Any] | PurePath, AfterValidator(validate_recipe)]

    @computed_field()
    def _recipe_model_(self) -> dict[str, Any]:
        recipe_model = {}
        if isinstance(self.recipe, PurePath):
            with open(self.recipe, "rb") as ff:
                recipe_model = json.loads(ff.read())
        else:
            recipe_model = self.recipe
        recipe_model.pop("scope", None)
        recipe_model.pop("code", None)
        return recipe_model

    @model_serializer(when_used="always")
    def ser_model(self, info) -> dict[str, Any]:
        style = info.context.get("style", "api") if info.context else "api"
        if style == "dump":
            return {
                "scope": self.scope,
                "code": self.code,
                "recipe": self._recipe_model_,
            }
        # api style. Get returns just the value, put requires the outer element
        return {
            "configurationRecipe":
            # Operator "|" not supported for types "dict[str, str]" and "() -> dict[str, Any]
            {"scope": self.scope, "code": self.code} | self._recipe_model_  # type:ignore
        }

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info):
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        return self.__get_recipe__(client, old_state.scope, old_state.code, as_at=None)

    def create(self, client: httpx.Client):
        source = self.model_dump(mode="json", exclude_none=True)
        as_at = client.post("/api/api/recipes", json=source).json()["value"]
        remote = self.__get_recipe__(client, self.scope, self.code, as_at)

        return {
            "scope": self.scope,
            "code": self.code,
            "source_version": self.__get_hash__(source),
            "remote_version": self.__get_hash__(remote),
        }

    def update(self, client, old_state):
        if [self.scope, self.code] != [old_state.scope, old_state.code]:
            self.delete(client, old_state)
            return self.create(client)

        remote = self.read(client, old_state) or {}
        dump = self.model_dump(mode="json", exclude_none=True)
        remote_version = self.__get_hash__(remote)
        source_version = self.__get_hash__(dump)
        if source_version == old_state.source_version and remote_version == old_state.remote_version:
            return None

        return self.create(client)

    @staticmethod
    def delete(client, old_state: SimpleNamespace):
        client.delete(f"/api/api/recipes/{old_state.scope}/{old_state.code}")

    def deps(self) -> list[Any]:
        return []

    @staticmethod
    def __get_recipe__(client: httpx.Client, scope: str, code: str, as_at: str | None) -> dict[str, Any]:
        r = client.get(
            f"/api/api/recipes/{scope}/{code}", params={"asAt": as_at} if as_at else None
        ).json()["value"]
        r.pop("scope", None)
        r.pop("code", None)
        return r

    @staticmethod
    def __get_hash__(content) -> str:
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
