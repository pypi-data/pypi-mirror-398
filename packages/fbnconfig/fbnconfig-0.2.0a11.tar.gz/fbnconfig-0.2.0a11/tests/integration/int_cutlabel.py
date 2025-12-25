import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import cutlabel as cl
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)


@fixture()
def base_resources(setup_deployment):
    # Create a simple cutlabel for London market
    london_cut = cl.CutLabelResource(
        id="london_cut",
        code="london-5pm",
        display_name="London 5PM Cut",
        description="London market close cut label",
        cut_local_time=cl.CutTime(hours=17, minutes=0, seconds=0.0),
        time_zone="Europe/London"
    )
    # Create a cutlabel for New York market
    ny_cut = cl.CutLabelResource(
        id="ny_cut",
        code="ny-4pm",
        display_name="New York 4PM Cut",
        description="New York market close cut label",
        cut_local_time=cl.CutTime(hours=16, minutes=0, seconds=0.0),
        time_zone="America/New_York"
    )
    # Create a cutlabel for Tokyo market
    tokyo_cut = cl.CutLabelResource(
        id="tokyo_cut",
        code="tokyo-3pm",
        display_name="Tokyo 3PM Cut",
        description="Tokyo market close cut label",
        cut_local_time=cl.CutTime(hours=15, minutes=0, seconds=0.0),
        time_zone="Asia/Tokyo"
    )
    return [london_cut, ny_cut, tokyo_cut]


@fixture(scope="module")
def setup_deployment():
    deployment_name = gen("cutlabel")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Clean up cutlabels after tests
    try:
        fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
        client.delete("/api/api/systemconfiguration/cutlabels/london-5pm")
        client.delete("/api/api/systemconfiguration/cutlabels/ny-4pm")
        client.delete("/api/api/systemconfiguration/cutlabels/tokyo-3pm")
    except Exception:
        pass  # Ignore cleanup errors


def test_create(setup_deployment, base_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # Verify London cutlabel was created
    london_response = client.get("/api/api/systemconfiguration/cutlabels/london-5pm").json()
    assert london_response["code"] == "london-5pm"
    assert london_response["displayName"] == "London 5PM Cut"
    assert london_response["description"] == "London market close cut label"
    assert london_response["cutLocalTime"]["hours"] == 17
    assert london_response["cutLocalTime"]["minutes"] == 0
    assert london_response["cutLocalTime"]["seconds"] == 0.0
    assert london_response["timeZone"] == "Europe/London"
    # Verify New York cutlabel was created
    ny_response = client.get("/api/api/systemconfiguration/cutlabels/ny-4pm").json()
    assert ny_response["code"] == "ny-4pm"
    assert ny_response["displayName"] == "New York 4PM Cut"
    assert ny_response["description"] == "New York market close cut label"
    assert ny_response["cutLocalTime"]["hours"] == 16
    assert ny_response["cutLocalTime"]["minutes"] == 0
    assert ny_response["cutLocalTime"]["seconds"] == 0.0
    assert ny_response["timeZone"] == "America/New_York"
    # Verify Tokyo cutlabel was created
    tokyo_response = client.get("/api/api/systemconfiguration/cutlabels/tokyo-3pm").json()
    assert tokyo_response["code"] == "tokyo-3pm"
    assert tokyo_response["displayName"] == "Tokyo 3PM Cut"
    assert tokyo_response["description"] == "Tokyo market close cut label"
    assert tokyo_response["cutLocalTime"]["hours"] == 15
    assert tokyo_response["cutLocalTime"]["minutes"] == 0
    assert tokyo_response["cutLocalTime"]["seconds"] == 0.0
    assert tokyo_response["timeZone"] == "Asia/Tokyo"


def test_nochange(setup_deployment, base_resources):
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we apply it again
    update = fbnconfig.deployex(deployment, lusid_env, token)
    # then there are no changes
    cutlabel_changes = [a.change for a in update if a.type == "CutLabelResource"]
    assert cutlabel_changes == ["nochange", "nochange", "nochange"]


def test_teardown(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we remove all the resources
    empty = fbnconfig.Deployment(deployment_name, [])
    update = fbnconfig.deployex(empty, lusid_env, token)
    # then all the cutlabels get removed
    cutlabel_changes = [a.change for a in update if a.type == "CutLabelResource"]
    assert cutlabel_changes == ["remove", "remove", "remove"]


def test_update(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    # Given we have deployed the base case
    initial = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(initial, lusid_env, token)
    # when we update a resource
    updated_resources = [
        # Update the London cutlabel with different time and description
        cl.CutLabelResource(
            id="london_cut",
            code="london-5pm",
            display_name="London 5:30PM Cut",  # Changed display name
            description="Updated London market close cut label",  # Changed description
            cut_local_time=cl.CutTime(hours=17, minutes=30, seconds=0.0),  # Changed time
            time_zone="Europe/London"
        ),
        # Keep NY cutlabel the same
        cl.CutLabelResource(
            id="ny_cut",
            code="ny-4pm",
            display_name="New York 4PM Cut",
            description="New York market close cut label",
            cut_local_time=cl.CutTime(hours=16, minutes=0, seconds=0.0),
            time_zone="America/New_York"
        ),
        # Keep Tokyo cutlabel the same
        cl.CutLabelResource(
            id="tokyo_cut",
            code="tokyo-3pm",
            display_name="Tokyo 3PM Cut",
            description="Tokyo market close cut label",
            cut_local_time=cl.CutTime(hours=15, minutes=0, seconds=0.0),
            time_zone="Asia/Tokyo"
        ),
    ]
    # and deploy it
    updated_deployment = fbnconfig.Deployment(deployment_name, updated_resources)  # type: ignore
    update = fbnconfig.deployex(updated_deployment, lusid_env, token)
    # then we expect only the modified resource to change
    cutlabel_changes = [a.change for a in update if a.type == "CutLabelResource"]
    assert cutlabel_changes == ["update", "nochange", "nochange"]
    # and it has the new values
    updated_response = client.get("/api/api/systemconfiguration/cutlabels/london-5pm").json()
    assert updated_response["displayName"] == "London 5:30PM Cut"
    assert updated_response["description"] == "Updated London market close cut label"
    assert updated_response["cutLocalTime"]["hours"] == 17
    assert updated_response["cutLocalTime"]["minutes"] == 30
    assert updated_response["cutLocalTime"]["seconds"] == 0.0
