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
    print("Creating new subscription")
    client = fbnconfig.create_client(lusid_env, token)

    # Deletes test subscription if it exsits
    try:
        client.delete("/notification/api/subscriptions/testScope/testCode")
    except Exception:
        pass

    # Creates new subscription to test notifications on
    desired = {
        "id": {
            "scope": "testScope",
            "code": "testCode"
        },
        "displayName": "TestDisplayName",
        "description": "TestDescription",
        "status": "Active",
        "matchingPattern": {
            "eventType": "Manual",
            "filter": "Body.Message eq 'TestMessage'"
        },
    }
    client.post("/notification/api/subscriptions", json=desired)

    deployment_name = gen("notifications")
    print(f"\nRunning for deployment {deployment_name}...")

    yield SimpleNamespace(name=deployment_name)
    # Teardown: Clean up resources (if any) after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    client.delete("/notification/api/subscriptions/testScope/testCode")


def configure(env):
    """Create a test email notification."""
    deployment_name = getattr(env, "name", "notification")

    email_type = notif.EmailNotificationType(
        subject="Test Event: {{body.subject}}",
        plain_text_body="Event received: {{body.message}}",
        html_body="<p>Event received: <strong>{{body.message}}</strong></p>",
        email_address_to=["test@finbourne.com"],
        email_address_cc=["testcc@finbourne.com"]
    )

    subscription_ref = notif.SubscriptionRef(
        id="subscription_ref",
        scope="testScope",
        code="testCode"
    )

    email_notification = notif.NotificationResource(
        id="testEmailNotification",
        subscription=subscription_ref,
        notification_id=f"emailNotif001-{deployment_name}",
        display_name="Test Email Notification",
        description="Testing email notification creation",
        notification_type=email_type
    )

    matching_pattern = notif.MatchingPattern(
        event_type="Manual",
        filter="Body.Message eq 'Test'"
    )

    sub_resource = notif.SubscriptionResource(
        id="SubExampleId",
        scope=f"testScopeSub-{deployment_name}",
        code="testCodeSub",
        display_name="Example display name",
        description="Example description",
        status=notif.SubscriptionStatus.ACTIVE,
        matching_pattern=matching_pattern
    )

    sms_type = notif.SmsNotificationType(
        body="Example_body",
        recipients=["+47000000000"]
    )

    sms_notification = notif.NotificationResource(
        id="testSmsNotification",
        subscription=sub_resource,
        notification_id=f"smsNotif001-{deployment_name}",
        display_name="Test sms Notification",
        description="Testing sms notification creation",
        notification_type=sms_type
    )

    return fbnconfig.Deployment(deployment_name, [email_notification, sms_notification])


def test_teardown(setup_deployment):
    deployment_name = setup_deployment.name
    client = fbnconfig.create_client(lusid_env, token)
    # setup deployment
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)

    # check they exists
    client.request("get", "/notification/api/subscriptions/testScope/testCode/"
        f"notifications/emailNotif001-{deployment_name}")

    client.get(f"/notification/api/subscriptions/testScopeSub-{deployment_name}/testCodeSub/"
        f"notifications/smsNotif001-{deployment_name}")

    # Tear it down
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)

    # check they were deleted
    try:
        client.request("get", "/notification/api/subscriptions/testScope/testCode/"
        f"notifications/emailNotif001-{deployment_name}")
    except HTTPStatusError as error:
        assert error.response.status_code == 404

    try:
        client.get(f"/notification/api/subscriptions/testScopeSub-{deployment_name}/testCodeSub/"
        f"notifications/smsNotif001-{deployment_name}")
    except HTTPStatusError as error:
        assert error.response.status_code == 404


def test_create_email_notification(setup_deployment):
    deployment_name = setup_deployment.name
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)

    # checks email and sms notifications are created
    email_response = client.get("/notification/api/subscriptions/testScope/testCode/"
    f"notifications/emailNotif001-{deployment_name}")

    sms_response = client.get(f"/notification/api/subscriptions/"
    f"testScopeSub-{deployment_name}/testCodeSub/notifications/smsNotif001-{deployment_name}")

    # assert codes
    assert email_response.status_code == 200
    assert sms_response.status_code == 200


def test_update_no_changes(setup_deployment):
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    update = fbnconfig.deployex(configure(setup_deployment), lusid_env, token)

    email_change = [a.change for a in update
                    if a.type == "NotificationResource" and a.id == "testEmailNotification"]
    sms_change = [a.change for a in update
                  if a.type == "NotificationResource" and a.id == "testSmsNotification"]
    assert email_change == ["nochange"]
    assert sms_change == ["nochange"]
