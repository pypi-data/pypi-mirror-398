import os
from types import SimpleNamespace

import pytest
from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
from fbnconfig import side_definition, transaction_type
from tests.integration.generate_test_name import gen


@fixture(scope="module")
def lusid_env():
    if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
        raise (
            RuntimeError("FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
        )

    env = os.environ["LUSID_ENV"]
    token = os.environ["FBN_ACCESS_TOKEN"]
    return SimpleNamespace(env=env, token=token)


@fixture(scope="module")
def client(lusid_env):
    return fbnconfig.create_client(lusid_env.env, lusid_env.token)


@fixture(scope="module")
def deployment_name():
    return gen("transaction_configuration")


def resources(deployment_name):
    test_side1 = side_definition.SideResource(
        id="side1",
        side="Side1",
        scope=deployment_name,
        security="Txn:LusidInstrumentId",
        currency="Txn:SettlementCurrency",
        rate="Txn:TradeToPortfolioRate",
        units="Txn:Units",
        amount="Txn:TotalConsideration",
        notional_amount="0",
    )

    test_side2 = side_definition.SideResource(
        id="side2",
        side="Side2",
        scope=deployment_name,
        security="Txn:SettlementCurrency",
        currency="Txn:SettlementCurrency",
        rate="SettledToPortfolioRate",
        units="Txn:TotalConsideration",
        amount="Txn:TotalConsideration",
        notional_amount="0",
        current_face="Txn:TotalConsideration",
    )

    test_buy_transaction_type = transaction_type.TransactionTypeResource(
        id="example",
        scope=deployment_name,
        source="default",
        aliases=[
            transaction_type.TransactionTypeAlias(
                type="Buy",
                description="Something",
                transaction_class="default",
                transaction_roles="LongLonger",
                is_default=False,
            ),
            transaction_type.TransactionTypeAlias(
                type="BY",
                description="Something but different",
                transaction_class="default",
                transaction_roles="LongLonger",
                is_default=False,
            ),
        ],
        movements=[
            transaction_type.TransactionTypeMovement(
                movement_types=transaction_type.MovementType.StockMovement,
                side=test_side1,
                direction=1,
                name="Stock Movement",
                movement_options=[transaction_type.MovementOption.DirectAdjustment],
            )
        ],
        calculations=[
            transaction_type.TransactionTypeCalculation(
                type=transaction_type.CalculationType.TaxAmounts, side=test_side2
            ),
            transaction_type.TransactionTypeCalculation(
                type=transaction_type.CalculationType.NotionalAmount
            ),
        ],
    )
    return {"side1": test_side1, "side2": test_side2, "type": test_buy_transaction_type}


@fixture()
def deployment(deployment_name, lusid_env):
    res = resources(deployment_name)
    print(f"\nRunning for deployment {deployment_name}...")
    yield fbnconfig.Deployment(deployment_name, list(res.values()))
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env.env, lusid_env.token)


def test_teardown_side(deployment, lusid_env, client):
    # create first
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    fbnconfig.deployex(fbnconfig.Deployment(deployment.id, []), lusid_env.env, lusid_env.token)
    with pytest.raises(HTTPStatusError) as error:
        client.get(
            "/api/api/transactionconfiguration/sides/Side1", params={"scope": deployment.id}
        )
        assert error.value.response.status_code == 404


def test_create_side(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    search = client.get(
        "/api/api/transactionconfiguration/sides/Side1", params={"scope": deployment.id}
    )
    assert search.status_code == 200


def test_nochange_side(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    update = fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    assert [a.change for a in update if a.type == "SideResource"] == ["nochange", "nochange"]


def test_teardown_transaction_type(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    fbnconfig.deployex(fbnconfig.Deployment(deployment.id, []), lusid_env.env, lusid_env.token)
    with pytest.raises(HTTPStatusError) as error:
        client.get(
            "/api/api/transactionconfiguration/types/default/Buy",
            params={"scope": deployment.id},
        )
        assert error.value.response.status_code == 404


def test_create_transaction_type(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    search = client.get(
        "/api/api/transactionconfiguration/types/default/Buy", params={"scope": deployment.id}
    )
    assert search.status_code == 200


def test_nochange_transaction_type(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    update = fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    assert [a.change for a in update if a.type == "TransactionTypeResource"] == ["nochange"]
