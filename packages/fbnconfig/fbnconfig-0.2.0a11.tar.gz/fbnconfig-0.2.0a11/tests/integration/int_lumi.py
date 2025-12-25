import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
import tests.integration.lumi as lumi
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
    deployment_name = gen("lumi")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Teardown: Clean up resources (if any) after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)


def test_teardown(setup_deployment):
    check = f"""
        select content from sys.file
        where path = 'databaseproviders/Views/fbnconfig/{setup_deployment.name}_vr.sql'
    """
    # create
    fbnconfig.deployex(lumi.configure(setup_deployment), lusid_env, token)
    # check it exists
    r = put_query(client, check)
    assert len(r) == 1
    # remove it
    fbnconfig.deployex(fbnconfig.Deployment(setup_deployment.name, []), lusid_env, token)
    # check it's gone
    r = put_query(client, check)
    assert len(r) == 0


def test_create(setup_deployment):
    fbnconfig.deployex(lumi.configure(setup_deployment), lusid_env, token)
    r = put_query(
        client,
        f"""
        select content from sys.file
        where path = 'databaseproviders/Views/fbnconfig/{setup_deployment.name}_vr.sql'
    """,
    )
    assert len(r) == 1


def test_nochange(setup_deployment):
    fbnconfig.deployex(lumi.configure(setup_deployment), lusid_env, token)
    update = fbnconfig.deployex(lumi.configure(setup_deployment), lusid_env, token)
    assert [a.change for a in update if a.type == "ViewResource"] == ["nochange"] * 4
