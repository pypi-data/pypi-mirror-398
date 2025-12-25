import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig.corporate_action import CorporateActionSourceResource
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
def base_resources(setup_deployment):
    deployment_name = setup_deployment.name
    # Create a corporate action source
    corporate_action_source = CorporateActionSourceResource(
        id="test_corporate_action",
        scope=deployment_name,
        code="test-ca-source-1",
        display_name="Test Corporate Action Source",
        description="A test corporate action source for integration testing",
        instrument_scopes=["robtest"]
    )
    return [corporate_action_source]


@fixture(scope="module")
def setup_deployment():
    deployment_name = gen("corporate_action")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Clean up corporate action sources after tests
    try:
        client.delete(f"/api/api/corporateactionsources/{deployment_name}/test-ca-source-1")
    except Exception:
        pass  # Ignore cleanup errors


def test_create(setup_deployment, base_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # Verify corporate action source was created
    filter_query = f"id.scope eq '{setup_deployment.name}' and id.code eq 'test-ca-source-1'"
    response = client.get("/api/api/corporateactionsources", params={"filter": filter_query}).json()
    values = response["values"]
    assert len(values) == 1
    source = values[0]
    assert source["id"]["scope"] == setup_deployment.name
    assert source["id"]["code"] == "test-ca-source-1"
    assert source["displayName"] == "Test Corporate Action Source"
    assert source["description"] == "A test corporate action source for integration testing"
    assert source["instrumentScopes"] == ["robtest"]


def test_nochange(setup_deployment, base_resources):
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we apply it again
    update = fbnconfig.deployex(deployment, lusid_env, token)
    # then there are no changes
    ca_changes = [a.change for a in update if a.type == "CorporateActionSourceResource"]
    assert ca_changes == ["nochange"]


def test_teardown(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we remove all the resources
    empty = fbnconfig.Deployment(deployment_name, [])
    update = fbnconfig.deployex(empty, lusid_env, token)
    # then there are no changes
    ca_changes = [a.change for a in update if a.type == "CorporateActionSourceResource"]
    assert ca_changes == ["remove"]


def test_update(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    # Given we have deployed the base case
    initial = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(initial, lusid_env, token)
    # when we update a resource
    updated_resources = [
        CorporateActionSourceResource(
            id="test_corporate_action",
            scope=deployment_name,
            code="test-ca-source-1",
            display_name="Updated Corporate Action Source",  # Changed display name
            description="An updated corporate action source",  # Changed description
            instrument_scopes=["robupdated"]  # Added scope
        )
    ]
    # and deploy it
    updated_deployment = fbnconfig.Deployment(deployment_name, updated_resources)
    update = fbnconfig.deployex(updated_deployment, lusid_env, token)
    # then we expect the resource to change
    ca_changes = [a.change for a in update if a.type == "CorporateActionSourceResource"]
    assert ca_changes == ["update"]
    # and it has the new values
    filter_query = f"id.scope eq '{deployment_name}' and id.code eq 'test-ca-source-1'"
    updated_response = client.get("/api/api/corporateactionsources",
                                  params={"filter": filter_query}).json()["values"]
    assert len(updated_response) == 1
    source = updated_response[0]
    assert source["displayName"] == "Updated Corporate Action Source"
    assert source["description"] == "An updated corporate action source"
    assert source["instrumentScopes"] == ["robupdated"]
