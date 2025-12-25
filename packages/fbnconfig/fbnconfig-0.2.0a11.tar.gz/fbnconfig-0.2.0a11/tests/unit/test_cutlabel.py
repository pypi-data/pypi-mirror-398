import json
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import cutlabel

TEST_BASE = "https://foo.lusid.com"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeCutLabelRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/api/api/systemconfiguration/cutlabels/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = cutlabel.CutLabelRef(
            id="one",
            code="cd1"
        )
        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised
        req = respx_mock.calls[0]
        assert req.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels/cd1"

    def test_attach_when_absent(self, respx_mock):
        # given that the remote definition does not exist
        respx_mock.get("/api/api/systemconfiguration/cutlabels/cd1").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        sut = cutlabel.CutLabelRef(
            id="one",
            code="cd1"
        )
        # when we call attach
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        # then a get request was made
        req = respx_mock.calls[0]
        assert req.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels/cd1"
        # and the exception explains
        assert str(ex.value) == "CutLabel cd1 not found"

    def test_attach_when_http_error(self, respx_mock):
        # given that the remote read fails with 500
        respx_mock.get("/api/api/systemconfiguration/cutlabels/cd1").mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        sut = cutlabel.CutLabelRef(
            id="one",
            code="cd1"
        )
        # when we call attach it throws
        with pytest.raises(httpx.HTTPStatusError):
            sut.attach(client)


class DescribeCutLabelResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def get_hash(self, obj: cutlabel.CutLabelResource) -> str:
        desired = obj.model_dump(mode="json", exclude_none=True, by_alias=True)
        sorted_desired = json.dumps(desired, sort_keys=True)
        return sha256(sorted_desired.encode()).hexdigest()

    def test_read(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/api/api/systemconfiguration/cutlabels/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = cutlabel.CutLabelResource(
            id="one",
            code="cd1",
            display_name="foo",
            cut_local_time=cutlabel.CutTime(hours=1, minutes=2, seconds=3.4),
            time_zone="UTC"
        )
        # when we call read
        sut.read(client, SimpleNamespace(code="cd1"))
        # then a get request was made and no exception raised
        req = respx_mock.calls[0]
        assert req.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels/cd1"

    def test_create(self, respx_mock):
        # given that the remote definition does not exist
        respx_mock.post("/api/api/systemconfiguration/cutlabels").mock(
            return_value=httpx.Response(201, json={})
        )
        client = self.client
        sut = cutlabel.CutLabelResource(
            id="one",
            code="cd1",
            display_name="foo",
            cut_local_time=cutlabel.CutTime(hours=1, minutes=2, seconds=3.4),
            time_zone="UTC"
        )
        # when we call create
        new_state = sut.create(client)
        # then a post request was made to create the remote
        post = respx_mock.calls[0]
        assert post.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels"
        assert json.loads(post.request.content) == {
            "code": "cd1",
            "displayName": "foo",
            "cutLocalTime": {"hours": 1, "minutes": 2, "seconds": 3.4},
            "timeZone": "UTC"
        }
        # and the new state is returned
        assert new_state == {"code": "cd1", "content_hash": self.get_hash(sut)}

    def test_delete(self, respx_mock):
        # given that the remote definition exists
        respx_mock.delete("/api/api/systemconfiguration/cutlabels/cd1").mock(
            return_value=httpx.Response(204, json={})
        )
        client = self.client
        sut = cutlabel.CutLabelResource(
            id="one",
            code="cd1",
            display_name="foo",
            cut_local_time=cutlabel.CutTime(hours=1, minutes=2, seconds=3.4),
            time_zone="UTC"
        )
        # when we call delete
        sut.delete(client, SimpleNamespace(code="cd1", content_hash=self.get_hash(sut)))
        # then a delete request was made
        req = respx_mock.calls[0]
        assert req.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels/cd1"

    def test_delete_special_chars(self, respx_mock):
        # given that the remote definition exists and has a slash in the code
        respx_mock.delete("/api/api/systemconfiguration/cutlabels/cd%2F1").mock(
            return_value=httpx.Response(204, json={})
        )
        client = self.client
        # when we call delete
        cutlabel.CutLabelResource.delete(client, SimpleNamespace(code="cd/1", content_hash="whatever"))
        # then a delete request was made with the code escaped in the url
        req = respx_mock.calls[0]
        assert req.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels/cd%2F1"

    def test_update_no_change(self):
        # given the remote state has the same has as the desired state
        client = self.client
        sut = cutlabel.CutLabelResource(
            id="one",
            code="cd1",
            display_name="foo",
            cut_local_time=cutlabel.CutTime(hours=1, minutes=2, seconds=3.4),
            time_zone="UTC"
        )
        remote_state = SimpleNamespace(code="cd1", content_hash=self.get_hash(sut))
        # when we call update with no change
        new_state = sut.update(client, remote_state)
        # then no request is made and the state returned is None
        assert not new_state

    def test_update_changed_hash_only(self, respx_mock):
        # given the remote state has a different hash to the desired state
        respx_mock.put("/api/api/systemconfiguration/cutlabels/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = cutlabel.CutLabelResource(
            id="one",
            code="cd1",
            display_name="foo",
            cut_local_time=cutlabel.CutTime(hours=1, minutes=2, seconds=3.4),
            time_zone="UTC"
        )
        remote_state = SimpleNamespace(code="cd1", content_hash="old")
        # when we call update
        new_state = sut.update(client, remote_state)
        # then a put request was made
        req = respx_mock.calls[0]
        assert req.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels/cd1"
        assert req.request.method == "PUT"
        assert json.loads(req.request.content) == {
            "code": "cd1",
            "displayName": "foo",
            "cutLocalTime": {"hours": 1, "minutes": 2, "seconds": 3.4},
            "timeZone": "UTC"
        }
        # and the new state is returned with a new hash
        assert new_state == {"code": "cd1", "content_hash": self.get_hash(sut)}

    def test_update_change_local_time(self, respx_mock):
        # given the remote state has a different hash to the desired state
        respx_mock.put("/api/api/systemconfiguration/cutlabels/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = cutlabel.CutLabelResource(
            id="one",
            code="cd1",
            display_name="foo",
            cut_local_time=cutlabel.CutTime(hours=1, minutes=2, seconds=3.4),
            time_zone="UTC"
        )
        remote_state = SimpleNamespace(code="cd1", content_hash=self.get_hash(sut))
        # and the desired has a different local time
        sut.cut_local_time = cutlabel.CutTime(hours=2, minutes=3, seconds=4.5)
        # when we update
        new_state = sut.update(client, remote_state)
        # then a put request is made
        req = respx_mock.calls[0]
        assert req.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels/cd1"
        assert req.request.method == "PUT"
        assert json.loads(req.request.content) == {
            "code": "cd1",
            "displayName": "foo",
            "cutLocalTime": {"hours": 2, "minutes": 3, "seconds": 4.5},
            "timeZone": "UTC"
        }
        # and the new state is returned with a new hash
        assert new_state == {"code": "cd1", "content_hash": self.get_hash(sut)}

    def test_update_change_code(self, respx_mock):
        # given the remote state has a different code to the desired state
        respx_mock.delete("/api/api/systemconfiguration/cutlabels/oldcode").mock(
            return_value=httpx.Response(204, json={})
        )
        respx_mock.post("/api/api/systemconfiguration/cutlabels").mock(
            return_value=httpx.Response(201, json={})
        )
        client = self.client
        sut = cutlabel.CutLabelResource(
            id="one",
            code="newcode",  # This is the new desired code
            display_name="foo",
            cut_local_time=cutlabel.CutTime(hours=1, minutes=2, seconds=3.4),
            time_zone="UTC"
        )
        remote_state = SimpleNamespace(code="oldcode", content_hash="whatever")
        # when we call update
        new_state = sut.update(client, remote_state)
        # then the remote is deleted
        delete_req = respx_mock.calls[0]
        assert delete_req.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels/oldcode"
        assert delete_req.request.method == "DELETE"
        # and a new cutlabel is created
        create_req = respx_mock.calls[1]
        assert create_req.request.url == f"{TEST_BASE}/api/api/systemconfiguration/cutlabels"
        assert create_req.request.method == "POST"
        assert json.loads(create_req.request.content) == {
            "code": "newcode",
            "displayName": "foo",
            "cutLocalTime": {"hours": 1, "minutes": 2, "seconds": 3.4},
            "timeZone": "UTC"
        }
        # and the new state is returned with the new code and hash
        assert new_state == {"code": "newcode", "content_hash": self.get_hash(sut)}

    def test_deps(self):
        # when we call deps
        sut = cutlabel.CutLabelResource(
            id="one",
            code="cd1",
            display_name="foo",
            cut_local_time=cutlabel.CutTime(hours=1, minutes=2, seconds=3.4),
            time_zone="UTC"
        )
        # then it returns an empty list
        assert sut.deps() == []

    def test_dump_undump_with_id_context(self):
        # given a cutlabel resource
        sut = cutlabel.CutLabelResource(
            id="test-cutlabel",
            code="cl1",
            display_name="Test CutLabel",
            description="A test cutlabel for dump/undump",
            cut_local_time=cutlabel.CutTime(hours=17, minutes=30, seconds=0.0),
            time_zone="Europe/London"
        )
        # when we dump it
        dumped = sut.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            round_trip=True,
            context={"style": "dump"}
        )
        # then the id should be excluded from the dump
        assert "id" not in dumped
        assert dumped == {
            "code": "cl1",
            "displayName": "Test CutLabel",
            "description": "A test cutlabel for dump/undump",
            "cutLocalTime": {"hours": 17, "minutes": 30, "seconds": 0.0},
            "timeZone": "Europe/London"
        }
        # when we undump it with id from context
        result = cutlabel.CutLabelResource.model_validate(
            dumped, context={"style": "dump", "id": "context-cutlabel"}
        )
        # then it should be correctly populated including id from context
        assert result.id == "context-cutlabel"
        assert result.code == "cl1"
        assert result.display_name == "Test CutLabel"
        assert result.description == "A test cutlabel for dump/undump"
        assert result.cut_local_time.hours == 17
        assert result.cut_local_time.minutes == 30
        assert result.cut_local_time.seconds == 0.0
        assert result.time_zone == "Europe/London"
