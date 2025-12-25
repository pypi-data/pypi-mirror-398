import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import datatype, property
from fbnconfig import reference_list as rl
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)


@fixture()
def property_list_resources(setup_deployment):
    deployment_name = setup_deployment.name + "-property-list"
    # Create property definitions for use in property list
    string_property = property.DefinitionResource(
        id="string_prop",
        domain=property.Domain.Instrument,
        scope=deployment_name,
        code="string-prop",
        display_name="Test String Property",
        data_type_id=datatype.DataTypeRef(id="default_str", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="Test string property for property list",
        life_time=property.LifeTime.Perpetual,
    )
    number_property = property.DefinitionResource(
        id="number_prop",
        domain=property.Domain.Instrument,
        scope=deployment_name,
        code="number-prop",
        display_name="Test Number Property",
        data_type_id=property.ResourceId(scope="system", code="number"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="Test number property for property list",
        life_time=property.LifeTime.Perpetual,
    )
    # Create property list reference list
    property_reflist = rl.ReferenceListResource(
        id="property_reflist",
        scope=deployment_name,
        code="property-list-1",
        name="Test Property Reference List",
        description="A test reference list with property values",
        tags=["test", "integration", "property"],
        reference_list=rl.PropertyList(values=[
            rl.PropertyListItem(
                key=string_property,
                value=rl.PropertyValue(label_value="value-1")
            ),
            rl.PropertyListItem(
                key=number_property,
                value=rl.PropertyValue(metric_value=rl.MetricValue(value=123.45, unit="USD"))
            )
        ])
    )
    return [string_property, number_property, property_reflist]


@fixture()
def base_resources(setup_deployment):
    deployment_name = setup_deployment.name
    # Create a simple string list reference list
    string_reflist = rl.ReferenceListResource(
        id="string_reflist",
        scope=deployment_name,
        code="string-list-1",
        name="Test String Reference List",
        description="A test reference list with string values",
        tags=["test", "integration"],
        reference_list=rl.StringList(values=["value1", "value2", "value3"])
    )
    # Create a decimal list reference list
    decimal_reflist = rl.ReferenceListResource(
        id="decimal_reflist",
        scope=deployment_name,
        code="decimal-list-1",
        name="Test Decimal Reference List",
        description="A test reference list with decimal values",
        reference_list=rl.DecimalList(values=[1.5, 2.75, 3.0])
    )
    # Create an address key list reference list
    address_reflist = rl.ReferenceListResource(
        id="address_reflist",
        scope=deployment_name,
        code="address-key-list-1",
        name="Test Address Key Reference List",
        reference_list=rl.AddressKeyList(values=["Portfolio/Name", "Portfolio/Currency"])
    )
    return [string_reflist, decimal_reflist, address_reflist]


@fixture(scope="module")
def setup_deployment():
    deployment_name = gen("reference_list")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Clean up reference lists after tests
    try:
        client.delete(f"/api/api/referencelists/{deployment_name}/string-list-1")
        client.delete(f"/api/api/referencelists/{deployment_name}/decimal-list-1")
        client.delete(f"/api/api/referencelists/{deployment_name}/address-key-list-1")
        client.delete(f"/api/api/referencelists/{deployment_name}/property-list-1")
    except Exception:
        pass  # Ignore cleanup errors


def test_create(setup_deployment, base_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # Verify string reference list was created
    string_response = client.get(f"/api/api/referencelists/{setup_deployment.name}/string-list-1").json()
    assert string_response["id"]["scope"] == setup_deployment.name
    assert string_response["id"]["code"] == "string-list-1"
    assert string_response["name"] == "Test String Reference List"
    assert string_response["description"] == "A test reference list with string values"
    assert string_response["tags"] == ["test", "integration"]
    assert string_response["referenceList"]["values"] == ["value1", "value2", "value3"]
    assert string_response["referenceList"]["referenceListType"] == "StringList"
    # Verify decimal reference list was created
    decimal_response = client.get(
        f"/api/api/referencelists/{setup_deployment.name}/decimal-list-1"
    ).json()
    assert decimal_response["id"]["scope"] == setup_deployment.name
    assert decimal_response["id"]["code"] == "decimal-list-1"
    assert decimal_response["name"] == "Test Decimal Reference List"
    assert decimal_response["referenceList"]["values"] == [1.5, 2.75, 3.0]
    assert decimal_response["referenceList"]["referenceListType"] == "DecimalList"
    # Verify address key reference list was created
    address_response = client.get(
        f"/api/api/referencelists/{setup_deployment.name}/address-key-list-1"
    ).json()
    assert address_response["id"]["scope"] == setup_deployment.name
    assert address_response["id"]["code"] == "address-key-list-1"
    assert address_response["name"] == "Test Address Key Reference List"
    assert address_response["referenceList"]["values"] == ["Portfolio/Name", "Portfolio/Currency"]
    assert address_response["referenceList"]["referenceListType"] == "AddressKeyList"


def test_nochange(setup_deployment, base_resources):
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we apply it again
    update = fbnconfig.deployex(deployment, lusid_env, token)
    # then there are no changes
    ref_list_changes = [a.change for a in update if a.type == "ReferenceListResource"]
    assert ref_list_changes == ["nochange", "nochange", "nochange"]


def test_teardown(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we remove all the resources
    empty = fbnconfig.Deployment(deployment_name, [])
    update = fbnconfig.deployex(empty, lusid_env, token)
    # then there are no changes
    ref_list_changes = [a.change for a in update if a.type == "ReferenceListResource"]
    assert ref_list_changes == ["remove", "remove", "remove"]


def test_update(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    # Given we have deployed the base case
    initial = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(initial, lusid_env, token)
    # when we update a resource
    updated_resources = [
        # Update the string list with different values
        rl.ReferenceListResource(
            id="string_reflist",
            scope=deployment_name,
            code="string-list-1",
            name="Updated String Reference List",  # Changed name
            description="An updated test reference list with string values",  # Changed description
            tags=["test", "integration", "updated"],  # Added tag
            reference_list=rl.StringList(
                values=["newvalue1", "newvalue2"]
            )  # Changed values
        ),
        # Keep decimal list the same
        rl.ReferenceListResource(
            id="decimal_reflist",
            scope=deployment_name,
            code="decimal-list-1",
            name="Test Decimal Reference List",
            description="A test reference list with decimal values",
            reference_list=rl.DecimalList(values=[1.5, 2.75, 3.0])
        ),
        # Keep address key list the same
        rl.ReferenceListResource(
            id="address_reflist",
            scope=deployment_name,
            code="address-key-list-1",
            name="Test Address Key Reference List",
            reference_list=rl.AddressKeyList(values=["Portfolio/Name", "Portfolio/Currency"])
        ),
    ]
    # and deploy it
    updated_deployment = fbnconfig.Deployment(deployment_name, updated_resources)  # type: ignore
    update = fbnconfig.deployex(updated_deployment, lusid_env, token)
    # then we expect only the modified resource to change
    ref_list_changes = [a.change for a in update if a.type == "ReferenceListResource"]
    assert ref_list_changes == ["update", "nochange", "nochange"]
    # and it has the new values
    updated_response = client.get(
        f"/api/api/referencelists/{deployment_name}/string-list-1"
    ).json()
    assert updated_response["name"] == "Updated String Reference List"
    assert updated_response["description"] == "An updated test reference list with string values"
    assert updated_response["tags"] == ["test", "integration", "updated"]
    assert updated_response["referenceList"]["values"] == ["newvalue1", "newvalue2"]


def test_property_list_create(setup_deployment, property_list_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, property_list_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # Verify property list reference list was created
    deployment_name = setup_deployment.name + "-property-list"
    response = client.get(f"/api/api/referencelists/{deployment_name}/property-list-1").json()
    assert response["id"]["scope"] == deployment_name
    assert response["id"]["code"] == "property-list-1"
    assert response["name"] == "Test Property Reference List"
    assert response["description"] == "A test reference list with property values"
    assert response["tags"] == ["test", "integration", "property"]
    assert response["referenceList"]["referenceListType"] == "PropertyList"
    assert len(response["referenceList"]["values"]) == 2


def test_property_list_update(setup_deployment, property_list_resources):
    deployment_name = setup_deployment.name
    # Given we have deployed the base case
    initial = fbnconfig.Deployment(deployment_name, property_list_resources)
    fbnconfig.deployex(initial, lusid_env, token)
    # when we update the property list
    updated_resources = property_list_resources.copy()
    # Update the property list reference list
    updated_property_reflist = rl.ReferenceListResource(
        id="property_reflist",
        scope=deployment_name,
        code="property-list-1",
        name="Updated Property Reference List",  # Changed name
        description="An updated test reference list with property values",  # Changed description
        tags=["test", "integration", "property", "updated"],  # Added tag
        reference_list=rl.PropertyList(values=[
            rl.PropertyListItem(
                key=updated_resources[0],  # string_property
                value=rl.PropertyValue(
                    label_value="updated-value-1"  # Changed value
                )
            ),
            rl.PropertyListItem(
                key=updated_resources[1],  # number_property
                value=rl.PropertyValue(
                    metric_value=rl.MetricValue(value=999.99, unit="EUR")  # Changed value and unit
                )
            ),
            rl.PropertyListItem(
                key=updated_resources[0],  # Add another item with the same property
                value=rl.PropertyValue(
                    label_value="additional-value"
                )
            )
        ])
    )
    updated_resources[2] = updated_property_reflist
    # and deploy it
    updated_deployment = fbnconfig.Deployment(deployment_name, updated_resources)
    update = fbnconfig.deployex(updated_deployment, lusid_env, token)
    # then we expect the property list to be updated
    ref_list_changes = [
        a.change for a in update if a.type == "ReferenceListResource" and a.id == "property_reflist"
    ]
    assert ref_list_changes == ["update"]
    # and it has the new values
    updated_response = client.get(f"/api/api/referencelists/{deployment_name}/property-list-1").json()
    assert updated_response["name"] == "Updated Property Reference List"
    assert updated_response["description"] == "An updated test reference list with property values"
    assert updated_response["tags"] == ["test", "integration", "property", "updated"]
    assert len(updated_response["referenceList"]["values"]) == 3


def test_property_list_delete(setup_deployment, property_list_resources):
    deployment_name = setup_deployment.name
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(deployment_name, property_list_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we remove the property list (but keep the property definitions)
    resources_without_reflist = property_list_resources[:2]  # Keep only property definitions
    empty_deployment = fbnconfig.Deployment(deployment_name, resources_without_reflist)
    update = fbnconfig.deployex(empty_deployment, lusid_env, token)
    # then the reference list should be removed
    ref_list_changes = [a.change for a in update if a.type == "ReferenceListResource"]
    assert ref_list_changes == ["remove"]
