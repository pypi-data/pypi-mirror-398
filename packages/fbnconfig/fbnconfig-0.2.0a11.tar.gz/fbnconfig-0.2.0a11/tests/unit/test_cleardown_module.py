import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import cleardown_module as cdm
from fbnconfig import fund_accounting as fa

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeCleardownModuleResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @staticmethod
    def create_chart_of_accounts():
        return fa.ChartOfAccountsRef(
            id="test_chart",
            scope="test-scope",
            code="test-code"
        )

    def test_create_with_rules(self, respx_mock):
        # given: mock API endpoint and create cleardown module with rules
        respx_mock.post("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_001",
                    general_ledger_account_code="test_account_code",
                    rule_filter="Account.Code startswith '200'"
                )
            ]
        )

        # when: create the resource
        state = sut.create(self.client)

        # then: verify API request and returned state
        expected_body = {
            "code": "test-cleardown-code",
            "displayName": "Test Cleardown Module",
            "rules": [
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "test_account_code",
                    "ruleFilter": "Account.Code startswith '200'"
                }
            ]
        }

        assert state["scope"] == "test-scope"
        assert state["code"] == "test-code"
        assert state["cleardown_module_code"] == "test-cleardown-code"
        assert "content_hash" in state
        assert state["rules"] == expected_body["rules"]  # Verify rules are serialized

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/test-scope/test-code/cleardownmodules"
        request_body = json.loads(request.content)
        assert request_body == expected_body

    def test_create_without_rules(self, respx_mock):
        # given: mock API endpoint and create cleardown module without rules
        respx_mock.post("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm2",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code-no-rules",
            display_name="Test Cleardown Module No Rules",
            rules=None
        )

        # when: create the resource
        state = sut.create(self.client)

        # then: verify request body excludes rules field
        expected_body = {
            "code": "test-cleardown-code-no-rules",
            "displayName": "Test Cleardown Module No Rules"
        }

        assert state["scope"] == "test-scope"
        assert state["code"] == "test-code"
        assert state["cleardown_module_code"] == "test-cleardown-code-no-rules"
        assert "content_hash" in state

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/test-scope/test-code/cleardownmodules"
        request_body = json.loads(request.content)
        assert request_body == expected_body
        assert "rules" not in request_body

    def test_create_with_multiple_rules(self, respx_mock):
        # given: mock API endpoint and create cleardown module with multiple rules
        respx_mock.post("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm4",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code-multi-rules",
            display_name="Test Cleardown Module Multiple Rules",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_001",
                    general_ledger_account_code="account_code_1",
                    rule_filter="Account.Code startswith '200'"
                ),
                cdm.CleardownModuleRule(
                    rule_id="rule_002",
                    general_ledger_account_code="account_code_2",
                    rule_filter="Account.Code startswith '300'"
                )
            ]
        )

        # when: create the resource
        sut.create(self.client)

        # then: verify both rules are included in request
        expected_body = {
            "code": "test-cleardown-code-multi-rules",
            "displayName": "Test Cleardown Module Multiple Rules",
            "rules": [
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "account_code_1",
                    "ruleFilter": "Account.Code startswith '200'"
                },
                {
                    "ruleId": "rule_002",
                    "generalLedgerAccountCode": "account_code_2",
                    "ruleFilter": "Account.Code startswith '300'"
                }
            ]
        }

        request = respx_mock.calls.last.request
        request_body = json.loads(request.content)
        assert len(request_body["rules"]) == 2
        assert request_body == expected_body

    def test_read(self, respx_mock):
        # given: mock API response and existing state
        mock_response = {
            "cleardownModuleCode": "test-cleardown-code",
            "displayName": "Test Cleardown Module",
            "chartOfAccountsId": {"scope": "test-scope", "code": "test-code"},
            "rules": [
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "test_account_code",
                    "ruleFilter": "Account.Code startswith '200'"
                }
            ]
        }
        respx_mock.get("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            rules=[]
        )

        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code"
        )

        # when: read the resource
        result = sut.read(self.client, old_state)

        # then: verify correct API call and response
        assert result == mock_response

        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == (
            "/api/api/chartofaccounts/test-scope/test-code/"
            "cleardownmodules/test-cleardown-code"
        )

    def test_update_with_no_changes(self, respx_mock):
        # given: resource with same content hash as old state
        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_001",
                    general_ledger_account_code="test_account_code",
                    rule_filter="Account.Code startswith '200'"
                )
            ]
        )

        desired = sut.model_dump(mode="json", exclude_none=True, by_alias=True,
                                 exclude={"scope", "code", "id", "chart_of_accounts"})
        desired["code"] = desired.pop("cleardownModuleCode")
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = cdm.sha256(sorted_desired.encode()).hexdigest()

        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            description=None,
            status="Active",
            rules=[
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "test_account_code",
                    "ruleFilter": "Account.Code startswith '200'"
                }
            ],
            content_hash=content_hash
        )

        # when: attempt update
        result = sut.update(self.client, old_state)

        # then: no API calls made
        assert result is None
        assert len(respx_mock.calls) == 0

    def test_update(self, respx_mock):
        # given: mock API endpoints and resource with updated metadata and rules
        respx_mock.put("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.put("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code/cleardownrules").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Updated Test Cleardown Module",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_002",
                    general_ledger_account_code="updated_account_code",
                    rule_filter="Account.Code startswith '300'"
                )
            ]
        )

        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            description=None,
            status="Active",
            rules=[
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "test_account_code",
                    "ruleFilter": "Account.Code startswith '200'"
                }
            ],
            content_hash="old_hash"
        )

        result = sut.update(self.client, old_state)

        assert result is not None
        assert result["scope"] == "test-scope"
        assert result["code"] == "test-code"
        assert result["cleardown_module_code"] == "test-cleardown-code"
        assert "content_hash" in result

        assert len(respx_mock.calls) == 2

        metadata_request = respx_mock.calls[0].request
        assert metadata_request.method == "PUT"
        assert metadata_request.url.path == (
            "/api/api/chartofaccounts/test-scope/test-code/"
            "cleardownmodules/test-cleardown-code"
        )

        metadata_body = json.loads(metadata_request.content)
        expected_metadata_body = {
            "displayName": "Updated Test Cleardown Module",
            "description": None,
            "status": "Active"
        }
        assert metadata_body == expected_metadata_body

        rules_request = respx_mock.calls[1].request
        assert rules_request.method == "PUT"
        assert rules_request.url.path == (
            "/api/api/chartofaccounts/test-scope/test-code/"
            "cleardownmodules/test-cleardown-code/cleardownrules"
        )

        rules_body = json.loads(rules_request.content)
        expected_rules_body = [
            {
                "ruleId": "rule_002",
                "generalLedgerAccountCode": "updated_account_code",
                "ruleFilter": "Account.Code startswith '300'"
            }
        ]
        assert rules_body == expected_rules_body

    def test_update_with_scope_code_changes(self, respx_mock):
        # given: mock endpoints and resource with changed scope/code/cleardown code
        respx_mock.delete("/api/api/chartofaccounts/old-scope/old-code/cleardownmodules/old-cleardown-code").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/api/api/chartofaccounts/new-scope/new-code/cleardownmodules").mock(
            return_value=httpx.Response(200, json={})
        )

        new_chart = fa.ChartOfAccountsRef(
            id="new_chart",
            scope="new-scope",
            code="new-code"
        )
        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=new_chart,
            cleardown_module_code="new-cleardown-code",
            display_name="Test Cleardown Module",
            rules=None
        )

        old_state = SimpleNamespace(
            scope="old-scope",
            code="old-code",
            cleardown_module_code="old-cleardown-code",
            content_hash="old_hash"
        )

        # when: update with changed identifiers
        result = sut.update(self.client, old_state)

        # then: old resource deleted and new one created
        assert result is not None
        assert result["scope"] == "new-scope"
        assert result["code"] == "new-code"
        assert result["cleardown_module_code"] == "new-cleardown-code"

        assert len(respx_mock.calls) == 2
        delete_request = respx_mock.calls[0].request
        create_request = respx_mock.calls[1].request
        assert delete_request.method == "DELETE"
        assert delete_request.url.path == (
            "/api/api/chartofaccounts/old-scope/old-code/"
            "cleardownmodules/old-cleardown-code"
        )

        expected_body = {
            "code": "new-cleardown-code",
            "displayName": "Test Cleardown Module"
        }
        request_body = json.loads(create_request.content)
        assert create_request.method == "POST"
        assert create_request.url.path == "/api/api/chartofaccounts/new-scope/new-code/cleardownmodules"
        assert request_body == expected_body

    def test_delete(self, respx_mock):
        # given: mock delete endpoint and existing state
        respx_mock.delete("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code").mock(
            return_value=httpx.Response(200, json={})
        )

        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code"
        )

        # when: delete the resource
        cdm.CleardownModuleResource.delete(self.client, old_state)

        # then: verify correct DELETE request
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == (
            "/api/api/chartofaccounts/test-scope/test-code/"
            "cleardownmodules/test-cleardown-code"
        )

    def test_update_metadata_only(self, respx_mock):
        """Test update when only display_name, description, or status changes (not rules)"""
        # given: mock only metadata endpoint (rules haven't changed)
        respx_mock.put("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Updated Display Name",
            description="Updated description",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_001",
                    general_ledger_account_code="test_account_code",
                    rule_filter="Account.Code startswith '200'"
                )
            ]
        )

        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code",
            display_name="Old Display Name",
            description="Old description",
            status="Active",
            rules=[
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "test_account_code",
                    "ruleFilter": "Account.Code startswith '200'"
                }
            ],
            content_hash="old_hash"
        )

        # when: update the resource
        result = sut.update(self.client, old_state)

        # then: only metadata endpoint called (rules haven't changed)
        assert result is not None
        assert result["scope"] == "test-scope"
        assert result["code"] == "test-code"
        assert result["cleardown_module_code"] == "test-cleardown-code"
        assert "content_hash" in result

        assert len(respx_mock.calls) == 1

        metadata_request = respx_mock.calls[0].request
        assert metadata_request.method == "PUT"
        assert metadata_request.url.path == (
            "/api/api/chartofaccounts/test-scope/test-code/"
            "cleardownmodules/test-cleardown-code"
        )

        metadata_body = json.loads(metadata_request.content)
        expected_metadata_body = {
            "displayName": "Updated Display Name",
            "description": "Updated description",
            "status": "Active"
        }
        assert metadata_body == expected_metadata_body

    def test_update_rules_only(self, respx_mock):
        """Test update when only rules change (not metadata)"""
        # given: mock endpoint and resource with only rules changed
        respx_mock.put("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code/cleardownrules").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Same Display Name",
            description="Same description",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_002",
                    general_ledger_account_code="new_account_code",
                    rule_filter="Account.Code startswith '300'"
                )
            ]
        )

        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code",
            display_name="Same Display Name",
            description="Same description",
            status="Active",
            content_hash="old_hash"
        )

        # when: update the resource
        result = sut.update(self.client, old_state)

        # then: only rules endpoint called
        assert result is not None
        assert result["scope"] == "test-scope"
        assert result["code"] == "test-code"
        assert result["cleardown_module_code"] == "test-cleardown-code"
        assert "content_hash" in result

        assert len(respx_mock.calls) == 1
        request = respx_mock.calls[0].request
        assert request.method == "PUT"
        assert request.url.path == (
            "/api/api/chartofaccounts/test-scope/test-code/"
            "cleardownmodules/test-cleardown-code/cleardownrules"
        )

        request_body = json.loads(request.content)
        expected_body = [
            {
                "ruleId": "rule_002",
                "generalLedgerAccountCode": "new_account_code",
                "ruleFilter": "Account.Code startswith '300'"
            }
        ]
        assert request_body == expected_body

    def test_update_both_metadata_and_rules_updates_both(self, respx_mock):
        """Test update when both metadata and rules change - should update both separately"""
        # given: mock both endpoints and resource with metadata and rules changed
        respx_mock.put("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.put("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code/cleardownrules").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Updated Display Name",
            description="Updated description",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_002",
                    general_ledger_account_code="new_account_code",
                    rule_filter="Account.Code startswith '300'"
                )
            ]
        )

        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code",
            display_name="Old Display Name",
            description="Old description",
            status="Active",
            content_hash="old_hash"
        )

        # when: update the resource
        result = sut.update(self.client, old_state)

        # then: both endpoints called separately
        assert result is not None
        assert result["scope"] == "test-scope"
        assert result["code"] == "test-code"
        assert result["cleardown_module_code"] == "test-cleardown-code"
        assert "content_hash" in result

        assert len(respx_mock.calls) == 2

        metadata_request = respx_mock.calls[0].request
        assert metadata_request.method == "PUT"
        assert metadata_request.url.path == (
            "/api/api/chartofaccounts/test-scope/test-code/"
            "cleardownmodules/test-cleardown-code"
        )

        metadata_body = json.loads(metadata_request.content)
        expected_metadata_body = {
            "displayName": "Updated Display Name",
            "description": "Updated description",
            "status": "Active"
        }
        assert metadata_body == expected_metadata_body

        # Second request should be rules update
        rules_request = respx_mock.calls[1].request
        assert rules_request.method == "PUT"
        assert rules_request.url.path == (
            "/api/api/chartofaccounts/test-scope/test-code/"
            "cleardownmodules/test-cleardown-code/cleardownrules"
        )

        rules_body = json.loads(rules_request.content)
        expected_rules_body = [
            {
                "ruleId": "rule_002",
                "generalLedgerAccountCode": "new_account_code",
                "ruleFilter": "Account.Code startswith '300'"
            }
        ]
        assert rules_body == expected_rules_body

    def test_update_status_only(self, respx_mock):
        """Test update when only status changes"""
        # given: mock only metadata endpoint (rules haven't changed)
        respx_mock.put("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Same Display Name",
            description="Same description",
            status="Inactive",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_001",
                    general_ledger_account_code="test_account_code",
                    rule_filter="Account.Code startswith '200'"
                )
            ]
        )

        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code",
            display_name="Same Display Name",
            description="Same description",
            status="Active",
            rules=[
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "test_account_code",
                    "ruleFilter": "Account.Code startswith '200'"
                }
            ],
            content_hash="old_hash"
        )

        # when: update the resource
        result = sut.update(self.client, old_state)

        # then: only metadata endpoint called (rules haven't changed)
        assert result is not None
        assert len(respx_mock.calls) == 1

        metadata_request = respx_mock.calls[0].request
        assert metadata_request.method == "PUT"
        assert metadata_request.url.path == (
            "/api/api/chartofaccounts/test-scope/test-code/"
            "cleardownmodules/test-cleardown-code"
        )

    def test_update_with_missing_old_state_attributes(self, respx_mock):
        """Test that update handles missing attributes in old_state gracefully"""
        # given: mock only metadata endpoint (rules are None in both old and new state)
        respx_mock.put("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="New Display Name",
            description="New description",
            rules=None
        )

        # Old state only has minimal fields (simulating deployment system state)
        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code",
            content_hash="old_hash"
            # Missing: display_name, description, status, rules
        )

        # when: update with incomplete old state
        result = sut.update(self.client, old_state)

        # then: handles missing attributes and updates only metadata (rules are both None)
        assert result is not None
        assert len(respx_mock.calls) == 1

        metadata_request = respx_mock.calls[0].request
        assert metadata_request.method == "PUT"

    def test_deps_returns_chart_of_accounts_when_no_rules(self):
        # given: cleardown module with no rules
        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            rules=[]
        )

        # when: get dependencies
        deps = sut.deps()

        # then: only chart of accounts returned
        assert len(deps) == 1
        assert deps[0] == sut.chart_of_accounts

    def test_deps_returns_chart_and_accounts_when_rules_exist(self):
        # given: cleardown module with multiple rules (including duplicate account)
        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_001",
                    general_ledger_account_code="account_1",
                    rule_filter="Account.Code startswith '200'"
                ),
                cdm.CleardownModuleRule(
                    rule_id="rule_002",
                    general_ledger_account_code="account_2",
                    rule_filter="Account.Code startswith '300'"
                )
            ]
        )

        # when: get dependencies
        deps = sut.deps()

        # then: chart plus unique account references returned
        # Should have chart of accounts + 2 unique account references
        assert len(deps) == 3
        assert deps[0] == sut.chart_of_accounts

        # Check account dependencies
        account_deps = [dep for dep in deps[1:] if isinstance(dep, fa.AccountRef)]
        assert len(account_deps) == 2
        account_codes = {dep.account_code for dep in account_deps}
        assert account_codes == {"account_1", "account_2"}

    def test_dump_model(self):
        # given: cleardown module resource
        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            rules=None
        )

        # when: dump model to dict
        result = sut.model_dump(
            mode="json", by_alias=True, exclude_none=True, context={"style": "dump"}, round_trip=True
        )

        # then: chart ref serialized correctly
        expected = {
            "cleardownModuleCode": "test-cleardown-code",
            "displayName": "Test Cleardown Module",
            "chartOfAccounts": {"$ref": "test_chart"}
        }

        assert result == expected

    def test_dump_model_with_rules(self):
        # given: cleardown module resource with rules
        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_001",
                    general_ledger_account_code="account_code_1",
                    rule_filter="Account.Code startswith '200'"
                )
            ]
        )

        # when: dump model to dict
        result = sut.model_dump(
            mode="json", by_alias=True, exclude_none=True, context={"style": "dump"}, round_trip=True
        )

        # then: chart ref and rules serialized correctly
        expected = {
            "cleardownModuleCode": "test-cleardown-code",
            "displayName": "Test Cleardown Module",
            "chartOfAccounts": {"$ref": "test_chart"},
            "rules": [
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "account_code_1",
                    "ruleFilter": "Account.Code startswith '200'"
                }
            ]
        }

        assert result == expected

    def test_undump_model(self):
        # given: dict representation with $ref for chart_of_accounts
        chart_of_accounts = self.create_chart_of_accounts()
        data = {
            "id": "cdm1",
            "chartOfAccounts": {"$ref": "test_chart"},
            "cleardownModuleCode": "test-cleardown-code",
            "displayName": "Test Cleardown Module",
            "rules": None
        }

        # when: validate dict to model with chart reference in context
        result = cdm.CleardownModuleResource.model_validate(
            data,
            context={
                "style": "undump",
                "id": "cdm1",
                "$refs": {
                    "test_chart": chart_of_accounts
                }
            }
        )

        # then: model fields populated correctly
        assert result.id == "cdm1"
        assert result.scope == "test-scope"
        assert result.code == "test-code"
        assert result.cleardown_module_code == "test-cleardown-code"
        assert result.display_name == "Test Cleardown Module"
        assert result.rules is None

    def test_undump_model_with_rules(self):
        # given: dict representation with $ref for chart_of_accounts and rules
        chart_of_accounts = self.create_chart_of_accounts()
        data = {
            "id": "cdm1",
            "chartOfAccounts": {"$ref": "test_chart"},
            "cleardownModuleCode": "test-cleardown-code",
            "displayName": "Test Cleardown Module",
            "rules": [
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "account_code_1",
                    "ruleFilter": "Account.Code startswith '200'"
                }
            ]
        }

        # when: validate dict to model with chart reference in context
        result = cdm.CleardownModuleResource.model_validate(
            data,
            context={
                "style": "undump",
                "id": "cdm1",
                "$refs": {
                    "test_chart": chart_of_accounts
                }
            }
        )

        # then: model fields and rules populated correctly
        assert result.id == "cdm1"
        assert result.scope == "test-scope"
        assert result.code == "test-code"
        assert result.cleardown_module_code == "test-cleardown-code"
        assert result.display_name == "Test Cleardown Module"
        assert result.rules is not None
        assert len(result.rules) == 1
        assert result.rules[0].rule_id == "rule_001"
        assert result.rules[0].general_ledger_account_code == "account_code_1"

    def test_create_returns_all_required_state_fields(self, respx_mock):
        # given: mock API endpoint
        respx_mock.post("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Test Cleardown Module",
            description="Test description",
            status="Active",
            rules=[
                cdm.CleardownModuleRule(
                    rule_id="rule_001",
                    general_ledger_account_code="test_account_code",
                    rule_filter="Account.Code startswith '200'"
                )
            ]
        )

        # when: create the resource
        state = sut.create(self.client)

        # then: verify all required state fields are present
        required_fields = [
            "scope",
            "code",
            "cleardown_module_code",
            "display_name",
            "description",
            "status",
            "rules",
            "content_hash"
        ]

        for field in required_fields:
            assert field in state, f"State missing required field: {field}"

        # Verify field values are correct
        expected_state = {
            "scope": "test-scope",
            "code": "test-code",
            "cleardown_module_code": "test-cleardown-code",
            "display_name": "Test Cleardown Module",
            "description": "Test description",
            "status": "Active",
            "rules": [
                {
                    "ruleId": "rule_001",
                    "generalLedgerAccountCode": "test_account_code",
                    "ruleFilter": "Account.Code startswith '200'"
                }
            ]
        }

        # Compare all fields except content_hash
        for key, value in expected_state.items():
            assert state[key] == value, f"State field {key} mismatch"

        # Validate content_hash separately
        assert isinstance(state["content_hash"], str)
        assert len(state["content_hash"]) == 64  # SHA256 hash length

    def test_update_returns_all_required_state_fields(self, respx_mock):
        # given: mock API endpoints
        respx_mock.put("/api/api/chartofaccounts/test-scope/test-code/cleardownmodules/test-cleardown-code").mock(
            return_value=httpx.Response(200, json={})
        )

        sut = cdm.CleardownModuleResource(
            id="cdm1",
            chart_of_accounts=self.create_chart_of_accounts(),
            cleardown_module_code="test-cleardown-code",
            display_name="Updated Display Name",
            description="Updated description",
            status="Inactive",
            rules=None
        )

        old_state = SimpleNamespace(
            scope="test-scope",
            code="test-code",
            cleardown_module_code="test-cleardown-code",
            display_name="Old Display Name",
            description="Old description",
            status="Active",
            rules=None,
            content_hash="old_hash"
        )

        # when: update the resource
        state = sut.update(self.client, old_state)

        # then: verify state is returned (not None) and contains all required fields
        assert state is not None, "Update should return state when changes are made"

        required_fields = [
            "scope",
            "code",
            "cleardown_module_code",
            "display_name",
            "description",
            "status",
            "rules",
            "content_hash"
        ]

        for field in required_fields:
            assert field in state, f"State missing required field: {field}"

        # Verify field values are correct
        expected_state = {
            "scope": "test-scope",
            "code": "test-code",
            "cleardown_module_code": "test-cleardown-code",
            "display_name": "Updated Display Name",
            "description": "Updated description",
            "status": "Inactive",
            "rules": None
        }

        # Compare all fields except content_hash
        for key, value in expected_state.items():
            assert state[key] == value, f"State field {key} mismatch"

        # Validate content_hash separately
        assert isinstance(state["content_hash"], str)
        assert len(state["content_hash"]) == 64  # SHA256 hash length
