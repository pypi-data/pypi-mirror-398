from fbnconfig import Deployment, datatype, fund_accounting, posting_module, property

"""
An example configuration for defining fund accounting related entities.
The script configures the following entities:
- Chart of accounts
- Accounts within a chart of account
- Posting module
"""


def configure(env):
    scope = "example-scope"

    fund_manager_property = property.DefinitionResource(
        id="fund_manager_prop",
        domain=property.Domain.ChartOfAccounts,
        scope=scope,
        code="FundManagerName",
        display_name="FundManagerName",
        data_type_id=datatype.DataTypeRef(id="default_str", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="FundManagerName",
        life_time=property.LifeTime.Perpetual,
    )

    chart_property = fund_accounting.PropertyValue(
        property_key=fund_manager_property, label_value="John Smith"
    )

    chart_of_account = fund_accounting.ChartOfAccountsResource(
        id="example_chart",
        scope=scope,
        code="DailyCoA",
        display_name="This is a CoA for a daily NAV",
        description="This is a CoA for a daily NAVn",
        properties=[chart_property],
    )

    account_property_definition = property.DefinitionResource(
        id="pd1",
        domain=property.Domain.Account,
        scope=scope,
        code="AccountantName",
        display_name="AccountantName",
        data_type_id=property.ResourceId(scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="AccountantName",
        life_time=property.LifeTime.Perpetual,
        collection_type=None,
    )

    account_property = fund_accounting.PropertyValue(
        property_key=account_property_definition, label_value="Jane Miller"
    )

    account = fund_accounting.AccountResource(
        id="example_account",
        chart_of_accounts=chart_of_account,
        code="1-Investments",
        description="Cash",
        type=fund_accounting.AccountType.ASSET,
        status=fund_accounting.AccountStatus.ACTIVE,
        control="Manual",
        properties=[account_property],
    )

    rule_1 = posting_module.PostingModuleRule(
        rule_id="rule_0001",
        general_ledger_account_code=account,
        rule_filter="EconomicBucket startswith 'NA' and HoldType neq 'P'",
    )

    rule_2 = posting_module.PostingModuleRule(
        rule_id="rule_0002",
        general_ledger_account_code=account,
        rule_filter="EconomicBucket startswith 'NA' and HoldType eq 'C'",
    )

    posting_mod = posting_module.PostingModuleResource(
        id="posting_module_id",
        chart_of_accounts=chart_of_account,
        code="DailyPM",
        display_name="Daily NAV posting module",
        description="This is a posting module for daily NAV",
        rules=[rule_1, rule_2],
    )

    return Deployment("fund_accounting_example", [chart_of_account, account, posting_mod])
