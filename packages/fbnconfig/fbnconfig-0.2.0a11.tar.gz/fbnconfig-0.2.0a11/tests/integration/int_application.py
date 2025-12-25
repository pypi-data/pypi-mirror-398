import os
from types import SimpleNamespace

import pytest

import fbnconfig
from fbnconfig import Deployment, identity
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}


# this cant be scope=module, it needs to be unique per test
@pytest.fixture()
def setup_deployment():
    deployment_name = gen("app", length=6)
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    try:
        fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture()
def deployment(setup_deployment):
    application = identity.ApplicationResource(
        id="test_app",
        client_id=f"inttest-app-{setup_deployment.name}",
        display_name=f"Application{setup_deployment.name}",
        type=identity.ApplicationType.NATIVE,
    )
    return Deployment(setup_deployment.name, [application])


def test_teardown(setup_deployment):
    deployment_name = setup_deployment.name
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    matches = get_applications_by_client_id(client, f"inttest-app-{deployment_name}")
    assert len(matches) == 0


def test_create(setup_deployment, deployment):
    fbnconfig.deployex(deployment, lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    matches = get_applications_by_client_id(client, f"inttest-app-{setup_deployment.name}")
    assert len(matches) == 1
    app = matches[0]
    assert app["displayName"] == f"Application{setup_deployment.name}"
    assert app["type"] == "Native"


def test_update(setup_deployment, deployment):
    fbnconfig.deployex(deployment, lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    matches = get_applications_by_client_id(client, f"inttest-app-{setup_deployment.name}")
    assert len(matches) == 1
    app = matches[0]
    assert app["displayName"] == f"Application{setup_deployment.name}"
    assert app["type"] == "Native"


def get_applications_by_client_id(client, client_id):
    get = client.request("get", "/identity/api/applications")
    get.raise_for_status()
    applications = get.json()
    return [app for app in applications if app["clientId"] == client_id]
