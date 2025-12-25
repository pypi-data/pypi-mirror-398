import json
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import configuration, identity, notifications

TEST_BASE = "https://foo.lusid.com"


@pytest.mark.respx(base_url=TEST_BASE)
class TestSubscriptionRef:
    """Test SubscriptionRef functionality."""

    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def subscription_ref(self):
        """Create a subscription reference for testing."""
        return notifications.SubscriptionRef(
            id="test-subscription-ref",
            scope="test",
            code="basic_sub"
        )

    def test_subscription_ref_properties(self, subscription_ref):
        """Test that scope and code are set correctly."""
        assert subscription_ref.scope == "test"
        assert subscription_ref.code == "basic_sub"
        assert subscription_ref.id == "test-subscription-ref"

    def test_subscription_ref_attach_success(self, respx_mock, subscription_ref):
        """Test attach method validates subscription exists."""
        respx_mock.get("/notification/api/subscriptions/test/basic_sub").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": {"scope": "test", "code": "basic_sub"},
                    "displayName": "Test Subscription",
                    "status": "Active"
                }
            )
        )
        # Should not raise an error for existing subscription
        subscription_ref.attach(self.client)

    def test_subscription_ref_attach_not_found(self, respx_mock, subscription_ref):
        """Test attach method raises error for non-existent subscription."""
        respx_mock.get("/notification/api/subscriptions/test/basic_sub").mock(
            return_value=httpx.Response(404)
        )
        with pytest.raises(RuntimeError, match="Subscription test/basic_sub does not exist"):
            subscription_ref.attach(self.client)
        assert "Subscription test/basic_sub does not exist"

    def test_subscription_ref_attach_when_http_error(self, respx_mock, subscription_ref):

        respx_mock.get("/notification/api/subscriptions/test/basic_sub").mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        sut = subscription_ref
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class TestSubscriptionResource:
    """Test SubscriptionResource functionality."""
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def simple_subscription(self):

        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        return notifications.SubscriptionResource(
            id="testId",
            scope="test",
            code="basic_sub",
            matching_pattern=matching_pattern,
            display_name="Basic Test Subscription",
            description="Testing subscription",
            status=notifications.SubscriptionStatus.ACTIVE,
        )

    def test_read_subscription(self, respx_mock, simple_subscription):
        respx_mock.get(
            "/notification/api/subscriptions/old_state_scope/old_state_code"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": {"scope": "old_state_scope", "code": "old_state_code"},
                    "displayName": "Old state display name",
                    "description": "Testing subscription",
                    "status": "Active",
                    "eventType": "Manual",
                    "matchingPattern": {
                        "eventType": "Manual",
                        "filter": "Body.Message eq 'Test'"
                    }
                }
            )
        )
        client = self.client
        old_state = SimpleNamespace(scope="old_state_scope", code="old_state_code")
        response = simple_subscription.read(client, old_state)
        assert response["id"]["scope"] == "old_state_scope"
        assert response["id"]["code"] == "old_state_code"
        assert response["displayName"] == "Old state display name"
        assert response["status"] == "Active"

    def test_read_subscription_raises_on_404(self, respx_mock, simple_subscription):
        """Test that read raises exception on 404 since resource should exist."""
        respx_mock.get(
            f"/notification/api/subscriptions/{simple_subscription.scope}/{simple_subscription.code}"
        ).mock(return_value=httpx.Response(404))

        client = self.client
        old_state = SimpleNamespace(scope="test", code="basic_sub")

        with pytest.raises(httpx.HTTPStatusError):
            simple_subscription.read(client, old_state)

    def test_create_subscription(self, respx_mock, simple_subscription):
        respx_mock.post("/notification/api/subscriptions").mock(
            return_value=httpx.Response(
                200,
                json={"id": {"scope": "test", "code": "basic_sub"}, "status": "Active"}
            )
        )
        client = self.client
        state = simple_subscription.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "displayName": "Basic Test Subscription",
            "description": "Testing subscription",
            "status": "Active",
            "matchingPattern": {
                "eventType": "Manual",
                "filter": "Body.Message eq 'Test'"
            },
            "id": {
                "scope": "test",
                "code": "basic_sub"
            },
        }

        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        # Verify version hashes are included
        assert "source_version" in state
        assert "remote_version" in state

    def test_create_subscription_with_no_filter(self, respx_mock):
        respx_mock.post("/notification/api/subscriptions").mock(
            return_value=httpx.Response(
                200,
                json={"id": {"scope": "test", "code": "basic_sub"}, "status": "Active"}
            )
        )
        client = self.client

        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
        )

        simple_sub_no_filter = notifications.SubscriptionResource(
            id="testId",
            scope="test",
            code="basic_sub",
            display_name="Basic Test Subscription",
            description="Testing subscription",
            matching_pattern=matching_pattern,
            status=notifications.SubscriptionStatus.ACTIVE,
        )

        state = simple_sub_no_filter.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure - filter not present
        assert body == {
            "displayName": "Basic Test Subscription",
            "description": "Testing subscription",
            "status": "Active",
            "matchingPattern": {
                "eventType": "Manual",
            },
            "id": {
                "scope": "test",
                "code": "basic_sub"
            },
        }

        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        # Verify version hashes are included
        assert "source_version" in state
        assert "remote_version" in state

    def test_create_subscription_with_no_description(self, respx_mock):
        respx_mock.post("/notification/api/subscriptions").mock(
            return_value=httpx.Response(
                200,
                json={"id": {"scope": "test", "code": "basic_sub"}, "status": "Active"}
            )
        )
        client = self.client

        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        simple_sub_no_description = notifications.SubscriptionResource(
            id="testId",
            scope="test",
            code="basic_sub",
            display_name="Basic Test Subscription",
            status=notifications.SubscriptionStatus.ACTIVE,
            matching_pattern=matching_pattern
        )

        state = simple_sub_no_description.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure - description not present
        assert body == {
            "displayName": "Basic Test Subscription",
            "status": "Active",
            "matchingPattern": {
                "eventType": "Manual",
                "filter": "Body.Message eq 'Test'"
            },
            "id": {
                "scope": "test",
                "code": "basic_sub"
            },
        }

        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        # Verify version hashes are included
        assert "source_version" in state
        assert "remote_version" in state

    def test_create_subscription_defaults_status(self, respx_mock):
        respx_mock.post("/notification/api/subscriptions").mock(
            return_value=httpx.Response(
                200,
                json={"id": {"scope": "test", "code": "basic_sub"}, "status": "Active"}
            )
        )
        client = self.client

        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        simple_sub_no_status = notifications.SubscriptionResource(
            id="testId",
            scope="test",
            code="basic_sub",
            display_name="Basic Test Subscription",
            description="Testing subscription",

            matching_pattern=matching_pattern
        )

        state = simple_sub_no_status.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure - status should default to active
        assert body == {
            "displayName": "Basic Test Subscription",
            "description": "Testing subscription",
            "status": "Active",
            "matchingPattern": {
                "eventType": "Manual",
                "filter": "Body.Message eq 'Test'"
            },
            "id": {
                "scope": "test",
                "code": "basic_sub"
            },
        }

        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        # Verify version hashes are included
        assert "source_version" in state
        assert "remote_version" in state

    def test_create_subscription_with_use_as_auth(self, respx_mock):
        respx_mock.post("/notification/api/subscriptions").mock(
            return_value=httpx.Response(
                200,
                json={"id": {"scope": "test", "code": "basic_sub"}, "status": "Active"}
            )
        )
        client = self.client

        user_ref = identity.UserRef(id="s", login="a")
        user_ref.user_id = "myrefuser"

        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        simple_sub_with_auth = notifications.SubscriptionResource(
            id="testId",
            scope="test",
            code="basic_sub",
            display_name="Basic Test Subscription",
            description="Testing subscription",
            matching_pattern=matching_pattern,
            use_as_auth=user_ref
        )

        state = simple_sub_with_auth.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure - status should default to active
        assert body == {
            "displayName": "Basic Test Subscription",
            "description": "Testing subscription",
            "status": "Active",
            "matchingPattern": {
                "eventType": "Manual",
                "filter": "Body.Message eq 'Test'"
            },
            "useAsAuth": "myrefuser",
            "id": {
                "scope": "test",
                "code": "basic_sub"
            },
        }

        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        # Verify version hashes are included
        assert "source_version" in state
        assert "remote_version" in state

    def test_create_subscription_failure(self, respx_mock, simple_subscription):
        """Test handling of invalid subscription creation."""
        respx_mock.post("/notification/api/subscriptions").mock(
            return_value=httpx.Response(400, json={"error": "Invalid subscription"})
        )
        client = self.client
        with pytest.raises(httpx.HTTPStatusError):
            simple_subscription.create(client)

    def test_update_subscription_without_change(self, respx_mock, simple_subscription):
        """Test update functionality."""
        remote_response = {
            "id": {"scope": "test", "code": "basic_sub"},
            "displayName": "Basic Test Subscription",
            "description": "Testing subscription",
            "status": "Active",
            "eventType": "Manual",
            "matchingPattern": {
                "eventType": "Manual",
                "filter": "Body.Message eq 'Test'"
            }
        }

        respx_mock.get(
            f"/notification/api/subscriptions/{simple_subscription.scope}/{simple_subscription.code}"
        ).mock(
            return_value=httpx.Response(
                200,
                json=remote_response
            )
        )

        # Set source_version hash to the same to test no change
        source_version = simple_subscription.__get_content_hash__()

        remote_hash = sha256(json.dumps(remote_response, sort_keys=True).encode()).hexdigest()

        old_state = SimpleNamespace(
            scope="test",
            code="basic_sub",
            source_version=source_version,
            remote_version=remote_hash)

        # Same hash so we expect to return None
        result = simple_subscription.update(self.client, old_state)
        assert result is None

    def test_update_subscription_with_change(self, respx_mock, simple_subscription):
        """Test update functionality."""
        respx_mock.get(
            "/notification/api/subscriptions/test/basic_sub"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": {"scope": "test", "code": "basic_sub"},
                    "displayName": "Old state display name",
                    "description": "Testing subscription",
                    "status": "Active",
                    "eventType": "Manual",
                    "matchingPattern": {
                        "eventType": "Manual",
                        "filter": "Body.Message eq 'Test'"
                    }
                }
            )
        )
        respx_mock.put("/notification/api/subscriptions/test/basic_sub").mock(
            return_value=httpx.Response(
                200,
                json={
                }
            )
        )
        old_state = SimpleNamespace(
            scope="test",
            code="basic_sub",
            source_version="different_source",
            remote_version="different_remote")
        result = simple_subscription.update(self.client, old_state)
        # Verify PUT was called
        put_calls = [call for call in respx_mock.calls if call.request.method == "PUT"]
        assert len(put_calls) == 1
        assert result is not None

        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "displayName": "Basic Test Subscription",
            "description": "Testing subscription",
            "status": "Active",
            "matchingPattern": {
                "eventType": "Manual",
                "filter": "Body.Message eq 'Test'"
            },
            "id": {
                "scope": "test",
                "code": "basic_sub"
            },
        }

        assert result["scope"] == "test"
        assert result["code"] == "basic_sub"
        # Verify version hashes are included
        assert "source_version" in result
        assert "remote_version" in result

    def test_cannot_update_if_scope_changes(self, respx_mock, simple_subscription):
        old_state = SimpleNamespace(
            scope="different_scope",
            code="basic_sub",
            source_version="different_source",
            remote_version="different_remote")

        error_message = "Cannot change the scope on an existing subscription"
        with pytest.raises(RuntimeError, match=error_message):
            simple_subscription.update(self.client, old_state)

    def test_cannot_update_if_code_changes(self, respx_mock, simple_subscription):
        old_state = SimpleNamespace(
            scope="test",
            code="different_code",
            source_version="different_source",
            remote_version="different_remote")

        error_message = "Cannot change the code on an existing subscription"
        with pytest.raises(RuntimeError, match=error_message):
            simple_subscription.update(self.client, old_state)

    def test_delete_subscription(self, respx_mock):
        respx_mock.delete(
            "/notification/api/subscriptions/test/basic_sub"
        ).mock(return_value=httpx.Response(200))
        client = self.client
        old_state = SimpleNamespace(scope="test", code="basic_sub")
        notifications.SubscriptionResource.delete(client, old_state)
        assert respx_mock.calls.last.request.method == "DELETE"

    def test_delete_subscription_not_found(self, respx_mock):
        """Test delete handles 404 gracefully."""
        respx_mock.delete(
            "/notification/api/subscriptions/test/basic_sub"
        ).mock(return_value=httpx.Response(404))

        # Create a client without automatic error raising for this specific test
        client_no_raise = httpx.Client(base_url=TEST_BASE)
        old_state = SimpleNamespace(scope="test", code="basic_sub")

        # Should not raise an error for 404
        notifications.SubscriptionResource.delete(client_no_raise, old_state)

    def test_deps(self):
        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        user_ref = identity.UserRef(id="s", login="a")
        user_ref.user_id = "myrefuser"

        sut = notifications.SubscriptionResource(
            id="testId",
            scope="test",
            code="basic_sub",
            display_name="Basic Test Subscription",
            description="Testing subscription",
            status=notifications.SubscriptionStatus.ACTIVE,
            matching_pattern=matching_pattern,
            use_as_auth=user_ref
        )

        assert sut.deps() == [user_ref]

    def test_dump(self, respx_mock):
        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        respx_mock.post("/identity/api/users").mock(
            return_value=httpx.Response(200, json={"id": "user02"})
        )
        user = identity.UserResource(
            id="user",
            login="match",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        user.create(self.client)

        sut = notifications.SubscriptionResource(
            id="notif_id",
            scope="scope_test",
            code="code_test",
            matching_pattern=matching_pattern,
            display_name="display_name",
            description="description",
            status=notifications.SubscriptionStatus.ACTIVE,
            use_as_auth=user
        )

        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )

        assert result == {
            "scope": "scope_test",
            "code": "code_test",
            "displayName": "display_name",
            "description": "description",
            "status": "Active",
            "matchingPattern": {
                "eventType": "Manual",
                "filter": "Body.Message eq 'Test'"
            },
            "useAsAuth": {
                "$ref": "user"
            }
        }

    def test_undump(self, respx_mock):
        respx_mock.post("/identity/api/users").mock(
            return_value=httpx.Response(200, json={"id": "user02"})
        )
        user = identity.UserResource(
            id="user_id",
            login="match",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        user.create(self.client)

        data = {
            "scope": "scope_test",
            "code": "code_test",
            "displayName": "display_name",
            "description": "description",
            "status": "Active",
            "matchingPattern": {
                "eventType": "Manual",
                "filter": "Body.Message eq 'Test'"
            },
            "useAsAuth": {"$ref": "user_id"}
        }

        result = notifications.SubscriptionResource.model_validate(
            data,
            context={
                "style": "undump",
                "id": "sub_id",
                "$refs": {
                    "user_id": user,
                },
            }
        )

        assert result.id == "sub_id"
        assert result.scope == "scope_test"
        assert result.code == "code_test"
        assert result.display_name == "display_name"
        assert result.description == "description"
        assert result.status == "Active"
        assert result.matching_pattern.event_type == "Manual"
        assert result.matching_pattern.filter == "Body.Message eq 'Test'"
        assert result.use_as_auth == user

    def test_parse_api_format(self):
        # api get response not including readonly fields
        api_format = {
            "id": {
                "scope": "TestScope",
                "code": "TestCode"
            },
            "displayName": "TestDisplayName",
            "description": "TestDescription",
            "status": "Active",
            "matchingPattern": {
                "eventType": "Manual",
                "filter": "Body.Message eq 'TestMessage'"
            },
        }
        converted = notifications.SubscriptionResource.model_validate(
            api_format, context={"id": "sub_id"})

        assert converted.id == "sub_id"
        assert converted.scope == "TestScope"
        assert converted.code == "TestCode"
        assert converted.display_name == "TestDisplayName"
        assert converted.description == "TestDescription"
        assert converted.status == "Active"
        assert converted.matching_pattern.event_type == "Manual"
        assert converted.matching_pattern.filter == "Body.Message eq 'TestMessage'"


@pytest.mark.respx(base_url=TEST_BASE)
class TestNotificationRef:
    """Test NotificationRef functionality."""

    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def notification_ref(self):
        """Create a notification reference for testing."""
        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        simple_sub = notifications.SubscriptionResource(
            id="testId",
            scope="test",
            code="basic_sub",
            display_name="Basic Test Subscription",
            description="Testing subscription",
            matching_pattern=matching_pattern,
            status=notifications.SubscriptionStatus.ACTIVE,
        )

        return notifications.NotificationRef(
            id="test-notification-ref",
            subscription=simple_sub,
            notification_id="email001"
        )

    def test_notification_ref_attach_success(self, respx_mock, notification_ref):
        """Test attach method validates notification exists."""
        respx_mock.get("/notification/api/subscriptions/test/basic_sub/notifications/email001").mock(
            return_value=httpx.Response(
                200,
                json={
                    "notificationId": "email001",
                    "displayName": "Test Notification",
                    "notificationType": {"type": "Email"}
                }
            )
        )
        # Should not raise an error for existing notification
        notification_ref.attach(self.client)

    def test_notification_ref_attach_not_found(self, respx_mock, notification_ref):
        """Test attach method raises error for non-existent notification."""
        respx_mock.get("/notification/api/subscriptions/test/basic_sub/notifications/email001").mock(
            return_value=httpx.Response(404)
        )
        with pytest.raises(RuntimeError) as ex:
            notification_ref.attach(self.client)
        assert "Notification email001 for subscription test/basic_sub does not exist" in str(ex.value)

    def test_notification_ref_attach_when_http_error(self, respx_mock, notification_ref):
        respx_mock.get("/notification/api/subscriptions/test/basic_sub/notifications/email001").mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        sut = notification_ref
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class TestNotificationResource:
    """Test NotificationResource functionality."""
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def simple_sub(self):
        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        return notifications.SubscriptionResource(
            id="testId",
            scope="test",
            code="basic_sub",
            display_name="Basic Test Subscription",
            description="Testing subscription",
            status=notifications.SubscriptionStatus.ACTIVE,
            matching_pattern=matching_pattern
        )

    @pytest.fixture
    def simple_email_notification(self, simple_sub):
        email_notification_type = notifications.EmailNotificationType(
            subject="Test Event: {{body.subject}}",
            plain_text_body="Event received: {{body.message}}",
            email_address_to=["test@finbourne.com"]
        )

        return notifications.NotificationResource(
            id="testEmailId",
            subscription=simple_sub,
            notification_id="email001",
            display_name="Basic Test Email Notification",
            description="Testing email notification",
            notification_type=email_notification_type
        )

    def test_read_notification(self, respx_mock, simple_email_notification):
        respx_mock.get("/notification/api/subscriptions/old_scope/old_code/notifications/sms001").mock(
            return_value=httpx.Response(
                200,
                json={
                    "notificationId": "sms001",
                    "displayName": "Old display name",
                    "description": "Old description",
                    "notificationType": {
                        "type": "Sms",
                        "bodt": "Hello",
                        "recipients": ["+447000000000"]
                    }
                }
            )
        )
        client = self.client
        old_state = SimpleNamespace(scope="old_scope", code="old_code", notification_id="sms001")
        response = simple_email_notification.read(client, old_state)
        assert response["notificationId"] == "sms001"
        assert response["displayName"] == "Old display name"
        assert response["description"] == "Old description"
        assert response["notificationType"]["type"] == "Sms"

    def test_create_email_notification(self, respx_mock, simple_email_notification):
        respx_mock.post("/notification/api/subscriptions/test/basic_sub/notifications").mock(
            return_value=httpx.Response(
                200,
                json={
                    "notificationId": "email001",
                    "displayName": "Basic Test Email Notification",
                    "notificationType": {"type": "Email"}
                }
            )
        )
        client = self.client
        state = simple_email_notification.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "notificationId": "email001",
            "displayName": "Basic Test Email Notification",
            "description": "Testing email notification",
            "notificationType": {
                "type": "Email",
                "subject": "Test Event: {{body.subject}}",
                "plainTextBody": "Event received: {{body.message}}",
                "emailAddressTo": [
                "test@finbourne.com"
                ]
            }
        }

        # Verify returned state
        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        assert state["notification_id"] == "email001"

    def test_create_sqs_notification(self, respx_mock, simple_sub):
        respx_mock.post("/notification/api/subscriptions/test/basic_sub/notifications").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client

        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        api_key = configuration.ItemRef(id="item-key", set=set, key="api_key")
        # fake the item being attached
        api_key.ref = "config://123"

        api_secret = configuration.ItemRef(id="item-secret", set=set, key="api_secret")
        api_secret.ref = "config://456"

        api_url = configuration.ItemRef(id="item-url", set=set, key="api_url")
        api_url.ref = "config://789"

        sqs_notification_type = notifications.AmazonSqsNotificationType(
            api_key_ref=api_key,
            api_secret_ref=api_secret,
            body='{"event": "{{body.eventType}}"}',
            queue_url_ref=api_url
        )

        simple_sqs_notification = notifications.NotificationResource(
            id="testSqsId",
            subscription=simple_sub,
            notification_id="sqs001",
            display_name="Basic Test SQS Notification",
            description="Testing SQS notification",
            notification_type=sqs_notification_type
        )

        state = simple_sqs_notification.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "notificationId": "sqs001",
            "displayName": "Basic Test SQS Notification",
            "description": "Testing SQS notification",
            "notificationType": {
                "type": "AmazonSqs",
                "apiKeyRef": "config://123",
                "apiSecretRef": "config://456",
                "body": '{"event": "{{body.eventType}}"}',
                "queueUrlRef": "config://789"
            }
        }

        # Verify returned state
        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        assert state["notification_id"] == "sqs001"

    def test_create_sqs_principal_auth_notification(self, respx_mock, simple_sub):
        respx_mock.post("/notification/api/subscriptions/test/basic_sub/notifications").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client

        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        url = configuration.ItemRef(id="item-url", set=set, key="url")
        # fake the item being attached
        url.ref = "config://123"

        notification_type = notifications.AmazonSqsPrincipalAuthNotificationType(
            body="example_body",
            queue_url_ref=url
        )

        notification = notifications.NotificationResource(
            id="testId",
            subscription=simple_sub,
            notification_id="notif_id",
            display_name="Display Name",
            description="Description",
            notification_type=notification_type
        )

        state = notification.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "notificationId": "notif_id",
            "displayName": "Display Name",
            "description": "Description",
            "notificationType": {
                "type": "AmazonSqsPrincipalAuth",
                "body": "example_body",
                "queueUrlRef": "config://123"
            },
        }
        # Verify returned state
        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        assert state["notification_id"] == "notif_id"

    def test_create_azure_notification(self, respx_mock, simple_sub):
        respx_mock.post("/notification/api/subscriptions/test/basic_sub/notifications").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client

        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        name_space_ref = configuration.ItemRef(id="item-name_space_ref", set=set, key="name_space_ref")
        name_space_ref.ref = "config://123"

        queue_name_ref = configuration.ItemRef(id="item-queue_name", set=set, key="queue")
        queue_name_ref.ref = "config://234"

        tenant_id_ref = configuration.ItemRef(id="item-tenant_id_ref", set=set, key="tenant_id_ref")
        tenant_id_ref.ref = "config://345"

        client_id_ref = configuration.ItemRef(id="item-client_id_ref", set=set, key="client_id_ref")
        client_id_ref.ref = "config://456"

        client_secret_ref = configuration.ItemRef(id="item-secret_ref", set=set, key="secret_ref")
        client_secret_ref.ref = "config://567"

        azure_notification_type = notifications.AzureServiceBusNotificationType(
            body="Event with message {{body.message}}",
            namespace_ref=name_space_ref,
            queue_name_ref=queue_name_ref,
            tenant_id_ref=tenant_id_ref,
            client_id_ref=client_id_ref,
            client_secret_ref=client_secret_ref
        )

        simple_azure_notification = notifications.NotificationResource(
            id="testSqsId",
            subscription=simple_sub,
            notification_id="az001",
            display_name="Basic Test Azure Notification",
            description="Testing Azure notification",
            notification_type=azure_notification_type
        )

        state = simple_azure_notification.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "notificationId": "az001",
            "displayName": "Basic Test Azure Notification",
            "description": "Testing Azure notification",
            "notificationType": {
                "type": "AzureServiceBus",
                "body": "Event with message {{body.message}}",
                "namespaceRef": "config://123",
                "queueNameRef": "config://234",
                "tenantIdRef": "config://345",
                "clientIdRef": "config://456",
                "clientSecretRef": "config://567"
            },
        }
        # Verify returned state
        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        assert state["notification_id"] == "az001"

    def test_create_webhook_notification(self, respx_mock, simple_sub):
        respx_mock.post("/notification/api/subscriptions/test/basic_sub/notifications").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client

        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        user_name = configuration.ItemRef(id="item-username", set=set, key="user_name")
        user_name.ref = "config://123"

        password = configuration.ItemRef(id="item-password", set=set, key="password")
        password.ref = "config://234"

        notification_type = notifications.WebhookNotificationType(
            http_method="Post",
            url="example_url",
            authentication_type="BasicAuth",
            authentication_configuration_item_paths={
                "Username": user_name,
                "Password": password
            },
            content_type="Example_content_type",
            content={
                "Key": "Value Example",
                "MessageKey": "{{body.message}}"
            }
        )

        notification = notifications.NotificationResource(
            id="testId",
            subscription=simple_sub,
            notification_id="notif_id",
            display_name="Display Name",
            description="Description",
            notification_type=notification_type
        )

        state = notification.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
            "notificationId": "notif_id",
            "displayName": "Display Name",
            "description": "Description",
            "notificationType": {
                "type": "Webhook",
                "httpMethod": "Post",
                "url": "example_url",
                "authenticationType": "BasicAuth",
                "authenticationConfigurationItemPaths": {
                    "Username": "config://123",
                    "Password": "config://234"},
                "contentType": "Example_content_type",
                "content": {
                    "Key": "Value Example",
                    "MessageKey": "{{body.message}}"
                },
            },
        }
        # Verify returned state
        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        assert state["notification_id"] == "notif_id"

    def test_create_sms_notification(self, respx_mock, simple_sub):
        respx_mock.post("/notification/api/subscriptions/test/basic_sub/notifications").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client

        notification_type = notifications.SmsNotificationType(
            body="example_body",
            recipients=["+447000000000"]
        )

        notification = notifications.NotificationResource(
            id="testId",
            subscription=simple_sub,
            notification_id="notif_id",
            display_name="Display Name",
            description="Description",
            notification_type=notification_type
        )

        state = notification.create(client)
        req = respx_mock.calls.last.request
        body = json.loads(req.content)

        # Verify request body structure
        assert body == {
        "notificationId": "notif_id",
        "displayName": "Display Name",
        "description": "Description",
        "notificationType": {
            "type": "Sms",
            "body": "example_body",
            "recipients": [
            "+447000000000"
            ]
        },
        }
        # Verify returned state
        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        assert state["notification_id"] == "notif_id"

    def test_create_notification_failure(self, respx_mock, simple_email_notification):
        """Test handling of invalid notification creation."""
        respx_mock.post("/notification/api/subscriptions/test/basic_sub/notifications").mock(
            return_value=httpx.Response(400, json={"error": "Invalid notification"})
        )
        client = self.client
        with pytest.raises(httpx.HTTPStatusError):
            simple_email_notification.create(client)

    def test_update_notification_without_change(self, respx_mock, simple_email_notification):
        """Test update functionality."""
        # Mock the GET request that update() calls first to read current state
        remote_response = {
            "notificationId": "email001",
            "displayName": "Basic Test Email Notification",
            "notificationType": {"type": "Email"}
        }

        respx_mock.get("/notification/api/subscriptions/test/basic_sub/notifications/email001").mock(
            return_value=httpx.Response(
                200,
                json=remote_response
            )
        )

        # Calculate hashes to simulate no change scenario
        source_hash = simple_email_notification.__get_content_hash__()

        # The remote hash should match what update() calculates from the read() response
        remote_hash = sha256(json.dumps(remote_response, sort_keys=True).encode()).hexdigest()

        old_state = SimpleNamespace(
            scope="test",
            code="basic_sub",
            notification_id="email001",
            source_version=source_hash,
            remote_version=remote_hash
            )
        result = simple_email_notification.update(self.client, old_state)
        assert result is None

    def test_update_notification_with_change(self, respx_mock, simple_email_notification):
        """Test update functionality."""
        # Mock the GET request that update() calls first to read current state
        respx_mock.get("/notification/api/subscriptions/test/basic_sub/notifications/email001").mock(
            return_value=httpx.Response(
                200,
                json={
                    "notificationId": "email001",
                    "displayName": "Basic Test Email Notification",
                    "notificationType": {"type": "Email"}
                }
            )
        )
        # Mock the PUT request for the actual update
        respx_mock.put("/notification/api/subscriptions/test/basic_sub/notifications/email001").mock(
            return_value=httpx.Response(
                200,
                json={
                    "notificationId": "email001",
                    "displayName": "Basic Test Email Notification",
                    "notificationType": {"type": "Email"}
                }
            )
        )
        old_state = SimpleNamespace(
            scope="test",
            code="basic_sub",
            notification_id="email001",
            source_version="another_source",
            remote_version="another_remote"
            )
        result = simple_email_notification.update(self.client, old_state)
        # Verify PUT was called
        put_calls = [call for call in respx_mock.calls if call.request.method == "PUT"]
        assert len(put_calls) == 1
        assert result is not None

    def test_update_cannot_change_code(self, simple_email_notification):
        old_state = SimpleNamespace(
            scope="test",
            code="different_code",
            notification_id="email001",
            source_version="different_source",
            remote_version="different_remote"
            )
        error_message = "Cannot change the code on a notification"
        with pytest.raises(RuntimeError, match=error_message):
            simple_email_notification.update(self.client, old_state)

    def test_update_cannot_change_scope(self, simple_email_notification):
        old_state = SimpleNamespace(
            scope="different_scope",
            code="basic_sub",
            notification_id="email001",
            source_version="different_source",
            remote_version="different_remote"
            )
        error_message = "Cannot change the scope on a notification"
        with pytest.raises(RuntimeError, match=error_message):
            simple_email_notification.update(self.client, old_state)

    def test_update_notif_id(self, respx_mock, simple_email_notification):
        respx_mock.delete("/notification/api/subscriptions/test/basic_sub/notifications/different_id").mock(
            return_value=httpx.Response(200)
        )
        respx_mock.post("/notification/api/subscriptions/test/basic_sub/notifications").mock(
            return_value=httpx.Response(
                200,
                json={
                    "notificationId": "email001",
                    "displayName": "Basic Test Email Notification",
                    "notificationType": {"type": "Email"}
                }
            )
        )

        old_state = SimpleNamespace(
            scope="test",
            code="basic_sub",
            notification_id="different_id",
            source_version="different_source",
            remote_version="different_remote"
            )
        state = simple_email_notification.update(self.client, old_state)
        delete_req = respx_mock.calls[-2].request
        create_req = respx_mock.calls.last.request

        assert delete_req.method == "DELETE"
        assert create_req.method == "POST"
        body = json.loads(create_req.content)

        # Verify request body structure
        assert body == {
            "notificationId": "email001",
            "displayName": "Basic Test Email Notification",
            "description": "Testing email notification",
            "notificationType": {
                "type": "Email",
                "subject": "Test Event: {{body.subject}}",
                "plainTextBody": "Event received: {{body.message}}",
                "emailAddressTo": [
                "test@finbourne.com"
                ]
            }
        }

        # Verify returned state
        assert state["scope"] == "test"
        assert state["code"] == "basic_sub"
        assert state["notification_id"] == "email001"

    def test_delete_notification(self, respx_mock):
        respx_mock.delete("/notification/api/subscriptions/test/basic_sub/notifications/email001").mock(
            return_value=httpx.Response(200)
        )
        client = self.client
        old_state = SimpleNamespace(scope="test", code="basic_sub", notification_id="email001")
        notifications.NotificationResource.delete(client, old_state)
        assert respx_mock.calls.last.request.method == "DELETE"

    def test_email_notification_dependencies(self, simple_email_notification):
        """Test that notification depends on its parent subscription."""
        deps = simple_email_notification.deps()

        assert len(deps) == 1
        subscription_ref = deps[0]
        assert subscription_ref.scope == "test"
        assert subscription_ref.code == "basic_sub"

    def test_sqs_dependencies(self, simple_sub):
        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        api_key = configuration.ItemRef(id="item-key", set=set, key="api_key")
        # fake the item being attached
        api_key.ref = "config://123"

        api_secret = configuration.ItemRef(id="item-secret", set=set, key="api_secret")
        api_secret.ref = "config://456"

        api_url = configuration.ItemRef(id="item-url", set=set, key="api_url")
        api_url.ref = "config://789"

        sqs_notification_type = notifications.AmazonSqsNotificationType(
            api_key_ref=api_key,
            api_secret_ref=api_secret,
            body='{"event": "{{body.eventType}}"}',
            queue_url_ref=api_url
        )

        simple_sqs_notification = notifications.NotificationResource(
            id="testSqsId",
            subscription=simple_sub,
            notification_id="sqs001",
            display_name="Basic Test SQS Notification",
            description="Testing SQS notification",
            notification_type=sqs_notification_type
        )

        deps = simple_sqs_notification.deps()

        assert len(deps) == 4
        subscription_ref = deps[0]
        assert subscription_ref.scope == "test"
        assert subscription_ref.code == "basic_sub"
        assert sqs_notification_type.api_key_ref in deps
        assert deps[1].key == "api_key"
        assert deps[2].key == "api_secret"
        assert deps[3].key == "api_url"

    def test_sqs_principal_auth_notification(self, simple_sub):

        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        url = configuration.ItemRef(id="item-url", set=set, key="url")
        # fake the item being attached
        url.ref = "config://123"

        notification_type = notifications.AmazonSqsPrincipalAuthNotificationType(
            body="example_body",
            queue_url_ref=url
        )

        notification = notifications.NotificationResource(
            id="testId",
            subscription=simple_sub,
            notification_id="notif_id",
            display_name="Display Name",
            description="Description",
            notification_type=notification_type
        )

        deps = notification.deps()

        assert len(deps) == 2
        subscription_ref = deps[0]
        assert subscription_ref.scope == "test"
        assert subscription_ref.code == "basic_sub"
        assert deps[1].key == "url"
        assert notification_type.queue_url_ref in deps

    def test_azure_notification(self, simple_sub):

        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        name_space_ref = configuration.ItemRef(id="item-name_space_ref", set=set, key="name_space_ref")
        name_space_ref.ref = "config://123"

        queue_name_ref = configuration.ItemRef(id="item-queue_name", set=set, key="queue")
        queue_name_ref.ref = "config://234"

        tenant_id_ref = configuration.ItemRef(id="item-tenant_id_ref", set=set, key="tenant_id_ref")
        tenant_id_ref.ref = "config://345"

        client_id_ref = configuration.ItemRef(id="item-client_id_ref", set=set, key="client_id_ref")
        client_id_ref.ref = "config://456"

        client_secret_ref = configuration.ItemRef(id="item-secret_ref", set=set, key="secret_ref")
        client_secret_ref.ref = "config://567"

        azure_notification_type = notifications.AzureServiceBusNotificationType(
            body="Event with message {{body.message}}",
            namespace_ref=name_space_ref,
            queue_name_ref=queue_name_ref,
            tenant_id_ref=tenant_id_ref,
            client_id_ref=client_id_ref,
            client_secret_ref=client_secret_ref
        )

        simple_azure_notification = notifications.NotificationResource(
            id="testSqsId",
            subscription=simple_sub,
            notification_id="az001",
            display_name="Basic Test Azure Notification",
            description="Testing Azure notification",
            notification_type=azure_notification_type
        )

        deps = simple_azure_notification.deps()

        assert len(deps) == 6
        subscription_ref = deps[0]
        assert subscription_ref.scope == "test"
        assert subscription_ref.code == "basic_sub"
        assert deps[1].key == "name_space_ref"
        assert deps[2].key == "queue"
        assert deps[3].key == "tenant_id_ref"
        assert deps[4].key == "client_id_ref"
        assert deps[5].key == "secret_ref"
        assert azure_notification_type.namespace_ref in deps
        assert azure_notification_type.queue_name_ref in deps
        assert azure_notification_type.tenant_id_ref in deps
        assert azure_notification_type.client_id_ref in deps
        assert azure_notification_type.client_secret_ref in deps

    def test_webhook_notification(self, simple_sub):
        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        user_name = configuration.ItemRef(id="item-username", set=set, key="user_name")
        user_name.ref = "config://123"

        password = configuration.ItemRef(id="item-password", set=set, key="password")
        password.ref = "config://234"

        notification_type = notifications.WebhookNotificationType(
            http_method="Post",
            url="example_url",
            authentication_type="BasicAuth",
            authentication_configuration_item_paths={
                "Username": user_name,
                "Password": password
            },
            content_type="Example_content_type",
            content={
                "Key": "Value Example",
                "MessageKey": "{{body.message}}"
            }
        )

        notification = notifications.NotificationResource(
            id="testId",
            subscription=simple_sub,
            notification_id="notif_id",
            display_name="Display Name",
            description="Description",
            notification_type=notification_type
        )

        deps = notification.deps()

        assert len(deps) == 3
        subscription_ref = deps[0]
        assert subscription_ref.scope == "test"
        assert subscription_ref.code == "basic_sub"
        assert deps[1].key == "user_name"
        assert deps[2].key == "password"

    def test_sms_notification_dependencies(self, simple_sub):
        notification_type = notifications.SmsNotificationType(
            body="example_body",
            recipients=["+447000000000"]
        )

        notification = notifications.NotificationResource(
            id="testId",
            subscription=simple_sub,
            notification_id="notif_id",
            display_name="Display Name",
            description="Description",
            notification_type=notification_type
        )

        deps = notification.deps()

        assert len(deps) == 1
        subscription_ref = deps[0]
        assert subscription_ref.scope == "test"
        assert subscription_ref.code == "basic_sub"

    def test_dump(self, respx_mock):
        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        respx_mock.post("/identity/api/users").mock(
            return_value=httpx.Response(200, json={"id": "user02"})
        )
        user = identity.UserResource(
            id="user",
            login="match",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        user.create(self.client)

        subscription = notifications.SubscriptionResource(
            id="notif_id",
            scope="scope_test",
            code="code_test",
            matching_pattern=matching_pattern,
            display_name="display_name",
            description="description",
            status=notifications.SubscriptionStatus.ACTIVE,
            use_as_auth=user
        )

        email_notification_type = notifications.EmailNotificationType(
            subject="Test Event: {{body.subject}}",
            plain_text_body="Event received: {{body.message}}",
            email_address_to=["test@finbourne.com"]
        )

        sut = notifications.NotificationResource(
            id="testEmailId",
            subscription=subscription,
            notification_id="email001",
            display_name="Basic Test Email Notification",
            description="Testing email notification",
            notification_type=email_notification_type
        )

        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )

        assert result == {
            "subscription": {
                "$ref": "notif_id"
            },
            "notificationId": "email001",
            "displayName": "Basic Test Email Notification",
            "description": "Testing email notification",
            "notificationType": {
                "type": "Email",
                "subject": "Test Event: {{body.subject}}",
                "plainTextBody": "Event received: {{body.message}}",
                "emailAddressTo": [
                "test@finbourne.com"
                ]
            }
        }

    def test_dump_including_config_key(self, simple_sub):
        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        url = configuration.ItemRef(id="item-url", set=set, key="url")
        # fake the item being attached
        url.ref = "config://123"

        notification_type = notifications.AmazonSqsPrincipalAuthNotificationType(
            body="example_body",
            queue_url_ref=url
        )

        sut = notifications.NotificationResource(
            id="testId",
            subscription=simple_sub,
            notification_id="notif_id",
            display_name="Display Name",
            description="Description",
            notification_type=notification_type
        )

        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )

        assert result == {
            "subscription": {
                "$ref": "testId"
            },
            "notificationId": "notif_id",
            "displayName": "Display Name",
            "description": "Description",
            "notificationType": {
                "type": "AmazonSqsPrincipalAuth",
                "body": "example_body",
                "queueUrlRef": {
                    "$ref": "item-url"
                }
            }
        }

    def test_undump(self, respx_mock):
        matching_pattern = notifications.MatchingPattern(
            event_type="Manual",
            filter="Body.Message eq 'Test'"
        )

        respx_mock.post("/identity/api/users").mock(
            return_value=httpx.Response(200, json={"id": "user02"})
        )
        user = identity.UserResource(
            id="user",
            login="match",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        user.create(self.client)

        subscription = notifications.SubscriptionResource(
            id="notif_id",
            scope="scope_test",
            code="code_test",
            matching_pattern=matching_pattern,
            display_name="display_name",
            description="description",
            status=notifications.SubscriptionStatus.ACTIVE,
            use_as_auth=user
        )

        data = {
            "subscription": {
                "$ref": "notif_id"
            },
            "notificationId": "email001",
            "displayName": "Basic Test Email Notification",
            "description": "Testing email notification",
            "notificationType": {
                "type": "Email",
                "subject": "Test Event: {{body.subject}}",
                "plainTextBody": "Event received: {{body.message}}",
                "emailAddressTo": [
                "test@finbourne.com"
                ],
            }
        }

        result = notifications.NotificationResource.model_validate(
            data,
            context={
                "style": "undump",
                "id": "email_notif_id",
                "$refs": {
                    "notif_id": subscription,
                },
            }
        )

        assert result.id == "email_notif_id"
        assert result.subscription == subscription
        assert result.notification_id == "email001"
        assert result.display_name == "Basic Test Email Notification"
        assert result.description == "Testing email notification"

        notif_type = result.notification_type
        assert isinstance(
            notif_type,
            notifications.EmailNotificationType)
        assert notif_type.subject == "Test Event: {{body.subject}}"
        assert notif_type.plain_text_body == "Event received: {{body.message}}"
        assert notif_type.email_address_to == ["test@finbourne.com"]

    def test_undump_including_config_key(self, simple_sub):
        configuration_type = configuration.SetType.PERSONAL
        set = configuration.SetRef(id="set", scope="cfgscope", code="cfgcode", type=configuration_type)
        url = configuration.ItemRef(id="item-url", set=set, key="url")
        # fake the item being attached
        url.ref = "config://123"

        data = {
            "subscription": {
                "$ref": "testId"
            },
            "notificationId": "notif_id",
            "displayName": "Display Name",
            "description": "Description",
            "notificationType": {
                "type": "AmazonSqsPrincipalAuth",
                "body": "example_body",
                "queueUrlRef": {
                    "$ref": "item-url"
                }
            }
        }

        result = notifications.NotificationResource.model_validate(
            data,
            context={
                "style": "undump",
                "id": "sqs_notif_id",
                "$refs": {
                    "testId": simple_sub,
                    "item-url": url
                },
            }
        )

        assert result.id == "sqs_notif_id"
        assert result.subscription == simple_sub
        assert result.notification_id == "notif_id"
        assert result.display_name == "Display Name"
        assert result.description == "Description"

        notif_type = result.notification_type
        assert isinstance(
            notif_type,
            notifications.AmazonSqsPrincipalAuthNotificationType)
        assert notif_type.body == "example_body"
        assert notif_type.queue_url_ref == url
