import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import datatype

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeDataTypeRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/api/api/datatypes/sc1/cd1").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        sut = datatype.DataTypeRef(id="one", scope="sc1", code="cd1")
        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/api/api/datatypes/sc1/cd1").mock(return_value=httpx.Response(404, json={}))
        client = self.client
        sut = datatype.DataTypeRef(id="one", scope="sc1", code="cd1")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Datatype sc1/cd1 not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/api/api/datatypes/sc1/cd1").mock(return_value=httpx.Response(400, json={}))
        client = self.client
        sut = datatype.DataTypeRef(id="one", scope="sc1", code="cd1")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeDataTypeResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):
        respx_mock.post("/api/api/datatypes").mock(return_value=httpx.Response(200, json={}))
        # given a desired definition with one field
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.OPEN,
            display_name="displayName 1",
            description="description one",
            value_type=datatype.ValueType.STRING,
            unit_schema=datatype.UnitSchema.NO_UNITS,
            reference_data=datatype.ReferenceData(
                field_definitions=[
                    datatype.FieldDefinition(key="fdone", is_required=True, is_unique=False),
                    datatype.FieldDefinition(
                        key="fdtwo",
                        is_required=False,
                        is_unique=False,
                        value_type=datatype.ValueType.STRING,
                    ),
                    datatype.FieldDefinition(
                        key="fdthree",
                        is_required=False,
                        is_unique=False,
                        value_type=datatype.ValueType.DECIMAL,
                    ),
                    datatype.FieldDefinition(
                        key="fdfour", is_required=False, is_unique=False, value_type="Decimal"
                    ),
                ],
                values=[datatype.FieldValue(value="valueone", fields={"fdone": "fdone-value"})],
            ),
        )
        # when we create it
        state = sut.create(self.client)
        # then the state the typename returned by the create call
        assert state == {"scope": "scope1", "code": "code1"}
        # and a create request was sent without the startValue
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/datatypes"
        assert json.loads(request.content) == {
            "scope": "scope1",
            "code": "code1",
            "typeValueRange": "Open",
            "displayName": "displayName 1",
            "description": "description one",
            "valueType": "String",
            "unitSchema": "NoUnits",
            "referenceData": {
                "fieldDefinitions": [
                    {"key": "fdone", "isRequired": True, "isUnique": False, "valueType": "String"},
                    {"key": "fdtwo", "isRequired": False, "isUnique": False, "valueType": "String"},
                    {"key": "fdthree", "isRequired": False, "isUnique": False, "valueType": "Decimal"},
                    {"key": "fdfour", "isRequired": False, "isUnique": False, "valueType": "Decimal"},
                ],
                "values": [{"value": "valueone", "fields": {"fdone": "fdone-value"}}],
            },
        }

    def test_update_with_no_changes(self, respx_mock):
        # given an existing CE where the field has a description
        respx_mock.get("/api/api/datatypes/scope1/code1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "scope": "scope1",
                    "code": "code1",
                    "typeValueRange": "Open",
                    "displayName": "displayName 1",
                    "description": "description one",
                    "valueType": "String",
                    "unitSchema": "NoUnits",
                    "referenceData": {
                        "fieldDefinitions": [
                            {
                                "key": "fdone",
                                "isRequired": True,
                                "isUnique": False,
                                "valueType": "String",
                            }
                        ],
                        "values": [{"value": "valueone", "fields": {"fdone": "fdone-value"}}],
                    },
                    "version": {},
                    "href": "http://.....",
                    "id": {"scope": "scope1", "code": "code1"},
                    "links": {},
                },
            )
        )
        # and a desired which is the same
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.OPEN,
            display_name="displayName 1",
            description="description one",
            value_type=datatype.ValueType.STRING,
            unit_schema=datatype.UnitSchema.NO_UNITS,
            reference_data=datatype.ReferenceData(
                field_definitions=[
                    datatype.FieldDefinition(key="fdone", is_required=True, is_unique=False)
                ],
                values=[datatype.FieldValue(value="valueone", fields={"fdone": "fdone-value"})],
            ),
        )
        old_state = SimpleNamespace(scope="scope1", code="code1")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is None
        assert state is None
        # and a read was made but no PUT

    def test_update_readonly(self, respx_mock):
        # given a remote with typeValueRange = Open
        respx_mock.get("/api/api/datatypes/scope1/code1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "scope": "scope1",
                    "code": "code1",
                    "typeValueRange": "Open",
                    "displayName": "displayName 1",
                    "description": "description one",
                    "valueType": "String",
                    "unitSchema": "NoUnits",
                    "referenceData": {
                        "fieldDefinitions": [
                            {
                                "key": "fdone",
                                "isRequired": True,
                                "isUnique": False,
                                "valueType": "String",
                            }
                        ],
                        "values": [{"value": "valueone", "fields": {"fdone": "fdone-value"}}],
                    },
                    "version": {},
                    "href": "http://.....",
                    "id": {"scope": "scope1", "code": "code1"},
                    "links": {},
                },
            )
        )
        # and a desired which has Closed
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.CLOSED,
            display_name="displayName 1",
            description="description two",
            value_type=datatype.ValueType.STRING,
            unit_schema=datatype.UnitSchema.NO_UNITS,
            reference_data=datatype.ReferenceData(
                field_definitions=[
                    datatype.FieldDefinition(key="fdone", is_required=True, is_unique=False)
                ],
                values=[datatype.FieldValue(value="valueone", fields={"fdone": "fdone-value"})],
            ),
        )
        old_state = SimpleNamespace(scope="scope1", code="code1")
        # when we update it it throws because the field is readonly
        with pytest.raises(RuntimeError) as ex:
            sut.update(self.client, old_state)
        assert "typeValueRange" in str(ex.value)

    def test_update_readonly_field_definitions(self, respx_mock):
        # given a remote with a field "fdone"
        respx_mock.get("/api/api/datatypes/scope1/code1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "scope": "scope1",
                    "code": "code1",
                    "typeValueRange": "Open",
                    "displayName": "displayName 1",
                    "description": "description one",
                    "valueType": "String",
                    "unitSchema": "NoUnits",
                    "referenceData": {
                        "fieldDefinitions": [
                            {
                                "key": "fdone",
                                "isRequired": True,
                                "isUnique": False,
                                "valueType": "String",
                            }
                        ],
                        "values": [{"value": "valueone", "fields": {"fdone": "fdone-value"}}],
                    },
                    "version": {},
                    "href": "http://.....",
                    "id": {"scope": "scope1", "code": "code1"},
                    "links": {},
                },
            )
        )
        # and a desired which has fdtwo
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.OPEN,
            display_name="displayName 1",
            description="description two",
            value_type=datatype.ValueType.STRING,
            unit_schema=datatype.UnitSchema.NO_UNITS,
            reference_data=datatype.ReferenceData(
                field_definitions=[
                    datatype.FieldDefinition(key="fdtwo", is_required=True, is_unique=False)
                ],
                values=[datatype.FieldValue(value="valueone", fields={"fdone": "fdone-value"})],
            ),
        )
        old_state = SimpleNamespace(scope="scope1", code="code1")
        # when we update it it throws because the field is readonly
        with pytest.raises(RuntimeError) as ex:
            sut.update(self.client, old_state)
        assert "fieldDefinitions" in str(ex.value)

    def test_update_with_changed_description(self, respx_mock):
        # given a remote with "description one"
        respx_mock.get("/api/api/datatypes/scope1/code1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "scope": "scope1",
                    "code": "code1",
                    "typeValueRange": "Open",
                    "displayName": "displayName 1",
                    "description": "description one",
                    "valueType": "String",
                    "unitSchema": "NoUnits",
                    "referenceData": {
                        "fieldDefinitions": [
                            {
                                "key": "fdone",
                                "isRequired": True,
                                "isUnique": False,
                                "valueType": "String",
                            }
                        ],
                        "values": [{"value": "valueone", "fields": {"fdone": "fdone-value"}}],
                    },
                    "version": {},
                    "href": "http://.....",
                    "id": {"scope": "scope1", "code": "code1"},
                    "links": {},
                },
            )
        )
        respx_mock.put("/api/api/datatypes/scope1/code1").mock(return_value=httpx.Response(200, json={}))
        # and a desired which has "description two"
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.OPEN,
            display_name="displayName 1",
            description="description two",
            value_type=datatype.ValueType.STRING,
            unit_schema=datatype.UnitSchema.NO_UNITS,
            reference_data=datatype.ReferenceData(
                field_definitions=[
                    datatype.FieldDefinition(key="fdone", is_required=True, is_unique=False)
                ],
                values=[datatype.FieldValue(value="valueone", fields={"fdone": "fdone-value"})],
            ),
        )
        old_state = SimpleNamespace(scope="scope1", code="code1")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is returned
        assert state == {"scope": "scope1", "code": "code1"}
        # and a put request was sent
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/api/api/datatypes/scope1/code1"
        assert json.loads(request.content) == {
            "typeValueRange": "Open",
            "displayName": "displayName 1",
            "description": "description two",
            "valueType": "String",
            "unitSchema": "NoUnits",
            "referenceData": {
                "fieldDefinitions": [
                    {"key": "fdone", "isRequired": True, "isUnique": False, "valueType": "String"}
                ],
                "values": [{"value": "valueone", "fields": {"fdone": "fdone-value"}}],
            },
        }

    def test_update_with_changed_reference_values(self, respx_mock):
        # given a remote with values of valueone
        respx_mock.get("/api/api/datatypes/scope1/code1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "scope": "scope1",
                    "code": "code1",
                    "typeValueRange": "Open",
                    "displayName": "displayName 1",
                    "description": "description one",
                    "valueType": "String",
                    "unitSchema": "NoUnits",
                    "referenceData": {
                        "fieldDefinitions": [
                            {
                                "key": "fdone",
                                "isRequired": True,
                                "isUnique": False,
                                "valueType": "String",
                            }
                        ],
                        "values": [{"value": "valueone", "fields": {"fdone": "fdone-value"}}],
                    },
                    "version": {},
                    "href": "http://.....",
                    "id": {"scope": "scope1", "code": "code1"},
                    "links": {},
                },
            )
        )
        respx_mock.put("/api/api/datatypes/scope1/code1/referencedatavalues").mock(
            return_value=httpx.Response(200, json={})
        )
        # and a desired which has an additional value allowed
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.OPEN,
            display_name="displayName 1",
            description="description one",
            value_type=datatype.ValueType.STRING,
            unit_schema=datatype.UnitSchema.NO_UNITS,
            reference_data=datatype.ReferenceData(
                field_definitions=[
                    datatype.FieldDefinition(key="fdone", is_required=True, is_unique=False)
                ],
                values=[
                    datatype.FieldValue(value="valueone", fields={"fdone": "fdone-value"}),
                    datatype.FieldValue(value="valuetwo", fields={"fdone": "fdone-value"}),
                ],
            ),
        )
        old_state = SimpleNamespace(scope="scope1", code="code1")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is returned
        assert state == {"scope": "scope1", "code": "code1"}
        # and a put request was sent to the refernce data endpoint
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/api/api/datatypes/scope1/code1/referencedatavalues"
        assert json.loads(request.content) == [
            {"value": "valueone", "fields": {"fdone": "fdone-value"}},
            {"value": "valuetwo", "fields": {"fdone": "fdone-value"}},
        ]
        # but no put on the main datatype endpoint because those values have not changed

    def test_update_with_same_acceptable_values(self, respx_mock):
        # given a remote with acceptable values A, C, B
        respx_mock.get("/api/api/datatypes/scope1/code1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "scope": "scope1",
                    "code": "code1",
                    "typeValueRange": "Open",
                    "displayName": "displayName 1",
                    "description": "description one",
                    "valueType": "String",
                    "unitSchema": "NoUnits",
                    "acceptableValues": ["A", "C", "B"],
                    "version": {},
                    "href": "http://.....",
                    "id": {"scope": "scope1", "code": "code1"},
                    "links": {},
                },
            )
        )
        # and a desired which has B, A, C  (same values but in different order)
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.OPEN,
            display_name="displayName 1",
            description="description one",
            value_type=datatype.ValueType.STRING,
            unit_schema=datatype.UnitSchema.NO_UNITS,
            acceptable_values=["B", "A", "C"],
        )
        old_state = SimpleNamespace(scope="scope1", code="code1")
        # when we update it
        state = sut.update(self.client, old_state)
        assert state is None

    def test_delete_datatype(self, respx_mock):
        respx_mock.delete("/api/api/datatypes/scope1/code1").mock(
            return_value=httpx.Response(200, json={"asAt": "123456"})
        )
        client = self.client
        # given a resource that exists in the remote
        old_state = SimpleNamespace(scope="scope1", code="code1")
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.OPEN,
            display_name="",
            description="",
            value_type=datatype.ValueType.STRING,
        )
        sut.delete(client, old_state)
        respx_mock.assert_all_called()

    def test_delete_data_type_missing(self, respx_mock):
        respx_mock.delete("/api/api/datatypes/scope1/code1").mock(return_value=httpx.Response(400))
        client = self.client
        old_state = SimpleNamespace(scope="scope1", code="code1")
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.OPEN,
            display_name="",
            description="",
            value_type=datatype.ValueType.STRING,
        )

        with pytest.raises(httpx.HTTPStatusError):
            sut.delete(client, old_state)

    @staticmethod
    def test_deps():
        sut = datatype.DataTypeResource(
            id="xyz",
            scope="scope1",
            code="code1",
            type_value_range=datatype.TypeValueRange.OPEN,
            display_name="",
            description="",
            value_type=datatype.ValueType.STRING,
        )
        # it's deps are empty
        assert sut.deps() == []

    def test_dump(self):
        # given a simple datatype resource
        sut = datatype.DataTypeResource(
            id="dt1",
            scope="test-scope",
            code="test-code",
            type_value_range=datatype.TypeValueRange.CLOSED,
            display_name="Test DataType",
            description="A test datatype",
            value_type=datatype.ValueType.STRING,
            acceptable_values=["A", "B", "C"],
            unit_schema=datatype.UnitSchema.NO_UNITS
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then the dumped state is correct
        assert dumped == {
            "scope": "test-scope",
            "code": "test-code",
            "typeValueRange": "Closed",
            "displayName": "Test DataType",
            "description": "A test datatype",
            "valueType": "String",
            "acceptableValues": ["A", "B", "C"],
            "unitSchema": "NoUnits"
        }

    def test_undump(self):
        # given a dumped datatype state
        dumped = {
            "scope": "test-scope",
            "code": "test-code",
            "typeValueRange": "Closed",
            "displayName": "Test DataType",
            "description": "A test datatype",
            "valueType": "String",
            "acceptableValues": ["A", "B", "C"],
            "unitSchema": "NoUnits"
        }
        # when we undump it
        sut = datatype.DataTypeResource.model_validate(
            dumped,
            context={
                "style": "undump",
                "$refs": {},
                "id": "dt1",
            }
        )
        # then the id has been extracted from the context
        assert sut.id == "dt1"
        assert sut.scope == "test-scope"
        assert sut.code == "test-code"
        assert sut.type_value_range == datatype.TypeValueRange.CLOSED
        assert sut.display_name == "Test DataType"
        assert sut.description == "A test datatype"
        assert sut.value_type == datatype.ValueType.STRING
        assert sut.acceptable_values == ["A", "B", "C"]
        assert sut.unit_schema == datatype.UnitSchema.NO_UNITS
        assert sut.reference_data is None

    def test_parse_api_format(self):
        # given an api style response with scope/code
        # nested
        resp = {
            "id": {"scope": "scope1", "code": "code1"},
            "typeValueRange": "Open",
            "displayName": "displayName 1",
            "description": "description one",
            "valueType": "String",
            "unitSchema": "NoUnits",
        }
        # when we parse it
        parsed = datatype.DataTypeResource.model_validate(
            resp,
            context={
                "style": "api",
                "$refs": {},
                "id": "dt1",
            }
        )
        assert parsed.id == "dt1"
        assert parsed.scope == "scope1"
        assert parsed.code == "code1"
