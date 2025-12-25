import os
from types import SimpleNamespace

from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
import tests.integration.datatype as example
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
    deployment_name = gen("datatype")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)


def test_teardown(setup_deployment):
    fbnconfig.deployex(example.configure(setup_deployment), lusid_env, token)

    fbnconfig.deployex(fbnconfig.Deployment(setup_deployment.name, []), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    try:
        client.get(f"/api/api/datatypes/{setup_deployment.name}/robtest_strategy")
    except HTTPStatusError as error:
        # check it was deleted
        assert error.response.status_code == 404


def test_create(setup_deployment):
    fbnconfig.deployex(example.configure(setup_deployment), lusid_env, token)
    res = client.get(f"/api/api/datatypes/{setup_deployment.name}/robtest_priority").json()
    assert res is not None


def test_nochange(setup_deployment):
    fbnconfig.deployex(example.configure(setup_deployment), lusid_env, token)
    update = fbnconfig.deployex(example.configure(setup_deployment), lusid_env, token)
    print(update)
    assert [a.change for a in update] == ["nochange"] * 3
