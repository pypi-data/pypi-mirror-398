import os

from pytest import fixture

import fbnconfig
from fbnconfig import customentity, datatype, property
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)


@fixture(scope="module")
def unique_name():
    deployment_name = gen("ce")
    print(f"\nRunning for deployment {deployment_name}...")
    return deployment_name


@fixture(scope="module")
def entity_type(unique_name):
    ce_type = fbnconfig.customentity.EntityTypeResource(
        id="ce2",
        entity_type_name=unique_name,
        display_name="Takeaway menu",
        description="A menu",
        field_schema=[
            fbnconfig.customentity.FieldDefinition(
                name="venueId",
                lifetime=fbnconfig.customentity.LifeTime.PERPETUAL,
                type=fbnconfig.customentity.FieldType.STRING,
                collection_type=fbnconfig.customentity.CollectionType.SINGLE,
                required=True,
            ),
            fbnconfig.customentity.FieldDefinition(
                name="venueOwner",
                lifetime=fbnconfig.customentity.LifeTime.TIMEVARIANT,
                type=fbnconfig.customentity.FieldType.STRING,
                required=True,
            ),
        ],
    )
    return ce_type


@fixture(scope="module")
def identifier_type(unique_name):
    identifier_type = property.DefinitionResource(
        id="exid",
        domain=property.Domain.CustomEntity,
        scope=f"ce-example-{unique_name}",
        code="ceidtype",
        display_name="Example Custom Entity ID",
        data_type_id=datatype.DataTypeRef(
            id="systemstring",
            scope="system",
            code="string",
        ),
        life_time=property.LifeTime.Perpetual,
        constraint_style=property.ConstraintStyle.Identifier,
    )
    return identifier_type


@fixture(scope="module")
def entity_instance(identifier_type, entity_type):
    ce_instance = customentity.EntityResource(
        id="ce1-instance",
        entity_type=entity_type,
        description="An example custom entity instance",
        display_name="Example Instance",
        identifiers=[
            customentity.EntityIdentifier(
                identifier_type=identifier_type,
                identifier_value="ce-example",
            )
        ],
        fields=[
            customentity.EntityField(
                name="venueId",
                value="Example Venue 1",
            ),
            customentity.EntityField(
                name="venueOwner",
                value="Example owner 1",
            )
        ]
    )
    return ce_instance


@fixture(scope="module")
def deployment(unique_name, entity_type, entity_instance):
    dep = fbnconfig.Deployment(unique_name, [entity_type, entity_instance])
    yield dep
    print("\nTearing down deployment but stranding entity type")
    fbnconfig.deployex(fbnconfig.Deployment(unique_name, [entity_type]), lusid_env, token)


def test_create(deployment, identifier_type):
    fbnconfig.deployex(deployment, lusid_env, token)
    res = client.get(f"/api/api/customentities/entitytypes/~{deployment.id}").json()
    assert res is not None
    res = client.get(f"/api/api/customentities/~{deployment.id}/{identifier_type.code}/ce-example",
        params={"identifierScope": identifier_type.scope}).json()
    assert res["fields"][0]["value"] == "Example Venue 1"


def test_nochange(deployment):
    fbnconfig.deployex(deployment, lusid_env, token)
    update = fbnconfig.deploy(deployment, lusid_env, token)
    assert [a.change for a in update] == ["nochange", "attach", "nochange", "nochange"]


def test_update_entity(deployment, entity_type, identifier_type):
    # given an existing deployment
    fbnconfig.deployex(deployment, lusid_env, token)
    # and an instance with some mnodified fields
    ce_instance = customentity.EntityResource(
        id="ce1-instance",
        entity_type=entity_type,
        description="An example custom entity instance",
        display_name="Example Instance",
        identifiers=[
            customentity.EntityIdentifier(
                identifier_type=identifier_type,
                identifier_value="ce-example",
            )
        ],
        fields=[
            customentity.EntityField(
                name="venueId",
                value="Different Venue 1",
            ),
            customentity.EntityField(
                name="venueOwner",
                value="Example owner 1",
            )
        ]
    )
    # when we deploy over the top
    mod_deploy = fbnconfig.Deployment(deployment.id, [entity_type, ce_instance])
    fbnconfig.deployex(mod_deploy, lusid_env, token)
    # then the field has changed
    res = client.get(f"/api/api/customentities/~{deployment.id}/{identifier_type.code}/ce-example",
        params={"identifierScope": identifier_type.scope}).json()
    assert res["fields"][0]["value"] == "Different Venue 1"


def test_update_entity_identifier(deployment, entity_type, identifier_type):
    # given an existing deployment
    fbnconfig.deployex(deployment, lusid_env, token)
    # and an instance with some mnodified fields
    ce_instance = customentity.EntityResource(
        id="ce1-instance",
        entity_type=entity_type,
        description="An example custom entity instance",
        display_name="Example Instance",
        identifiers=[
            customentity.EntityIdentifier(
                identifier_type=identifier_type,
                identifier_value="different-example",
            )
        ],
        fields=[
            customentity.EntityField(
                name="venueId",
                value="Different Venue 1",
            ),
            customentity.EntityField(
                name="venueOwner",
                value="Example owner 1",
            )
        ]
    )
    # when we deploy over the top
    mod_deploy = fbnconfig.Deployment(deployment.id, [entity_type, ce_instance])
    fbnconfig.deployex(mod_deploy, lusid_env, token)
    # then the field has changed
    res = client.get("/api/api/customentities/"
        f"~{deployment.id}/{identifier_type.code}/different-example",
        params={"identifierScope": identifier_type.scope}).json()
    assert res["fields"][0]["value"] == "Different Venue 1"
