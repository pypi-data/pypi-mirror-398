import os

import pytest

import fbnconfig
import tests.integration.identity as identity

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}


def test_teardown():
    deployment_name = identity.configure({}).id
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    matches = get_roles_by_name(client, "robTest_role2")
    assert len(matches) == 0
    users = get_users_by_login(client, "robtest_jane3@robtest.com")
    assert len(users) == 0


@pytest.mark.skip(reason="This creates actual users; should be run explicitly")
def test_create():
    fbnconfig.deployex(identity.configure(host_vars), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    matches = get_roles_by_name(client, "robTest_role2")
    assert len(matches) == 1
    users = get_users_by_login(client, "robtest_jane3@robtest.com")
    assert len(users) == 1


def test_update():
    fbnconfig.deployex(identity.configure(host_vars), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    matches = get_roles_by_name(client, "robTest_role2")
    assert len(matches) == 1
    users = get_users_by_login(client, "robtest_jane3@robtest.com")
    assert len(users) == 1


def get_roles_by_name(client, name):
    get = client.request("get", "/identity/api/roles")
    get.raise_for_status()
    roles = get.json()
    return [role for role in roles if role["name"] == name]


def get_users_by_login(client, login):
    get = client.request("get", "/identity/api/users")
    get.raise_for_status()
    users = get.json()
    return [user for user in users if user["login"] == login]
