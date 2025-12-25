from pydantic import BaseModel, Field, field_serializer, field_validator


class ComputedRead(BaseModel):
    scope: str = Field(init=True)
    code: str = Field(init=True)


class ComputedResource(ComputedRead):
    id: str = Field(exclude=True)


def test_validate():
    raw = {"scope": "sc1", "code": "cd1"}
    ext = {"id": raw["scope"] + "/" + raw["code"]}
    result = ComputedRead.model_validate(ext | raw)
    print(result.model_dump())
    assert result.model_dump() == {"scope": "sc1", "code": "cd1"}


class Reference():
    pass


class Child(BaseModel, Reference):
    id: str = Field(exclude=True)
    scope: str
    code: str


class Parent(BaseModel):
    id: str = Field(exclude=True)
    child: Child

    @field_serializer("child")
    def ser_child(self, v, info):
        if info.context and info.context.get("refs"):
            return "$ref:idc"
        return {"scope": v.scope, "code": v.code}

    @field_validator("child", mode="before")
    @classmethod
    def des_child(cls, v, info):
        print(info.context, "++++++++++++++++++++++++++")
        print(v, "++++++++++++++++++")
        if info.context and info.context.get("refs"):
            # return Child(id="idc", scope="ref", code="ref")
            return info.context["objects"][v["$ref"]]
        return v


def test_serialize_normal():
    ch = Child(id="idc", scope="sc1", code="cd1")
    pa = Parent(id="idp", child=ch)
    ser = pa.model_dump(context=None)
    assert ser == {"child": {"scope": "sc1", "code": "cd1"}}


def test_serialize_reference():
    ch = Child(id="idc", scope="sc1", code="cd1")
    pa = Parent(id="idp", child=ch)
    ser = pa.model_dump(context={"refs": True})
    assert ser == {"child": "$ref:idc"}


def test_deserialize_normal():
    ser = {"id": "idp", "child": {"id": "idc", "scope": "sc1", "code": "cd1"}}
    pa = Parent.model_validate(ser)
    assert pa.model_dump() == {"child": {"scope": "sc1", "code": "cd1"}}


def test_deserialize_reference():
    others = {"idc": Child(id="idc", scope="ref", code="ref")}
    ser = {"id": "idp", "child": {"$ref": "idc"}}
    pa = Parent.model_validate(ser, context={"refs": True, "objects": others})
    assert pa.model_dump() == {"child": {"scope": "ref", "code": "ref"}}
