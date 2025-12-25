import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import custom_data_model
from fbnconfig import property as prop
from fbnconfig.coretypes import ResourceId

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeCustomDataModelRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_when_present(self, respx_mock):
        # given a custom data model exists
        respx_mock.get("/api/api/datamodel/Instrument/TestScope/TestModel").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dataModelSummary": {
                        "id": {"scope": "TestScope", "code": "TestModel"},
                        "entityType": "Instrument",
                    }
                },
            )
        )
        # when we attach a reference to it
        ref = custom_data_model.CustomDataModelRef(
            id="test_ref",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="TestModel"),
        )
        ref.attach(self.client)
        # then it succeeds and verifies existence
        assert respx_mock.calls.last.request.method == "GET"
        assert ref.resource_id.scope == "TestScope"
        assert ref.resource_id.code == "TestModel"

    def test_attach_when_missing(self, respx_mock):
        # given a custom data model does not exist
        respx_mock.get("/api/api/datamodel/Instrument/TestScope/Missing").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )
        # when we try to attach a reference to it
        ref = custom_data_model.CustomDataModelRef(
            id="test_ref",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="Missing"),
        )
        # then it raises an error
        with pytest.raises(RuntimeError, match="CustomDataModel Instrument/TestScope/Missing not found"):
            ref.attach(self.client)

    def test_attach_when_http_error(self, respx_mock):
        # given the API returns an error
        respx_mock.get("/api/api/datamodel/Instrument/TestScope/Error").mock(
            return_value=httpx.Response(500, json={"error": "Internal error"})
        )
        # when we try to attach a reference
        ref = custom_data_model.CustomDataModelRef(
            id="test_ref",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="Error"),
        )
        # then it raises the HTTP error
        with pytest.raises(httpx.HTTPStatusError):
            ref.attach(self.client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeCustomDataModelResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):
        # given we want to create a custom data model
        respx_mock.post("/api/api/datamodel/Instrument").mock(
            return_value=httpx.Response(
                201,
                json={
                    "dataModelSummary": {
                        "id": {"scope": "TestScope", "code": "MyModel"},
                        "entityType": "Instrument",
                    },
                    "version": {"asAtVersionNumber": 1},
                },
            )
        )

        # when we create it
        rating_prop = prop.DefinitionRef(
            id="rating_prop", domain=prop.Domain.Instrument, scope="TestScope", code="Rating"
        )
        model = custom_data_model.CustomDataModelResource(
            id="test_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="MyModel"),
            display_name="My Model",
            description="A test model",
            conditions="InstrumentDefinition.InstrumentType eq 'bond'",
            properties=[custom_data_model.DataModelProperty(property_key=rating_prop, required=True)],
        )
        state = model.create(self.client)

        # then the state is returned with entity_type, scope, code, and versions
        assert state["entity_type"] == "Instrument"
        assert state["scope"] == "TestScope"
        assert state["code"] == "MyModel"
        assert "source_version" in state
        assert "remote_version" in state
        assert state["remote_version"] == "1"

        # and the API was called with the correct data
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/datamodel/Instrument"
        body = json.loads(request.content)
        # resourceId should be serialized with camelCase as "id"
        assert "id" in body
        assert body["id"] == {"scope": "TestScope", "code": "MyModel"}
        assert body["displayName"] == "My Model"
        assert body["description"] == "A test model"
        assert body["conditions"] == "InstrumentDefinition.InstrumentType eq 'bond'"
        assert len(body["properties"]) == 1
        assert body["properties"][0]["propertyKey"] == "Instrument/TestScope/Rating"

    def test_create_with_parent(self, respx_mock):
        # given we want to create a custom data model with a parent
        respx_mock.post("/api/api/datamodel/Instrument").mock(
            return_value=httpx.Response(
                201,
                json={
                    "dataModelSummary": {
                        "id": {"scope": "TestScope", "code": "ChildModel"},
                        "entityType": "Instrument",
                    },
                    "version": {"asAtVersionNumber": 1},
                },
            )
        )

        # when we create it with a parent
        parent_ref = custom_data_model.CustomDataModelRef(
            id="parent",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="ParentModel"),
        )
        model = custom_data_model.CustomDataModelResource(
            id="child_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="ChildModel"),
            display_name="Child Model",
            description="Child model description",
            parent_data_model=parent_ref,
        )
        state = model.create(self.client)

        # then it succeeds
        assert state["scope"] == "TestScope"
        assert state["code"] == "ChildModel"

        # and parent is in the request body
        request = respx_mock.calls.last.request
        body = json.loads(request.content)
        assert body["parentDataModel"] == {"scope": "TestScope", "code": "ParentModel"}

    def test_create_without_optional_fields(self, respx_mock):
        # given we want to create a minimal custom data model
        respx_mock.post("/api/api/datamodel/Portfolio").mock(
            return_value=httpx.Response(
                201,
                json={
                    "dataModelSummary": {
                        "id": {"scope": "TestScope", "code": "SimpleModel"},
                        "entityType": "Portfolio",
                    },
                    "version": {"asAtVersionNumber": 1},
                },
            )
        )

        # when we create it
        model = custom_data_model.CustomDataModelResource(
            id="simple_model",
            entity_type="Portfolio",
            resource_id=ResourceId(scope="TestScope", code="SimpleModel"),
            display_name="Simple Model",
            description="Simple model description",
        )
        state = model.create(self.client)

        # then it succeeds
        assert state["entity_type"] == "Portfolio"
        assert state["scope"] == "TestScope"
        assert state["code"] == "SimpleModel"

        # and optional fields are not in the request body
        request = respx_mock.calls.last.request
        body = json.loads(request.content)
        assert "conditions" not in body
        assert "properties" not in body

    def test_update_with_no_changes(self, respx_mock):
        # given an existing custom data model
        respx_mock.get("/api/api/datamodel/Instrument/TestScope/MyModel").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dataModelSummary": {
                        "id": {"scope": "TestScope", "code": "MyModel"},
                        "entityType": "Instrument",
                    },
                    "version": {"asAtVersionNumber": 2},
                },
            )
        )

        model = custom_data_model.CustomDataModelResource(
            id="test_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="MyModel"),
            display_name="My Model",
            description="A test model",
        )

        # Calculate the source_version hash
        source_version = model.__get_content_hash__()

        old_state = SimpleNamespace(
            entity_type="Instrument",
            scope="TestScope",
            code="MyModel",
            source_version=source_version,
            remote_version="2",
        )

        # when we update it
        state = model.update(self.client, old_state)

        # then no change is detected
        assert state is None
        # and only a read was made, no PUT
        assert len(respx_mock.calls) == 1
        assert respx_mock.calls[0].request.method == "GET"

    def test_update_with_remote_changes(self, respx_mock):
        # given an existing custom data model with different content
        respx_mock.get("/api/api/datamodel/Instrument/TestScope/MyModel").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dataModelSummary": {
                        "id": {"scope": "TestScope", "code": "MyModel"},
                        "entityType": "Instrument",
                    },
                    "version": {"asAtVersionNumber": 2},
                },
            )
        )
        respx_mock.put("/api/api/datamodel/Instrument/TestScope/MyModel").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dataModelSummary": {
                        "id": {"scope": "TestScope", "code": "MyModel"},
                        "entityType": "Instrument",
                    },
                    "version": {"asAtVersionNumber": 3},
                },
            )
        )

        # when we update with new content
        new_property = prop.DefinitionRef(
            id="new_prop", domain=prop.Domain.Instrument, scope="TestScope", code="NewProperty"
        )
        model = custom_data_model.CustomDataModelResource(
            id="test_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="MyModel"),
            display_name="My Updated Model",
            description="Updated description",
            properties=[custom_data_model.DataModelProperty(property_key=new_property, required=False)],
        )

        old_state = SimpleNamespace(
            entity_type="Instrument",
            scope="TestScope",
            code="MyModel",
            source_version="old_source_hash",
            remote_version="2",
        )

        state = model.update(self.client, old_state)

        # then the update is applied
        assert state is not None
        assert state["entity_type"] == "Instrument"
        assert state["scope"] == "TestScope"
        assert state["code"] == "MyModel"
        assert "source_version" in state
        assert "remote_version" in state
        assert state["remote_version"] == "3"

        # and the API was called correctly
        assert len(respx_mock.calls) == 2
        assert respx_mock.calls[0].request.method == "GET"
        assert respx_mock.calls[1].request.method == "PUT"
        assert respx_mock.calls[1].request.url.path == "/api/api/datamodel/Instrument/TestScope/MyModel"

    def test_update_with_entity_type_change_deletes_and_creates(self, respx_mock):
        # given we want to change entity_type (which requires delete + create)
        respx_mock.delete("/api/api/datamodel/Instrument/TestScope/MyModel").mock(
            return_value=httpx.Response(204)
        )
        respx_mock.post("/api/api/datamodel/Portfolio").mock(
            return_value=httpx.Response(
                201,
                json={
                    "dataModelSummary": {
                        "id": {"scope": "TestScope", "code": "MyModel"},
                        "entityType": "Portfolio",
                    },
                    "version": {"asAtVersionNumber": 1},
                },
            )
        )

        # when we update with different entity_type
        model = custom_data_model.CustomDataModelResource(
            id="test_model",
            entity_type="Portfolio",
            resource_id=ResourceId(scope="TestScope", code="MyModel"),
            display_name="My Model",
            description="Model description",
        )

        old_state = SimpleNamespace(
            entity_type="Instrument",
            scope="TestScope",
            code="MyModel",
            source_version="some_hash",
            remote_version="2",
        )

        state = model.update(self.client, old_state)

        # then it deletes the old and creates the new
        assert state is not None
        assert state["entity_type"] == "Portfolio"
        assert state["scope"] == "TestScope"
        assert state["code"] == "MyModel"

        # verify both delete and create were called
        assert len(respx_mock.calls) == 2
        assert respx_mock.calls[0].request.method == "DELETE"
        assert respx_mock.calls[1].request.method == "POST"

    def test_delete(self, respx_mock):
        # given a custom data model exists
        respx_mock.delete("/api/api/datamodel/Instrument/TestScope/MyModel").mock(
            return_value=httpx.Response(204)
        )

        # when we delete it
        old_state = SimpleNamespace(entity_type="Instrument", scope="TestScope", code="MyModel")
        custom_data_model.CustomDataModelResource.delete(self.client, old_state)

        # then the API is called correctly
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/api/api/datamodel/Instrument/TestScope/MyModel"

    @staticmethod
    def test_deps_with_no_parent():
        # given a custom data model resource without parent
        model = custom_data_model.CustomDataModelResource(
            id="test_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="MyModel"),
            display_name="My Model",
            description="Model description",
        )

        # when we check its dependencies
        deps = model.deps()

        # then it has no dependencies
        assert deps == []

    @staticmethod
    def test_deps_with_parent():
        # given a custom data model resource with parent
        parent_ref = custom_data_model.CustomDataModelRef(
            id="parent",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="ParentModel"),
        )
        model = custom_data_model.CustomDataModelResource(
            id="child_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="ChildModel"),
            display_name="Child Model",
            description="Child description",
            parent_data_model=parent_ref,
        )

        # when we check its dependencies
        deps = model.deps()

        # then it depends on the parent
        assert len(deps) == 1
        assert deps[0] == parent_ref

    @staticmethod
    def test_deps_with_properties():
        # given a custom data model with property dependencies
        rating_prop = prop.DefinitionRef(
            id="rating_prop", domain=prop.Domain.Instrument, scope="TestScope", code="Rating"
        )
        maturity_prop = prop.DefinitionRef(
            id="maturity_prop", domain=prop.Domain.Instrument, scope="TestScope", code="MaturityDate"
        )
        model = custom_data_model.CustomDataModelResource(
            id="test_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="MyModel"),
            display_name="My Model",
            description="Model description",
            properties=[
                custom_data_model.DataModelProperty(property_key=rating_prop, required=True),
                custom_data_model.DataModelProperty(property_key=maturity_prop, required=False),
            ],
        )

        # when we check its dependencies
        deps = model.deps()

        # then it depends on both properties
        assert len(deps) == 2
        assert rating_prop in deps
        assert maturity_prop in deps

    @staticmethod
    def test_deps_with_parent_and_properties():
        # given a custom data model with both parent and property dependencies
        parent_ref = custom_data_model.CustomDataModelRef(
            id="parent",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="ParentModel"),
        )
        rating_prop = prop.DefinitionRef(
            id="rating_prop", domain=prop.Domain.Instrument, scope="TestScope", code="Rating"
        )
        model = custom_data_model.CustomDataModelResource(
            id="child_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="ChildModel"),
            display_name="Child Model",
            description="Child description",
            parent_data_model=parent_ref,
            properties=[custom_data_model.DataModelProperty(property_key=rating_prop, required=True)],
        )

        # when we check its dependencies
        deps = model.deps()

        # then it depends on both parent and property
        assert len(deps) == 2
        assert parent_ref in deps
        assert rating_prop in deps

    @staticmethod
    def test_dump():
        # given a custom data model resource
        rating_prop = prop.DefinitionRef(
            id="rating_prop", domain=prop.Domain.Instrument, scope="TestScope", code="Rating"
        )
        isin_identifier = custom_data_model.IdentifierType(
            identifier_key="Instrument/default/Isin", required=True
        )
        model = custom_data_model.CustomDataModelResource(
            id="test_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="MyModel"),
            display_name="My Model",
            description="Test description",
            conditions="AssetClass eq 'Credit'",
            properties=[custom_data_model.DataModelProperty(property_key=rating_prop, required=True)],
            identifier_types=[isin_identifier],
        )

        # when we dump it
        result = model.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )

        # then it's correctly serialized with camelCase
        # resourceId becomes "id" in API format
        assert result["id"]["scope"] == "TestScope"
        assert result["id"]["code"] == "MyModel"
        assert result["displayName"] == "My Model"
        assert result["description"] == "Test description"
        assert result["conditions"] == "AssetClass eq 'Credit'"
        properties = result.get("properties")
        assert properties is not None and len(properties) == 1
        # In dump context, propertyKey becomes a $ref
        assert properties[0]["propertyKey"] == {"$ref": "rating_prop"}

    @staticmethod
    def test_undump():
        # given dump data in camelCase with nested id
        # In reality, propertyKey would be deserialized from API as objects or refs
        data = {
            "id": {"scope": "TestScope", "code": "MyModel"},
            "displayName": "My Model",
            "description": "Test description",
            "conditions": "AssetClass eq 'Credit'",
        }

        # when we undump it
        result = custom_data_model.CustomDataModelResource.model_validate(
            data, context={"style": "undump", "id": "test_model", "entity_type": "Instrument"}
        )

        # then it's correctly populated
        assert result.id == "test_model"
        assert result.resource_id.scope == "TestScope"
        assert result.resource_id.code == "MyModel"
        assert result.display_name == "My Model"
        assert result.description == "Test description"
        assert result.conditions == "AssetClass eq 'Credit'"

    def test_read(self, respx_mock):
        # given a custom data model exists
        respx_mock.get("/api/api/datamodel/Instrument/TestScope/MyModel").mock(
            return_value=httpx.Response(
                200,
                json={
                    "dataModelSummary": {
                        "id": {"scope": "TestScope", "code": "MyModel"},
                        "displayName": "My Model",
                        "entityType": "Instrument",
                    }
                },
            )
        )

        # when we read it
        model = custom_data_model.CustomDataModelResource(
            id="test_model",
            entity_type="Instrument",
            resource_id=ResourceId(scope="TestScope", code="MyModel"),
            display_name="My Model",
            description="Model description",
        )
        old_state = SimpleNamespace(entity_type="Instrument", scope="TestScope", code="MyModel")
        result = model.read(self.client, old_state)

        # then we get the data back
        assert result["dataModelSummary"]["id"]["scope"] == "TestScope"
        assert result["dataModelSummary"]["id"]["code"] == "MyModel"
