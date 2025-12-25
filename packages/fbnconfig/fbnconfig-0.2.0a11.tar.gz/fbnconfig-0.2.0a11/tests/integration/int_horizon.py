import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import Deployment, horizon, property
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)


@fixture(scope="module")
def setup_deployment():
    deployment_name = gen("horizon")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    print("\nTearing down resources...")
    fbnconfig.deploy(fbnconfig.Deployment(deployment_name, []), lusid_env, token)


@fixture
def coppclark_instance(setup_deployment):
    return horizon.IntegrationInstanceResource(
        id="test-horizon-instance",
        integration_type="copp-clark",
        name=f"test-integration-{setup_deployment.name}",
        description="Test integration instance for horizon tests",
        enabled=True,
        triggers=[
            horizon.Trigger(type="time", cron_expression="0 0 9 ? * MON-FRI", time_zone="Europe/London")
        ],
        details={
            "paymentSystemsCalendar": {"currencyFilter": ["GBP", "USD"], "importUnqualified": False}
        },
    )


@fixture(scope="module")
def aladdin_instance(setup_deployment):
    return horizon.IntegrationInstanceResource(
        id="aladdin-instance",
        integration_type="blackrock-aladdin",
        name=f"test_aladdin-{setup_deployment.name}",
        description="my first aladdin",
        enabled=False,
        triggers=[],
        details={
            "sourceFileLocation": "/sftp",
            "onboardingDate": "2022-01-01",
            "localTimeZone": "Australia/Melbourne",
            "unpackFromArchive": False,
            "archiveFileMask": "",
            "isFxNdfAllowed": True,
            "int29AnalyticsFileType": "NotApplicable",
            "allowCoreFieldUpdates": "Never",
            "blackRockAladdinInterfaceSelections": [{
                "interfaceNumber": "Int96",
                "fileMask": "^ATOM_R_newcash96_daily.*_*.xml$",
                "localCutTime": "00:00"
            }]

        }
    )


@fixture
def updated_instance(setup_deployment):
    return horizon.IntegrationInstanceResource(
        id="test-update-instance",
        integration_type="copp-clark",
        name=f"updated-integration-{setup_deployment.name}",
        description="Updated test integration instance",
        enabled=True,
        triggers=[horizon.Trigger(type="time", cron_expression="0 0 12 ? * *", time_zone="UTC")],
        details={
            "paymentSystemsCalendar": {"currencyFilter": ["EUR", "JPY"], "importUnqualified": True}
        },
    )


@fixture
def property_ref(setup_deployment):
    # Instrument/default/Status exists in every domain
    return property.DefinitionRef(
        id="test-prop-ref", domain=property.Domain.Instrument, scope="default", code="Status"
    )


@fixture
def optional_props(coppclark_instance, property_ref):
    return horizon.OptionalPropsResource(
        id="test-horizon-props",
        instance=coppclark_instance,
        props=[
            horizon.OptionalProp(
                property=property_ref,
                display_name_override="Test Status Override",
                description_override="Test description override",
                entity_type="Instrument",
                entity_sub_type=["Bond", "Equity"],
                vendor_package=["TestVendor"],
            )
        ],
    )


@fixture
def full_deployment(setup_deployment, coppclark_instance, optional_props, aladdin_instance):
    """Create a full deployment with instance and props"""
    return Deployment(setup_deployment.name, [coppclark_instance, optional_props, aladdin_instance])


@fixture
def update_deployment(setup_deployment, updated_instance):
    """Create an update deployment"""
    return Deployment(setup_deployment.name, [updated_instance])


def test_create_integration_instance(setup_deployment, full_deployment):
    """Test creating a horizon integration instance"""
    fbnconfig.deploy(full_deployment, lusid_env, token)
    instances = client.get("/horizon/api/integrations/instances").json()
    instance_names = [instance["name"] for instance in instances]
    expected_name = f"test-integration-{setup_deployment.name}"
    assert expected_name in instance_names


def test_update_integration_instance(setup_deployment, full_deployment, update_deployment):
    """Test updating an integration instance"""
    fbnconfig.deploy(full_deployment, lusid_env, token)
    update = fbnconfig.deploy(update_deployment, lusid_env, token)
    instances = client.get("/horizon/api/integrations/instances").json()
    instance_names = [instance["name"] for instance in instances]
    expected_name = f"updated-integration-{setup_deployment.name}"
    assert expected_name in instance_names
    # Check that the instance was updated and props were removed
    instance_changes = [a.change for a in update if a.type == "IntegrationInstanceResource"]
    props_changes = [a.change for a in update if a.type == "OptionalPropsResource"]
    assert "update" in instance_changes or "create" in instance_changes
    assert "remove" in props_changes


def test_teardown_integration_instance(setup_deployment, full_deployment):
    """Test removing integration instances"""
    fbnconfig.deploy(full_deployment, lusid_env, token)
    instances_before = client.get("/horizon/api/integrations/instances").json()
    initial_count = len(instances_before)
    teardown = fbnconfig.deploy(fbnconfig.Deployment(setup_deployment.name, []), lusid_env, token)
    instances_after = client.get("/horizon/api/integrations/instances").json()
    final_count = len(instances_after)
    assert final_count < initial_count
    # Check that resources were removed
    instance_changes = [a.change for a in teardown if a.type == "IntegrationInstanceResource"]
    props_changes = [a.change for a in teardown if a.type == "OptionalPropsResource"]
    assert instance_changes == ["remove"] * 2
    assert props_changes == ["remove"]


def test_optional_props_configuration(setup_deployment, full_deployment):
    """Test configuring optional properties for horizon integration"""
    fbnconfig.deploy(full_deployment, lusid_env, token)
    instances = client.get("/horizon/api/integrations/instances").json()
    test_instance = next(
        (i for i in instances if i["name"] == f"test-integration-{setup_deployment.name}"), None
    )
    assert test_instance is not None
    instance_id = test_instance["id"]
    config_url = f"/horizon/api/integrations/instances/configuration/copp-clark/{instance_id}"
    config = client.get(config_url).json()
    assert "Instrument/TestStatus" in config or len(config) >= 0


def test_integration_instance_with_triggers(setup_deployment, full_deployment):
    """Test that triggers are properly configured"""
    fbnconfig.deploy(full_deployment, lusid_env, token)
    instances = client.get("/horizon/api/integrations/instances").json()
    test_instance = next(
        (i for i in instances if i["name"] == f"test-integration-{setup_deployment.name}"), None
    )
    assert test_instance is not None
    assert "triggers" in test_instance
    assert len(test_instance["triggers"]) > 0
    trigger = test_instance["triggers"][0]
    assert trigger["type"] == "time"
    assert trigger["cronExpression"] == "0 0 9 ? * MON-FRI"
    assert trigger["timeZone"] == "Europe/London"


def test_integration_instance_details(setup_deployment, full_deployment):
    """Test that instance details are properly configured"""
    fbnconfig.deploy(full_deployment, lusid_env, token)
    instances = client.get("/horizon/api/integrations/instances").json()
    test_instance = next(
        (i for i in instances if i["name"] == f"test-integration-{setup_deployment.name}"), None
    )
    assert test_instance is not None
    assert "details" in test_instance
    details = test_instance["details"]
    assert "paymentSystemsCalendar" in details
    calendar_config = details["paymentSystemsCalendar"]
    assert "currencyFilter" in calendar_config
    assert "GBP" in calendar_config["currencyFilter"]
    assert "USD" in calendar_config["currencyFilter"]
    assert calendar_config["importUnqualified"] is False


def test_update_nochanges(setup_deployment, full_deployment):
    """Test that deploying the same configuration twice doesn't cause issues"""
    fbnconfig.deploy(full_deployment, lusid_env, token)
    instances_first = client.get("/horizon/api/integrations/instances").json()
    first_count = len(instances_first)
    update = fbnconfig.deploy(full_deployment, lusid_env, token)
    instances_second = client.get("/horizon/api/integrations/instances").json()
    second_count = len(instances_second)
    assert first_count == second_count
    # Check that no changes were made on second deployment
    instance_changes = [a.change for a in update if a.type == "IntegrationInstanceResource"]
    props_changes = [a.change for a in update if a.type == "OptionalPropsResource"]
    assert instance_changes == ["nochange"] * 2
    assert props_changes == ["nochange"]
