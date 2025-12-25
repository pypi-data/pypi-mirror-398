import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import fund_configurations as fc
from fbnconfig import property as prop
from tests.integration.generate_test_name import gen

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)
base_url = "api/api/fundconfigurations"


@fixture(scope="module")
def setup_deployment():
    deployment_name = gen("fund_configuration")
    print(f"\nRunning deployment for {deployment_name}")
    yield SimpleNamespace(name=deployment_name)
    try:
        fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    except Exception:
        pass
    items_to_delete = [
        f"/api/api/fundconfigurations/{deployment_name}/fund_configuration_code_int_test",
        f"/api/api/fundconfigurations/{deployment_name}_updated_fund/fund_configuration_code_updated_int_test",
        f"/api/api/propertydefinitions/{prop.Domain.FundConfiguration}/{deployment_name}_property/MyFundConfigProperty",
        f"/api/api/propertydefinitions/{prop.Domain.FundConfiguration}/{deployment_name}_updated_property/MyUpdatedFundConfigProperty"
    ]
    try:
        for item in items_to_delete:
            try:
                client.delete(item)
            except Exception:
                print(f"Failed to delete {item}")
                pass

    except Exception:
        print("Failed to delete transaction template")
        pass


@fixture
def base_resources(setup_deployment):
    deployment_name = setup_deployment.name
    property_def = prop.DefinitionResource(
          id="property_definition_for_fund_configuration_int_test",
          code="MyFundConfigProperty",
          data_type_id=prop.ResourceId(scope="system", code="string"),
          display_name="Fund configuration display name",
          domain=prop.Domain.FundConfiguration,
          scope=f"{deployment_name}_property",
          life_time=prop.LifeTime.TimeVariant
      )

    fund_template = [
        property_def,
        fc.FundConfigurationResource(
            id=f"{deployment_name}_id",
            scope=f"{deployment_name}",
            code="fund_configuration_code_int_test",
            display_name="fund configuration display name",
            description="fund configuration description",
            dealing_filters=[
                fc.ComponentFilter(
                  filter_id="SUB",
                  filter="account.code startswith '3001'"
                ),
                fc.ComponentFilter(
                  filter_id="RED",
                  filter="account.code startswith '3002'"
                )
            ],
            pnl_filters=[
                fc.ComponentFilter(
                  filter_id="SUB",
                  filter="account.code startswith '3001'"
                ),
                fc.ComponentFilter(
                  filter_id="RED",
                  filter="account.code startswith '3002'"
                )
            ],
            back_out_filters=[
                fc.ComponentFilter(
                  filter_id="SUB",
                  filter="account.code startswith '3001'"
                ),
                fc.ComponentFilter(
                  filter_id="RED",
                  filter="account.code startswith '3002'"
                )
            ],
            external_fee_filters=[
                fc.ExternalFeeComponentFilter(
                    filter_id="ShareClassAPnLAdjustment",
                    filter="account.code eq 'ShareClassAPnl'",
                    applies_to=fc.AppliesToEnum.PnLBucket
                )
            ],
            properties=[
                fc.PropertyValue.create(
                    key=property_def,
                    label_value="My fund configuration property value",
                )
            ]
        )
    ]
    return fund_template


def test_fund_configuration(setup_deployment, base_resources):
    from urllib.parse import urlencode

    deployment_name = setup_deployment.name

    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    property_scope = f"{deployment_name}_property"
    query_params = {
        "propertyKeys": [f"FundConfiguration/{property_scope}/MyFundConfigProperty"]
    }
    # Use doseq=True for list parameters
    query_string = urlencode(query_params, doseq=True)
    code = "fund_configuration_code_int_test"

    formatted_url = f"{base_url}/{deployment_name}/{code}/?{query_string}"

    response = client.get(formatted_url).json()

    assert response is not None

    expected_id = {
        "scope": f"{deployment_name}",
        "code": "fund_configuration_code_int_test",
    }

    expected_dealings_filters = [
        {
            "filterId": "SUB",
            "filter": "account.code startswith '3001'"
        },
        {
            "filterId": "RED",
            "filter": "account.code startswith '3002'"
        }
    ]
    expected_pnl_filters = [
        {
            "filterId": "SUB",
            "filter": "account.code startswith '3001'"
        },
        {
            "filterId": "RED",
            "filter": "account.code startswith '3002'"
        }
    ]
    expected_back_out_filters = [
                  {"filterId": "SUB",
                  "filter": "account.code startswith '3001'"},
                  {"filterId": "RED",
                  "filter": "account.code startswith '3002'"}
            ]
    expected_external_fee_filters = [
        {
            "filterId": "ShareClassAPnLAdjustment",
            "filter": "account.code eq 'ShareClassAPnl'",
            "appliesTo": fc.AppliesToEnum.PnLBucket.value
        }
    ]

    expected_properties = {
        f"FundConfiguration/{deployment_name}_property/MyFundConfigProperty": {
            "key": f"FundConfiguration/{deployment_name}_property/MyFundConfigProperty",
            "value": {
                "labelValue": "My fund configuration property value"
            },
            # The effective values are not present in the
            "effectiveFrom": "0001-01-01T00:00:00.0000000+00:00",
            "effectiveUntil": "9999-12-31T23:59:59.9999999+00:00"
        }
    }

    assert response["displayName"] == "fund configuration display name"
    assert response["description"] == "fund configuration description"
    assert response["id"] == expected_id
    assert response["dealingFilters"] == expected_dealings_filters
    assert response["pnlFilters"] == expected_pnl_filters
    assert response["backOutFilters"] == expected_back_out_filters
    assert response["externalFeeFilters"] == expected_external_fee_filters
    assert response["properties"] == expected_properties


def test_update_scope_fund_configuration(setup_deployment, base_resources):
    from urllib.parse import urlencode

    deployment_name = setup_deployment.name

    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    property_def_code = "MyUpdatedFundConfigProperty"
    property_def_scope = f"{deployment_name}_updated_property"
    fund_configuration_code = "fund_configuration_code_updated_int_test"
    fund_configuration_scope = f"{deployment_name}_updated_fund"

    property_def = prop.DefinitionResource(
          id="prop_def_for_fund_configuration_updated_int_test",
          code=property_def_code,
          data_type_id=prop.ResourceId(scope="system", code="string"),
          display_name="Fund configuration display name",
          domain=prop.Domain.FundConfiguration,
          scope=property_def_scope,
          life_time=prop.LifeTime.TimeVariant
      )

    updated_fund_configuration = fc.FundConfigurationResource(
            id=f"{deployment_name}_updated_id",
            scope=fund_configuration_scope,
            code=fund_configuration_code,
            display_name="fund configuration display name",
            description="fund configuration description",
            dealing_filters=[
                fc.ComponentFilter(
                  filter_id="SUB",
                  filter="account.code startswith '1001'"
                ),
                fc.ComponentFilter(
                  filter_id="RED",
                  filter="account.code startswith '1002'"
                )
            ],
            pnl_filters=[
                fc.ComponentFilter(
                  filter_id="SUB",
                  filter="account.code startswith '1001'"
                ),
                fc.ComponentFilter(
                  filter_id="RED",
                  filter="account.code startswith '1002'"
                )
            ],
            back_out_filters=[
                fc.ComponentFilter(
                  filter_id="SUB",
                  filter="account.code startswith '3001'"
                ),
                fc.ComponentFilter(
                  filter_id="RED",
                  filter="account.code startswith '3002'"
                )
            ],
            external_fee_filters=[
                fc.ExternalFeeComponentFilter(
                    filter_id="ShareClassAPnLAdjustment",
                    filter="account.code eq 'ShareClassAPnl'",
                    applies_to=fc.AppliesToEnum.PnLBucket
                )
            ],
            properties=[
                fc.PropertyValue.create(
                    key=property_def,
                    label_value="My updated fund configuration property value",
                )
            ]
        )
    # Property needs to be created before it can be used in the fund configuration
    updated_deployment = fbnconfig.Deployment(
        setup_deployment.name, [property_def, updated_fund_configuration]
    )
    updated_resource = fbnconfig.deployex(updated_deployment, lusid_env, token)

    query_params = {
        "propertyKeys": [f"FundConfiguration/{property_def_scope}/{property_def_code}"]
    }
    # Use doseq=True for list parameters
    query_string = urlencode(query_params, doseq=True)

    formatted_url = f"{base_url}/{fund_configuration_scope}/{fund_configuration_code}/?{query_string}"

    response = client.get(formatted_url).json()

    updated_list = [res.change for res in updated_resource if res.type == "FundConfigurationResource"]

    definition_list = [res.change for res in updated_resource if res.type == "DefinitionResource"]

    assert response is not None

    assert updated_list == ["create", "remove"]
    assert definition_list == ["create", "remove"]

    expected_id = {
        "scope": fund_configuration_scope,
        "code": fund_configuration_code
    }

    expected_dealings_filters = [
        {
            "filterId": "SUB",
            "filter": "account.code startswith '1001'"
        },
        {
            "filterId": "RED",
            "filter": "account.code startswith '1002'"
        }
    ]
    expected_pnl_filters = [
        {
            "filterId": "SUB",
            "filter": "account.code startswith '1001'"
        },
        {
            "filterId": "RED",
            "filter": "account.code startswith '1002'"
        }
    ]
    expected_back_out_filters = [
                  {"filterId": "SUB",
                  "filter": "account.code startswith '3001'"},
                  {"filterId": "RED",
                  "filter": "account.code startswith '3002'"}
            ]
    expected_external_fee_filters = [
        {
            "filterId": "ShareClassAPnLAdjustment",
            "filter": "account.code eq 'ShareClassAPnl'",
            "appliesTo": fc.AppliesToEnum.PnLBucket.value
        }
    ]

    expected_properties = {
        f"FundConfiguration/{property_def_scope}/{property_def_code}": {
            "key": f"FundConfiguration/{property_def_scope}/{property_def_code}",
            "value": {
                "labelValue": "My updated fund configuration property value"
            },
            # The effective values are not present in the
            "effectiveFrom": "0001-01-01T00:00:00.0000000+00:00",
            "effectiveUntil": "9999-12-31T23:59:59.9999999+00:00"
        }
    }

    assert response["displayName"] == "fund configuration display name"
    assert response["description"] == "fund configuration description"
    assert response["id"] == expected_id
    assert response["dealingFilters"] == expected_dealings_filters
    assert response["pnlFilters"] == expected_pnl_filters
    assert response["backOutFilters"] == expected_back_out_filters
    assert response["externalFeeFilters"] == expected_external_fee_filters
    assert response["properties"] == expected_properties


def test_update_fund_configuration_no_change(setup_deployment, base_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    no_change_resource = fbnconfig.deployex(deployment, lusid_env, token)

    no_change_list = [
        res.change for res in no_change_resource if res.type == "FundConfigurationResource"
    ]
    no_change_definition_list = [
        res.change for res in no_change_resource if res.type == "DefinitionResource"
    ]

    assert no_change_list == ["nochange"]
    assert no_change_definition_list == ["nochange"]


def test_teardown(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    deployment = fbnconfig.Deployment(deployment_name, base_resources)

    fbnconfig.deployex(deployment, lusid_env, token)
    empty = fbnconfig.Deployment(deployment_name, [])
    update = fbnconfig.deployex(empty, lusid_env, token)

    fund_config_changes = [a.change for a in update if a.type == "FundConfigurationResource"]
    definition_changes = [a.change for a in update if a.type == "DefinitionResource"]
    assert fund_config_changes == ["remove"]
    assert definition_changes == ["remove"]
