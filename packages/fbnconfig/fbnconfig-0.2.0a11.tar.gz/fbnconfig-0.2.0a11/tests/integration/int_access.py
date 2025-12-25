import os
from types import SimpleNamespace

from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
import tests.integration.access as access
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}


@fixture()
def setup_deployment():
    deployment_name = gen("access")
    print(f"\nRunning for deployment {deployment_name}...")

    yield SimpleNamespace(name=deployment_name)
    # Teardown: Clean up resources (if any) after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)


def test_teardown(setup_deployment):
    deployment_name = setup_deployment.name
    client = fbnconfig.create_client(lusid_env, token)
    # setup deployment
    fbnconfig.deployex(access.configure(setup_deployment), lusid_env, token)
    # check it exists
    client.request("get", f"/access/api/policies/policy-{deployment_name}")
    # Tear it down
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    # check it was deleted
    try:
        client.request("get", f"/access/api/policies/policy-{deployment_name}")
    except HTTPStatusError as error:
        assert error.response.status_code == 404


def test_create(setup_deployment):
    fbnconfig.deployex(access.configure(setup_deployment), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    search = client.request("get", f"/access/api/roles/role-{setup_deployment.name}")
    assert search.status_code == 200


def test_update_nochange(setup_deployment):
    fbnconfig.deployex(access.configure(setup_deployment), lusid_env, token)
    update = fbnconfig.deployex(access.configure(setup_deployment), lusid_env, token)
    assert [a.change for a in update] == ["nochange"] * 2 + ["attach"] + ["nochange"] * 6
