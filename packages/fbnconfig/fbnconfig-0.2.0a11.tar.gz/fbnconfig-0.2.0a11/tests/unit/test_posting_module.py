import json
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import fund_accounting, posting_module, property

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribePostingModuleRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        url = "/api/api/chartofaccounts/testScope/testCode/postingmodules/module_code"
        respx_mock.get(url).mock(
            return_value=httpx.Response(200, json={})
        )

        client = self.client
        post_mod = posting_module.PostingModuleRef(
            id="example_post_module",
            scope="testScope",
            code="testCode",
            posting_module_code="module_code"
        )

        # when we call attach
        post_mod.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        url = "/api/api/chartofaccounts/testScope/testCode/postingmodules/module_code"
        respx_mock.get(url).mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        post_mod = posting_module.PostingModuleRef(
            id="example_post_module",
            scope="testScope",
            code="testCode",
            posting_module_code="module_code"
        )
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            post_mod.attach(client)
        assert "Posting Module module_code not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        url = "/api/api/chartofaccounts/testScope/testCode/postingmodules/module_code"
        respx_mock.get(url).mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        post_mod = posting_module.PostingModuleRef(
            id="example_post_module",
            scope="testScope",
            code="testCode",
            posting_module_code="module_code"
        )
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            post_mod.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribePostingModule:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def stock_posting_module(self):
        chart = fund_accounting.ChartOfAccountsResource(
            id="chart_example_id",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        perp_prop = fund_accounting.PropertyValue(
            property_key=property.DefinitionRef(
                id="one", domain=property.Domain.Account, scope="sc1", code="cd4"
            ),
            label_value="Hello"
        )

        account = fund_accounting.AccountResource(
            id="account_example_id",
            chart_of_accounts=chart,
            code="account_code",
            description="example_desc",
            type=fund_accounting.AccountType.ASSET,
            status=fund_accounting.AccountStatus.ACTIVE,
            control="Manual",
            properties=[perp_prop]
        )

        rule = posting_module.PostingModuleRule(
            rule_id="rule_id",
            general_ledger_account_code=account,
            rule_filter="Transaction.TransactionId eq 'Transaction_1'"
        )

        return posting_module.PostingModuleResource(
            id="post_mod_id",
            chart_of_accounts=chart,
            code="post_mod_code",
            display_name="post_mod_display",
            description="post_mod_desc",
            rules=[rule]
        )

    def test_read(self, respx_mock, stock_posting_module):
        response = {
            "href": "http://example.com",
            "postingModuleCode": "oldPostCode",
            "chartOfAccountsId": {
                "scope": "oldScope",
                "code": "oldCode"
            },
            "displayName": "string",
            "description": "string",
            "rules": [
                {
                "ruleId": "string",
                "generalLedgerAccountCode": "string",
                "ruleFilter": "string"
                }
            ],
            "status": "string",
            "version": {
                "effectiveFrom": "2019-08-24T14:15:22Z",
                "asAtDate": "2019-08-24T14:15:22Z",
                "asAtCreated": "2019-08-24T14:15:22Z",
                "userIdCreated": "string",
                "requestIdCreated": "string",
                "reasonCreated": "string",
                "asAtModified": "2019-08-24T14:15:22Z",
                "userIdModified": "string",
                "requestIdModified": "string",
                "reasonModified": "string",
                "asAtVersionNumber": -2147483648,
                "entityUniqueId": "string",
                "stagedModificationIdModified": "string"
            },
            "links": [
                {
                "relation": "string",
                "href": "http://example.com",
                "description": "string",
                "method": "string"
                }
            ]
        }

        respx_mock.get("/api/api/chartofaccounts/oldScope/oldCode/postingmodules/oldPostCode").mock(
            return_value=httpx.Response(
                200,
                json=response

            )
        )
        sut = stock_posting_module
        old_state = SimpleNamespace(
            scope="oldScope",
            code="oldCode",
            module_code="oldPostCode"
        )
        result = sut.read(self.client, old_state)
        assert result is not None

        # Simulate popped fields and assert they are now the same
        response.pop("href", None)
        response.pop("links", None)
        response.pop("status", None)
        response.pop("version", None)
        assert result == response

    def test_create_with_rules(self, respx_mock, stock_posting_module):
        response = {
            "postingModuleCode": "string",
            "chartOfAccountsId": {
                "scope": "testScope",
                "code": "testCode"
            },
            "displayName": "example_display_name",
            "description": "example_description",
            "rules": [
                {
                    "ruleId": "rule_id",
                    "generalLedgerAccountCode": "example_id",
                    "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ]
        }
        respx_mock.post("/api/api/chartofaccounts/testScope/testCode/postingmodules").mock(
            return_value=httpx.Response(200, json=response))

        sut = stock_posting_module
        result = sut.create(self.client)

        assert result is not None

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope/testCode/postingmodules"

        body = json.loads(request.content)
        assert body == {
            "code": "post_mod_code",
            "displayName": "post_mod_display",
            "description": "post_mod_desc",
            "rules": [
                {
                    "ruleId": "rule_id",
                    "generalLedgerAccountCode": "account_code",
                    "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ]
        }

        source_hash = sut.__get_content_hash__()
        remote_hash = sha256(json.dumps(response, sort_keys=True).encode()).hexdigest()

        assert result == {
            "module_code": "post_mod_code",
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_hash,
            "remote_version": remote_hash
        }

    def test_create_without_rules(self, respx_mock):
        response = {
            "postingModuleCode": "string",
            "chartOfAccountsId": {
                "scope": "testScope",
                "code": "testCode"
            },
            "displayName": "example_display_name",
            "description": "example_description",
            "rules": []
        }
        respx_mock.post("/api/api/chartofaccounts/testScope/testCode/postingmodules").mock(
            return_value=httpx.Response(200, json=response))

        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        sut = posting_module.PostingModuleResource(
            id="post_mod_id",
            chart_of_accounts=chart,
            code="post_mod_code",
            display_name="post_mod_display",
            description="post_mod_desc",
        )

        result = sut.create(self.client)

        assert result is not None

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope/testCode/postingmodules"

        # Rules is not present
        body = json.loads(request.content)
        assert body == {
            "code": "post_mod_code",
            "displayName": "post_mod_display",
            "description": "post_mod_desc",
        }

        source_hash = sut.__get_content_hash__()
        remote_hash = sha256(json.dumps(response, sort_keys=True).encode()).hexdigest()

        assert result == {
            "module_code": "post_mod_code",
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_hash,
            "remote_version": remote_hash
        }

    def test_create_without_description(self, respx_mock):
        response = {
            "postingModuleCode": "string",
            "chartOfAccountsId": {
                "scope": "testScope",
                "code": "testCode"
            },
            "displayName": "example_display_name",
            "rules": [
                {
                    "ruleId": "rule_id",
                    "generalLedgerAccountCode": "example_id",
                    "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ]
        }
        respx_mock.post("/api/api/chartofaccounts/testScope/testCode/postingmodules").mock(
            return_value=httpx.Response(200, json=response))

        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        account = fund_accounting.AccountResource(
            id="example_id",
            chart_of_accounts=chart,
            code="account_code",
            description="example_desc",
            type=fund_accounting.AccountType.ASSET,
            status=fund_accounting.AccountStatus.ACTIVE,
            control="Manual",
        )

        rule = posting_module.PostingModuleRule(
            rule_id="rule_id",
            general_ledger_account_code=account,
            rule_filter="Transaction.TransactionId eq 'Transaction_1'"
        )

        sut = posting_module.PostingModuleResource(
            id="post_mod_id",
            chart_of_accounts=chart,
            code="post_mod_code",
            display_name="post_mod_display",
            rules=[rule]
        )

        result = sut.create(self.client)

        assert result is not None

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope/testCode/postingmodules"

        # Description is not present
        body = json.loads(request.content)
        assert body == {
            "code": "post_mod_code",
            "displayName": "post_mod_display",
            "rules": [
                {
                "ruleId": "rule_id",
                "generalLedgerAccountCode": "account_code",
                "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ]

        }

        source_hash = sut.__get_content_hash__()
        remote_hash = sha256(json.dumps(response, sort_keys=True).encode()).hexdigest()

        assert result == {
            "module_code": "post_mod_code",
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_hash,
            "remote_version": remote_hash
        }

    def test_update_no_change(self, respx_mock, stock_posting_module):
        remote_response = {
            "code": "post_mod_code",
            "displayName": "post_mod_display",
            "description": "post_mod_desc",
            "rules": [
                {
                "ruleId": "rule_id",
                "generalLedgerAccountCode": "account_code",
                "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ],
        }
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/postingmodules/post_mod_code").mock(
            return_value=httpx.Response(200, json=remote_response)
        )
        sut = stock_posting_module

        # Calculate hashes to simulate no change scenario
        source_hash = sut.__get_content_hash__()
        remote_hash = sha256(json.dumps(remote_response, sort_keys=True).encode()).hexdigest()

        old_state = SimpleNamespace(
            module_code="post_mod_code",
            scope="testScope",
            code="testCode",
            source_version=source_hash,
            remote_version=remote_hash
        )
        result = sut.update(self.client, old_state)
        assert result is None

    def test_update_change_code(self, respx_mock, stock_posting_module):
        respx_mock.delete("/api/api/chartofaccounts/testScope/testCode/postingmodules/different_code").mock(
            return_value=httpx.Response(200)
        )
        response = {
            "postingModuleCode": "string",
            "chartOfAccountsId": {
                "scope": "testScope",
                "code": "testCode"
            },
            "displayName": "example_display_name",
            "description": "example_description",
            "rules": [
                {
                "ruleId": "rule_id",
                "generalLedgerAccountCode": "example_id",
                "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ]
        }
        respx_mock.post("/api/api/chartofaccounts/testScope/testCode/postingmodules").mock(
            return_value=httpx.Response(200, json=response)
        )
        sut = stock_posting_module

        # Calculate hashes
        source_hash = sut.__get_content_hash__()

        # Only code is different (module code)
        old_state = SimpleNamespace(
            module_code="different_code",
            scope="testScope",
            code="testCode",
            source_version=source_hash,
            remote_version=-2147483648
        )
        result = sut.update(self.client, old_state)
        assert result is not None

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope/testCode/postingmodules"

        # Verify delete and create were called - we don't expect a read
        assert len(respx_mock.calls) == 2
        assert respx_mock.calls[0].request.method == "DELETE"
        assert respx_mock.calls.last.request.method == "POST"

        body = json.loads(request.content)
        assert body == {
            "code": "post_mod_code",
            "displayName": "post_mod_display",
            "description": "post_mod_desc",
            "rules": [
                {
                    "ruleId": "rule_id",
                    "generalLedgerAccountCode": "account_code",
                    "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ]
        }

        source_hash = sut.__get_content_hash__()
        remote_hash = sha256(json.dumps(response, sort_keys=True).encode()).hexdigest()

        assert result == {
            "module_code": "post_mod_code",
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_hash,
            "remote_version": remote_hash
        }

    def test_update_with_change(self, respx_mock, stock_posting_module):
        remote_response = {
            "code": "post_mod_code",
            "displayName": "post_mod_display",
            "description": "post_mod_desc",
            "rules": [
                {
                    "ruleId": "rule_id",
                    "generalLedgerAccountCode": "account_code",
                    "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ],

        }
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/postingmodules/post_mod_code").mock(
            return_value=httpx.Response(200, json=remote_response)
        )

        respx_mock.delete("/api/api/chartofaccounts/testScope/testCode/postingmodules/post_mod_code").mock(
            return_value=httpx.Response(200)
        )
        new_response = {
            "postingModuleCode": "post_mod_id",
            "chartOfAccountsId": {
                "scope": "testScope",
                "code": "testCode"
            },
            "displayName": "updated_post_mod_display",
            "description": "updated_post_mod_desc",
            "rules": []
        }
        respx_mock.post("/api/api/chartofaccounts/testScope/testCode/postingmodules").mock(
            return_value=httpx.Response(200, json=new_response)
        )

        old_source = stock_posting_module.__get_content_hash__()
        old_remote = sha256(json.dumps(remote_response, sort_keys=True).encode()).hexdigest()

        old_state = SimpleNamespace(
            module_code="post_mod_code",
            scope="testScope",
            code="testCode",
            remote_version=old_remote,
            source_version=old_source
        )

        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        updated_post_mod = posting_module.PostingModuleResource(
            id="post_mod_id",
            chart_of_accounts=chart,
            code="post_mod_code",
            display_name="updated_post_mod_display",
            description="updated_post_mod_desc",
        )

        result = updated_post_mod.update(self.client, old_state)
        assert result is not None

        source_hash = updated_post_mod.__get_content_hash__()
        remote_hash = sha256(json.dumps(new_response, sort_keys=True).encode()).hexdigest()

        assert result == {
            "module_code": "post_mod_code",
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_hash,
            "remote_version": remote_hash
        }

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope/testCode/postingmodules"

        body = json.loads(request.content)

        # Body is now the updated version
        assert body == {
            "code": "post_mod_code",
            "displayName": "updated_post_mod_display",
            "description": "updated_post_mod_desc",
        }

        # Verify read, delete and create were called
        assert len(respx_mock.calls) == 3
        assert respx_mock.calls[0].request.method == "GET"
        assert respx_mock.calls[1].request.method == "DELETE"
        assert respx_mock.calls.last.request.method == "POST"

    def test_cannot_update_if_scope_changes(self, stock_posting_module):
        old_state = SimpleNamespace(
            module_code="post_mod_code",
            scope="different_scope",
            code="testCode",
            remote_version="oldhash",
            source_version="different_hash"
        )

        sut = stock_posting_module
        error_message = "Cannot change the scope of the chart of account on an posting module"
        with pytest.raises(RuntimeError, match=error_message):
            sut.update(self.client, old_state)

    def test_cannot_update_if_code_changes(self, stock_posting_module):
        old_state = SimpleNamespace(
            module_code="post_mod_code",
            scope="testScope",
            code="different_code",
            remote_version="oldhash",
            source_version="different_hash"
        )

        sut = stock_posting_module
        error_message = "Cannot change the code of the chart of account on an posting module"
        with pytest.raises(RuntimeError, match=error_message):
            sut.update(self.client, old_state)

    def test_delete(self, respx_mock):
        respx_mock.delete(
            "/api/api/chartofaccounts/testScope/testCode/postingmodules/post_mod_code"
        ).mock(return_value=httpx.Response(200))
        client = self.client
        old_state = SimpleNamespace(module_code="post_mod_code", scope="testScope", code="testCode")
        posting_module.PostingModuleResource.delete(client, old_state)
        assert respx_mock.calls.last.request.method == "DELETE"

    def test_deps(self):
        chart_prop = property.DefinitionRef(
            id="one", domain=property.Domain.Account, scope="sc1", code="cd4"
        )

        chart_perp_prop = fund_accounting.PropertyValue(
            property_key=chart_prop,
            label_value="Hello"
        )

        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
            properties=[chart_perp_prop]
        )

        acc_prop = property.DefinitionRef(
            id="two", domain=property.Domain.Account, scope="sc1", code="cd4"
        )

        acc_perp_prop = fund_accounting.PropertyValue(
            property_key=acc_prop,
            label_value="Hello"
        )

        account = fund_accounting.AccountResource(
            id="example_id",
            chart_of_accounts=chart,
            code="account_code",
            description="example_desc",
            type=fund_accounting.AccountType.ASSET,
            status=fund_accounting.AccountStatus.ACTIVE,
            control="Manual",
            properties=[acc_perp_prop]
        )

        rule = posting_module.PostingModuleRule(
            rule_id="rule_id",
            general_ledger_account_code=account,
            rule_filter="Transaction.TransactionId eq 'Transaction_1'"
        )

        post_mod = posting_module.PostingModuleResource(
            id="post_mod_id",
            chart_of_accounts=chart,
            code="post_mod_code",
            display_name="post_mod_display",
            description="post_mod_desc",
            rules=[rule]
        )

        deps = post_mod.deps()

        assert len(deps) == 2
        assert chart in deps
        assert account in deps

    def test_dump(self, stock_posting_module):
        sut = stock_posting_module

        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )

        assert result == {
            "chartOfAccounts": {
                "$ref": "chart_example_id"
            },
            "code": "post_mod_code",
            "displayName": "post_mod_display",
            "description": "post_mod_desc",
            "rules": [
                {
                    "ruleId": "rule_id",
                    "generalLedgerAccountCode": {
                        "$ref": "account_example_id"
                    },
                    "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ]
        }

    def test_undump(self):
        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        account = fund_accounting.AccountResource(
            id="example_id",
            chart_of_accounts=chart,
            code="account_code",
            description="example_desc",
            type=fund_accounting.AccountType.ASSET,
            status=fund_accounting.AccountStatus.ACTIVE,
            control="Manual",
        )

        rule = posting_module.PostingModuleRule(
            rule_id="rule_id",
            general_ledger_account_code=account,
            rule_filter="Transaction.TransactionId eq 'Transaction_1'"
        )

        data = {
            "chartOfAccounts": {
                "$ref": "exampleId"
            },
            "code": "post_mod_code",
            "displayName": "post_mod_display",
            "description": "post_mod_desc",
            "rules": [
                {
                    "ruleId": "rule_id",
                    "generalLedgerAccountCode": {
                        "$ref": "example_id"
                    },
                    "ruleFilter": "Transaction.TransactionId eq 'Transaction_1'"
                }
            ]
        }

        result = posting_module.PostingModuleResource.model_validate(
            data,
            context={
                "style": "undump",
                "$refs": {
                    "exampleId": chart,
                    "example_id": account
                },
                "id": "undump_post",
            }
        )

        assert result.id == "undump_post"
        assert result.chart_of_accounts == chart
        assert result.chart_of_accounts.code == "testCode"
        assert result.chart_of_accounts.scope == "testScope"
        assert result.code == "post_mod_code"
        assert result.display_name == "post_mod_display"
        assert result.description == "post_mod_desc"
        assert result.rules == [rule]
