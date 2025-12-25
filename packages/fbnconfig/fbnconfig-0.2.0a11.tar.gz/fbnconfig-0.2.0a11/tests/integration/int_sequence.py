import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
import tests.integration.sequence as sequence
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
    deployment_name = gen("sequence")
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Cant tear down sequence resources as no api to delete


def test_create(setup_deployment):
    fbnconfig.deployex(sequence.configure(setup_deployment), lusid_env, token)
    client.get(f"/api/api/sequences/{setup_deployment.name}/seq1").json()


def test_nochange(setup_deployment):
    fbnconfig.deployex(sequence.configure(setup_deployment), lusid_env, token)
    update = fbnconfig.deployex(sequence.configure(setup_deployment), lusid_env, token)
    assert [a.change for a in update if a.type == "SequenceResource"] == ["nochange"]
