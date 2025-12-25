import os
import pathlib
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import drive
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
    return gen("drive")


def resources(deployment_name):
    base_folder = deployment_name
    f1 = drive.FolderResource(id="base_folder", name=base_folder, parent=drive.root)
    f2 = drive.FolderResource(id="sub_folder", name="subfolder", parent=f1)
    f3 = drive.FolderResource(id="sub_sub_folder", name="subfolder2", parent=f2)
    content_path = pathlib.Path(__file__).parent.resolve() / pathlib.Path("poem.txt")
    ff = drive.FileResource(id="file1", folder=f3, name="myfile.txt", content_path=content_path)
    return {r.id: r for r in [f1, f2, f3, ff]}


@fixture()
def deployment(deployment_name, lusid_env):
    res = resources(deployment_name)
    print(f"\nRunning for deployment {deployment_name}...")
    yield fbnconfig.Deployment(deployment_name, list(res.values()))
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env.env, lusid_env.token)


def test_teardown(deployment, client, lusid_env):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    fbnconfig.deployex(fbnconfig.Deployment(deployment.id, []), lusid_env.env, lusid_env.token)
    search = client.post("/drive/api/search/", json={"withPath": "/", "name": deployment.id})
    assert search.json()["values"] == []


def test_create(deployment, client, lusid_env):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    search = client.post("/drive/api/search/", json={"withPath": "/", "name": deployment.id})
    assert len(search.json()["values"]) == 1


def test_update(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    search = client.post("/drive/api/search/", json={"withPath": "/", "name": deployment.id})
    assert len(search.json()["values"]) == 1
