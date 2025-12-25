from fbnconfig import Deployment, side_definition, transaction_type


def configure(env):
    deployment_name = getattr(env, "name", "transaction_configuration")

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

    return Deployment(deployment_name, [test_buy_transaction_type])
