import os

import fbnconfig

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]


def test_setup():
    client = fbnconfig.create_client(lusid_env, token)
    fbnconfig.setup(client)
    # check that something is returned
    assert len(fbnconfig.list_deployments(client)) >= 0
