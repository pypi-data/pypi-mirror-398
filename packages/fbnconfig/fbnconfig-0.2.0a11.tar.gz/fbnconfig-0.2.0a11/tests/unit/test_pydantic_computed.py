from abc import ABC, abstractmethod
from typing import Any, Dict

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import AliasGenerator, BaseModel, ConfigDict, Field, alias_generators, computed_field

alias_generator = ConfigDict(
    alias_generator=AliasGenerator(
        serialization_alias=lambda field_name: alias_generators.to_camel(field_name)
    )
)


class BaseResource(ABC):
    model_config = alias_generator

    @abstractmethod
    def read(self) -> Any:
        pass


class SomeOtherObject(BaseModel):
    model_config = alias_generator
    some_other_field: str
    some: str


#
# when mapping multiple flat fields into a structure
# for the request, mark the fields the user sets
# as exclude=True and add a computed field
# to convert to the serialized representation
#
class ComputedResource(BaseResource, BaseModel):
    id: str = Field(exclude=True)
    scope: str = Field(init=True, exclude=True)
    code: str = Field(init=True, exclude=True)
    test_field: str
    other_field: SomeOtherObject

    @computed_field(alias="Id")
    def set_id(self) -> Dict[str, str]:
        return {"scope": self.scope, "code": self.code}

    def read(self):
        return 3


def test_dump():
    c = ComputedResource(
        id="id",
        scope="scope1",
        code="code1",
        test_field="something",
        other_field=SomeOtherObject(some_other_field="myvalue", some="testings"),
    )

    desired = c.model_dump(mode="json", exclude_none=True, by_alias=True)
    assert desired == {
        "Id": {"scope": "scope1", "code": "code1"},
        "testField": "something",
        "otherField": {"someOtherField": "myvalue", "some": "testings"},
    }


def test_computed_factory() -> None:
    class ComputedRFactory(ModelFactory[ComputedResource]): ...

    computed_instance = ComputedRFactory.build()
    assert isinstance(computed_instance, ComputedResource)
    assert isinstance(computed_instance.id, str)
    assert isinstance(computed_instance.scope, str)
    assert isinstance(computed_instance.code, str)
    assert isinstance(computed_instance.test_field, str)
    assert isinstance(computed_instance.other_field, SomeOtherObject)
