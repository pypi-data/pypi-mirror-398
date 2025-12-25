import os
from types import SimpleNamespace

from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
from fbnconfig import notifications as notif
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise RuntimeError(
        "Both FBN_ACCESS_TOKEN and LUSID_ENV variables need "
        "to be set to run integration tests"
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]


@fixture(scope="module")
def setup_deployment():
    deployment_name = gen("subscriptions")
    print(f"\nRunning for deployment {deployment_name}...")

    yield SimpleNamespace(name=deployment_name)
    # Teardown: Clean up resources (if any) after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)


def configure(env):
    deployment_name = getattr(env, "name", "subscriptions")

    matching_pattern = notif.MatchingPattern(
        event_type="Manual",
        filter="Body.Message eq 'Test'"
    )

    basic_sub = notif.SubscriptionResource(
        id="testScopetestCode",
        scope=f"testScope-{deployment_name}",
        code="testCode",
        display_name="Basic Test Subscription",
        description="Testing basic subscription creation",
        status=notif.SubscriptionStatus.ACTIVE,
        matching_pattern=matching_pattern
    )
    return fbnconfig.Deployment(deployment_name, [basic_sub])


def test_teardown(setup_deployment):
    deployment_name = setup_deployment.name
    client = fbnconfig.create_client(lusid_env, token)
    # setup deployment
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    # check it exists
    client.request("get", f"/notification/api/subscriptions/testScope-{deployment_name}/testCode")
    # Tear it down
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    # check it was deleted
    try:
        client.request("get", f"/notification/api/subscriptions/testScope-{deployment_name}/testCode")
    except HTTPStatusError as error:
        assert error.response.status_code == 404


def test_create(setup_deployment):
    deployment_name = setup_deployment.name
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    # check it exists
    response = client.get(f"/notification/api/subscriptions/testScope-{deployment_name}/testCode")
    assert response.status_code == 200
    data = response.json()

    # check body
    assert data["id"]["scope"] == f"testScope-{deployment_name}"
    assert data["id"]["code"] == "testCode"
    assert data["displayName"] == "Basic Test Subscription"
    assert data["description"] == "Testing basic subscription creation"
    assert data["status"] == "Active"
    assert data["matchingPattern"]["eventType"] == "Manual"


def test_update_no_changes(setup_deployment):
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    update = fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    assert [a.change for a in update if a.type == "SubscriptionResource"] == ["nochange"]
