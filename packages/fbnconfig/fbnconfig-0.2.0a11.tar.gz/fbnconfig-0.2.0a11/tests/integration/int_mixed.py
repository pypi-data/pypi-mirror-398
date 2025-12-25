import os
from types import SimpleNamespace

from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
import tests.integration.mixed as mixed
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]


@fixture(scope="module")
def setup_deployment():
    deployment_name = gen("mixed")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(base_dir=deployment_name, name=deployment_name)
    # Teardown: Clean up resources (if any) after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)


def test_teardown(setup_deployment):
    # create first
    fbnconfig.deployex(mixed.configure(setup_deployment), lusid_env, token)

    fbnconfig.deployex(fbnconfig.Deployment(setup_deployment.name, []), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    try:
        client.get(f"/scheduler2/api/schedules/{setup_deployment.name}/data-sched")
    except HTTPStatusError as error:
        assert error.response.status_code == 404


def test_create(setup_deployment):
    fbnconfig.deployex(mixed.configure(setup_deployment), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    search = client.get(f"/scheduler2/api/schedules/{setup_deployment.name}/data-sched")
    assert search.status_code == 200


def test_update(setup_deployment):
    fbnconfig.deployex(mixed.configure(setup_deployment), lusid_env, token)
    fbnconfig.deployex(mixed.configure(setup_deployment), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    search = client.get(f"/scheduler2/api/schedules/{setup_deployment.name}/data-sched")
    assert search.status_code == 200
