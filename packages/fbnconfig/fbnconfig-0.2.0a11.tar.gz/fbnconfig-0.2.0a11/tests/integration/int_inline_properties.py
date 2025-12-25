import os
import time
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import lumi
from fbnconfig import property as prop
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)


def put_query(client, sql):
    res = client.put(
        "/honeycomb/api/Sql/json",
        content=sql,
        params={"jsonProper": True},
        headers={"Content-type": "text/plain"},
    )
    return res.json()


@fixture(scope="module")
def setup_deployment():
    deployment_name = gen("inlineproperties")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Teardown: Clean up resources (if any) after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)


@fixture()
def get_deployment(setup_deployment):
    # Reference an existing property definition
    test_property_one = prop.DefinitionRef(
        id="test-property-ref", domain=prop.Domain.Transaction, scope="default", code="Custodian"
    )
    test_property_two = prop.DefinitionRef(
        id="test-property-two", domain=prop.Domain.Transaction, scope="default",
        code="SourcePortfolioScope"
    )
    # Create inline properties resource
    inline_properties = lumi.InlinePropertiesResource(
        id="test-inline-properties",
        provider="Lusid.Portfolio.Txn",
        provider_name_extension=setup_deployment.name,
        properties=[
            lumi.InlineProperty(
                key=test_property_one,
                name="TestProperty",
                data_type=lumi.InlineDataType.Text,
                description="Test property for integration testing",
            ),
            lumi.InlineProperty(
                key=test_property_two,
                name="TestProperty2",
                data_type=lumi.InlineDataType.Text,
                description="Test property for integration testing",
            )
        ],
    )
    # create custom entity inline for the fbnconfig setup log (because we know it exists)
    setup_identifier = prop.DefinitionRef(
        id="ce-setup-id",
        domain=prop.Domain.CustomEntity,
        scope="deployment",
        code="resource",
    )
    custom_inline = lumi.InlinePropertiesResource(
        id="test-custom-properties",
        provider="Lusid.CustomEntity.deployment",
        properties=[
            lumi.InlineProperty(
                key=setup_identifier,
                name="deployment_identifier",
                description="Identifier for an fbnconfig deployment resource",
            )
        ],
    )
    return [inline_properties, custom_inline]


def wait_for_it(client, sql, expected_rows):
    tries = 10
    sleep = 10
    while True:
        r = put_query(client, sql)
        if len(r) == expected_rows:
            return r
        tries -= 1
        if tries == 0:
            print("Failed to get", expected_rows, "after", tries, sql, r)
            assert len(r) == expected_rows, f"Failed to get {expected_rows}"
        time.sleep(sleep)


def test_teardown(setup_deployment, get_deployment):
    # Check if properties exist before creating
    check_path = (
        "config/lusid/factories/" f"{setup_deployment.name}_portfoliotransactionproviderfactory.csv"
    )
    check = f"select Content from sys.file where path = '{check_path}'"
    # Create the inline properties
    deployment = fbnconfig.Deployment(setup_deployment.name, get_deployment)
    fbnconfig.deployex(deployment, lusid_env, token)
    # Check it exists
    wait_for_it(client, check, 1)
    # Remove it
    fbnconfig.deployex(fbnconfig.Deployment(setup_deployment.name, []), lusid_env, token)
    # Check it's gone
    wait_for_it(client, check, 0)


def test_create(setup_deployment, get_deployment):
    deployment = fbnconfig.Deployment(setup_deployment.name, get_deployment)
    fbnconfig.deployex(deployment, lusid_env, token)
    check_path = (
        "config/lusid/factories/" f"{setup_deployment.name}_portfoliotransactionproviderfactory.csv"
    )
    r = put_query(client, f"select Content from sys.file where path = '{check_path}'")
    assert len(r) == 1
    # Verify the content contains our test property
    content = r[0]["Content"]
    assert "TestProperty" in content
    assert "Transaction/default/Custodian" in content


def test_update_with_extension_change(setup_deployment, get_deployment):
    # First deployment
    deployment = fbnconfig.Deployment(setup_deployment.name, get_deployment)
    fbnconfig.deployex(deployment, lusid_env, token)
    # Modify the provider_name_extension to trigger an update
    extension = "Ext" + setup_deployment.name
    get_deployment[0].provider_name_extension = extension
    update = fbnconfig.deployex(deployment, lusid_env, token)
    assert [a.change for a in update if a.type == "InlinePropertiesResource"] == ["update", "nochange"]
    # check the old one is gone
    old_path = (
        "config/lusid/factories/" f"{setup_deployment.name}_portfoliotransactionproviderfactory.csv"
    )
    old_check = f"select Content from sys.file where path = '{old_path}'"
    wait_for_it(client, old_check, 0)
    # check the new one has been created
    new_path = (
        "config/lusid/factories/" f"Ext{setup_deployment.name}_portfoliotransactionproviderfactory.csv"
    )
    check = f"select Content from sys.file where path = '{new_path}'"
    wait_for_it(client, check, 1)


def test_update_change(setup_deployment, get_deployment):
    # First deployment
    deployment = fbnconfig.Deployment(setup_deployment.name, get_deployment)
    fbnconfig.deployex(deployment, lusid_env, token)
    # Modify the provider_name_extension to trigger an update
    get_deployment[0].properties[0].description = "Updated description"
    update = fbnconfig.deployex(deployment, lusid_env, token)
    assert [a.change for a in update if a.type == "InlinePropertiesResource"] == ["update", "nochange"]


def test_nochange(setup_deployment, get_deployment):
    deployment = fbnconfig.Deployment(setup_deployment.name, get_deployment)
    fbnconfig.deployex(deployment, lusid_env, token)
    update = fbnconfig.deployex(deployment, lusid_env, token)
    assert [a.change for a in update if a.type == "InlinePropertiesResource"] == ["nochange", "nochange"]
