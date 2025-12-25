import os
from types import SimpleNamespace

import pytest
from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
from fbnconfig import workspace
from tests.integration.generate_test_name import gen


@fixture(scope="module")
def lusid_env():
    if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
        raise (
            RuntimeError("FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
        )

    env = os.environ["LUSID_ENV"]
    token = os.environ["FBN_ACCESS_TOKEN"]
    return SimpleNamespace(env=env, token=token)


@fixture(scope="module")
def client(lusid_env):
    return fbnconfig.create_client(lusid_env.env, lusid_env.token)


@fixture(scope="module")
def deployment_name():
    return gen("workflows")


def resources(deployment_name):
    wksp = workspace.WorkspaceResource(
        id="wk1",
        visibility=workspace.Visibility.SHARED,
        name=deployment_name,
        description="workspace number one",
    )
    item1 = workspace.WorkspaceItemResource(
        id="item1",
        workspace=wksp,
        group="group1",
        name="item1",
        description="item one version two",
        type="lusid-web-dashboard",
        format=1,
        content={"msg": "some text"},
    )
    item2 = workspace.WorkspaceItemResource(
        id="item2",
        workspace=wksp,
        group="group1",
        name="item2",
        description="item one version two",
        format=1,
        type="lusid-web-dashboard",
        content={"msg": "some text", "foo": 10},
    )
    return {
        "workspace": wksp,
        "item1": item1,
        "item2": item2
    }


@fixture()
def deployment(deployment_name, lusid_env):
    res = resources(deployment_name)
    print(f"\nRunning for deployment {deployment_name}...")
    yield fbnconfig.Deployment(deployment_name, list(res.values()))
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env.env, lusid_env.token)


def test_teardown(deployment, lusid_env, client):
    # create first
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    fbnconfig.deployex(fbnconfig.Deployment(deployment.id, []), lusid_env.env, lusid_env.token)
    with pytest.raises(HTTPStatusError) as error:
        client.get(f"/api/api/workspaces/shared/{deployment.id}")
    assert error.value.response.status_code == 404


def test_create(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    search = client.get(f"/api/api/workspaces/shared/{deployment.id}/items/group1/item1")
    assert search.status_code == 200


def test_update(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    search = client.get(f"/api/api/workspaces/shared/{deployment.id}/items/group1/item1")
    assert search.status_code == 200
