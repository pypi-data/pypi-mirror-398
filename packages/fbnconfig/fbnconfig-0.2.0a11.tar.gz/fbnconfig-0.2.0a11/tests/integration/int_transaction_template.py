import os
from types import SimpleNamespace
from typing import List, Union

from pytest import fixture

import fbnconfig
from fbnconfig import instrument_events as ctt
from fbnconfig import property as prop
from fbnconfig.resource_abc import Ref, Resource
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)
base_url: str = "api/api/instrumenteventtypes"


@fixture()
def base_resources(setup_deployment):
    deployment_name = setup_deployment.name

    # Create the property definition first
    property_def = prop.DefinitionResource(
        id="property_definition_for_transaction_template_int_test",
        code="MyCurrencyProperty",
        data_type_id=prop.ResourceId(scope="system", code="string"),
        display_name="My Currency Property",
        domain=prop.Domain.Transaction,
        scope=f"{deployment_name}withProps"
    )

    transaction_template = [
        property_def,
        ctt.TransactionTemplateResource(
        id="transaction_template_int_test",
        description="transaction template int test description",
        scope=deployment_name,
        instrument_event_type="BondCouponEvent",
        instrument_type="Bond",
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
                transaction_id="Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}",
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
            market_open_time_adjustments=None)
        ]),
        ctt.TransactionTemplateResource(
            id="transaction_template_int_test_with_props",
            description="transaction template int test description",
            scope=f"{deployment_name}withProps",
            instrument_event_type="BondCouponEvent",  # This needs to be changed to an enum
            instrument_type="Bond",
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
                                id="property_definition_id",
                                domain=prop.Domain.Transaction,
                                scope=f"{deployment_name}withProps",
                                code="MyCurrencyProperty"
                            ),
                            value="{{BondCouponEvent.currency}}"
                        )
                    ],
                    preserve_tax_lot_structure=None,
                    market_open_time_adjustments=None)
        ])
    ]

    return transaction_template


@fixture(scope="module")
def setup_deployment():
    deployment_name = gen("transaction_template")
    print(f"\nRunning deployment for {deployment_name}")
    yield SimpleNamespace(name=deployment_name)
    try:
        instrument_event = "BondCouponEvent"
        instrument_type = "Bond"
        formatted_url = (
            f"{base_url}/{instrument_event}/transactiontemplates/"
            f"{instrument_type}/{deployment_name}"
        )
        client.delete(formatted_url)
    except Exception:
        print("Failed to delete transaction template")
        pass


def test_create(setup_deployment, base_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    instrument_event = "BondCouponEvent"
    instrument_type = "Bond"
    formatted_url = (
        f"{base_url}/{instrument_event}/transactiontemplates/"
        f"{instrument_type}/{setup_deployment.name}"
    )

    response = client.get(formatted_url).json()

    component = response["componentTransactions"][0]
    transaction_field_map = component["transactionFieldMap"]

    assert response["description"] == "transaction template int test description"
    assert response["instrumentType"] == "Bond"
    assert response["instrumentEventType"] == "BondCouponEvent"
    assert response["scope"] == setup_deployment.name
    assert component["displayName"] == "Bond Income Override"
    assert component["condition"] == "{{eligibleBalance}} gt 200"
    assert transaction_field_map["instrument"] == "{{instrument}}"
    assert transaction_field_map["settlementDate"] == "{{BondCouponEvent.paymentDate}}"
    assert transaction_field_map["transactionCurrency"] == "{{BondCouponEvent.currency}}"
    assert transaction_field_map["transactionDate"] == "{{BondCouponEvent.exDate}}"
    assert (
        transaction_field_map["transactionId"] ==
        "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
    )
    assert transaction_field_map["type"] == "BondCoupon"
    assert transaction_field_map["units"] == "{{eligibleBalance}}"
    assert (
        transaction_field_map["transactionPrice"]["price"] ==
        "{{BondCouponEvent.couponPerUnit}}"
    )
    assert transaction_field_map["transactionPrice"]["type"] == "CashFlowPerUnit"
    assert transaction_field_map["exchangeRate"] == "1"
    assert (
        transaction_field_map["totalConsideration"]["currency"] ==
        "{{BondCouponEvent.currency}}"
    )
    assert (
        transaction_field_map["totalConsideration"]["amount"] ==
        "{{BondCouponEvent.couponAmount}}"
    )
    assert component["transactionPropertyMap"] == []
    assert "preserveTaxLotStructure" not in component
    assert "marketOpenTimeAdjustments" not in component

    formatted_url_with_props = (
        f"{base_url}/{instrument_event}/transactiontemplates/"
        f"{instrument_type}/{setup_deployment.name}withProps"
    )

    response_with_props = client.get(formatted_url_with_props).json()

    component_with_props = response_with_props["componentTransactions"][0]
    transaction_field_map_with_props = component_with_props["transactionFieldMap"]

    assert response_with_props["description"] == "transaction template int test description"
    assert response_with_props["instrumentType"] == "Bond"
    assert response_with_props["instrumentEventType"] == "BondCouponEvent"
    assert response_with_props["scope"] == f"{setup_deployment.name}withProps"
    assert component_with_props["displayName"] == "Bond Income Override"
    assert component_with_props["condition"] == "{{eligibleBalance}} gt 200"
    assert (
        component_with_props["transactionFieldMap"]["instrument"] ==
        "{{instrument}}"
    )
    assert (
        transaction_field_map_with_props["settlementDate"] ==
        "{{BondCouponEvent.paymentDate}}"
    )
    assert (
        transaction_field_map_with_props["transactionCurrency"] ==
        "{{BondCouponEvent.currency}}"
    )
    assert (
        transaction_field_map_with_props["transactionDate"] ==
        "{{BondCouponEvent.exDate}}"
    )
    assert (
        transaction_field_map_with_props["transactionId"] ==
        "Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}"
    )
    assert transaction_field_map_with_props["type"] == "BondCoupon"
    assert transaction_field_map_with_props["units"] == "{{eligibleBalance}}"
    assert (
        transaction_field_map_with_props["transactionPrice"]["price"] ==
        "{{BondCouponEvent.couponPerUnit}}"
    )
    assert (
        transaction_field_map_with_props["transactionPrice"]["type"] ==
        "CashFlowPerUnit"
    )
    assert transaction_field_map_with_props["exchangeRate"] == "1"
    assert (
        transaction_field_map_with_props["totalConsideration"]["currency"] ==
        "{{BondCouponEvent.currency}}"
    )
    assert (
        transaction_field_map_with_props["totalConsideration"]["amount"] ==
        "{{BondCouponEvent.couponAmount}}"
    )
    assert component_with_props["transactionPropertyMap"] == [
        {
            "propertyKey": f"Transaction/{setup_deployment.name}withProps/MyCurrencyProperty",
            "value": "{{BondCouponEvent.currency}}"
        }
    ]
    assert "preserveTaxLotStructure" not in response["componentTransactions"][0]


def test_update(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    updated_template = ctt.TransactionTemplateResource(
        id="transaction_template_int_test",
        description="transaction template int test description",
        scope=deployment_name,
        instrument_event_type="BondCouponEvent",  # This needs to be changed to an enum
        instrument_type="Bond",
        component_transactions=[
            ctt.ComponentTransactions(
            display_name="Bond Income Override",
            condition="{{eligibleBalance}} gt 300",
            transaction_field_map=ctt.TransactionFieldMap(
                instrument="{{instrument}}",
                settlement_date="{{BondCouponEvent.paymentDate}}",
                source="MyOtherTransactionTypeSource",
                transaction_currency="{{BondCouponEvent.currency}}",
                transaction_date="{{BondCouponEvent.exDate}}",
                transaction_id="Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}",
                type="BondCoupon",
                units="{{eligibleBalance}}",
                transaction_price=ctt.TransactionPriceAndType(
                    price="{{BondCouponEvent.couponPerUnit}}",
                    type="CashFlowPerUnit"
                ),
                exchange_rate="2",
                total_consideration=ctt.TransactionCurrencyAndAmount(
                    currency="{{BondCouponEvent.currency}}",
                    amount="{{BondCouponEvent.couponAmount}}"
                ),
                ),
            transaction_property_map=[],
            preserve_tax_lot_structure=None,
            market_open_time_adjustments=None)
        ]
    )

    updated_deployment = fbnconfig.Deployment(setup_deployment.name, [updated_template])
    updated_resource = fbnconfig.deployex(updated_deployment, lusid_env, token)
    updated_list = [res.change for res in updated_resource if res.type == "TransactionTemplateResource"]

    # The second resource is 'removed' as it contains a transactionPropertyMap
    assert updated_list == ["update", "remove"]

    updated_template_data = client.get(
        f"{base_url}/{updated_template.instrument_event_type}/transactiontemplates/"
        f"{updated_template.instrument_type}/{deployment_name}"
    ).json()

    assert updated_template_data["componentTransactions"][0]["condition"] == "{{eligibleBalance}} gt 300"
    assert (
        updated_template_data["componentTransactions"][0]["transactionFieldMap"]["source"] ==
        "MyOtherTransactionTypeSource"
    )
    assert (
        updated_template_data["componentTransactions"][0]["transactionFieldMap"]["exchangeRate"] ==
        "2"
    )


def test_removing_transaction_property_map(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    updated_template = ctt.TransactionTemplateResource(
        id="transaction_template_int_test",
        description="transaction template int test description",
        scope=deployment_name,
        instrument_event_type="BondCouponEvent",  # This needs to be changed to an enum
        instrument_type="Bond",
        component_transactions=[
            ctt.ComponentTransactions(
            display_name="Bond Income Override",
            condition="{{eligibleBalance}} gt 300",
            transaction_field_map=ctt.TransactionFieldMap(
                instrument="{{instrument}}",
                settlement_date="{{BondCouponEvent.paymentDate}}",
                source="MyOtherTransactionTypeSource",
                transaction_currency="{{BondCouponEvent.currency}}",
                transaction_date="{{BondCouponEvent.exDate}}",
                transaction_id="Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}",
                type="BondCoupon",
                units="{{eligibleBalance}}",
                transaction_price=ctt.TransactionPriceAndType(
                    price="{{BondCouponEvent.couponPerUnit}}",
                    type="CashFlowPerUnit"
                ),
                exchange_rate="2",
                total_consideration=ctt.TransactionCurrencyAndAmount(
                    currency="{{BondCouponEvent.currency}}",
                    amount="{{BondCouponEvent.couponAmount}}"
                ),
                ),
            transaction_property_map=[],
            preserve_tax_lot_structure=None,
            market_open_time_adjustments=None)
        ]
    )

    updated_deployment = fbnconfig.Deployment(setup_deployment.name, [updated_template])
    updated_resource = fbnconfig.deployex(updated_deployment, lusid_env, token)
    updated_list = [res.change for res in updated_resource if res.type == "TransactionTemplateResource"]
    updated_definition_list = [res.change for res in updated_resource
                               if res.type == "DefinitionResource"]

    assert updated_list == ["update", "remove"]
    assert updated_definition_list == ["remove"]

    updated_template_data = client.get(
        f"{base_url}/{updated_template.instrument_event_type}/transactiontemplates/"
        f"{updated_template.instrument_type}/{deployment_name}"
    ).json()
    component = updated_template_data["componentTransactions"][0]
    transaction_field_map = component["transactionFieldMap"]

    assert component["condition"] == "{{eligibleBalance}} gt 300"
    assert component["transactionPropertyMap"] == []
    assert transaction_field_map["source"] == "MyOtherTransactionTypeSource"
    assert transaction_field_map["exchangeRate"] == "2"


def test_adding_transaction_property_map(setup_deployment, base_resources):
    deployment_name = setup_deployment.name

    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    # Create the property definition for the updated template
    property_def = prop.DefinitionResource(
        id="property_definition",
        code="MyCurrencyProperty",
        data_type_id=prop.ResourceId(scope="system", code="string"),
        display_name="My Currency Property",
        domain=prop.Domain.Transaction,
        scope=deployment_name
    )

    updated_template: List[Union[Resource, Ref]] = [
        property_def,
        ctt.TransactionTemplateResource(
        id="transaction_template_int_test",
        description="transaction template int test description",
        scope=deployment_name,
        instrument_event_type="BondCouponEvent",
        instrument_type="Bond",
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
                transaction_id="Automatically-generated txn: {{instrumentEventId}}-{{holdingId}}",
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
                        id="property_definition_id",
                        domain=prop.Domain.Transaction,
                        scope=deployment_name,
                        code="MyCurrencyProperty"
                    ),
                    value="{{BondCouponEvent.currency}}"
                )
            ],
            preserve_tax_lot_structure=None,
            market_open_time_adjustments=None)
        ]),
        ctt.TransactionTemplateResource(
            id="transaction_template_int_test_with_props",
            description="transaction template int test description",
            scope=f"{deployment_name}withProps",
            instrument_event_type="BondCouponEvent",  # This needs to be changed to an enum
            instrument_type="Bond",
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
                    market_open_time_adjustments=None)
        ])
    ]

    updated_deployment = fbnconfig.Deployment(setup_deployment.name, updated_template)
    updated_resource = fbnconfig.deployex(updated_deployment, lusid_env, token)
    updated_list = [res.change for res in updated_resource if res.type == "TransactionTemplateResource"]
    updated_definition_list = [res.change for res in updated_resource
                               if res.type == "DefinitionResource"]

    assert updated_list == ["update", "update"]
    assert updated_definition_list == ["create", "remove"]

    property_def_url = (
        f"api/api/propertydefinitions/{prop.Domain.Transaction}/"
        f"{deployment_name}/MyCurrencyProperty"
    )

    property_def = client.get(property_def_url).json()
    assert property_def["scope"] == deployment_name
    assert property_def["code"] == "MyCurrencyProperty"
    assert property_def["domain"] == prop.Domain.Transaction
    assert property_def["dataTypeId"] == {"scope": "system", "code": "string"}
    assert property_def["displayName"] == "My Currency Property"

    assert_dict_contains(property_def, {
        "scope": deployment_name,
        "code": "MyCurrencyProperty",
        "domain": prop.Domain.Transaction,
        "dataTypeId": {"scope": "system", "code": "string"},
        "displayName": "My Currency Property"
    })

    # Resource 1
    transaction_template_url = (
        f"{base_url}/BondCouponEvent/transactiontemplates/"
        f"Bond/{setup_deployment.name}"
    )

    response = client.get(transaction_template_url).json()
    assert_dict_contains(response, {
        "scope": deployment_name,
        "instrumentEventType": "BondCouponEvent",
        "instrumentType": "Bond"
    })

    assert response["componentTransactions"][0]["transactionPropertyMap"][0] == {
        "propertyKey": f"Transaction/{setup_deployment.name}/MyCurrencyProperty",
        "value": "{{BondCouponEvent.currency}}"
    }

    transaction_template_with_props_url = (
        f"{base_url}/BondCouponEvent/transactiontemplates/"
        f"Bond/{setup_deployment.name}withProps"
    )

    transaction_template_with_no_props = client.get(transaction_template_with_props_url).json()
    assert_dict_contains(transaction_template_with_no_props, {
        "scope": f"{deployment_name}withProps",
        "instrumentEventType": "BondCouponEvent",
        "instrumentType": "Bond"
    })
    assert transaction_template_with_no_props["componentTransactions"][0]["transactionPropertyMap"] == []


def test_no_change(setup_deployment, base_resources):
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we apply it again
    update = fbnconfig.deployex(deployment, lusid_env, token)
    # then there are no changes
    ref_list_changes = [a.change for a in update if a.type == "TransactionTemplateResource"]
    assert ref_list_changes == ["nochange", "nochange"]


def test_teardown(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we remove all the resources
    empty = fbnconfig.Deployment(deployment_name, [])
    update = fbnconfig.deployex(empty, lusid_env, token)
    # then there are no changes
    ref_list_changes = [a.change for a in update if a.type == "TransactionTemplateResource"]
    assert ref_list_changes == ["remove", "remove"]


def assert_dict_contains(actual, expected):
    for key, value in expected.items():
        assert key in actual, f"Missing key: {key}"
        assert actual[key] == value, f"Key '{key}': expected {value}, got {actual[key]}"
