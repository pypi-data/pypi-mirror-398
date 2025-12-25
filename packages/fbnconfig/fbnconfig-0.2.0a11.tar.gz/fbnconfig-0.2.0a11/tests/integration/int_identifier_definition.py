import datetime as dt
import os
from types import SimpleNamespace

from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
from fbnconfig import identifier_definition, property
from fbnconfig.deploy import Deployment
from fbnconfig.property import LifeTime
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}


def configure(env):
    deployment_name = getattr(env, "name", "identifier_definition")

    prop_value = identifier_definition.PropertyValue(
        property_key=property.DefinitionRef(
            id="one", domain=property.Domain.IdentifierDefinition, scope="sc1", code="cd1"
        ),
        label_value="AverageCost",
        effective_from=dt.datetime(2000, 10, 2, 14, 30, 45),
        effective_until=dt.datetime(2030, 10, 2, 14, 30, 45)
    )

    id_def = identifier_definition.IdentifierDefinitionResource(
        id="id_def",
        domain=identifier_definition.SupportedDomain.Instrument,
        identifier_scope=deployment_name,
        identifier_type="testType",
        life_time=LifeTime.Perpetual,
        properties=[prop_value]
    )

    return Deployment(deployment_name, [id_def])


@fixture()
def setup_deployment():
    print("Creating new property")
    client = fbnconfig.create_client(lusid_env, token)

    # Deletes test property for chart of account if it exsits
    try:
        client.delete("/api/api/propertydefinitions/IdentifierDefinition/sc1/cd1")
    except Exception:
        pass

    # Creates new property to add to the chart of accounts
    prop = {
        "domain": "IdentifierDefinition",
        "scope": "sc1",
        "code": "cd1",
        "valueRequired": False,
        "displayName": "My Property Display Name",
        "dataTypeId": {
            "scope": "system",
            "code": "string"
        },
        "lifeTime": "TimeVariant",
    }
    client.post("/api/api/propertydefinitions", json=prop)

    deployment_name = gen("identifier_definition")
    print(f"\nRunning for deployment {deployment_name}...")

    yield SimpleNamespace(name=deployment_name)
    # Teardown: Clean up resources (if any) after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    client.delete("/api/api/propertydefinitions/IdentifierDefinition/sc1/cd1")


def test_teardown(setup_deployment):
    deployment_name = setup_deployment.name
    client = fbnconfig.create_client(lusid_env, token)
    # setup deployment
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    # check it exists
    client.request("get", f"/api/api/identifierdefinitions/Instrument/{deployment_name}/testType")
    # Tear it down
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    # check it was deleted
    try:
        client.request("get", "/api/api/identifierdefinitions/Instrument/"
                       f"{deployment_name}/testType")
    except HTTPStatusError as error:
        assert error.response.status_code == 404


def test_create(setup_deployment):
    deployment_name = setup_deployment.name
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    search = client.request("get", f"/api/api/identifierdefinitions/Instrument/"
                            f"{deployment_name}/testType")
    assert search.status_code == 200


def test_update_nochange(setup_deployment):
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    update = fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    assert [a.change for a in update if a.type == "IdentifierDefinitionResource"] == ["nochange"]
