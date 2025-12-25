import os
from types import SimpleNamespace

import pytest
from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
import tests.integration.recipe as recipe
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)


@fixture
def setup_deployment():
    deployment_name = gen("recipe")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Teardown: Clean up resources (if any) after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)


def test_teardown(setup_deployment):
    # create first
    fbnconfig.deployex(recipe.configure(setup_deployment), lusid_env, token)
    fbnconfig.deployex(fbnconfig.Deployment(setup_deployment.name, []), lusid_env, token)
    with pytest.raises(HTTPStatusError) as error:
        client.get("/api/api/recipes/sc1/cd1")
    assert error.value.response.status_code == 404
    with pytest.raises(HTTPStatusError) as error:
        client.get("/api/api/recipes/sc1/cd2")
    assert error.value.response.status_code == 404


def test_create(setup_deployment):
    fbnconfig.deployex(recipe.configure(setup_deployment), lusid_env, token)
    search_1 = client.get("/api/api/recipes/sc1/cd1")
    assert search_1.status_code == 200
    search_2 = client.get("/api/api/recipes/sc1/cd2")
    assert search_2.status_code == 200


def test_update(setup_deployment):
    fbnconfig.deployex(recipe.configure(setup_deployment), lusid_env, token)
    update = fbnconfig.deployex(recipe.configure(setup_deployment), lusid_env, token)
    search_1 = client.get("/api/api/recipes/sc1/cd1")
    assert search_1.status_code == 200
    search_2 = client.get("/api/api/recipes/sc1/cd2")
    assert search_2.status_code == 200
    assert [a.change for a in update if a.type == "RecipeResource"] == ["nochange", "nochange"]
