import copy
import json

import httpx
import pytest
from pydantic import BaseModel, Field

#
# These are not really tests, but a way of capturing how we can handle
# different client/server data behaviours using pydantic, the tests make sure it works
#
# There are a few cases:
# * a normal field that is part of the resource model on the server. Usually these are
#   required inputs and returned when you read the resource.
# * a field that we need on the resource class but isn't part of the server resource at all.
#   doesn't appear in requests or responses. The resource id (`id`) is the common case of these.
# * a field which is not controlled by the client, but calculated by the server
#   and appear in the responses. An AsAt time would be like this
# * fields the user can choose to set, but if they don't then the server calculates
#   a value for them. They might not be in the request, but will usually be in the response


class FieldTypes(BaseModel):
    # internal field that is provided by user but not sent to server
    id: str = Field(exclude=True)
    # normal field, provided by user and sent to server as-is
    data_field: str
    # something calculated on the server that the user doesn't provide (like userId or driveId)
    server_calculated: str | None = Field(None, exclude=True, init=False)
    # user can provide, but server will default if not given
    server_defaulted: str | None

    def read(self, client, old_state) -> None:
        get = client.get("/reference").json()
        get.pop("excess_field")  # field from server we don't need at all
        self._remote = get

    def create(self, client):
        desired = self.model_dump(mode="json", exclude_none=True)
        create = client.post("/reference", json=desired).json()
        self.server_calculated = create["server_calculated"]
        return {"server_calculated": self.server_calculated}

    def update(self, client, old_state):
        self.read(client, old_state)
        current = copy.deepcopy(self._remote)
        if self.server_defaulted is None:  # defaulted fields ignore if desired is None
            current.pop("server_defaulted")
        current.pop("server_calculated")  # calculated fields not compared
        desired = self.model_dump(mode="json", exclude_none=True)
        if desired == current:
            return None
        update = client.put("/reference/1", json=desired).json()
        self.server_calculated = update["server_calculated"]
        return {"server_calculated": self.server_calculated}


TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeFieldTypes:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):
        respx_mock.post("/reference").mock(
            return_value=httpx.Response(200, json={"server_calculated": 56})
        )
        sut = FieldTypes(id="123", data_field="some data", server_defaulted=None)
        new_state = sut.create(self.client)
        assert new_state["server_calculated"] == 56
        assert sut.server_calculated == 56
        request = respx_mock.calls.last.request
        assert json.loads(request.content) == {"data_field": "some data"}

    def test_update(self, respx_mock):
        respx_mock.get("/reference").mock(
            return_value=httpx.Response(
                200,
                json={
                    "server_calculated": 45,
                    "excess_field": "not needed",
                    "data_field": "other data",
                    "server_defaulted": "server default",
                },
            )
        )
        respx_mock.put("/reference/1").mock(
            return_value=httpx.Response(200, json={"server_calculated": 45})
        )
        old_state = {}
        sut = FieldTypes(id="123", data_field="some data", server_defaulted=None)
        new_state = sut.update(self.client, old_state)
        assert new_state == {"server_calculated": 45}

    def test_update_no_change(self, respx_mock):
        respx_mock.get("/reference").mock(
            return_value=httpx.Response(
                200,
                json={
                    "server_calculated": 45,
                    "excess_field": "not needed",
                    "data_field": "some data",
                    "server_defaulted": "server default",
                },
            )
        )
        old_state = {}
        sut = FieldTypes(id="123", data_field="some data", server_defaulted=None)
        new_state = sut.update(self.client, old_state)
        assert new_state is None
