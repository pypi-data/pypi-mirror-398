
import datetime as dt
import json
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import httpx
import pytest

from fbnconfig import identifier_definition, property

TEST_BASE = "https://foo.lusid.com"


@pytest.mark.respx(base_url=TEST_BASE)
class TestIdentifierDefinitionRef:
    """Test IdentifierDefinitionRef functionality."""

    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def identifier_definition_ref(self):
        """Create a identifier definition reference for testing."""
        return identifier_definition.IdentifierDefinitionRef(
            id="identDefId",
            domain=identifier_definition.SupportedDomain.Instrument,
            identifier_scope="testScope",
            identifier_type="testType"
        )

    def test_identifier_def_ref_attach_success(self, respx_mock, identifier_definition_ref):
        respx_mock.get("/api/api/identifierdefinitions/Instrument/testScope/testType").mock(
            return_value=httpx.Response(200, json={})
        )
        # Should not raise an error
        identifier_definition_ref.attach(self.client)

    def test_identifier_def_ref_attach_not_found(self, respx_mock, identifier_definition_ref):
        respx_mock.get("/api/api/identifierdefinitions/Instrument/testScope/testType").mock(
            return_value=httpx.Response(404)
        )
        with pytest.raises(RuntimeError) as ex:
            identifier_definition_ref.attach(self.client)
        assert "Identifier Definition Instrument/testScope/testType does not exist" in str(ex.value)

    def test_identifier_def_ref_attach_when_http_error(self, respx_mock, identifier_definition_ref):
        respx_mock.get("/api/api/identifierdefinitions/Instrument/testScope/testType").mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        sut = identifier_definition_ref
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class TestIdentifierDefinitionResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def simple_identifier(self):
        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.Instrument, scope="sc1", code="cd4"
        )

        perp_prop = identifier_definition.PropertyValue(
            property_key=property_example,
            label_value="Hello"
        )

        return identifier_definition.IdentifierDefinitionResource(
            id="identDefId",
            domain=identifier_definition.SupportedDomain.Instrument,
            identifier_scope="testScope",
            identifier_type="testType",
            life_time=property.LifeTime.Perpetual,
            hierarchy_usage="ParentIdentifier",
            hierarchy_level="hierarchyLevelExample",
            display_name="example_display_name",
            description="example_description",
            properties=[perp_prop]
        )

    def test_read_ident_def(self, respx_mock, simple_identifier):
        response = {
            "href": "http://example.lusid.com/api/identifierdefinitions/Instrument/oldScope/oldType",
            "domain": "Instrument",
            "identifierScope": "oldScope",
            "identifierType": "oldType",
            "lifeTime": "Perpetual",
            "hierarchyUsage": "MasterIdentifer",
            "hierarchyLevel": "Exchange",
            "displayName": "My Identifier Definition",
            "description": "Optional Identifier definition description",
            "properties": {},
            "version": {
                "effectiveFrom": "2024-06-01T10:30:00.0000000+00:00",
                "asAtDate": "2024-06-01T10:30:00.0000000+00:00",
                "asAtCreated": "2024-06-01T10:30:00.0000000+00:00",
                "userIdCreated": "User1",
                "requestIdCreated": "RequestId1",
                "reasonCreated": "",
                "asAtModified": "2024-06-04T10:30:00.0000000+00:00",
                "userIdModified": "User2",
                "requestIdModified": "RequestId2",
                "reasonModified": "",
                "asAtVersionNumber": 2,
                "entityUniqueId": "00000000-0000-0000-0000-000000000000"
            }
        }

        respx_mock.get(
            "/api/api/identifierdefinitions/Instrument/oldScope/oldType"
        ).mock(return_value=httpx.Response(200, json=response))

        client = self.client
        old_state = SimpleNamespace(
            domain="Instrument",
            identifier_scope="oldScope",
            identifier_type="oldType"
        )
        actual_response = simple_identifier.read(client, old_state)

        # Actual response should have popped href
        assert actual_response != response

        # Simulate pop for response and now assert they're the same
        response.pop("href", None)
        assert actual_response == response

    def test_create_ident_def(self, respx_mock, simple_identifier):
        respx_mock.post("/api/api/identifierdefinitions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "version": {
                        "asAtVersionNumber": 2,
                    }
                }
            )
        )
        client = self.client
        state = simple_identifier.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
            "hierarchyUsage": "ParentIdentifier",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "Instrument/sc1/cd4": {
                    "key": "Instrument/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            }
        }

        source_version = simple_identifier.__get_content_hash__()

        # Verify returned state
        assert state == {
            "domain": "Instrument",
            "identifier_scope": "testScope",
            "identifier_type": "testType",
            "source_version": source_version,
            "remote_version": 2
        }

    def test_create_ident_def_prop_with_time_var(self, respx_mock):
        respx_mock.post("/api/api/identifierdefinitions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "version": {
                        "asAtVersionNumber": 2,
                    }
                }
            )
        )
        client = self.client
        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.Instrument, scope="sc1", code="cd4"
        )

        effective_from = dt.datetime(2000, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))
        effective_until = dt.datetime(2030, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))

        time_prop = identifier_definition.PropertyValue(
            property_key=property_example,
            label_value="Hello",
            effective_from=effective_from,
            effective_until=effective_until
        )

        sut = identifier_definition.IdentifierDefinitionResource(
            id="identDefId",
            domain=identifier_definition.SupportedDomain.Instrument,
            identifier_scope="testScope",
            identifier_type="testType",
            life_time=property.LifeTime.Perpetual,
            hierarchy_usage="ParentIdentifier",
            hierarchy_level="hierarchyLevelExample",
            display_name="example_display_name",
            description="example_description",
            properties=[time_prop]
        )

        state = sut.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
            "hierarchyUsage": "ParentIdentifier",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "Instrument/sc1/cd4": {
                    "key": "Instrument/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                    "effectiveFrom": "2000-10-02T13:30:45Z",
                    "effectiveUntil": "2030-10-02T13:30:45Z"
                }
            }
        }

        source_version = sut.__get_content_hash__()

        # Verify returned state
        assert state == {
            "domain": "Instrument",
            "identifier_scope": "testScope",
            "identifier_type": "testType",
            "source_version": source_version,
            "remote_version": 2
        }

    def test_create_ident_def_defaults_fields(self, respx_mock):
        respx_mock.post("/api/api/identifierdefinitions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "version": {
                        "asAtVersionNumber": 2,
                    }
                }
            )
        )
        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.Instrument, scope="sc1", code="cd4"
        )

        perp_prop = identifier_definition.PropertyValue(
            property_key=property_example,
            label_value="Hello"
        )

        missing_hierarchy_usage_field = identifier_definition.IdentifierDefinitionResource(
            id="identDefId",
            domain=identifier_definition.SupportedDomain.Instrument,
            identifier_scope="testScope",
            identifier_type="testType",
            life_time=property.LifeTime.Perpetual,
            hierarchy_level="hierarchyLevelExample",
            display_name="example_display_name",
            description="example_description",
            properties=[perp_prop]
        )

        client = self.client
        state = missing_hierarchy_usage_field.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure - hierarchyUsage is defaulted
        assert body == {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "Instrument/sc1/cd4": {
                    "key": "Instrument/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            }
        }

        source_version = missing_hierarchy_usage_field.__get_content_hash__()

        # Verify returned state
        assert state == {
            "domain": "Instrument",
            "identifier_scope": "testScope",
            "identifier_type": "testType",
            "source_version": source_version,
            "remote_version": 2
        }

    def test_create_ident_def_missing_null_fields(self, respx_mock):
        respx_mock.post("/api/api/identifierdefinitions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "version": {
                        "asAtVersionNumber": 2,
                    }
                }
            )
        )
        missing_fields_ident_def = identifier_definition.IdentifierDefinitionResource(
            id="identDefId",
            domain=identifier_definition.SupportedDomain.Instrument,
            identifier_scope="testScope",
            identifier_type="testType",
            life_time=property.LifeTime.Perpetual,
        )

        client = self.client
        state = missing_fields_ident_def.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure - hierarchyUsage is defaulted
        assert body == {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
        }

        source_version = missing_fields_ident_def.__get_content_hash__()

        # Verify returned state
        assert state == {
            "domain": "Instrument",
            "identifier_scope": "testScope",
            "identifier_type": "testType",
            "source_version": source_version,
            "remote_version": 2
        }

    def test_update_ident_def_without_change(self, respx_mock, simple_identifier):
        respx_mock.get(
            "/api/api/identifierdefinitions/Instrument/"
            f"{simple_identifier.identifier_scope}/{simple_identifier.identifier_type}"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "version": {
                        "asAtVersionNumber": 2,
                    }
                }
            )
        )

        # Set source_version hash to the same to test no change
        source_version = simple_identifier.__get_content_hash__()

        old_state = SimpleNamespace(
            domain="Instrument",
            identifier_scope="testScope",
            identifier_type="testType",
            remote_version=2,
            source_version=source_version
        )

        # Same hash so we expect to return None
        result = simple_identifier.update(self.client, old_state)
        assert result is None

    def test_update_ident_def_with_change(self, respx_mock, simple_identifier):
        respx_mock.get(
            "/api/api/identifierdefinitions/Instrument/"
            "testScope/testType"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Instrument",
                    "identifierScope": "testScope",
                    "identifierType": "testType",
                    "lifeTime": "Perpetual",
                    "hierarchyUsage": "MasterIdentifier",
                    "hierarchyLevel": "Exchange",
                    "displayName": "My Identifier Definition",
                    "description": "Optional Identifier definition description",
                    "properties": {},
                    "version": {
                        "effectiveFrom": "2024-06-01T10:30:00.0000000+00:00",
                        "asAtDate": "2024-06-01T10:30:00.0000000+00:00",
                        "asAtCreated": "2024-06-01T10:30:00.0000000+00:00",
                        "userIdCreated": "User1",
                        "requestIdCreated": "RequestId1",
                        "reasonCreated": "",
                        "asAtModified": "2024-06-04T10:30:00.0000000+00:00",
                        "userIdModified": "User2",
                        "requestIdModified": "RequestId2",
                        "reasonModified": "",
                        "asAtVersionNumber": 2,
                        "entityUniqueId": "00000000-0000-0000-0000-000000000000"
                    }
                }
            )
        )
        respx_mock.put(
            "/api/api/identifierdefinitions/Instrument/"
            "testScope/testType"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "version": {
                        "asAtVersionNumber": 2,
                    }
                }
            )
        )

        source_version = simple_identifier.__get_content_hash__()

        old_state = SimpleNamespace(
            domain="Instrument",
            identifier_scope="testScope",
            identifier_type="testType",
            remote_version=123456789,
            source_version=source_version
        )

        # Different hashes so we expect change
        state = simple_identifier.update(self.client, old_state)
        req = respx_mock.calls.last.request
        assert req.method == "PUT"
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "lifeTime": "Perpetual",
            "hierarchyUsage": "ParentIdentifier",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "Instrument/sc1/cd4": {
                    "key": "Instrument/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            }
        }

        # Verify returned state
        assert state == {
            "domain": "Instrument",
            "identifier_scope": "testScope",
            "identifier_type": "testType",
            "source_version": source_version,
            "remote_version": 2
        }

    def test_update_ident_def_change_domain(self, respx_mock, simple_identifier):
        respx_mock.delete(
            "/api/api/identifierdefinitions/Person/"
            "testScope/testType"
            ).mock(
            side_effect=[httpx.Response(200, json={})]
        )
        respx_mock.post("/api/api/identifierdefinitions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "version": {
                        "asAtVersionNumber": 2,
                    }
                }
            )
        )

        source_version = simple_identifier.__get_content_hash__()

        #  Domain is different - should call delete, create
        old_state = SimpleNamespace(
            domain="Person",
            identifier_scope="testScope",
            identifier_type="testType",
            remote_version=2,
            source_version=source_version
        )

        state = simple_identifier.update(self.client, old_state)

        #  Assert Delete and Post are called
        assert respx_mock.calls[0].request.method == "DELETE"
        assert respx_mock.calls.last.request.method == "POST"
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
            "hierarchyUsage": "ParentIdentifier",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "Instrument/sc1/cd4": {
                    "key": "Instrument/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            }
        }

        # Verify returned state
        assert state == {
            "domain": "Instrument",
            "identifier_scope": "testScope",
            "identifier_type": "testType",
            "source_version": source_version,
            "remote_version": 2
        }

    def test_update_ident_def_change_type(self, respx_mock, simple_identifier):
        respx_mock.delete(
            "/api/api/identifierdefinitions/Instrument/"
            "testScope/differentType"
            ).mock(
            side_effect=[httpx.Response(200, json={})]
        )
        respx_mock.post("/api/api/identifierdefinitions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "version": {
                        "asAtVersionNumber": 2,
                    }
                }
            )
        )

        source_version = simple_identifier.__get_content_hash__()

        #  Type is different - should call delete, create
        old_state = SimpleNamespace(
            domain="Instrument",
            identifier_scope="testScope",
            identifier_type="differentType",
            remote_version=2,
            source_version=source_version
        )

        state = simple_identifier.update(self.client, old_state)

        #  Assert Delete and Post are called
        assert respx_mock.calls[0].request.method == "DELETE"
        assert respx_mock.calls.last.request.method == "POST"
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
            "hierarchyUsage": "ParentIdentifier",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "Instrument/sc1/cd4": {
                    "key": "Instrument/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            }
        }

        # Verify returned state
        assert state == {
            "domain": "Instrument",
            "identifier_scope": "testScope",
            "identifier_type": "testType",
            "source_version": source_version,
            "remote_version": 2
        }

    def test_update_ident_def_change_scope(self, respx_mock, simple_identifier):
        respx_mock.delete(
            "/api/api/identifierdefinitions/Instrument/"
            "oldScope/testType"
            ).mock(
            side_effect=[httpx.Response(200, json={})]
        )
        respx_mock.post("/api/api/identifierdefinitions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "version": {
                        "asAtVersionNumber": 2,
                    }
                }
            )
        )

        source_version = simple_identifier.__get_content_hash__()

        #  Scope is different - should call delete, create
        old_state = SimpleNamespace(
            domain="Instrument",
            identifier_scope="oldScope",
            identifier_type="testType",
            remote_version=2,
            source_version=source_version
        )

        state = simple_identifier.update(self.client, old_state)

        #  Assert Delete and Post are called
        assert respx_mock.calls[0].request.method == "DELETE"
        assert respx_mock.calls.last.request.method == "POST"
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
            "hierarchyUsage": "ParentIdentifier",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "Instrument/sc1/cd4": {
                    "key": "Instrument/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            }
        }

        # Verify returned state
        assert state == {
            "domain": "Instrument",
            "identifier_scope": "testScope",
            "identifier_type": "testType",
            "source_version": source_version,
            "remote_version": 2
        }

    def test_delete_ident_def(self, respx_mock):
        respx_mock.delete(
            "/api/api/identifierdefinitions/Instrument/"
            "testScope/testType"
            ).mock(
            side_effect=[httpx.Response(200, json={})]
        )
        client = self.client
        old_state = SimpleNamespace(
            domain="Instrument",
            identifier_scope="testScope",
            identifier_type="testType"
        )
        identifier_definition.IdentifierDefinitionResource.delete(client, old_state)
        assert respx_mock.calls.last.request.method == "DELETE"

    def test_deps_without(self, simple_identifier):
        sut = identifier_definition.IdentifierDefinitionResource(
            id="identDefId",
            domain=identifier_definition.SupportedDomain.Instrument,
            identifier_scope="testScope",
            identifier_type="testType",
            life_time=property.LifeTime.Perpetual,
        )
        assert sut.deps() == []

    def test_deps_with_properties(self, simple_identifier):
        sut = simple_identifier
        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.Instrument, scope="sc1", code="cd4"
        )
        assert sut.deps() == [property_example]

    def test_dump(self):
        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.Instrument, scope="sc1", code="cd4"
        )

        effective_from = dt.datetime(2000, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))
        effective_until = dt.datetime(2030, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))

        time_prop = identifier_definition.PropertyValue(
            property_key=property_example,
            label_value="Hello",
            effective_from=effective_from,
            effective_until=effective_until
        )

        sut = identifier_definition.IdentifierDefinitionResource(
            id="identDefId",
            domain=identifier_definition.SupportedDomain.Instrument,
            identifier_scope="testScope",
            identifier_type="testType",
            life_time=property.LifeTime.Perpetual,
            hierarchy_usage="ParentIdentifier",
            hierarchy_level="hierarchyLevelExample",
            display_name="example_display_name",
            description="example_description",
            properties=[time_prop]
        )

        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )

        assert result == {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
            "hierarchyUsage": "ParentIdentifier",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": [
                {
                    "propertyKey": {
                        "$ref": "property_id"
                    },
                    "labelValue": "Hello",
                    "effectiveFrom": "2000-10-02T13:30:45+00:00",
                    "effectiveUntil": "2030-10-02T13:30:45+00:00"
                }
            ]
        }

    def test_undump(self):
        prop1 = property.DefinitionRef(
            id="property_id", domain=property.Domain.Instrument, scope="sc1", code="TestProp"
        )

        effective_from = dt.datetime(2000, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))
        effective_until = dt.datetime(2030, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))

        data = {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
            "hierarchyUsage": "ParentIdentifier",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": [
                {
                    "propertyKey": {
                        "$ref": "property_id"
                    },
                    "labelValue": "Test Label",
                    "effectiveFrom": "2000-10-02T13:30:45+00:00",
                    "effectiveUntil": "2030-10-02T13:30:45+00:00"
                }
            ]
        }

        result = identifier_definition.IdentifierDefinitionResource.model_validate(
            data,
            context={
                "style": "undump",
                "$refs": {
                    "property_id": prop1
                },
                "id": "undump_ident_def",
            }
        )

        assert result.id == "undump_ident_def"
        assert result.domain == identifier_definition.SupportedDomain.Instrument
        assert result.identifier_scope == "testScope"
        assert result.identifier_type == "testType"
        assert result.life_time == "Perpetual"
        assert result.hierarchy_usage == "ParentIdentifier"
        assert result.hierarchy_level == "hierarchyLevelExample"
        assert result.display_name == "example_display_name"
        assert result.description == "example_description"
        assert result.properties
        assert len(result.properties) == 1
        assert result.properties[0].property_key == prop1
        assert result.properties[0].property_key.code == "TestProp"
        assert result.properties[0].label_value == "Test Label"
        assert result.properties[0].effective_from == effective_from
        assert result.properties[0].effective_until == effective_until

    def test_parse_api_format(self):
        prop1 = property.DefinitionRef(
            id="property_id", domain=property.Domain.Instrument, scope="sc1", code="TestProp"
        )

        effective_from = dt.datetime(2000, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))
        effective_until = dt.datetime(2030, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))

        data = {
            "domain": "Instrument",
            "identifierScope": "testScope",
            "identifierType": "testType",
            "lifeTime": "Perpetual",
            "hierarchyUsage": "ParentIdentifier",
            "hierarchyLevel": "hierarchyLevelExample",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "Instrument/sc1/cd4": {
                    "key": {
                        "$ref": "property_id"
                    },
                    "labelValue": "Test Label",
                    "effectiveFrom": "2000-10-02T13:30:45Z",
                    "effectiveUntil": "2030-10-02T13:30:45Z"
                },
            }
        }

        result = identifier_definition.IdentifierDefinitionResource.model_validate(
            data,
            context={
                "style": "api",
                "$refs": {
                    "property_id": prop1
                },
                "id": "undump_ident_def",
            }
        )

        assert result.id == "undump_ident_def"
        assert result.domain == identifier_definition.SupportedDomain.Instrument
        assert result.identifier_scope == "testScope"
        assert result.identifier_type == "testType"
        assert result.life_time == "Perpetual"
        assert result.hierarchy_usage == "ParentIdentifier"
        assert result.hierarchy_level == "hierarchyLevelExample"
        assert result.display_name == "example_display_name"
        assert result.description == "example_description"
        assert result.properties
        assert len(result.properties) == 1
        assert result.properties[0].property_key == prop1
        assert result.properties[0].property_key.code == "TestProp"
        assert result.properties[0].label_value == "Test Label"
        assert result.properties[0].effective_from == effective_from
        assert result.properties[0].effective_until == effective_until
