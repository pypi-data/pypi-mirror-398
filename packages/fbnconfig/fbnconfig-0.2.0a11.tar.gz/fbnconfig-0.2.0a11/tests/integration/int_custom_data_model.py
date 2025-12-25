import os
from types import SimpleNamespace

import pytest
from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
import tests.integration.custom_data_model as custom_data_model_config
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
def setup_deployment():
    deployment_name = gen("custom_data_model")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Teardown: Clean up resources after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)


def test_create(setup_deployment):
    """Test creating custom data models."""
    fbnconfig.deployex(custom_data_model_config.configure(setup_deployment), lusid_env, token)
    # Verify the base model was created
    base_model = client.get(f"/api/api/datamodel/Instrument/{setup_deployment.name}/BaseInstrumentModel")
    assert base_model.status_code == 200
    base_data = base_model.json()
    assert base_data["dataModelSummary"]["displayName"] == "Base Instrument Model"

    # Verify the bond model was created
    bond_model = client.get(f"/api/api/datamodel/Instrument/{setup_deployment.name}/BondModel")
    assert bond_model.status_code == 200
    bond_data = bond_model.json()
    assert bond_data["dataModelSummary"]["displayName"] == "Bond Data Model"
    # Verify it has inherited properties from parent
    assert "inherited" in bond_data
    assert "properties" in bond_data["inherited"]
    # Should have inherited the rating property from base model
    inherited_props = [p["propertyKey"] for p in bond_data["inherited"]["properties"]]
    assert any("Rating" in prop for prop in inherited_props)


def test_update(setup_deployment):
    """Test updating custom data models (no change)."""
    # Deploy once
    fbnconfig.deployex(custom_data_model_config.configure(setup_deployment), lusid_env, token)
    # Deploy again without changes
    result = fbnconfig.deployex(custom_data_model_config.configure(setup_deployment), lusid_env, token)
    # Check that custom data models show no change
    custom_data_model_changes = [a.change for a in result if a.type == "CustomDataModelResource"]
    assert "nochange" in custom_data_model_changes


def test_teardown(setup_deployment):
    """Test deleting custom data models."""
    # Create first
    fbnconfig.deployex(custom_data_model_config.configure(setup_deployment), lusid_env, token)
    # Delete all resources
    fbnconfig.deployex(fbnconfig.Deployment(setup_deployment.name, []), lusid_env, token)

    # Verify the models were deleted
    with pytest.raises(HTTPStatusError) as error:
        client.get(f"/api/api/datamodel/Instrument/{setup_deployment.name}/BondModel")
    assert error.value.response.status_code == 404

    with pytest.raises(HTTPStatusError) as error:
        client.get(f"/api/api/datamodel/Instrument/{setup_deployment.name}/BaseInstrumentModel")
    assert error.value.response.status_code == 404


def test_property_dependencies(setup_deployment):
    """Test that property definitions are created before custom data models."""
    fbnconfig.deployex(custom_data_model_config.configure(setup_deployment), lusid_env, token)

    # Verify property definitions were created
    rating_prop = client.get(f"/api/api/propertydefinitions/Instrument/{setup_deployment.name}/Rating")
    assert rating_prop.status_code == 200

    maturity_prop = client.get(
        f"/api/api/propertydefinitions/Instrument/{setup_deployment.name}/MaturityDate"
    )
    assert maturity_prop.status_code == 200

    # Verify custom data models reference these properties
    bond_model = client.get(f"/api/api/datamodel/Instrument/{setup_deployment.name}/BondModel")
    assert bond_model.status_code == 200
    bond_data = bond_model.json()

    # Check that properties are referenced in the model (in applied section)
    assert "applied" in bond_data
    assert "properties" in bond_data["applied"]
    property_keys = [p["propertyKey"] for p in bond_data["applied"]["properties"]]
    assert f"Instrument/{setup_deployment.name}/MaturityDate" in property_keys
