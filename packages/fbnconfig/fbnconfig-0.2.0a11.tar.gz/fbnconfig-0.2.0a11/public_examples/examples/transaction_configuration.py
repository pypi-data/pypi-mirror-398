from fbnconfig import Deployment, side_definition, transaction_type

"""
An example configuration for defining transaction configuration related entities.
The script configures the following entities:
- Side
- Transaction type

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01749/
"""


def configure(env):
    test_side1 = side_definition.SideResource(
        id="side1",
        side="Side1",
        scope="sc1",
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
        scope="sc1",
        security="Txn:SettlementCurrency",
        currency="Txn:SettlementCurrency",
        rate="SettledToPortfolioRate",
        units="Txn:TotalConsideration",
        amount="Txn:TotalConsideration",
        notional_amount="0",
    )

    test_buy_transaction_type = transaction_type.TransactionTypeResource(
        id="example",
        scope="sc1",
        source="default",
        aliases=[
            transaction_type.TransactionTypeAlias(
                type="Buy",
                description="Example buy",
                transaction_class="default",
                transaction_roles="LongLonger",
                is_default=False,
            ),
            transaction_type.TransactionTypeAlias(
                type="BY",
                description="Example buy alias",
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
            )
        ],
    )

    return Deployment("transaction_configuration_example", [test_buy_transaction_type])
