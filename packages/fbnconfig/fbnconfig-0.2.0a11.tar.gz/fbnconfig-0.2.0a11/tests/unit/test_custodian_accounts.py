import json
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import custodian_accounts, property
from fbnconfig.properties import PropertyValue

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeCustodianAccountRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_success(self, respx_mock):
        """Test that attach succeeds when custodian account exists."""
        route = respx_mock.get(
            "/api/api/transactionportfolios/TestPortfolio/EQUITY-GROWTH/custodianaccounts/CustodianAccounts/HSBC-FIFO"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "custodianAccountId": {"scope": "CustodianAccounts", "code": "HSBC-FIFO"},
                    "status": "Active",
                },
            )
        )

        ref = custodian_accounts.CustodianAccountRef(
            id="test-ref",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
        )

        ref.attach(self.client)
        assert route.called

    def test_attach_not_found(self, respx_mock):
        """Test that attach raises error when custodian account doesn't exist."""
        respx_mock.get(
            "/api/api/transactionportfolios/TestPortfolio/EQUITY-GROWTH/custodianaccounts/CustodianAccounts/HSBC-FIFO"
        ).mock(return_value=httpx.Response(404))

        ref = custodian_accounts.CustodianAccountRef(
            id="test-ref",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
        )

        with pytest.raises(RuntimeError, match="CustodianAccount.*not found"):
            ref.attach(self.client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeCustodianAccountResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):
        """Test creating a new custodian account."""
        route = respx_mock.post(
            "/api/api/transactionportfolios/TestPortfolio/EQUITY-GROWTH/custodianaccounts"
        ).mock(
            return_value=httpx.Response(
                201,
                json={
                    "custodianAccounts": [
                        {
                            "custodianAccountId": {"scope": "CustodianAccounts", "code": "HSBC-FIFO"},
                            "status": "Active",
                        }
                    ]
                },
            )
        )

        custodian_account_resource = custodian_accounts.CustodianAccountResource(
            id="test-custodian",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
            account_number="1234",
            account_name="HSBC FIFO Account",
            accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
            currency="GBP",
            custodian_identifier=custodian_accounts.CustodianIdentifier(
                id_type_scope="InternationalBanks", id_type_code="BankId", code="HSBC"
            ),
            account_type=custodian_accounts.AccountTypeEnum.Margin,
        )

        state = custodian_account_resource.create(self.client)

        # Assert the entire state including hash
        assert state == {
            "portfolio_scope": "TestPortfolio",
            "portfolio_code": "EQUITY-GROWTH",
            "scope": "CustodianAccounts",
            "code": "HSBC-FIFO",
            "content_hash": state["content_hash"],  # Verify it exists
        }
        assert route.called

        # Assert the whole request body
        request = route.calls.last.request
        body = json.loads(request.content)
        assert body == [
            {
                "scope": "CustodianAccounts",
                "code": "HSBC-FIFO",
                "accountNumber": "1234",
                "accountName": "HSBC FIFO Account",
                "accountingMethod": "FirstInFirstOut",
                "currency": "GBP",
                "custodianIdentifier": {
                    "idTypeScope": "InternationalBanks",
                    "idTypeCode": "BankId",
                    "code": "HSBC",
                },
                "accountType": "Margin",
            }
        ]

    def test_read(self, respx_mock):
        """Test reading an existing custodian account."""
        # Mock old_state with different values than desired state
        old_state = SimpleNamespace(
            portfolio_scope="OldPortfolio", portfolio_code="OLD-CODE", scope="OldScope", code="OLD-HSBC"
        )

        # Mock GET using old_state values
        route = respx_mock.get(
            "/api/api/transactionportfolios/OldPortfolio/OLD-CODE/custodianaccounts/OldScope/OLD-HSBC"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "custodianAccountId": {"scope": "OldScope", "code": "OLD-HSBC"},
                    "accountNumber": "1234",
                    "accountName": "HSBC FIFO Account",
                },
            )
        )

        # Desired state (different from old_state)
        custodian_account_resource = custodian_accounts.CustodianAccountResource(
            id="test-custodian",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
            account_number="1234",
            account_name="HSBC FIFO Account",
            accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
            currency="GBP",
            custodian_identifier=custodian_accounts.CustodianIdentifier(
                id_type_scope="InternationalBanks", id_type_code="BankId", code="HSBC"
            ),
            account_type=custodian_accounts.AccountTypeEnum.Margin,
        )

        result = custodian_account_resource.read(self.client, old_state)

        # Verify URL uses old_state identifiers
        assert route.called
        assert result["custodianAccountId"]["scope"] == "OldScope"
        assert result["custodianAccountId"]["code"] == "OLD-HSBC"

    def test_update_no_change(self, respx_mock):
        """Test update when nothing has changed."""
        custodian_account_resource = custodian_accounts.CustodianAccountResource(
            id="test-custodian",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
            account_number="1234",
            account_name="HSBC FIFO Account",
            accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
            currency="GBP",
            custodian_identifier=custodian_accounts.CustodianIdentifier(
                id_type_scope="InternationalBanks", id_type_code="BankId", code="HSBC"
            ),
            account_type=custodian_accounts.AccountTypeEnum.Margin,
        )

        # Calculate expected hash
        desired = custodian_account_resource.model_dump(
            mode="json",
            exclude_none=True,
            exclude={"id", "portfolio_scope", "portfolio_code"},
            by_alias=True,
        )
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode("utf-8")).hexdigest()

        old_state = SimpleNamespace(
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
            content_hash=content_hash,
        )

        result = custodian_account_resource.update(self.client, old_state)

        # Should return None when no changes
        assert result is None

    def test_update_with_changes(self, respx_mock):
        """Test update when content has changed."""
        route = respx_mock.post(
            "/api/api/transactionportfolios/TestPortfolio/EQUITY-GROWTH/custodianaccounts"
        ).mock(return_value=httpx.Response(200, json={}))

        custodian_account_resource = custodian_accounts.CustodianAccountResource(
            id="test-custodian",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
            account_number="1234",
            account_name="HSBC FIFO Account",
            accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
            currency="GBP",
            custodian_identifier=custodian_accounts.CustodianIdentifier(
                id_type_scope="InternationalBanks", id_type_code="BankId", code="HSBC"
            ),
            account_type=custodian_accounts.AccountTypeEnum.Margin,
        )

        old_state = SimpleNamespace(
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
            content_hash="old-hash-value",
        )

        result = custodian_account_resource.update(self.client, old_state)

        assert route.called
        assert result is not None
        assert result["content_hash"] != "old-hash-value"

    def test_update_identifier_changed(self, respx_mock):
        """Test update when identifier changes (requires delete + recreate)."""
        # Mock POST to the $delete endpoint using OLD identifiers
        delete_route = respx_mock.post(
            "/api/api/transactionportfolios/OldPortfolio/OLD-CODE/custodianaccounts/$delete?deleteMode=Soft"
        ).mock(return_value=httpx.Response(200, json={}))

        # Mock POST to create endpoint using NEW identifiers
        create_route = respx_mock.post(
            "/api/api/transactionportfolios/TestPortfolio/EQUITY-GROWTH/custodianaccounts"
        ).mock(return_value=httpx.Response(201, json={}))

        custodian_account_resource = custodian_accounts.CustodianAccountResource(
            id="test-custodian",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
            account_number="1234",
            account_name="HSBC FIFO Account",
            accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
            currency="GBP",
            custodian_identifier=custodian_accounts.CustodianIdentifier(
                id_type_scope="InternationalBanks", id_type_code="BankId", code="HSBC"
            ),
            account_type=custodian_accounts.AccountTypeEnum.Margin,
        )

        old_state = SimpleNamespace(
            portfolio_scope="OldPortfolio",
            portfolio_code="OLD-CODE",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
            content_hash="some-hash",
        )

        result = custodian_account_resource.update(self.client, old_state)

        assert delete_route.called
        assert create_route.called
        assert result is not None

    def test_delete(self, respx_mock):
        """Test deleting a custodian account."""
        # Mock POST to the $delete endpoint
        post_route = respx_mock.post(
            "/api/api/transactionportfolios/OldPortfolio/OLD-CODE/custodianaccounts/$delete?deleteMode=Soft"
        ).mock(return_value=httpx.Response(200, json={}))

        old_state = SimpleNamespace(
            portfolio_scope="OldPortfolio", portfolio_code="OLD-CODE", scope="OldScope", code="OLD-HSBC"
        )

        custodian_accounts.CustodianAccountResource.delete(self.client, old_state)

        assert post_route.called

        # Assert the whole request body contains old_state values
        last_request = post_route.calls.last.request
        request_data = json.loads(last_request.content)
        assert request_data == [{"scope": "OldScope", "code": "OLD-HSBC"}]

    @staticmethod
    def test_deps_no_properties():
        """Test deps returns empty list when no properties."""
        custodian_account_resource = custodian_accounts.CustodianAccountResource(
            id="test-custodian",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY-GROWTH",
            scope="CustodianAccounts",
            code="HSBC-FIFO",
            account_number="1234",
            account_name="HSBC FIFO Account",
            accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
            currency="GBP",
            custodian_identifier=custodian_accounts.CustodianIdentifier(
                id_type_scope="InternationalBanks", id_type_code="BankId", code="HSBC"
            ),
            account_type=custodian_accounts.AccountTypeEnum.Margin,
        )
        deps = custodian_account_resource.deps()
        assert deps == []

    @staticmethod
    def test_deps_with_properties():
        """Test deps returns property keys when properties are defined."""
        prop_key = property.DefinitionRef(
            id="prop1", domain=property.Domain.CustodianAccount, scope="Test", code="Prop1"
        )

        resource = custodian_accounts.CustodianAccountResource(
            id="test",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY",
            scope="CustodianAccounts",
            code="TEST",
            account_number="123",
            account_name="Test Account",
            accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
            currency="GBP",
            custodian_identifier=custodian_accounts.CustodianIdentifier(
                id_type_scope="Test", id_type_code="Test", code="TEST"
            ),
            properties=[PropertyValue(property_key=prop_key, label_value="Value1")],
        )

        deps = resource.deps()
        assert len(deps) == 1
        assert deps[0] == prop_key

    @staticmethod
    def test_serialization_with_properties():
        """Test serialization with properties."""
        prop_key = property.DefinitionRef(
            id="rating", domain=property.Domain.CustodianAccount, scope="Test", code="Rating"
        )

        resource = custodian_accounts.CustodianAccountResource(
            id="test",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY",
            scope="CustodianAccounts",
            code="TEST",
            account_number="123",
            account_name="Test Account",
            accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
            currency="GBP",
            custodian_identifier=custodian_accounts.CustodianIdentifier(
                id_type_scope="Test", id_type_code="Test", code="TEST"
            ),
            properties=[PropertyValue(property_key=prop_key, label_value="AA+")],
        )

        # Serialize for API
        dumped = resource.model_dump(mode="json", by_alias=True, exclude={"id"})

        # Assert the whole properties structure
        assert dumped["properties"] == {
            "CustodianAccount/Test/Rating": {
                "key": "CustodianAccount/Test/Rating",
                "value": {"labelValue": "AA+"},
            }
        }

    @staticmethod
    def test_dump():
        """Test dump serialization for deployment persistence."""
        prop_key = property.DefinitionRef(
            id="rating", domain=property.Domain.CustodianAccount, scope="Test", code="Rating"
        )

        resource = custodian_accounts.CustodianAccountResource(
            id="test",
            portfolio_scope="TestPortfolio",
            portfolio_code="EQUITY",
            scope="CustodianAccounts",
            code="TEST",
            account_number="123",
            account_name="Test Account",
            accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
            currency="GBP",
            custodian_identifier=custodian_accounts.CustodianIdentifier(
                id_type_scope="Test", id_type_code="Test", code="TEST"
            ),
            properties=[PropertyValue(property_key=prop_key, label_value="AA+")],
        )

        # Dump for deployment serialization
        result = resource.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )

        # In dump context, property keys become $ref
        assert result["scope"] == "CustodianAccounts"
        assert result["code"] == "TEST"
        assert result["accountNumber"] == "123"
        assert result["accountName"] == "Test Account"
        assert result["accountingMethod"] == "FirstInFirstOut"
        assert result["currency"] == "GBP"
        properties = result.get("properties")
        assert properties is not None and len(properties) == 1
        # Property key should be serialized as $ref in dump context
        assert properties[0]["propertyKey"] == {"$ref": "rating"}

    @staticmethod
    def test_undump():
        """Test undump deserialization from deployment persistence."""
        # Given dump data with property key as $ref
        data = {
            "portfolioScope": "TestPortfolio",
            "portfolioCode": "EQUITY",
            "scope": "CustodianAccounts",
            "code": "TEST",
            "accountNumber": "123",
            "accountName": "Test Account",
            "accountingMethod": "FirstInFirstOut",
            "currency": "GBP",
            "custodianIdentifier": {
                "idTypeScope": "Test",
                "idTypeCode": "Test",
                "code": "TEST",
            },
            "properties": [
                {
                    "propertyKey": {"$ref": "rating"},
                    "labelValue": "AA+",  # In dump format, value fields are at the top level
                }
            ],
        }

        # Create the referenced property definition
        prop_key = property.DefinitionRef(
            id="rating", domain=property.Domain.CustodianAccount, scope="Test", code="Rating"
        )

        # When we undump with $refs context
        result = custodian_accounts.CustodianAccountResource.model_validate(
            data, context={"style": "undump", "id": "test", "$refs": {"rating": prop_key}}
        )

        # Then it's correctly populated
        assert result.id == "test"
        assert result.portfolio_scope == "TestPortfolio"
        assert result.portfolio_code == "EQUITY"
        assert result.scope == "CustodianAccounts"
        assert result.code == "TEST"
        assert result.account_number == "123"
        assert result.account_name == "Test Account"
        assert result.accounting_method == custodian_accounts.AccountingMethodEnum.FirstInFirstOut
        assert result.currency == "GBP"
        assert result.properties is not None
        assert len(result.properties) == 1
        assert result.properties[0].property_key == prop_key
        assert result.properties[0].label_value == "AA+"
