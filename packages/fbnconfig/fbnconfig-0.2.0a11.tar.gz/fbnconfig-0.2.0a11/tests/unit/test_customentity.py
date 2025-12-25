import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import customentity, property

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeEntityTypeResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):
        respx_mock.post("/api/api/customentities/entitytypes").mock(
            return_value=httpx.Response(200, json={"entityType": "~typename"})
        )
        # given a desired definition with one field
        sut = customentity.EntityTypeResource(
            id="xyz",
            entity_type_name="animal",
            display_name="Animal",
            description="Not mineral or vegetable",
            field_schema=[
                customentity.FieldDefinition(
                    name="legs",
                    lifetime=customentity.LifeTime.PERPETUAL,
                    type=customentity.FieldType.DECIMAL,
                    required=False,
                )
            ],
        )
        # when we create it
        state = sut.create(self.client)
        # then the state the typename returned by the create call
        assert state == {"entitytype": "~typename"}
        # and a create request was sent without the startValue
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/customentities/entitytypes"
        assert json.loads(request.content) == {
            "entityTypeName": "animal",
            "displayName": "Animal",
            "description": "Not mineral or vegetable",
            "fieldSchema": [
                {
                    "name": "legs",
                    "lifetime": "Perpetual",
                    "type": "Decimal",
                    "description": "",
                    "collectionType": "Single",
                    "required": False,
                }
            ],
        }

    def test_update_with_no_changes(self, respx_mock):
        # given an existing CE where the field has a description
        respx_mock.get("/api/api/customentities/entitytypes/~whatevah").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entityTypeName": "animal",
                    "displayName": "Animal",
                    "description": "Not mineral or vegetable",
                    "fieldSchema": [
                        {
                            "name": "legs",
                            "lifetime": "Perpetual",
                            "type": "Decimal",
                            "description": "",
                            "collectionType": "Single",
                            "required": False,
                        }
                    ],
                },
            )
        )
        # and a desired which is the same but the field description is none
        sut = customentity.EntityTypeResource(
            id="xyz",
            entity_type_name="animal",
            display_name="Animal",
            description="Not mineral or vegetable",
            field_schema=[
                customentity.FieldDefinition(
                    name="legs",
                    lifetime=customentity.LifeTime.PERPETUAL,
                    type=customentity.FieldType.DECIMAL,
                    required=False,
                )
            ],
        )
        old_state = SimpleNamespace(entitytype="~whatevah")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is None
        assert state is None
        # and a read was made but no PUT

    def test_update_with_collection_single(self, respx_mock):
        # given an existing CE with a collection type of single
        # note, api will not return single here even if the user has
        # set it
        respx_mock.get("/api/api/customentities/entitytypes/~whatevah").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entityTypeName": "animal",
                    "displayName": "Animal",
                    "description": "Not mineral or vegetable",
                    "fieldSchema": [
                        {
                            "name": "arms",
                            "lifetime": "Perpetual",
                            "type": "Decimal",
                            "required": False,
                            # no collectionType member from GET
                        }
                    ],
                },
            )
        )
        # and a desired where the user has explicitly asked for single
        sut = customentity.EntityTypeResource(
            id="xyz",
            entity_type_name="animal",
            display_name="Animal",
            description="Not mineral or vegetable",
            field_schema=[
                customentity.FieldDefinition(
                    name="arms",
                    lifetime=customentity.LifeTime.PERPETUAL,
                    type=customentity.FieldType.DECIMAL,
                    collection_type=customentity.CollectionType.SINGLE,
                    required=False,
                )
            ],
        )
        old_state = SimpleNamespace(entitytype="~whatevah")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state None because there is no change
        assert state is None

    def test_update_with_changed_field(self, respx_mock):
        # given an existing CE with an arms field
        respx_mock.get("/api/api/customentities/entitytypes/~whatevah").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entityTypeName": "animal",
                    "displayName": "Animal",
                    "description": "Not mineral or vegetable",
                    "fieldSchema": [
                        {
                            "name": "arms",
                            "lifetime": "Perpetual",
                            "type": "Decimal",
                            "description": "a default descriptoin",
                        }
                    ],
                },
            )
        )
        respx_mock.put("/api/api/customentities/entitytypes/~whatevah").mock(
            return_value=httpx.Response(200, json={"entityType": "~whatevah"})
        )
        # and a desired with a legs field
        sut = customentity.EntityTypeResource(
            id="xyz",
            entity_type_name="animal",
            display_name="Animal",
            description="Not mineral or vegetable",
            field_schema=[
                customentity.FieldDefinition(
                    name="legs",
                    lifetime=customentity.LifeTime.PERPETUAL,
                    type=customentity.FieldType.DECIMAL,
                    required=False,
                )
            ],
        )
        old_state = SimpleNamespace(entitytype="~whatevah")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is the same
        assert state == {"entitytype": "~whatevah"}
        # and a put request was sent with legs
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/api/api/customentities/entitytypes/~whatevah"
        assert json.loads(request.content) == {
            "entityTypeName": "animal",
            "displayName": "Animal",
            "description": "Not mineral or vegetable",
            "fieldSchema": [
                {
                    "name": "legs",
                    "lifetime": "Perpetual",
                    "type": "Decimal",
                    "required": False,
                    "description": "",
                    "collectionType": "Single",
                }
            ],
        }

    def test_update_with_removed_field(self, respx_mock):
        # given an existing CE with arms and legs
        respx_mock.get("/api/api/customentities/entitytypes/~whatevah").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entityTypeName": "animal",
                    "displayName": "Animal",
                    "description": "Not mineral or vegetable",
                    "fieldSchema": [
                        {
                            "name": "legs",
                            "lifetime": "Perpetual",
                            "type": "Decimal",
                            "description": "a default descriptoin",
                        },
                        {
                            "name": "arms",
                            "lifetime": "Perpetual",
                            "type": "Decimal",
                            "description": "a default descriptoin",
                        },
                    ],
                },
            )
        )
        respx_mock.put("/api/api/customentities/entitytypes/~whatevah").mock(
            return_value=httpx.Response(200, json={"entityType": "~whatevah"})
        )
        # and a desired with a legs field
        sut = customentity.EntityTypeResource(
            id="xyz",
            entity_type_name="animal",
            display_name="Animal",
            description="Not mineral or vegetable",
            field_schema=[
                customentity.FieldDefinition(
                    name="legs",
                    lifetime=customentity.LifeTime.PERPETUAL,
                    type=customentity.FieldType.DECIMAL,
                    required=False,
                )
            ],
        )
        old_state = SimpleNamespace(entitytype="~whatevah")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is the same
        assert state == {"entitytype": "~whatevah"}
        # and a put request was sent with legs
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/api/api/customentities/entitytypes/~whatevah"
        assert json.loads(request.content) == {
            "entityTypeName": "animal",
            "displayName": "Animal",
            "description": "Not mineral or vegetable",
            "fieldSchema": [
                {
                    "name": "legs",
                    "lifetime": "Perpetual",
                    "type": "Decimal",
                    "required": False,
                    "description": "",
                    "collectionType": "Single",
                }
            ],
        }

    def test_update_with_additional_field(self, respx_mock):
        # given an existing CE with an arms field
        respx_mock.get("/api/api/customentities/entitytypes/~whatevah").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entityTypeName": "animal",
                    "displayName": "Animal",
                    "description": "Not mineral or vegetable",
                    "fieldSchema": [
                        {
                            "name": "arms",
                            "lifetime": "Perpetual",
                            "type": "Decimal",
                            "description": "a default descriptoin",
                        }
                    ],
                },
            )
        )
        respx_mock.put("/api/api/customentities/entitytypes/~whatevah").mock(
            return_value=httpx.Response(200, json={"entityType": "~whatevah"})
        )
        # and a desired with an arms and a legs field
        sut = customentity.EntityTypeResource(
            id="xyz",
            entity_type_name="animal",
            display_name="Animal",
            description="Not mineral or vegetable",
            field_schema=[
                customentity.FieldDefinition(
                    name="legs",
                    lifetime=customentity.LifeTime.PERPETUAL,
                    type=customentity.FieldType.DECIMAL,
                    required=False,
                ),
                customentity.FieldDefinition(
                    name="arms",
                    lifetime=customentity.LifeTime.PERPETUAL,
                    type=customentity.FieldType.DECIMAL,
                    required=False,
                ),
            ],
        )
        old_state = SimpleNamespace(entitytype="~whatevah")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is the same
        assert state == {"entitytype": "~whatevah"}
        # and a put request was sent with the new fields
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/api/api/customentities/entitytypes/~whatevah"
        assert json.loads(request.content) == {
            "entityTypeName": "animal",
            "displayName": "Animal",
            "description": "Not mineral or vegetable",
            "fieldSchema": [
                {
                    "name": "legs",
                    "lifetime": "Perpetual",
                    "type": "Decimal",
                    "required": False,
                    "description": "",
                    "collectionType": "Single",
                },
                {
                    "name": "arms",
                    "lifetime": "Perpetual",
                    "type": "Decimal",
                    "required": False,
                    "description": "",
                    "collectionType": "Single",
                },
            ],
        }

    def test_delete_throws(self):
        # given a resource that exists in the remnte
        old_state = SimpleNamespace(entitytype="~whatever")
        # when we delete it throws brcause uou cant delete a CE
        with pytest.raises(RuntimeError):
            customentity.EntityTypeResource.delete(self.client, old_state)

    def test_deps(self):
        sut = customentity.EntityTypeResource(
            id="xyz",
            entity_type_name="animal",
            display_name="Animal",
            description="Not mineral or vegetable",
            field_schema=[],
        )
        # it's deps are empty
        assert sut.deps() == []

    def test_dump(self):
        # given an entity type resource
        sut = customentity.EntityTypeResource(
            id="et1",
            entity_type_name="TestEntity",
            display_name="Test Entity Type",
            description="A test entity type",
            field_schema=[
                customentity.FieldDefinition(
                    name="field1",
                    lifetime=customentity.LifeTime.PERPETUAL,
                    type=customentity.FieldType.STRING,
                    collection_type=customentity.CollectionType.SINGLE,
                    required=True,
                    description="First field"
                ),
                customentity.FieldDefinition(
                    name="field2",
                    lifetime=customentity.LifeTime.TIMEVARIANT,
                    type=customentity.FieldType.DECIMAL,
                    collection_type=customentity.CollectionType.ARRAY,
                    required=False,
                    description="Second field"
                )
            ]
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
            "entityTypeName": "TestEntity",
            "displayName": "Test Entity Type",
            "description": "A test entity type",
            "fieldSchema": [
                {
                    "name": "field1",
                    "lifetime": "Perpetual",
                    "type": "String",
                    "collectionType": "Single",
                    "required": True,
                    "description": "First field"
                },
                {
                    "name": "field2",
                    "lifetime": "TimeVariant",
                    "type": "Decimal",
                    "collectionType": "Array",
                    "required": False,
                    "description": "Second field"
                }
            ]
        }

    def test_undump(self):
        # given a dumped entity type state
        dumped = {
            "entityTypeName": "TestEntity",
            "displayName": "Test Entity Type",
            "description": "A test entity type",
            "fieldSchema": [
                {
                    "name": "field1",
                    "lifetime": "Perpetual",
                    "type": "String",
                    "collectionType": "Single",
                    "required": True,
                    "description": "First field"
                },
                {
                    "name": "field2",
                    "lifetime": "TimeVariant",
                    "type": "Decimal",
                    "collectionType": "Array",
                    "required": False,
                    "description": "Second field"
                }
            ]
        }
        # when we undump it
        sut = customentity.EntityTypeResource.model_validate(
            dumped,
            context={
                "style": "undump",
                "$refs": {},
                "id": "et1",
            }
        )
        # then the id has been extracted from the context
        assert sut.id == "et1"
        assert sut.entity_type_name == "TestEntity"
        assert sut.display_name == "Test Entity Type"
        assert sut.description == "A test entity type"
        # and the field schema is correctly reconstructed
        assert len(sut.field_schema) == 2
        # first field
        assert sut.field_schema[0].name == "field1"
        assert sut.field_schema[0].lifetime == customentity.LifeTime.PERPETUAL
        assert sut.field_schema[0].type == customentity.FieldType.STRING
        assert sut.field_schema[0].collection_type == customentity.CollectionType.SINGLE
        assert sut.field_schema[0].required is True
        assert sut.field_schema[0].description == "First field"
        # second field
        assert sut.field_schema[1].name == "field2"
        assert sut.field_schema[1].lifetime == customentity.LifeTime.TIMEVARIANT
        assert sut.field_schema[1].type == customentity.FieldType.DECIMAL
        assert sut.field_schema[1].collection_type == customentity.CollectionType.ARRAY
        assert sut.field_schema[1].required is False
        assert sut.field_schema[1].description == "Second field"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeEntityTypeRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_success(self, respx_mock):
        respx_mock.get("/api/api/customentities/entitytypes/TestEntity").mock(
            return_value=httpx.Response(200, json={
                "entityTypeName": "TestEntity",
                "displayName": "Test Entity Type",
                "description": "A test entity type",
                "fieldSchema": []
            })
        )
        # given an entity type ref
        sut = customentity.EntityTypeRef(
            id="et1",
            entity_type_name="TestEntity"
        )
        # when we attach it (should not raise)
        sut.attach(self.client)
        # then a GET request was made
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == "/api/api/customentities/entitytypes/TestEntity"

    def test_attach_not_found(self, respx_mock):
        respx_mock.get("/api/api/customentities/entitytypes/NonExistentEntity").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )
        # given an entity type ref for a non-existent entity
        sut = customentity.EntityTypeRef(
            id="et1",
            entity_type_name="NonExistentEntity"
        )
        # when we try to attach it
        with pytest.raises(RuntimeError) as exc_info:
            sut.attach(self.client)
        # then it raises a descriptive error
        assert "Custom Entity Definition NonExistentEntity does not exist" in str(exc_info.value)

    def test_attach_server_error(self, respx_mock):
        respx_mock.get("/api/api/customentities/entitytypes/TestEntity").mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )
        # given an entity type ref
        sut = customentity.EntityTypeRef(
            id="et1",
            entity_type_name="TestEntity"
        )
        # when we try to attach it and the server returns an error
        with pytest.raises(httpx.HTTPStatusError):
            sut.attach(self.client)

    def test_dump(self):
        # given an entity type ref
        sut = customentity.EntityTypeRef(
            id="et1",
            entity_type_name="TestEntity"
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then the dumped state excludes the id field
        assert dumped == {
            "entityTypeName": "TestEntity"
        }

    def test_undump(self):
        # given dumped entity type ref data with id included
        dumped = {
            "entityTypeName": "TestEntity"
        }
        # when we create it directly (since Ref classes don't typically use model_validate with context)
        sut = customentity.EntityTypeRef(
            id="et1",
            entity_type_name=dumped["entityTypeName"]
        )
        # then the fields are correctly set
        assert sut.id == "et1"
        assert sut.entity_type_name == "TestEntity"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeEntityResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture()
    def entity_type(self):
        return customentity.EntityTypeRef(
            id="et1",
            entity_type_name="TestEntity"
        )

    @pytest.fixture()
    def entity_identifier(self):
        return property.DefinitionRef(
            id="id1",
            domain=property.Domain.CustomEntity,
            scope="default",
            code="ClientInternal"
        )

    def test_create(self, respx_mock, entity_type, entity_identifier):
        respx_mock.post("/api/api/customentities/~TestEntity").mock(
            return_value=httpx.Response(200, json={})
        )
        # and a desired entity with fields and identifiers
        sut = customentity.EntityResource(
            id="ent1",
            entity_type=entity_type,
            display_name="Test Entity",
            description="A test entity",
            fields=[
                customentity.EntityField(
                    name="field1",
                    value="test_value"
                )
            ],
            identifiers=[
                customentity.EntityIdentifier(
                    identifier_type=entity_identifier,
                    identifier_value="TEST001"
                )
            ]
        )
        # when we create it
        state = sut.create(self.client)
        # then the state contains the entity details
        assert "content_hash" in state
        assert state["entity_type"] == "TestEntity"
        assert state["identifier_type"] == "ClientInternal"
        assert state["identifier_value"] == "TEST001"
        assert state["identifier_scope"] == "default"
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/customentities/~TestEntity"
        request_data = json.loads(request.content)
        assert request_data == {
            "fields": [{
                "name": "field1", "value": "test_value"
            }],
            "identifiers": [{
                "identifierScope": "default",
                "identifierType": "ClientInternal",
                "identifierValue": "TEST001"
            }],
            "description": "A test entity",
            "displayName": "Test Entity"
        }

    def test_update_no_changes(self, entity_type, entity_identifier):
        # given an entity with a specific content hash
        sut = customentity.EntityResource(
            id="ent1",
            entity_type=entity_type,
            display_name="Test Entity",
            description="A test entity",
            fields=[
                customentity.EntityField(
                    name="field1",
                    value="test_value"
                )
            ],
            identifiers=[
                customentity.EntityIdentifier(
                    identifier_type=entity_identifier,
                    identifier_value="TEST001"
                )
            ]
        )
        # and an old state with the same content hash
        desired = sut.model_dump(mode="json", exclude_none=True,
                                 by_alias=True, exclude={"id", "scope", "entity_type"})
        sorted_desired = json.dumps(desired, sort_keys=True)
        from hashlib import sha256
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        old_state = SimpleNamespace(
            entity_type="TestEntity",
            identifier_scope="default",
            identifier_type="ClientInternal",
            identifier_value="TEST001",
            content_hash=content_hash
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then no update is needed
        assert state is None

    def test_update_with_identifier_changes(self, respx_mock, entity_type, entity_identifier):
        respx_mock.delete("/api/api/customentities/~TestEntity/ClientInternal/TEST001").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/api/api/customentities/~TestEntity").mock(
            return_value=httpx.Response(200, json={})
        )
        # given an entity
        sut = customentity.EntityResource(
            id="ent1",
            entity_type=entity_type,
            display_name="Updated Entity",
            description="An updated entity",
            fields=[
                customentity.EntityField(
                    name="field1",
                    value="updated_value"
                )
            ],
            identifiers=[
                customentity.EntityIdentifier(
                    identifier_type=entity_identifier,
                    identifier_value="CHANGED"
                )
            ]
        )
        # and an old state with a different identifier value
        old_state = SimpleNamespace(
            entity_type="TestEntity",
            identifier_scope="default",
            identifier_type="ClientInternal",
            identifier_value="TEST001",
            content_hash="different_hash"
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is updated
        assert state is not None
        assert state["entity_type"] == "TestEntity"
        # and the delete and post calls were made because this is a delete/recrete operation

    def test_update_with_non_identifier_changes(self, respx_mock, entity_type, entity_identifier):
        respx_mock.post("/api/api/customentities/~TestEntity").mock(
            return_value=httpx.Response(200, json={})
        )
        # given an entity
        sut = customentity.EntityResource(
            id="ent1",
            entity_type=entity_type,
            display_name="Updated Entity",
            description="An updated entity",
            fields=[
                customentity.EntityField(
                    name="field1",
                    value="updated_value"
                )
            ],
            identifiers=[
                customentity.EntityIdentifier(
                    identifier_type=entity_identifier,
                    identifier_value="TEST001"
                )
            ]
        )
        # and an old state the same identifier but a different hash
        old_state = SimpleNamespace(
            entity_type="TestEntity",
            identifier_scope="default",
            identifier_type="ClientInternal",
            identifier_value="TEST001",
            content_hash="different_hash"
        )
        # when we update it
        sut.update(self.client, old_state)
        # then only a put call is made

    def test_delete(self, respx_mock):
        respx_mock.delete("/api/api/customentities/~TestEntity/ClientInternal/TEST001").mock(
            return_value=httpx.Response(200, json={})
        )
        # given an old state
        old_state = SimpleNamespace(
            entity_type="TestEntity",
            identifier_scope="default",
            identifier_type="ClientInternal",
            identifier_value="TEST001"
        )
        # when we delete it
        customentity.EntityResource.delete(self.client, old_state)
        # then a DELETE request was sent
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/api/api/customentities/~TestEntity/ClientInternal/TEST001"
        assert "identifierScope=default" in str(request.url)

    def test_deps(self, entity_type, entity_identifier):
        # given an entity with an entity type reference
        sut = customentity.EntityResource(
            id="ent1",
            entity_type=entity_type,
            display_name="Test Entity",
            description="A test entity",
            fields=[],
            identifiers=[
                customentity.EntityIdentifier(
                    identifier_type=entity_identifier,
                    identifier_value="TEST001"
                )
            ]
        )
        # when we get its dependencies
        deps = sut.deps()
        # then it depends on the entity type
        assert deps == [entity_type, entity_identifier]

    def test_deps_including_property(self, entity_type, entity_identifier):
        # given an entity with a property
        prop_ref = property.DefinitionRef(
            id="p1",
            domain=property.Domain.CustomEntity,
            scope="default",
            code="legCount"
        )
        sut = customentity.EntityResource(
            id="ent1",
            entity_type=entity_type,
            display_name="Test Entity",
            description="A test entity",
            fields=[],
            identifiers=[
                customentity.EntityIdentifier(
                    identifier_type=entity_identifier,
                    identifier_value="TEST001"
                )
            ],
            properties=[
                customentity.PropertyValue(
                    property_key=prop_ref,
                    metric_value=customentity.MetricValue(value=3)
                )
            ]
        )
        # when we get its dependencies
        deps = sut.deps()
        # then it depends on the entity type
        assert deps == [entity_type, entity_identifier, prop_ref]

    def test_dump(self, entity_type, entity_identifier):
        # given an entity resource
        sut = customentity.EntityResource(
            id="ent1",
            entity_type=entity_type,
            display_name="Test Entity",
            description="A test entity",
            fields=[
                customentity.EntityField(
                    name="field1",
                    value="test_value"
                ),
                customentity.EntityField(
                    name="field2",
                    value=123.45
                )
            ],
            identifiers=[
                customentity.EntityIdentifier(
                    identifier_type=entity_identifier,
                    identifier_value="TEST001",
                )
            ]
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then the dumped state excludes the id field and uses $ref for references
        assert dumped == {
            "entityType": {
                "$ref": "et1"
            },
            "displayName": "Test Entity",
            "description": "A test entity",
            "fields": [{
                "name": "field1",
                "value": "test_value"
            }, {
                "name": "field2",
                "value": 123.45
            }],
            "identifiers": [{
                "identifierType": {
                    "$ref": "id1"
                },
                "identifierValue": "TEST001",
            }]
        }

    def test_undump(self, entity_type, entity_identifier):
        # given dumped entity data with $ref style references
        dumped = {
            "entityType": {
                "$ref": "et1"
            },
            "displayName": "Test Entity",
            "description": "A test entity",
            "fields": [{
                "name": "field1",
                "value": "test_value"
            }, {
                "name": "field2",
                "value": 123.45
            }],
            "identifiers": [{
                "identifierType": {
                    "$ref": "id1"
                },
                "identifierValue": "TEST001",
            }]
        }
        refs = {
            "et1": entity_type,
            "id1": entity_identifier
        }
        # when we undump it
        sut = customentity.EntityResource.model_validate(
            dumped,
            context={
                "style": "undump",
                "$refs": refs,
                "id": "ent1",
            }
        )
        # then the id has been extracted from the context
        assert sut.id == "ent1"
        assert sut.display_name == "Test Entity"
        assert sut.description == "A test entity"
        # and the entity type is correctly reconstructed
        assert isinstance(sut.entity_type, customentity.EntityTypeRef)
        assert sut.entity_type.entity_type_name == "TestEntity"
        # and the fields are correctly reconstructed
        assert len(sut.fields) == 2
        assert sut.fields[0].name == "field1"
        assert sut.fields[0].value == "test_value"
        assert sut.fields[1].name == "field2"
        assert sut.fields[1].value == 123.45
        # and the identifiers are correctly reconstructed
        assert len(sut.identifiers) == 1
        assert sut.identifiers[0].identifier_value == "TEST001"
        assert sut.identifiers[0].identifier_type == entity_identifier

    def test_read(self, entity_type, entity_identifier, respx_mock):
        # given an entity instance
        respx_mock.get("/api/api/customentities/~TestEntity/ClientInternal/TEST001?identifierScope=default").mock(
            return_value=httpx.Response(
                200,
                json={
                    "href": "https://myco.lusid.com/api/api/customentities/~SupportTicket",
                    "entityType": "~SupportTicket",
                    "version": {
                      "effectiveFrom": "0001-01-01T00:00:00.0000000+00:00",
                      "asAtDate": "2022-03-02T09:00:00.0000000+00:00"
                    },
                    "displayName": "Portfolio Access Denied",
                    "description": "User cannot access the portfolio",
                    "identifiers": [
                      {
                        "identifierScope": "default",
                        "identifierType": "CLientInternal",
                        "identifierValue": "TEST001",
                        "effectiveFrom": "0001-01-01T00:00:00.0000000+00:00",
                        "effectiveUntil": "9999-12-31T23:59:59.9999999+00:00"
                      }
                    ],
                    "fields": [
                      {
                        "name": "field1",
                        "value": "AcmeLtd",
                        "effectiveFrom": "0001-01-01T00:00:00.0000000+00:00",
                        "effectiveUntil": "9999-12-31T23:59:59.9999999+00:00"
                      },
                    ],
                    "relationships": []
                }
            )
        )
        # when we create a desired entity instance
        sut = customentity.EntityResource(
            id="ent1",
            entity_type=entity_type,
            display_name="Test Entity",
            description="A test entity",
            fields=[
                customentity.EntityField(
                    name="field1",
                    value="test_value"
                )
            ],
            identifiers=[
                customentity.EntityIdentifier(
                    identifier_type=entity_identifier,
                    identifier_value="NOT_TEST001"
                )
            ]
        )
        # and we load it from some old state
        old_state = SimpleNamespace(
            entity_type="TestEntity",
            identifier_scope="default",
            identifier_type="ClientInternal",
            identifier_value="TEST001",
            content_hash=None
        )
        result = sut.read(self.client, old_state)
        # then the get request matches the mock
        # and we get a result
        assert result is not None
        assert len(result["fields"]) == 1
