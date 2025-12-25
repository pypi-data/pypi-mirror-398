import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import instrument_events as ctt
from fbnconfig import property as prop

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeTransactionTemplate:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):

        scope = "test_scope"
        instrument_event_type = "BondCouponEvent"
        instrument_type = "Bond"

        respx_mock.post(
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        ).mock(return_value=httpx.Response(200, json={}))

        sut = ctt.TransactionTemplateResource(
            id="template_id",
            scope=scope,
            instrument_type=instrument_type,
            instrument_event_type=instrument_event_type,
            description="A test transaction template",
            component_transactions=[
                ctt.ComponentTransactions(
                    display_name="Bond Income Override",
                    condition="{{eligibleBalance}} gt 200",
                    transaction_field_map=ctt.TransactionFieldMap(
                        instrument="{{instrument}}",
                        settlement_date="{{BondCouponEvent.paymentDate}}",
                        source="MyTransactionTypeSource",
                        transaction_currency="{{BondCouponEvent.currency}}",
                        transaction_date="{{BondCouponEvent.exDate}}",
                        transaction_id=(
                            "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
                        ),
                        type="BondCoupon",
                        units="{{eligibleBalance}}",
                        transaction_price=ctt.TransactionPriceAndType(
                            price="{{BondCouponEvent.couponPerUnit}}",
                            type="CashFlowPerUnit"
                        ),
                        exchange_rate="1",
                        total_consideration=ctt.TransactionCurrencyAndAmount(
                            currency="{{BondCouponEvent.currency}}",
                            amount="{{BondCouponEvent.couponAmount}}"
                        ),
                        ),
                    transaction_property_map=[],
                    preserve_tax_lot_structure=None,
                    market_open_time_adjustments=None
                )
        ])

        state = sut.create(self.client)
        assert state["id"] == "template_id"
        assert state["scope"] == scope
        assert state["instrumentType"] == instrument_type
        assert state["instrumentEventType"] == instrument_event_type

        request = respx_mock.calls.last.request

        assert request.method == "POST"
        assert request.url.path == (
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        )
        request_body = json.loads(request.content)

        assert request_body["scope"] == scope
        assert request_body["instrumentType"] == instrument_type
        assert request_body["instrumentEventType"] == instrument_event_type
        assert request_body["description"] == "A test transaction template"

        # Assert componentTransactions structure
        assert "componentTransactions" in request_body
        assert len(request_body["componentTransactions"]) == 1

        component_txn = request_body["componentTransactions"][0]
        assert component_txn["displayName"] == "Bond Income Override"
        assert component_txn["condition"] == "{{eligibleBalance}} gt 200"

        # Assert transactionFieldMap
        expected_txn_field_map = {
            "instrument": "{{instrument}}",
            "settlementDate": "{{BondCouponEvent.paymentDate}}",
            "source": "MyTransactionTypeSource",
            "transactionCurrency": "{{BondCouponEvent.currency}}",
            "transactionDate": "{{BondCouponEvent.exDate}}",
            "transactionId": "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}",
            "type": "BondCoupon",
            "units": "{{eligibleBalance}}",
            "exchangeRate": "1",
            "transactionPrice": {
                "price": "{{BondCouponEvent.couponPerUnit}}",
                "type": "CashFlowPerUnit"
            },
            "totalConsideration": {
                "currency": "{{BondCouponEvent.currency}}",
                "amount": "{{BondCouponEvent.couponAmount}}"
            }
        }
        assert component_txn["transactionFieldMap"] == expected_txn_field_map

        # Assert other fields
        assert component_txn["transactionPropertyMap"] == []
        assert (
            "preserveTaxLotStructure" not in component_txn or
            component_txn["preserveTaxLotStructure"] is None
        )
        assert (
            "marketOpenTimeAdjustments" not in component_txn or
            component_txn["marketOpenTimeAdjustments"] is None
        )

    def test_create_with_props(self, respx_mock):

        scope = "test_scope_with_props"
        instrument_event_type = "BondCouponEvent"
        instrument_type = "Bond"

        respx_mock.post(
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        ).mock(return_value=httpx.Response(200, json={}))

        sut = ctt.TransactionTemplateResource(
            id="template_id_with_props",
            scope=scope,
            instrument_type=instrument_type,
            instrument_event_type=instrument_event_type,
            description="A test transaction template with properties",
            component_transactions=[
                ctt.ComponentTransactions(
                    display_name="Bond Income Override",
                    condition="{{eligibleBalance}} gt 200",
                    transaction_field_map=ctt.TransactionFieldMap(
                        instrument="{{instrument}}",
                        settlement_date="{{BondCouponEvent.paymentDate}}",
                        source="MyTransactionTypeSource",
                        transaction_currency="{{BondCouponEvent.currency}}",
                        transaction_date="{{BondCouponEvent.exDate}}",
                        transaction_id=(
                            "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
                        ),
                        type="BondCoupon",
                        units="{{eligibleBalance}}",
                        transaction_price=ctt.TransactionPriceAndType(
                            price="{{BondCouponEvent.couponPerUnit}}",
                            type="CashFlowPerUnit"
                        ),
                        exchange_rate="1",
                        total_consideration=ctt.TransactionCurrencyAndAmount(
                            currency="{{BondCouponEvent.currency}}",
                            amount="{{BondCouponEvent.couponAmount}}"
                        ),
                        ),
                    transaction_property_map=[
                        ctt.TransactionPropertyMap(
                            property_key=prop.DefinitionRef(
                                id="currency_property_ref",
                                domain=prop.Domain.Transaction,
                                scope="test-scope",
                                code="MyCurrencyProperty"
                            ),
                            value="{{BondCouponEvent.currency}}"
                        ),
                        ctt.TransactionPropertyMap(
                            property_key=prop.DefinitionRef(
                                id="instrument_property_ref",
                                domain=prop.Domain.Transaction,
                                scope="test-scope",
                                code="MyInstrumentProperty"
                            ),
                            value="{{instrument}}"
                        )
                    ],
                    preserve_tax_lot_structure=None,
                    market_open_time_adjustments=None
                )
        ])

        state = sut.create(self.client)
        assert state["scope"] == scope
        assert state["instrumentType"] == instrument_type
        assert state["instrumentEventType"] == instrument_event_type

        request = respx_mock.calls.last.request

        assert request.method == "POST"
        assert request.url.path == (
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        )
        request_body = json.loads(request.content)

        assert request_body["scope"] == scope
        assert request_body["instrumentType"] == instrument_type
        assert request_body["instrumentEventType"] == instrument_event_type
        assert request_body["description"] == "A test transaction template with properties"

        # Assert componentTransactions structure
        assert "componentTransactions" in request_body
        assert len(request_body["componentTransactions"]) == 1

        component_txn = request_body["componentTransactions"][0]
        assert component_txn["displayName"] == "Bond Income Override"
        assert component_txn["condition"] == "{{eligibleBalance}} gt 200"

        # Assert transactionFieldMap
        expected_txn_field_map = {
            "instrument": "{{instrument}}",
            "settlementDate": "{{BondCouponEvent.paymentDate}}",
            "source": "MyTransactionTypeSource",
            "transactionCurrency": "{{BondCouponEvent.currency}}",
            "transactionDate": "{{BondCouponEvent.exDate}}",
            "transactionId": "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}",
            "type": "BondCoupon",
            "units": "{{eligibleBalance}}",
            "exchangeRate": "1",
            "transactionPrice": {
                "price": "{{BondCouponEvent.couponPerUnit}}",
                "type": "CashFlowPerUnit"
            },
            "totalConsideration": {
                "currency": "{{BondCouponEvent.currency}}",
                "amount": "{{BondCouponEvent.couponAmount}}"
            }
        }
        assert component_txn["transactionFieldMap"] == expected_txn_field_map

        # Assert transactionPropertyMap
        txn_property_map = component_txn["transactionPropertyMap"]
        assert len(txn_property_map) == 2
        assert txn_property_map[0]["propertyKey"] == "Transaction/test-scope/MyCurrencyProperty"
        assert txn_property_map[0]["value"] == "{{BondCouponEvent.currency}}"
        assert txn_property_map[1]["propertyKey"] == "Transaction/test-scope/MyInstrumentProperty"
        assert txn_property_map[1]["value"] == "{{instrument}}"

        # Assert other fields
        assert (
            "preserveTaxLotStructure" not in component_txn or
            component_txn["preserveTaxLotStructure"] is None
        )
        assert (
            "marketOpenTimeAdjustments" not in component_txn or
            component_txn["marketOpenTimeAdjustments"] is None
        )

    def test_update_with_no_changes(self, respx_mock):
        scope = "test_scope"
        instrument_event_type = "BondCouponEvent"
        instrument_type = "Bond"

        sut = ctt.TransactionTemplateResource(
            id="template_id",
            scope=scope,
            instrument_type=instrument_type,
            instrument_event_type=instrument_event_type,
            description="A test transaction template",
            component_transactions=[
                ctt.ComponentTransactions(
                    display_name="Bond Income Override",
                    condition="{{eligibleBalance}} gt 200",
                    transaction_field_map=ctt.TransactionFieldMap(
                        instrument="{{instrument}}",
                        settlement_date="{{BondCouponEvent.paymentDate}}",
                        source="MyTransactionTypeSource",
                        transaction_currency="{{BondCouponEvent.currency}}",
                        transaction_date="{{BondCouponEvent.exDate}}",
                        transaction_id=(
                            "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
                        ),
                        type="BondCoupon",
                        units="{{eligibleBalance}}",
                        transaction_price=ctt.TransactionPriceAndType(
                            price="{{BondCouponEvent.couponPerUnit}}",
                            type="CashFlowPerUnit"
                        ),
                        exchange_rate="1",
                        total_consideration=ctt.TransactionCurrencyAndAmount(
                            currency="{{BondCouponEvent.currency}}",
                            amount="{{BondCouponEvent.couponAmount}}"
                        ),
                        ),
                    transaction_property_map=[],
                    preserve_tax_lot_structure=None,
                    market_open_time_adjustments=None
                )
        ])

        desired = sut.model_dump(mode="json", exclude_none=True, by_alias=True)

        sorted_desired = json.dumps(desired, sort_keys=True)
        from hashlib import sha256
        content_hash = sha256(sorted_desired.encode()).hexdigest()

        old_state = SimpleNamespace(
            scope=scope,
            instrumentEventType=instrument_event_type,
            instrumentType=instrument_type,
            content_hash=content_hash
        )

        state = sut.update(self.client, old_state)
        assert state is None
        assert len(respx_mock.calls) == 0

    def test_update_with_changes(self, respx_mock):
        scope = "test_scope"
        instrument_event_type = "BondCouponEvent"
        instrument_type = "Bond"

        respx_mock.delete(
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        ).mock(return_value=httpx.Response(200, json={}))
        respx_mock.post(
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        ).mock(return_value=httpx.Response(200, json={}))

        sut = ctt.TransactionTemplateResource(
            id="template_id",
            scope=scope,
            instrument_type=instrument_type,
            instrument_event_type=instrument_event_type,
            description="A test transaction template",
            component_transactions=[
                ctt.ComponentTransactions(
                    display_name="Bond Income Override",
                    condition="{{eligibleBalance}} gt 200",
                    transaction_field_map=ctt.TransactionFieldMap(
                        instrument="{{instrument}}",
                        settlement_date="{{BondCouponEvent.paymentDate}}",
                        source="MyTransactionTypeSource",
                        transaction_currency="{{BondCouponEvent.currency}}",
                        transaction_date="{{BondCouponEvent.exDate}}",
                        transaction_id=(
                            "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
                        ),
                        type="BondCoupon",
                        units="{{eligibleBalance}}",
                        transaction_price=ctt.TransactionPriceAndType(
                            price="{{BondCouponEvent.couponPerUnit}}",
                            type="CashFlowPerUnit"
                        ),
                        exchange_rate="1",
                        total_consideration=ctt.TransactionCurrencyAndAmount(
                            currency="{{BondCouponEvent.currency}}",
                            amount="{{BondCouponEvent.couponAmount}}"
                        ),
                        ),
                    transaction_property_map=[],
                    preserve_tax_lot_structure=None,
                    market_open_time_adjustments=None
                )
        ])

        old_state = SimpleNamespace(
            scope=scope,
            instrumentEventType=instrument_event_type,
            instrumentType=instrument_type,
            content_hash="different_hash"
        )
        state = sut.update(self.client, old_state)

        assert state is not None
        assert len(respx_mock.calls) == 2
        assert state["scope"] == scope
        assert state["instrumentEventType"] == instrument_event_type
        assert state["instrumentType"] == instrument_type
        assert "content_hash" in state
        assert state["content_hash"] != "different_hash"

        # Verify the delete request
        delete_request = respx_mock.calls[0].request
        assert delete_request.method == "DELETE"
        assert delete_request.url.path == (
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        )

        post_request = respx_mock.calls[1].request
        assert post_request.method == "POST"
        assert post_request.url.path == (
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        )

    def test_update_with_scope_change(self, respx_mock):
        old_scope = "old_test_scope"
        new_scope = "new_test_scope"
        instrument_event_type = "BondCouponEvent"
        instrument_type = "Bond"

        respx_mock.delete(
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{old_scope}"
        ).mock(return_value=httpx.Response(200, json={}))
        respx_mock.post(
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{new_scope}"
        ).mock(return_value=httpx.Response(200, json={}))

        # Create a transaction template with new scope
        sut = ctt.TransactionTemplateResource(
            id="template_id",
            scope=new_scope,  # Different scope than old state
            instrument_type=instrument_type,
            instrument_event_type=instrument_event_type,
            description="A test transaction template",
            component_transactions=[
                ctt.ComponentTransactions(
                    display_name="Bond Income Override",
                    condition="{{eligibleBalance}} gt 200",
                    transaction_field_map=ctt.TransactionFieldMap(
                        instrument="{{instrument}}",
                        settlement_date="{{BondCouponEvent.paymentDate}}",
                        source="MyTransactionTypeSource",
                        transaction_currency="{{BondCouponEvent.currency}}",
                        transaction_date="{{BondCouponEvent.exDate}}",
                        transaction_id=(
                            "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
                        ),
                        type="BondCoupon",
                        units="{{eligibleBalance}}",
                        transaction_price=ctt.TransactionPriceAndType(
                            price="{{BondCouponEvent.couponPerUnit}}",
                            type="CashFlowPerUnit"
                        ),
                        exchange_rate="1",
                        total_consideration=ctt.TransactionCurrencyAndAmount(
                            currency="{{BondCouponEvent.currency}}",
                            amount="{{BondCouponEvent.couponAmount}}"
                        ),
                        ),
                    transaction_property_map=[],
                    preserve_tax_lot_structure=None,
                    market_open_time_adjustments=None
                )
        ])

        # Create old state with different scope
        old_state = SimpleNamespace(
            scope=old_scope,
            instrumentEventType=instrument_event_type,
            instrumentType=instrument_type,
            content_hash="old_hash"
        )

        # When we update it
        state = sut.update(self.client, old_state)

        # Then the old one is deleted and a new one is created
        assert len(respx_mock.calls) == 2
        delete_request = respx_mock.calls[0].request
        assert delete_request.method == "DELETE"
        assert delete_request.url.path == (
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{old_scope}"
        )

        post_request = respx_mock.calls[1].request
        assert post_request.method == "POST"
        assert post_request.url.path == (
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{new_scope}"
        )
        assert state is not None
        assert state["scope"] == new_scope
        assert state["instrumentEventType"] == instrument_event_type
        assert state["instrumentType"] == instrument_type
        assert "content_hash" in state

    def test_delete(self, respx_mock):
        scope = "test_scope"
        instrument_event_type = "BondCouponEvent"
        instrument_type = "Bond"

        # Mock the DELETE request
        respx_mock.delete(
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        ).mock(return_value=httpx.Response(200, json={}))

        # Create old state to delete
        old_state = SimpleNamespace(
            scope=scope,
            instrumentEventType=instrument_event_type,
            instrumentType=instrument_type
        )

        # When we delete it
        ctt.TransactionTemplateResource.delete(self.client, old_state)

        # Then a DELETE request was made
        assert len(respx_mock.calls) == 1
        delete_request = respx_mock.calls[0].request
        assert delete_request.method == "DELETE"
        assert delete_request.url.path == (
            f"/api/api/instrumenteventtypes/{instrument_event_type}/"
            f"transactiontemplates/{instrument_type}/{scope}"
        )

    def test_deps_no_props(self):
        sut = ctt.TransactionTemplateResource(
            id="template_id",
            scope="test_scope",
            instrument_type="Bond",
            instrument_event_type="BondCouponEvent",
            description="A test transaction template",
            component_transactions=[
                ctt.ComponentTransactions(
                    display_name="Bond Income Override",
                    condition="{{eligibleBalance}} gt 200",
                    transaction_field_map=ctt.TransactionFieldMap(
                        instrument="{{instrument}}",
                        settlement_date="{{BondCouponEvent.paymentDate}}",
                        source="MyTransactionTypeSource",
                        transaction_currency="{{BondCouponEvent.currency}}",
                        transaction_date="{{BondCouponEvent.exDate}}",
                        transaction_id=(
                            "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
                        ),
                        type="BondCoupon",
                        units="{{eligibleBalance}}",
                        transaction_price=ctt.TransactionPriceAndType(
                            price="{{BondCouponEvent.couponPerUnit}}",
                            type="CashFlowPerUnit"
                        ),
                        exchange_rate="1",
                        total_consideration=ctt.TransactionCurrencyAndAmount(
                            currency="{{BondCouponEvent.currency}}",
                            amount="{{BondCouponEvent.couponAmount}}"
                        ),
                        ),
                    transaction_property_map=[],
                    preserve_tax_lot_structure=None,
                    market_open_time_adjustments=None
                )
        ])
        assert sut.deps() == []

    def test_deps_with_props(self):
        currency_prop = prop.DefinitionRef(
            id="currency_property_ref",
            domain=prop.Domain.Transaction,
            scope="test-scope",
            code="MyCurrencyProperty"
        )
        instrument_prop = prop.DefinitionRef(
            id="instrument_property_ref",
            domain=prop.Domain.Transaction,
            scope="test-scope",
            code="MyInstrumentProperty"
        )

        sut = ctt.TransactionTemplateResource(
            id="template_id_with_props",
            scope="test_scope_with_props",
            instrument_type="Bond",
            instrument_event_type="BondCouponEvent",
            description="A test transaction template with properties",
            component_transactions=[
                ctt.ComponentTransactions(
                    display_name="Bond Income Override",
                    condition="{{eligibleBalance}} gt 200",
                    transaction_field_map=ctt.TransactionFieldMap(
                        instrument="{{instrument}}",
                        settlement_date="{{BondCouponEvent.paymentDate}}",
                        source="MyTransactionTypeSource",
                        transaction_currency="{{BondCouponEvent.currency}}",
                        transaction_date="{{BondCouponEvent.exDate}}",
                        transaction_id=(
                            "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
                        ),
                        type="BondCoupon",
                        units="{{eligibleBalance}}",
                        transaction_price=ctt.TransactionPriceAndType(
                            price="{{BondCouponEvent.couponPerUnit}}",
                            type="CashFlowPerUnit"
                        ),
                        exchange_rate="1",
                        total_consideration=ctt.TransactionCurrencyAndAmount(
                            currency="{{BondCouponEvent.currency}}",
                            amount="{{BondCouponEvent.couponAmount}}"
                        ),
                        ),
                    transaction_property_map=[
                        ctt.TransactionPropertyMap(
                            property_key=currency_prop,
                            value="{{BondCouponEvent.currency}}"
                        ),
                        ctt.TransactionPropertyMap(
                            property_key=instrument_prop,
                            value="{{somevalue}}"
                        )
                    ],
                    preserve_tax_lot_structure=None,
                    market_open_time_adjustments=None
                )
        ])

        deps = sut.deps()
        assert len(deps) == 2
        assert currency_prop in deps
        assert instrument_prop in deps

    def test_dump(self):
        currency_prop = prop.DefinitionRef(
            id="currency_property_ref",
            domain=prop.Domain.Transaction,
            scope="test-scope",
            code="MyCurrencyProperty"
        )
        instrument_prop = prop.DefinitionRef(
            id="instrument_property_ref",
            domain=prop.Domain.Transaction,
            scope="test-scope",
            code="MyInstrumentProperty"
        )
        sut = ctt.TransactionTemplateResource(
            id="template_id_with_props",
            scope="test_scope_with_props",
            instrument_type="Bond",
            instrument_event_type="BondCouponEvent",
            description="A test transaction template with properties",
            component_transactions=[
                ctt.ComponentTransactions(
                    display_name="Bond Income Override",
                    condition="{{eligibleBalance}} gt 200",
                    transaction_field_map=ctt.TransactionFieldMap(
                        instrument="{{instrument}}",
                        settlement_date="{{BondCouponEvent.paymentDate}}",
                        source="MyTransactionTypeSource",
                        transaction_currency="{{BondCouponEvent.currency}}",
                        transaction_date="{{BondCouponEvent.exDate}}",
                        transaction_id=(
                            "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
                        ),
                        type="BondCoupon",
                        units="{{eligibleBalance}}",
                        transaction_price=ctt.TransactionPriceAndType(
                            price="{{BondCouponEvent.couponPerUnit}}",
                            type="CashFlowPerUnit"
                        ),
                        exchange_rate="1",
                        total_consideration=ctt.TransactionCurrencyAndAmount(
                            currency="{{BondCouponEvent.currency}}",
                            amount="{{BondCouponEvent.couponAmount}}"
                        ),
                        ),
                    transaction_property_map=[
                        ctt.TransactionPropertyMap(
                            property_key=currency_prop,
                            value="{{BondCouponEvent.currency}}"
                        ),
                        ctt.TransactionPropertyMap(
                            property_key=instrument_prop,
                            value="{{somevalue}}"
                        )
                    ],
                    preserve_tax_lot_structure=None,
                    market_open_time_adjustments=None
                )
        ])
        # when we dump it
        dump = sut.model_dump(by_alias=True, exclude_none=True,
                              round_trip=True, context={"style": "dump"})
        # the id is exluded
        assert dump.get("id", None) is None
        # The properties are serialized as $refs
        tpm = dump["componentTransactions"][0]["transactionPropertyMap"]
        assert tpm[0]["propertyKey"] == {"$ref": currency_prop.id}

    def test_undump(self):
        # given we are parsing a dump and we have already parsed the
        # properties
        currency_prop = prop.DefinitionRef(
            id="currency_property_ref",
            domain=prop.Domain.Transaction,
            scope="test-scope",
            code="MyCurrencyProperty"
        )
        instrument_prop = prop.DefinitionRef(
            id="instrument_property_ref",
            domain=prop.Domain.Transaction,
            scope="test-scope",
            code="MyInstrumentProperty"
        )
        # but we have to parse the transaction template
        dump = {
            "componentTransactions": [
              {
                "condition": "{{eligibleBalance}} gt 200",
                "displayName": "Bond Income Override",
                "transactionFieldMap": {
                  "exchangeRate": "1",
                  "instrument": "{{instrument}}",
                  "settlementDate": "{{BondCouponEvent.paymentDate}}",
                  "source": "MyTransactionTypeSource",
                  "totalConsideration": {
                    "amount": "{{BondCouponEvent.couponAmount}}",
                    "currency": "{{BondCouponEvent.currency}}"
                  },
                  "transactionCurrency": "{{BondCouponEvent.currency}}",
                  "transactionDate": "{{BondCouponEvent.exDate}}",
                  "transactionId": "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}",
                  "transactionPrice": {
                    "price": "{{BondCouponEvent.couponPerUnit}}",
                    "type": "CashFlowPerUnit"
                  },
                  "type": "BondCoupon",
                  "units": "{{eligibleBalance}}"
                },
                "transactionPropertyMap": [
                  {
                    "propertyKey": {
                      "$ref": "currency_property_ref"
                    },
                    "value": "{{BondCouponEvent.currency}}"
                  },
                  {
                    "propertyKey": {
                      "$ref": "instrument_property_ref"
                    },
                    "value": "{{somevalue}}"
                  }
                ]
              }
            ],
            "description": "A test transaction template with properties",
            "instrumentEventType": "BondCouponEvent",
            "instrumentType": "Bond",
            "scope": "test_scope_with_props"
          }
        # when we undump it
        sut = ctt.TransactionTemplateResource.model_validate(
            dump,
            context={
                "style": "dump",
                "id": "template-id",
                "$refs": {p.id: p for p in [currency_prop, instrument_prop]}
            }
        )
        # then the properties get resolved from the $refs
        tpm = sut.component_transactions[0].transaction_property_map
        assert tpm[0].property_key == currency_prop
        # and the resource id is extracted from the context
        assert sut.id == "template-id"
