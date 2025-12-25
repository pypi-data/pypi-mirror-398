
import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import cleardown_module as cdm
from fbnconfig import fund_accounting as fa
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)
base_url = "api/api/chartofaccounts"


@fixture(scope="module")
def setup_deployment():
    scope = gen("cleardown_module")
    yield SimpleNamespace(name=scope)

    items_to_delete = [
        f"{base_url}/{scope}/cdm_int_test_code/cleardownmodules/int_test_cleardown_code",
        f"{base_url}/{scope}/cdm_int_test_code/cleardownmodules/int_test_fbnconfig_cdm_no_rules",
        f"{base_url}/{scope}/cdm_int_test_code/accounts/int_test_account_code",
        f"{base_url}/chartofaccounts/{scope}/cdm_int_test_code"
    ]

    for item in items_to_delete:
        try:
            client.delete(item)
        except Exception as e:
            print(f"Error deleting {item}: {e}")


@fixture
def updated_resources(setup_deployment):
    scope = setup_deployment.name
    chart_of_account_code = "cdm_int_test_code"

    chart_of_account = fa.ChartOfAccountsResource(
        id="int_test_chart_of_account",
        scope=scope,
        code=chart_of_account_code,
        display_name="fbn config COA integration test"
    )

    account = fa.AccountResource(
        id="int_test_account",
        chart_of_accounts=chart_of_account,
        code="int_test_account_code",
        description="example_desc",
        type=fa.AccountType.ASSET,
        status=fa.AccountStatus.ACTIVE,
        control="Manual"
    )
    # Need to create a chart of account first and general ledger profile is the code for the account

    cdm_resource = cdm.CleardownModuleResource(
        id="int_test_clearndown_module",
        chart_of_accounts=chart_of_account,
        cleardown_module_code="int_test_cleardown_code",
        display_name="updated clear down module display name",
        rules=[cdm.CleardownModuleRule(
            rule_id="rule_0002",
            general_ledger_account_code="int_test_account_code",
            rule_filter="Account.Code startswith '300'",
        )]
    )

    cdm_no_rules_resource = cdm.CleardownModuleResource(
        id="int_test_cleardown_module_no_rules",
        chart_of_accounts=chart_of_account,
        cleardown_module_code="int_test_fbnconfig_cdm_no_rules",
        display_name="clear down module with no rules",
        rules=None
    )

    return [chart_of_account, account, cdm_resource, cdm_no_rules_resource]


@fixture
def base_resources(setup_deployment):
    scope = setup_deployment.name
    chart_of_account_code = "cdm_int_test_code"

    chart_of_account = fa.ChartOfAccountsResource(
        id="int_test_chart_of_account",
        scope=scope,
        code=chart_of_account_code,
        display_name="fbn config COA integration test"
    )

    account = fa.AccountResource(
        id="int_test_account",
        chart_of_accounts=chart_of_account,
        code="int_test_account_code",
        description="example_desc",
        type=fa.AccountType.ASSET,
        status=fa.AccountStatus.ACTIVE,
        control="Manual"
    )
    # Need to create a chart of account first and general ledger profile is the code for the account

    cdm_resource = cdm.CleardownModuleResource(
        id="int_test_clearndown_module",
        chart_of_accounts=chart_of_account,
        cleardown_module_code="int_test_cleardown_code",
        display_name="clear down module code",
        rules=[cdm.CleardownModuleRule(
            rule_id="rule_0001",
            general_ledger_account_code="int_test_account_code",
            rule_filter="Account.Code startswith '200'",
        )]
    )

    cdm_no_rules_resource = cdm.CleardownModuleResource(
        id="int_test_cleardown_module_no_rules",
        chart_of_accounts=chart_of_account,
        cleardown_module_code="int_test_fbnconfig_cdm_no_rules",
        display_name="clear down module with no rules",
        rules=None
    )

    return [chart_of_account, account, cdm_resource, cdm_no_rules_resource]


@fixture
def metadata_only_update_resources(setup_deployment):
    """Resources for testing metadata-only updates (display_name, description)"""
    scope = setup_deployment.name
    chart_of_account_code = "cdm_int_test_code"

    chart_of_account = fa.ChartOfAccountsResource(
        id="int_test_chart_of_account",
        scope=scope,
        code=chart_of_account_code,
        display_name="fbn config COA integration test"
    )

    account = fa.AccountResource(
        id="int_test_account",
        chart_of_accounts=chart_of_account,
        code="int_test_account_code",
        description="example_desc",
        type=fa.AccountType.ASSET,
        status=fa.AccountStatus.ACTIVE,
        control="Manual"
    )

    # Same rules, but different display_name and description
    cdm_resource = cdm.CleardownModuleResource(
        id="int_test_clearndown_module",
        chart_of_accounts=chart_of_account,
        cleardown_module_code="int_test_cleardown_code",
        display_name="METADATA ONLY UPDATE - display name",
        description="Updated description for metadata-only test",
        rules=[cdm.CleardownModuleRule(
            rule_id="rule_0001",  # Same rule as base
            general_ledger_account_code="int_test_account_code",
            rule_filter="Account.Code startswith '200'",
        )]
    )

    cdm_no_rules_resource = cdm.CleardownModuleResource(
        id="int_test_cleardown_module_no_rules",
        chart_of_accounts=chart_of_account,
        cleardown_module_code="int_test_fbnconfig_cdm_no_rules",
        display_name="METADATA ONLY UPDATE - no rules display name",
        description="Updated description for no-rules module",
        rules=None
    )

    return [chart_of_account, account, cdm_resource, cdm_no_rules_resource]


@fixture
def rules_only_update_resources(setup_deployment):
    """Resources for testing rules-only updates"""
    scope = setup_deployment.name
    chart_of_account_code = "cdm_int_test_code"

    chart_of_account = fa.ChartOfAccountsResource(
        id="int_test_chart_of_account",
        scope=scope,
        code=chart_of_account_code,
        display_name="fbn config COA integration test"
    )

    account = fa.AccountResource(
        id="int_test_account",
        chart_of_accounts=chart_of_account,
        code="int_test_account_code",
        description="example_desc",
        type=fa.AccountType.ASSET,
        status=fa.AccountStatus.ACTIVE,
        control="Manual"
    )

    # Same display_name, but different rules
    cdm_resource = cdm.CleardownModuleResource(
        id="int_test_clearndown_module",
        chart_of_accounts=chart_of_account,
        cleardown_module_code="int_test_cleardown_code",
        display_name="clear down module code",  # Same as base
        description=None,  # Same as base (None)
        rules=[
            cdm.CleardownModuleRule(
                rule_id="rule_0001",  # Same rule_id but different filter
                general_ledger_account_code="int_test_account_code",
                rule_filter="Account.Code startswith '400'",  # Different filter
            ),
            cdm.CleardownModuleRule(  # Additional rule
                rule_id="rule_0003",
                general_ledger_account_code="int_test_account_code",
                rule_filter="Account.Code startswith '300'",
            )
        ]
    )

    cdm_no_rules_resource = cdm.CleardownModuleResource(
        id="int_test_cleardown_module_no_rules",
        chart_of_accounts=chart_of_account,
        cleardown_module_code="int_test_fbnconfig_cdm_no_rules",
        display_name="clear down module with no rules",  # Same as base
        description=None,  # Same as base
        rules=None
    )

    return [chart_of_account, account, cdm_resource, cdm_no_rules_resource]


def test_cleardown_module(base_resources, setup_deployment):
    scope = setup_deployment.name

    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    formatted_url = (
        f"api/api/chartofaccounts/{scope}/cdm_int_test_code/"
        f"cleardownmodules/int_test_cleardown_code"
    )

    response = client.get(formatted_url).json()

    assert response is not None

    expected_rules = [
        {
            "ruleId": "rule_0001",
            "generalLedgerAccountCode": "int_test_account_code",
            "ruleFilter": "Account.Code startswith '200'"
        }
    ]
    assert response["cleardownModuleCode"] == "int_test_cleardown_code"
    assert response["displayName"] == "clear down module code"
    assert len(response["rules"]) == 1
    assert response["rules"] == expected_rules
    assert response["chartOfAccountsId"] == {"scope": scope, "code": "cdm_int_test_code"}

    chart_of_account_code = "cdm_int_test_code"
    no_rules_cdm_code = "int_test_fbnconfig_cdm_no_rules"

    no_cdm_rules_url = (
        f"api/api/chartofaccounts/{scope}/{chart_of_account_code}/"
        f"cleardownmodules/{no_rules_cdm_code}"
    )

    no_rules_response = client.get(no_cdm_rules_url).json()
    assert no_rules_response is not None
    assert no_rules_response["cleardownModuleCode"] == "int_test_fbnconfig_cdm_no_rules"
    assert no_rules_response["displayName"] == "clear down module with no rules"
    assert no_rules_response["chartOfAccountsId"] == {"scope": scope, "code": "cdm_int_test_code"}
    assert no_rules_response["rules"] == []


def test_update_cleardown_module(base_resources, setup_deployment, updated_resources):
    scope = setup_deployment.name
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    formatted_url = (
        f"api/api/chartofaccounts/{scope}/cdm_int_test_code/"
        f"cleardownmodules/int_test_cleardown_code"
    )

    response = client.get(formatted_url).json()

    assert response is not None

    expected_rules = [
        {
            "ruleId": "rule_0001",
            "generalLedgerAccountCode": "int_test_account_code",
            "ruleFilter": "Account.Code startswith '200'"
        }
    ]
    assert response["cleardownModuleCode"] == "int_test_cleardown_code"
    assert response["displayName"] == "clear down module code"
    assert len(response["rules"]) == 1
    assert response["rules"] == expected_rules
    assert response["chartOfAccountsId"] == {"scope": scope, "code": "cdm_int_test_code"}

    deployment = fbnconfig.Deployment(setup_deployment.name, updated_resources)
    updated_deployment = fbnconfig.deploy(deployment, lusid_env, token)

    chart_of_accounts_changes = [
        a.change for a in updated_deployment if a.type == "ChartOfAccountsResource"
    ]
    account_changes = [
        a.change for a in updated_deployment if a.type == "AccountResource"
    ]
    cleardown_list_changes = [
        a.change for a in updated_deployment if a.type == "CleardownModuleResource"
    ]

    assert chart_of_accounts_changes == ["nochange"]
    assert account_changes == ["nochange"]
    # cdm_no_rules_resource should be nochange as no rules have been updated
    assert cleardown_list_changes == ["update", "nochange"]

    updated_response = client.get(formatted_url).json()
    assert updated_response is not None
    expected_updated_rules = [
        {
            "ruleId": "rule_0002",
            "generalLedgerAccountCode": "int_test_account_code",
            "ruleFilter": "Account.Code startswith '300'"
        }
    ]
    assert updated_response["cleardownModuleCode"] == "int_test_cleardown_code"
    assert updated_response["displayName"] == "updated clear down module display name"
    assert updated_response["chartOfAccountsId"] == response["chartOfAccountsId"]
    assert len(updated_response["rules"]) == 1
    assert updated_response["rules"] == expected_updated_rules
    assert updated_response["chartOfAccountsId"] == {"scope": scope, "code": "cdm_int_test_code"}


def test_nochange(setup_deployment, base_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)
    updated_deployment = fbnconfig.deploy(deployment, lusid_env, token)

    chart_of_accounts_changes = [
        a.change for a in updated_deployment if a.type == "ChartOfAccountsResource"
    ]
    account_changes = [
        a.change for a in updated_deployment if a.type == "AccountResource"
    ]
    cleardown_list_changes = [
        a.change for a in updated_deployment if a.type == "CleardownModuleResource"
    ]

    assert chart_of_accounts_changes == ["nochange"]
    assert account_changes == ["nochange"]
    assert cleardown_list_changes == ["nochange", "nochange"]


def test_update_metadata_only_integration(base_resources, setup_deployment,
                                          metadata_only_update_resources):
    """Integration test for metadata-only updates (display_name, description)"""
    scope = setup_deployment.name

    # Deploy base resources first
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    # Deploy metadata-only update
    metadata_deployment = fbnconfig.Deployment(setup_deployment.name, metadata_only_update_resources)
    updated_deployment = fbnconfig.deploy(metadata_deployment, lusid_env, token)

    cleardown_list_changes = [
        a.change for a in updated_deployment if a.type == "CleardownModuleResource"
    ]

    # Should be update for the main resource (metadata changed) and nochange for no-rules resource
    assert cleardown_list_changes == ["update", "update"]

    # Verify the changes were applied
    formatted_url = (
        f"api/api/chartofaccounts/{scope}/cdm_int_test_code/"
        f"cleardownmodules/int_test_cleardown_code"
    )

    response = client.get(formatted_url).json()
    assert response["displayName"] == "METADATA ONLY UPDATE - display name"
    assert response["description"] == "Updated description for metadata-only test"

    # Rules should be unchanged
    expected_rules = [
        {
            "ruleId": "rule_0001",
            "generalLedgerAccountCode": "int_test_account_code",
            "ruleFilter": "Account.Code startswith '200'"
        }
    ]
    assert response["rules"] == expected_rules


def test_update_rules_only_integration(base_resources, setup_deployment, rules_only_update_resources):
    """Integration test for rules-only updates"""
    scope = setup_deployment.name

    # Deploy base resources first
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    # Deploy rules-only update
    rules_deployment = fbnconfig.Deployment(setup_deployment.name, rules_only_update_resources)
    updated_deployment = fbnconfig.deploy(rules_deployment, lusid_env, token)

    cleardown_list_changes = [
        a.change for a in updated_deployment if a.type == "CleardownModuleResource"
    ]

    # Should be update for the main resource (rules changed) and nochange for no-rules resource
    assert cleardown_list_changes == ["update", "nochange"]

    # Verify the changes were applied
    formatted_url = (
        f"api/api/chartofaccounts/{scope}/cdm_int_test_code/"
        f"cleardownmodules/int_test_cleardown_code"
    )

    response = client.get(formatted_url).json()
    assert response["displayName"] == "clear down module code"  # Unchanged
    assert response.get("description") is None  # Unchanged

    # Rules should be updated
    expected_rules = [
        {
            "ruleId": "rule_0001",
            "generalLedgerAccountCode": "int_test_account_code",
            "ruleFilter": "Account.Code startswith '400'"  # Updated filter
        },
        {
            "ruleId": "rule_0003",
            "generalLedgerAccountCode": "int_test_account_code",
            "ruleFilter": "Account.Code startswith '300'"  # New rule
        }
    ]
    assert len(response["rules"]) == 2
    assert response["rules"] == expected_rules


def test_delete_cleardown_module(base_resources, setup_deployment):
    scope = setup_deployment.name
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deploy(deployment, lusid_env, token)

    resources_without_cleardown_modules = base_resources[:2]
    new_deployment = fbnconfig.Deployment(scope, resources_without_cleardown_modules)
    updated_deployment = fbnconfig.deploy(new_deployment, lusid_env, token)

    cleardown_list_changes = [
        a.change for a in updated_deployment if a.type == "CleardownModuleResource"
    ]

    assert cleardown_list_changes == ["remove", "remove"]
