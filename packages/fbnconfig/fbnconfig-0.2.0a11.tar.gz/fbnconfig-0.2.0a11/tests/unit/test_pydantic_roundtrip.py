import json

import pytest
from pydantic import BaseModel

from fbnconfig.resource_abc import CamelAlias


class InheritConfig(CamelAlias, BaseModel):
    snake_case_required: str
    snake_case_optional: int | None = None


@pytest.fixture()
def klass():
    return InheritConfig


def test_init_snake(klass):
    sut = klass(
        snake_case_required="a string"
    )
    assert sut.snake_case_required == "a string"


def test_init_camel(klass):
    # note: this is not quite the behaviour we wanted
    # but there does not seem to be a way to require snake for the init
    # and still be able to deserialize camel
    sut = klass(
        snakeCaseRequired="a string"
    )
    assert sut.snake_case_required == "a string"


def test_serialize(klass):
    sut = klass(
        snake_case_required="a string"
    )
    ser = sut.model_dump(mode="json", exclude_none=True, by_alias=True)
    assert ser == {"snakeCaseRequired": "a string"}


def test_deserialize_dict(klass):
    ser = {"snakeCaseRequired": "a string"}
    sut = klass.model_validate(ser)
    assert sut.snake_case_required == "a string"


def test_deserialize_json(klass):
    ser = json.dumps({"snakeCaseRequired": "a string"})
    sut = klass.model_validate_json(ser)
    assert sut.snake_case_required == "a string"
