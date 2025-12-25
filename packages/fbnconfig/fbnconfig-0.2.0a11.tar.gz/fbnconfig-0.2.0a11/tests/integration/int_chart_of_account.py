import os
from types import SimpleNamespace

from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
from fbnconfig import Deployment, fund_accounting, posting_module, property
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}


def configure(env):
    deployment_name = getattr(env, "name", "chart_of_accounts")

    perp_prop = fund_accounting.PropertyValue(
        property_key=property.DefinitionRef(
            id="one", domain=property.Domain.ChartOfAccounts, scope="sc1", code="cd1"
        ),
        label_value="Hello"
    )

    chart_of_account = fund_accounting.ChartOfAccountsResource(
        id="example_id",
        scope=f"testScope-{deployment_name}",
        code="testCode",
        display_name="example_display_name",
        description="example_description",
        properties=[perp_prop]
    )

    perp_prop_two = fund_accounting.PropertyValue(
        property_key=property.DefinitionRef(
            id="two", domain=property.Domain.Account, scope="sc2", code="cd2"
        ),
        label_value="Goodbye"
    )

    account = fund_accounting.AccountResource(
        id=f"example_id-{deployment_name}",
        chart_of_accounts=chart_of_account,
        code=f"account_code-{deployment_name}",
        description="example_desc",
        type=fund_accounting.AccountType.ASSET,
        status=fund_accounting.AccountStatus.ACTIVE,
        control="Manual",
        properties=[perp_prop_two]
    )

    rule = posting_module.PostingModuleRule(
        rule_id="rule_id",
        general_ledger_account_code=account,
        rule_filter="SourceType eq 'LusidTransaction'"
    )

    post_mod = posting_module.PostingModuleResource(
        id="posting_module_id",
        chart_of_accounts=chart_of_account,
        code=f"module_code-{deployment_name}",
        display_name="example_display_name",
        description="example_description",
        rules=[rule]
    )

    return Deployment(deployment_name, [account, chart_of_account, post_mod])


@fixture(scope="module")
def setup_deployment():
    print("Creating new property")
    client = fbnconfig.create_client(lusid_env, token)

    # Deletes test property for chart of account if it exsits
    try:
        client.delete("/api/api/propertydefinitions/ChartOfAccounts/sc1/cd1")
    except Exception:
        pass
    # Deletes test property for account if it exsits
    try:
        client.delete("/api/api/propertydefinitions/Account/sc2/cd2")
    except Exception:
        pass

    # Creates new property to add to the chart of accounts
    chart_property = {
        "domain": "ChartOfAccounts",
        "scope": "sc1",
        "code": "cd1",
        "valueRequired": False,
        "displayName": "My Property Display Name",
        "dataTypeId": {
            "scope": "system",
            "code": "string"
        },
        "lifeTime": "Perpetual",
    }
    client.post("/api/api/propertydefinitions", json=chart_property)

    # Creates new property add to the chart of accounts
    account_property = {
        "domain": "Account",
        "scope": "sc2",
        "code": "cd2",
        "valueRequired": False,
        "displayName": "My Property Display Name",
        "dataTypeId": {
            "scope": "system",
            "code": "string"
        },
        "lifeTime": "Perpetual",
    }
    client.post("/api/api/propertydefinitions", json=account_property)

    deployment_name = gen("chart_of_accounts")
    print(f"\nRunning for deployment {deployment_name}...")

    yield SimpleNamespace(name=deployment_name)
    # Teardown: Clean up resources (if any) after the test
    print("\nTearing down resources...")
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    client.delete("/api/api/propertydefinitions/ChartOfAccounts/sc1/cd1")
    client.delete("/api/api/propertydefinitions/Account/sc2/cd2")


def test_teardown(setup_deployment):
    deployment_name = setup_deployment.name
    client = fbnconfig.create_client(lusid_env, token)
    # setup deployment
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)

    chart_url = f"/api/api/chartofaccounts/testScope-{deployment_name}/testCode"
    account_url = chart_url + f"/accounts/account_code-{deployment_name}"
    posting_mod_url = chart_url + f"/postingmodules/module_code-{deployment_name}"

    # check it exists
    client.request("get", chart_url)
    client.request("get", account_url)
    client.request("get", posting_mod_url)
    # Tear it down
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)

    # check account was deleted
    try:
        client.request("get", account_url)
    except HTTPStatusError as error:
        assert error.response.status_code == 404
    # check chart was deleted
    try:
        client.request("get", posting_mod_url)
    except HTTPStatusError as error:
        assert error.response.status_code == 404
    # check chart was deleted
    try:
        client.request("get", chart_url)
    except HTTPStatusError as error:
        assert error.response.status_code == 404


def test_create(setup_deployment):
    deployment_name = setup_deployment.name
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    client = fbnconfig.create_client(lusid_env, token)
    chart_url = f"/api/api/chartofaccounts/testScope-{deployment_name}/testCode"
    search_chart = client.request("get", chart_url)
    account_url = chart_url + f"/accounts/account_code-{deployment_name}"
    search_account = client.request("get", account_url)
    assert search_chart.status_code == 200
    assert search_account.status_code == 200


def test_update_nochange(setup_deployment):
    fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    update = fbnconfig.deployex(configure(setup_deployment), lusid_env, token)
    assert [a.change for a in update if a.type == "ChartOfAccountsResource"] == ["nochange"]
    assert [a.change for a in update if a.type == "AccountResource"] == ["nochange"]
    assert [a.change for a in update if a.type == "PostingModuleResource"] == ["nochange"]
