import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import fund_configurations as fc
from fbnconfig import property as pd
from fbnconfig.http_client import response_hook

TEST_BASE = "https://foo.lusid.com"


@pytest.fixture
def property_def():
    """Fixture for creating a property definition resource"""
    property_def_scope = "MyPropertyScope"
    return pd.DefinitionResource(
        id="property_definition_for_fund_configuration_unit_test",
        code="MyFundConfigProperty",
        data_type_id=pd.ResourceId(scope="system", code="string"),
        display_name="Fund configuration display name",
        domain=pd.Domain.FundConfiguration,
        scope=property_def_scope,
        life_time=pd.LifeTime.TimeVariant
    )


@pytest.fixture
def fund_configuration_with_properties(property_def):
    """Fixture for creating a fund configuration resource with properties"""
    return fc.FundConfigurationResource(
        id="fundconfig1",
        scope="scope-fund-configuration",
        code="code-fund-configuration",
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
                effective_from="0001-01-01T00:00:00.0000000+00:00",
                    effective_until="9999-12-31T23:59:59.9999999+00:00"
                )
        ]
    )


@pytest.fixture
def fund_configuration_without_properties():
    """Fixture for creating a fund configuration resource without properties"""
    return fc.FundConfigurationResource(
        id="fundconfig1",
        scope="scope-fund-configuration",
        code="code-fund-configuration",
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
        ]
    )


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeFundConfiguration:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock, fund_configuration_with_properties, property_def):
        base_url = "api/api/fundconfigurations"
        scope = "scope-fund-configuration"
        respx_mock.post(f"{TEST_BASE}/{base_url}/{scope}").mock(
            return_value=httpx.Response(201, json={})
        )

        sut = fund_configuration_with_properties
        state = sut.create(self.client)

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

        property_def_scope = "MyPropertyScope"
        expected_properties = {
            f"FundConfiguration/{property_def_scope}/MyFundConfigProperty": {
                "key": f"FundConfiguration/{property_def_scope}/MyFundConfigProperty",
                "value": {
                    "labelValue": "My fund configuration property value"
                },
                # The effective values are not present in the
                "effectiveFrom": "0001-01-01T00:00:00.0000000+00:00",
                "effectiveUntil": "9999-12-31T23:59:59.9999999+00:00"
            }
        }

        assert state["code"] == "code-fund-configuration"
        assert state["scope"] == "scope-fund-configuration"
        assert "content_hash" in state

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/fundconfigurations/{scope}"
        request_body = json.loads(request.content)

        assert request_body["displayName"] == "fund configuration display name"
        assert request_body["description"] == "fund configuration description"
        assert request_body["dealingFilters"] == expected_dealings_filters
        assert request_body["pnlFilters"] == expected_pnl_filters
        assert request_body["backOutFilters"] == expected_back_out_filters
        assert request_body["externalFeeFilters"] == expected_external_fee_filters
        assert request_body["properties"] == expected_properties

    def test_deps_with_properties(self, respx_mock, fund_configuration_with_properties, property_def):
        sut = fund_configuration_with_properties
        deps = sut.deps()

        assert len(deps) == 1
        assert deps[0] == property_def

    def test_deps_with_no_properties(self, respx_mock, fund_configuration_without_properties):
        sut = fund_configuration_without_properties
        deps = sut.deps()

        assert len(deps) == 0
        assert deps == []

    def test_update_with_changes(self, respx_mock, fund_configuration_with_properties):
        base_url = "api/api/fundconfigurations"
        scope = "scope-fund-configuration"
        code = "code-fund-configuration"
        old_scope = "replaced-scope"
        old_code = "replaced-code"
        respx_mock.post(f"{TEST_BASE}/{base_url}/{scope}").mock(
            return_value=httpx.Response(201, json={})
        )
        respx_mock.delete(f"{TEST_BASE}/{base_url}/{old_scope}/{old_code}").mock(
            return_value=httpx.Response(200, json={})
        )

        old_state = SimpleNamespace(scope=old_scope, code=old_code, content_hash="different_hash")

        sut = fund_configuration_with_properties

        updated_state = sut.update(self.client, old_state)

        delete_request = respx_mock.calls[0].request
        post_request = respx_mock.calls[1].request
        assert delete_request.method == "DELETE"
        assert delete_request.url.path == f"/api/api/fundconfigurations/{old_scope}/{old_code}"
        assert post_request.method == "POST"
        assert post_request.url.path == f"/api/api/fundconfigurations/{scope}"
        assert updated_state is not None
        assert updated_state["content_hash"] != "different_hash"
        assert updated_state["scope"] == scope
        assert updated_state["code"] == code

    def test_update_with_no_changes(self, respx_mock, fund_configuration_with_properties):
        sut = fund_configuration_with_properties
        scope = "scope-fund-configuration"
        code = "code-fund-configuration"

        desired_state = sut.model_dump(mode="json", exclude_none=True, by_alias=True)

        sorted_desired = json.dumps(desired_state, sort_keys=True)
        from hashlib import sha256
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        old_state = SimpleNamespace(scope=scope, code=code, content_hash=content_hash)
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is None (no changes needed)
        assert state is None
        # and no HTTP requests were made
        assert len(respx_mock.calls) == 0

    def test_delete(self, respx_mock):
        base_url = "api/api/fundconfigurations"
        scope = "scope-fund-configuration"
        code = "code-fund-configuration"
        respx_mock.delete(f"{TEST_BASE}/{base_url}/{scope}/{code}").mock(
            return_value=httpx.Response(201, json={})
        )

        old_state = SimpleNamespace(scope=scope, code=code, content_hash="some_hash")

        fc.FundConfigurationResource.delete(self.client, old_state)
        assert len(respx_mock.calls) == 1
        assert respx_mock.calls[0].request.method == "DELETE"
        assert respx_mock.calls[0].request.url.path == f"/api/api/fundconfigurations/{scope}/{code}"

    def test_dump_properties_with_fund_configuration(
        self, fund_configuration_with_properties: fc.FundConfigurationResource,
        property_def: pd.DefinitionResource
    ):
        sut = fund_configuration_with_properties
        dump = sut.model_dump(by_alias=True, exclude_none=True,
                              round_trip=True, context={"style": "dump"})

        property_key = list(dump["properties"].keys())[0]
        property_value = dump["properties"][property_key]
        assert "properties" in dump
        assert len(dump["properties"]) == 1
        assert property_key == "FundConfiguration/MyPropertyScope/MyFundConfigProperty"
        assert property_value["key"] == {
            "$ref": property_def.id
        }
        assert property_value["value"]["labelValue"] == "My fund configuration property value"
        assert property_value["effectiveFrom"] == "0001-01-01T00:00:00.0000000+00:00"
        assert property_value["effectiveUntil"] == "9999-12-31T23:59:59.9999999+00:00"

        expected_body = {
            "key": {"$ref": property_def.id},
            "value": {
                "labelValue": "My fund configuration property value"
            },
            "effectiveFrom": "0001-01-01T00:00:00.0000000+00:00",
            "effectiveUntil": "9999-12-31T23:59:59.9999999+00:00"
        }
        assert property_value == expected_body

    def test_undump_properties_with_fund_configuration(self, property_def: pd.DefinitionResource):
        dump = {
            "scope": "scope-fund-configuration",
            "code": "code-fund-configuration",
            "display_name": "fund configuration display name",
            "description": "fund configuration description",
            "dealing_filters": [
                {"filter_id": "SUB", "filter": "account.code startswith '3001'"},
                {"filter_id": "RED", "filter": "account.code startswith '3002'"}
            ],
            "pnl_filters": [
                {"filter_id": "SUB", "filter": "account.code startswith '3001'"},
                {"filter_id": "RED", "filter": "account.code startswith '3002'"}
            ],
            "back_out_filters": [
                {"filter_id": "SUB", "filter": "account.code startswith '3001'"},
                {"filter_id": "RED", "filter": "account.code startswith '3002'"}
            ],
            "external_fee_filters": [
                {
                    "filter_id": "ShareClassAPnLAdjustment",
                    "filter": "account.code eq 'ShareClassAPnl'",
                    "applies_to": "PnLBucket"
                }
            ],
            "properties": [
                {
                    "key": {"$ref": property_def.id},
                    "value": {
                        "label_value": "My fund configuration property value",
                        "metric_value": None,
                        "label_set_value": None
                    },
                    "effective_from": "0001-01-01T00:00:00.0000000+00:00",
                    "effective_until": "9999-12-31T23:59:59.9999999+00:00"
                }
            ]
        }

        sut = fc.FundConfigurationResource.model_validate(dump, context={
            "style": "dump",
            "id": "template-id",
            "$refs": {p.id: p for p in [property_def]}
        })

        expected_body = {
            "scope": "scope-fund-configuration",
            "code": "code-fund-configuration",
            "display_name": "fund configuration display name",
            "description": "fund configuration description",
            "dealing_filters": [
                {"filter_id": "SUB", "filter": "account.code startswith '3001'"},
                {"filter_id": "RED", "filter": "account.code startswith '3002'"}
            ],
            "pnl_filters": [
                {"filter_id": "SUB", "filter": "account.code startswith '3001'"},
                {"filter_id": "RED", "filter": "account.code startswith '3002'"}
            ],
            "back_out_filters": [
                {"filter_id": "SUB", "filter": "account.code startswith '3001'"},
                {"filter_id": "RED", "filter": "account.code startswith '3002'"}
            ],
            "external_fee_filters": [
                {
                    "filter_id": "ShareClassAPnLAdjustment",
                    "filter": "account.code eq 'ShareClassAPnl'",
                    "applies_to": "PnLBucket"
                }
            ],
            "properties": {
                f"FundConfiguration/{property_def.scope}/{property_def.code}": {
                    "key": f"FundConfiguration/{property_def.scope}/{property_def.code}",
                    "value": {
                        "label_value": "My fund configuration property value",
                    },
                    "effective_from": "0001-01-01T00:00:00.0000000+00:00",
                    "effective_until": "9999-12-31T23:59:59.9999999+00:00"
                }
            }
        }

        actual_body = sut.model_dump(exclude_none=True, by_alias=False)

        assert actual_body == expected_body
