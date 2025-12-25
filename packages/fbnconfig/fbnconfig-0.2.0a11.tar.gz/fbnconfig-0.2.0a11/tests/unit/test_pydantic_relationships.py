import json
from typing import Any, Dict

import httpx
import pytest
from pydantic import BaseModel, Field, field_serializer

#
# Not really a test, this shows how to handle the case where
# we want to reference another resource. The user passes in the
# actual resource but when we send we only want to refer to it's
# identifiers.


# Mock/fake resource that will be referenced by another resource
# we pretend that unique_id is a server calculated value
class StubResource(BaseModel):
    id: str = Field(exclude=True)
    scope: str
    code: str
    unique_id: int = Field(None, exclude=True, init=False)

    def read(self):
        self.unique_id = 2345


# a resource that depends on another resource
class UsesAnotherResource(BaseModel):
    id: str = Field(exclude=True)
    # object field which is passed to init but only it's id is sent to the server
    referenced: StubResource = Field(serialization_alias="referencedId")
    _remote: None | Dict[str, Any] = None

    # only send the identifier part of the referenced resource
    @field_serializer("referenced", when_used="always")
    def serialize_job(self, ref: StubResource):
        return ref.unique_id

    def read(self, client, old_state):
        self._remote = client.get("/uses/1").json()

    def create(self, client):
        # use by_alias to call output "referencedId"
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        client.post("/uses", json=desired).json()
        return {}


TEST_BASE = "https://foo.lusid.com"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeUses:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda r: r.raise_for_status()]})

    def test_create(self, respx_mock):
        respx_mock.post("/uses").mock(return_value=httpx.Response(200, json={}))
        # given a stub resource and a uses
        stub = StubResource(id="stub1", scope="default", code="code1")
        sut = UsesAnotherResource(id="uses1", referenced=stub)
        # and the stub has been (fake) created on the remote
        stub.read()
        # when we create the uses
        sut.create(self.client)
        # then the unique_id of the referenced object gets sent
        # and the alias referenceId gets used as the key
        request = respx_mock.calls.last.request
        assert json.loads(request.content) == {"referencedId": 2345}
