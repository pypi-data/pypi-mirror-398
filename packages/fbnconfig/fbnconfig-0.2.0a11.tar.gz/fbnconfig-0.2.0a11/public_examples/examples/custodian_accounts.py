"""
Example: Managing Custodian Accounts

This example demonstrates how to create and manage custodian accounts for a transaction portfolio.
Custodian accounts allow you to segregate holdings and track which custodian holds specific assets.
"""

from fbnconfig import Deployment, custodian_accounts, datatype, property
from fbnconfig.custodian_accounts import PropertyValue


def configure(env):
    """
    Configure custodian accounts for segregating holdings within a portfolio.

    This example creates two custodian accounts with different accounting methods:
    - HSBC account using FIFO (First In First Out)
    - JPM account using LIFO (Last In First Out)
    """

    # Define a property to attach to custodian accounts
    custodian_prop = property.DefinitionResource(
        id="custodian-rating",
        domain=property.Domain.CustodianAccount,
        scope="CustodianAccounts",
        code="Rating",
        display_name="Custodian Credit Rating",
        life_time=property.LifeTime.Perpetual,
        data_type_id=datatype.DataTypeRef(id="string-type", scope="system", code="string"),
    )

    # Create a FIFO custodian account with HSBC
    hsbc_account = custodian_accounts.CustodianAccountResource(
        id="hsbc-fifo",
        portfolio_scope="Equities",
        portfolio_code="Growth",
        scope="CustodianAccounts",
        code="HSBC-FIFO",
        account_number="ACC-HSBC-001",
        account_name="HSBC FIFO Account",
        accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
        currency="GBP",
        custodian_identifier=custodian_accounts.CustodianIdentifier(
            id_type_scope="InternationalBanks",
            id_type_code="BankId",
            code="HSBC",
        ),
        account_type=custodian_accounts.AccountTypeEnum.Margin,
        properties=[
            PropertyValue(
                property_key=custodian_prop,
                label_value="AA+",
            )
        ],
    )

    # Create a LIFO custodian account with JP Morgan
    jpm_account = custodian_accounts.CustodianAccountResource(
        id="jpm-lifo",
        portfolio_scope="Equities",
        portfolio_code="Growth",
        scope="CustodianAccounts",
        code="JPM-LIFO",
        account_number="ACC-JPM-002",
        account_name="JP Morgan LIFO Account",
        accounting_method=custodian_accounts.AccountingMethodEnum.LastInFirstOut,
        currency="USD",
        custodian_identifier=custodian_accounts.CustodianIdentifier(
            id_type_scope="InternationalBanks",
            id_type_code="BankId",
            code="JPM",
        ),
        account_type=custodian_accounts.AccountTypeEnum.Cash,
        properties=None
    )

    # Reference an existing custodian account
    existing_account_ref = custodian_accounts.CustodianAccountRef(
        id="existing-custodian",
        portfolio_scope="Equities",
        portfolio_code="Growth",
        scope="CustodianAccounts",
        code="EXISTING-ACCOUNT",
    )

    return Deployment(
        "custodian-accounts-example",
        [
            custodian_prop,
            hsbc_account,
            jpm_account,
            existing_account_ref,
        ],
    )


"""
To use this configuration:

1. Ensure you have a transaction portfolio created (scope: "Equities", code: "Growth")

2. Ensure you have legal entities mastered in LUSID for the custodians (HSBC, JPM)
   with the appropriate identifiers (InternationalBanks/BankId/HSBC, etc.)

3. Run the deployment:
   fbnconfig run custodian_accounts.py

4. After creation, you can assign transactions to specific custodian accounts:
   - Use the custodianAccountId field in transaction requests
   - Or use the Transaction/default/AllocationMethod property to prorate across accounts

5. To segregate holdings, register the Transaction/system/CustodianAccountUniqueId
   as a sub-holding key on the portfolio.

For more information on custodian accounts, see:
https://support.lusid.com/docs/segregating-holdings-using-custodian-accounts
"""
