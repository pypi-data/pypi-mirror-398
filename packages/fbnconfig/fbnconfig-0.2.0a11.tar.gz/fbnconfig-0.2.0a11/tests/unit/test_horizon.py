import json
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import datatype as dt
from fbnconfig import horizon
from fbnconfig import property as prop

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeIntegrationInstanceResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):
        respx_mock.post("/horizon/api/integrations/instances").mock(
            return_value=httpx.Response(200, json={"id": "instance-123"})
        )
        # given a desired integration instance with cron trigger
        sut = horizon.IntegrationInstanceResource(
            id="test-integration",
            integration_type="luminesce",
            name="Test Integration",
            description="A test integration instance",
            enabled=True,
            triggers=[horizon.Trigger(type="cron", cron_expression="0 8 * * MON-FRI", time_zone="UTC")],
            details={"database": "test_db", "schema": "test_schema"},
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with instance ID
        assert state["instanceId"] == "instance-123"
        assert "content_hash" in state
        # and the instance id is captured on the resource
        assert sut.instance_id == "instance-123"
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/horizon/api/integrations/instances"
        request_body = json.loads(request.content)
        expected_body = {
            "integrationType": "luminesce",
            "name": "Test Integration",
            "description": "A test integration instance",
            "enabled": True,
            "triggers": [{"type": "cron", "cronExpression": "0 8 * * MON-FRI", "timeZone": "UTC"}],
            "details": {"database": "test_db", "schema": "test_schema"},
        }
        assert request_body == expected_body

    def test_read(self, respx_mock):
        respx_mock.get("/horizon/api/integrations/instances").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "instance-123",
                        "integrationType": "luminesce",
                        "name": "Test Integration",
                        "description": "A test integration instance",
                        "enabled": True,
                        "triggers": [
                            {"type": "cron", "cronExpression": "0 8 * * MON-FRI", "timeZone": "UTC"}
                        ],
                        "details": {"database": "test_db"},
                    },
                    {
                        "id": "instance-456",
                        "integrationType": "rest-api",
                        "name": "Other Integration",
                        "description": "Another integration",
                        "enabled": False,
                        "triggers": [],
                        "details": {},
                    },
                ],
            )
        )
        # given an integration instance resource
        sut = horizon.IntegrationInstanceResource(
            id="test-integration",
            integration_type="luminesce",
            name="Test Integration",
            description="A test integration instance",
            enabled=True,
            triggers=[],
            details={},
        )
        # and an old state with instance ID
        old_state = SimpleNamespace(instanceId="instance-123")
        # when we read it
        result = sut.read(self.client, old_state)
        # then the remote data is returned
        assert result["id"] == "instance-123"
        assert result["integrationType"] == "luminesce"
        assert result["name"] == "Test Integration"
        assert result["description"] == "A test integration instance"
        assert result["enabled"] is True
        # and a GET request was made
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == "/horizon/api/integrations/instances"

    def test_update_with_no_changes(self, respx_mock):
        # given an integration instance with known content
        sut = horizon.IntegrationInstanceResource(
            id="test-integration",
            integration_type="luminesce",
            name="Test Integration",
            description="A test integration instance",
            enabled=True,
            triggers=[horizon.Trigger(type="cron", cron_expression="0 8 * * MON-FRI", time_zone="UTC")],
            details={"database": "test_db", "schema": "test_schema"},
        )
        # and an old state with the same content hash
        desired = sut.model_dump(mode="json", exclude_none=True, by_alias=True)
        content_hash = sha256(json.dumps(desired, sort_keys=True).encode()).hexdigest()
        old_state = SimpleNamespace(instanceId="instance-123", content_hash=content_hash)
        # when we update it
        state = sut.update(self.client, old_state)
        # then no update is needed
        assert state is None
        # and no HTTP requests were made
        assert len(respx_mock.calls) == 0

    def test_update_with_changes(self, respx_mock):
        respx_mock.put("/horizon/api/integrations/instances/instance-123").mock(
            return_value=httpx.Response(200, json={})
        )
        # given an integration instance with updated properties
        sut = horizon.IntegrationInstanceResource(
            id="test-integration",
            integration_type="luminesce",
            name="Updated Integration",
            description="Updated description",
            enabled=False,
            triggers=[
                horizon.Trigger(
                    type="cron", cron_expression="0 9 * * MON-FRI", time_zone="America/New_York"
                )
            ],
            details={"database": "updated_db", "schema": "updated_schema"},
        )
        # and an old state with different content hash
        old_state = SimpleNamespace(instanceId="instance-123", content_hash="old_hash")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is returned with updated content hash
        assert state is not None
        assert state["instanceId"] == "instance-123"
        assert "content_hash" in state
        assert (
            state["content_hash"] == "fbf509d2f0ca569fb40d0be1eaba6d90366f1175323cbaf9b6fe45533afcb8c1"
        )
        # and a PUT request was sent
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/horizon/api/integrations/instances/instance-123"
        request_body = json.loads(request.content)
        expected_body = {
            "id": "instance-123",
            "integrationType": "luminesce",
            "name": "Updated Integration",
            "description": "Updated description",
            "enabled": False,
            "triggers": [
                {"type": "cron", "cronExpression": "0 9 * * MON-FRI", "timeZone": "America/New_York"}
            ],
            "details": {"database": "updated_db", "schema": "updated_schema"},
        }
        assert request_body == expected_body

    def test_delete(self, respx_mock):
        respx_mock.delete("/horizon/api/integrations/instances/instance-123").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a resource that exists in the remote
        old_state = SimpleNamespace(instanceId="instance-123")
        # when we delete it
        horizon.IntegrationInstanceResource.delete(self.client, old_state)
        # then a DELETE request was sent
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/horizon/api/integrations/instances/instance-123"

    def test_deps(self):
        # given an integration instance resource
        sut = horizon.IntegrationInstanceResource(
            id="test-integration",
            integration_type="luminesce",
            name="Test Integration",
            description="A test integration instance",
            enabled=True,
            triggers=[],
            details={},
        )
        # when we get its dependencies
        deps = sut.deps()
        # then it has no dependencies
        assert deps == []

    def test_dump_integration_instance(self):
        # given an integration instance resource with triggers and details
        sut = horizon.IntegrationInstanceResource(
            id="dump-integration",
            integration_type="luminesce",
            name="Dump Test Integration",
            description="Integration for dump testing",
            enabled=True,
            triggers=[horizon.Trigger(type="cron", cron_expression="0 8 * * MON-FRI", time_zone="UTC")],
            details={"database": "dump_db", "schema": "dump_schema", "timeout": 300},
        )
        # when we dump it
        dumped = sut.model_dump(
            mode="json", by_alias=True, exclude_none=True, round_trip=True, context={"style": "dump"}
        )
        # then the dumped data contains all expected fields
        assert dumped == {
            "description": "Integration for dump testing",
            "details": {"database": "dump_db", "schema": "dump_schema", "timeout": 300},
            "enabled": True,
            "integrationType": "luminesce",
            "name": "Dump Test Integration",
            "triggers": [{"cronExpression": "0 8 * * MON-FRI", "timeZone": "UTC", "type": "cron"}],
        }

    def test_undump_integration_instance(self):
        # given dump data for an integration instance
        data = {
            "description": "Integration for dump testing",
            "details": {"database": "dump_db", "schema": "dump_schema", "timeout": 300},
            "enabled": True,
            "integrationType": "luminesce",
            "name": "Dump Test Integration",
            "triggers": [{"cronExpression": "0 8 * * MON-FRI", "timeZone": "UTC", "type": "cron"}],
        }
        # when we undump it with id from context
        result = horizon.IntegrationInstanceResource.model_validate(
            data, context={"style": "dump", "id": "undump-integration"}
        )
        # then it's correctly populated including id from context
        assert result.id == "undump-integration"
        assert result.integration_type == "luminesce"
        assert len(result.triggers) == 1
        assert result.triggers[0].type == "cron"
        assert result.triggers[0].cron_expression == "0 8 * * MON-FRI"
        assert result.details["database"] == "dump_db"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeOptionalPropsResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def test_instance(self):
        """Common test integration instance."""
        instance = horizon.IntegrationInstanceResource(
            id="test-integration",
            integration_type="luminesce",
            name="Test Integration",
            description="A test integration instance",
            enabled=True,
            triggers=[],
            details={},
        )
        instance.instance_id = "instance-123"
        return instance

    @pytest.fixture
    def prop_def1(self):
        """First test property definition."""
        return prop.DefinitionResource(
            id="test-prop1",
            domain=prop.Domain.Portfolio,
            scope="TestScope",
            code="Property1",
            display_name="Property 1",
            data_type_id=dt.DataTypeRef(id="string-dt", scope="system", code="string"),
            property_description="First property",
        )

    @pytest.fixture
    def prop_def2(self):
        """Second test property definition."""
        return prop.DefinitionResource(
            id="test-prop2",
            domain=prop.Domain.Portfolio,
            scope="TestScope",
            code="Property2",
            display_name="Property 2",
            data_type_id=dt.DataTypeRef(id="string-dt", scope="system", code="string"),
            property_description="Second property",
        )

    def test_create(self, respx_mock, test_instance, prop_def1, prop_def2):
        respx_mock.put("/horizon/api/integrations/instances/configuration/luminesce/instance-123").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a desired optional props resource
        sut = horizon.OptionalPropsResource(
            id="test-props",
            props=[
                horizon.OptionalProp(
                    property=prop_def1,
                    display_name_override="Property 1",
                    description_override="First property",
                ),
                horizon.OptionalProp(
                    property=prop_def2,
                    display_name_override="Property 2",
                    description_override="Second property",
                    entity_type="Portfolio",
                    entity_sub_type=["Fund"],
                    vendor_package=["vendor1"],
                ),
            ],
            instance=test_instance,
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with instance info
        assert state["integrationType"] == "luminesce"
        assert state["instanceId"] == "instance-123"
        assert "content_hash" in state
        # and a PUT request was sent
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert (
            request.url.path
            == "/horizon/api/integrations/instances/configuration/luminesce/instance-123"
        )
        request_body = json.loads(request.content)
        expected_body = {
            "Portfolio/TestScope/Property1": {
                "displayNameOverride": "Property 1",
                "descriptionOverride": "First property",
            },
            "Portfolio/TestScope/Property2": {
                "displayNameOverride": "Property 2",
                "descriptionOverride": "Second property",
                "entityType": "Portfolio",
                "entitySubType": ["Fund"],
                "vendorPackage": ["vendor1"],
            },
        }
        assert request_body == expected_body

    def test_read(self, respx_mock, test_instance):
        respx_mock.get("/horizon/api/integrations/instances/configuration/luminesce/instance-123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "Portfolio/TestScope/Property1": {
                        "displayNameOverride": "Property 1",
                        "descriptionOverride": "First property",
                    },
                    "Portfolio/TestScope/Property2": {
                        "displayNameOverride": "Property 2",
                        "descriptionOverride": "Second property",
                        "entityType": "Portfolio",
                        "entitySubType": ["Fund"],
                        "vendorPackage": ["vendor1"],
                    },
                    "Instrument/GlobalScope/InstrumentProperty": {
                        "displayNameOverride": "Instrument Property",
                        "descriptionOverride": "Property for instruments",
                    },
                },
            )
        )
        # given an optional props resource
        sut = horizon.OptionalPropsResource(id="test-props", props=[], instance=test_instance)
        # and an old state with instance info
        old_state = SimpleNamespace(integrationType="luminesce", instanceId="instance-123")
        # when we read it
        result = sut.read(self.client, old_state)
        # then the remote configuration is returned with multiple properties
        assert len(result) == 3
        assert "Portfolio/TestScope/Property1" in result
        assert result["Portfolio/TestScope/Property1"]["displayNameOverride"] == "Property 1"
        assert "Portfolio/TestScope/Property2" in result
        assert result["Portfolio/TestScope/Property2"]["displayNameOverride"] == "Property 2"
        assert result["Portfolio/TestScope/Property2"]["descriptionOverride"] == "Second property"
        # and a GET request was made

    def test_update_with_no_changes(self, respx_mock, test_instance, prop_def1):
        # given an optional props resource with properties
        sut = horizon.OptionalPropsResource(
            id="test-props",
            props=[
                horizon.OptionalProp(
                    property=prop_def1,
                    display_name_override="Property 1",
                    description_override="First property",
                )
            ],
            instance=test_instance,
        )
        # and an old state with the same content hash
        desired = sut.model_dump(mode="json", exclude_none=True, by_alias=True)
        content_hash = sha256(json.dumps(desired, sort_keys=True).encode()).hexdigest()
        old_state = SimpleNamespace(
            integrationType="luminesce", instanceId="instance-123", content_hash=content_hash
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then no update is needed
        assert state is None
        # and no HTTP requests were made
        assert len(respx_mock.calls) == 0

    def test_update_with_changes(self, respx_mock, test_instance, prop_def1, prop_def2):
        respx_mock.put("/horizon/api/integrations/instances/configuration/luminesce/instance-123").mock(
            return_value=httpx.Response(200, json={})
        )
        # given an optional props resource with updated properties
        sut = horizon.OptionalPropsResource(
            id="test-props",
            props=[
                horizon.OptionalProp(
                    property=prop_def1,
                    display_name_override="Updated Property 1",
                    description_override="Updated first property",
                ),
                horizon.OptionalProp(
                    property=prop_def2,
                    display_name_override="New Property 2",
                    description_override="New second property",
                ),
            ],
            instance=test_instance,
        )
        # and an old state with different content hash
        old_state = SimpleNamespace(
            integrationType="luminesce", instanceId="instance-123", content_hash="old_hash"
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is returned with updated content hash
        assert state is not None
        assert state["integrationType"] == "luminesce"
        assert state["instanceId"] == "instance-123"
        assert "content_hash" in state
        assert state["content_hash"] != "old_hash"
        # and a PUT request was sent
        request = respx_mock.calls.last.request
        request_body = json.loads(request.content)
        expected_body = {
            "Portfolio/TestScope/Property1": {
                "displayNameOverride": "Updated Property 1",
                "descriptionOverride": "Updated first property",
            },
            "Portfolio/TestScope/Property2": {
                "displayNameOverride": "New Property 2",
                "descriptionOverride": "New second property",
            },
        }
        assert request_body == expected_body

    def test_update_with_instance_change(self, respx_mock, prop_def1):
        respx_mock.put("/horizon/api/integrations/instances/configuration/rest-api/instance-456").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.put("/horizon/api/integrations/instances/configuration/luminesce/instance-123").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a new integration instance with different type and ID
        new_instance = horizon.IntegrationInstanceResource(
            id="new-integration",
            integration_type="rest-api",
            name="New Integration",
            description="A new integration instance",
            enabled=True,
            triggers=[],
            details={},
        )
        new_instance.instance_id = "instance-456"
        # and an optional props resource pointing to the new instance
        sut = horizon.OptionalPropsResource(
            id="test-props",
            props=[
                horizon.OptionalProp(
                    property=prop_def1,
                    display_name_override="Property 1",
                    description_override="First property",
                )
            ],
            instance=new_instance,
        )
        # and an old state with different instance info
        old_state = SimpleNamespace(
            integrationType="luminesce", instanceId="instance-123", content_hash="old_hash"
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is returned with new instance info
        assert state is not None
        assert state["integrationType"] == "rest-api"
        assert state["instanceId"] == "instance-456"
        assert "content_hash" in state
        # and two requests were made: create for new instance, delete for old
        assert len(respx_mock.calls) == 2
        create_request = respx_mock.calls[0].request
        assert create_request.method == "PUT"
        assert (
            create_request.url.path
            == "/horizon/api/integrations/instances/configuration/rest-api/instance-456"
        )
        delete_request = respx_mock.calls[1].request
        assert delete_request.method == "PUT"
        assert (
            delete_request.url.path
            == "/horizon/api/integrations/instances/configuration/luminesce/instance-123"
        )
        delete_body = json.loads(delete_request.content)
        assert delete_body == {}

    def test_delete(self, respx_mock):
        respx_mock.put("/horizon/api/integrations/instances/configuration/luminesce/instance-123").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a resource that exists in the remote
        old_state = SimpleNamespace(integrationType="luminesce", instanceId="instance-123")
        # when we delete it
        horizon.OptionalPropsResource.delete(self.client, old_state)
        # then a PUT request with empty body was sent
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert (
            request.url.path
            == "/horizon/api/integrations/instances/configuration/luminesce/instance-123"
        )
        request_body = json.loads(request.content)
        assert request_body == {}

    def test_deps(self, test_instance, prop_def1):
        # given an optional props resource
        sut = horizon.OptionalPropsResource(
            id="test-props",
            props=[
                horizon.OptionalProp(
                    property=prop_def1,
                    display_name_override="Property 1",
                    description_override="First property",
                )
            ],
            instance=test_instance,
        )
        # when we get its dependencies
        deps = sut.deps()
        # then it should return both the instance and property definition
        assert len(deps) == 2
        assert test_instance in deps
        assert prop_def1 in deps

    def test_deps_with_multiple_props(self, test_instance, prop_def1, prop_def2):
        # given a property reference
        prop_ref = prop.DefinitionRef(
            id="test-prop-ref",
            domain=prop.Domain.Portfolio,
            scope="test-scope",
            code="test-property-ref",
        )
        # and an optional props resource with multiple properties
        sut = horizon.OptionalPropsResource(
            id="test-props",
            props=[
                horizon.OptionalProp(
                    property=prop_def1,
                    display_name_override="Property 1",
                    description_override="First property",
                ),
                horizon.OptionalProp(
                    property=prop_ref,
                    display_name_override="Property 2",
                    description_override="Second property",
                ),
            ],
            instance=test_instance,
        )
        # when we get its dependencies
        deps = sut.deps()
        # then it should return the instance and all property definitions
        assert len(deps) == 3
        assert test_instance in deps
        assert prop_def1 in deps
        assert prop_ref in deps

    def test_dump_optional_props_with_ref_serialization(self):
        # given an integration instance
        instance = horizon.IntegrationInstanceResource(
            id="dump-integration",
            integration_type="luminesce",
            name="Dump Integration",
            description="Integration for dump testing",
            enabled=True,
            triggers=[],
            details={},
        )
        # and property definitions
        prop_def = prop.DefinitionResource(
            id="dump-prop-def",
            domain=prop.Domain.Portfolio,
            scope="dump-scope",
            code="dump-property",
            display_name="Dump Property",
            data_type_id=dt.DataTypeRef(id="string-dt", scope="system", code="string"),
            property_description="Property for dump testing",
        )
        prop_ref = prop.DefinitionRef(
            id="dump-prop-ref",
            domain=prop.Domain.Portfolio,
            scope="dump-scope",
            code="dump-ref-property",
        )
        # and an optional props resource
        sut = horizon.OptionalPropsResource(
            id="dump-props",
            props=[
                horizon.OptionalProp(
                    property=prop_def,
                    display_name_override="Dump Override 1",
                    description_override="First dump property",
                ),
                horizon.OptionalProp(
                    property=prop_ref,
                    display_name_override="Dump Override 2",
                    description_override="Second dump property",
                    entity_type="Portfolio",
                    entity_sub_type=["Fund", "Equity"],
                    vendor_package=["vendor1", "vendor2"],
                ),
            ],
            instance=instance,
        )
        # when we dump it
        dumped = sut.model_dump(
            mode="json", by_alias=True, exclude_none=True, round_trip=True, context={"style": "dump"}
        )
        # then referenced objects should be serialized as $refs
        assert len(dumped["props"]) == 2
        # Check first property has $ref
        first_prop = dumped["props"][0]
        assert first_prop["property"] == {"$ref": "dump-prop-def"}
        assert first_prop["displayNameOverride"] == "Dump Override 1"
        assert first_prop["descriptionOverride"] == "First dump property"
        # Check second property has $ref and optional fields
        second_prop = dumped["props"][1]
        assert second_prop["property"] == {"$ref": "dump-prop-ref"}
        assert second_prop["displayNameOverride"] == "Dump Override 2"
        assert second_prop["descriptionOverride"] == "Second dump property"
        assert second_prop["entityType"] == "Portfolio"
        assert second_prop["entitySubType"] == ["Fund", "Equity"]
        assert second_prop["vendorPackage"] == ["vendor1", "vendor2"]
        # Check instance is serialized as $ref
        assert dumped["instance"] == {"$ref": "dump-integration"}

    def test_undump_optional_props_with_refs(self):
        # given dump data with property and instance $refs
        data = {
            "props": [
                {
                    "property": {"$ref": "undump-prop-def"},
                    "displayNameOverride": "Undump Override 1",
                    "descriptionOverride": "First undump property",
                },
                {
                    "property": {"$ref": "undump-prop-ref"},
                    "displayNameOverride": "Undump Override 2",
                    "descriptionOverride": "Second undump property",
                    "entityType": "Instrument",
                    "entitySubType": ["Bond"],
                    "vendorPackage": ["bloomberg"],
                },
            ],
            "instance": {"$ref": "undump-integration"},
        }
        # and refs in context
        instance = horizon.IntegrationInstanceResource(
            id="undump-integration",
            integration_type="rest-api",
            name="Undump Integration",
            description="Integration for undump testing",
            enabled=True,
            triggers=[],
            details={},
        )
        prop_def = prop.DefinitionResource(
            id="undump-prop-def",
            domain=prop.Domain.Portfolio,
            scope="undump-scope",
            code="undump-property-1",
            display_name="Undump Property 1",
            data_type_id=dt.DataTypeRef(id="string-dt", scope="system", code="string"),
            property_description="First undump property",
        )
        prop_ref = prop.DefinitionRef(
            id="undump-prop-ref",
            domain=prop.Domain.Instrument,
            scope="undump-scope",
            code="undump-property-2",
        )
        refs_dict = {
            "undump-integration": instance,
            "undump-prop-def": prop_def,
            "undump-prop-ref": prop_ref,
        }
        # when we undump it
        result = horizon.OptionalPropsResource.model_validate(
            data, context={"style": "dump", "$refs": refs_dict, "id": "undump-props"}
        )
        # then properties and instance are correctly resolved
        assert result.id == "undump-props"
        assert result.instance == instance
        assert len(result.props) == 2
        # and properties
        first_prop = result.props[0]
        assert first_prop.property == prop_def
        second_prop = result.props[1]
        assert second_prop.property == prop_ref
