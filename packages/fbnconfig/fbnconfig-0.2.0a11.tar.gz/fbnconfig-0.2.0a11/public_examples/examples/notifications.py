from fbnconfig import Deployment, notifications


def configure(env):
    deployment_name = getattr(env, "name", "subscriptions")

    matching_pattern = notifications.MatchingPattern(
        event_type="Manual",
        filter="Body.Message eq 'Test'"
    )

    basic_sub = notifications.SubscriptionResource(
        id="ExampleId",
        scope="sc1",
        code="cd1",
        display_name="Example display name",
        description="Example description",
        status=notifications.SubscriptionStatus.ACTIVE,
        matching_pattern=matching_pattern
    )

    email_type = notifications.EmailNotificationType(
        subject="Example of Email Notification",
        plain_text_body="Example body",
        html_body="<p>Event received: <strong>{{body.message}}</strong></p>",
        email_address_to=["example@gmail.com"],
        email_address_cc=["example2@gmail.com"]
    )

    email_notification = notifications.NotificationResource(
        id="ExampleEmailId",
        subscription=basic_sub,
        notification_id="ExampleNotifId",
        display_name="Example display name",
        description="Example description",
        notification_type=email_type
    )

    return Deployment(deployment_name, [basic_sub, email_notification])
