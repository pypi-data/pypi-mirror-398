import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import sequence

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeSequenceResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):
        respx_mock.post("/api/api/sequences/scope-a").mock(return_value=httpx.Response(200, json={}))
        # given a desired sequence where we default the startValue
        sut = sequence.SequenceResource(
            id="xyz",
            scope="scope-a",
            code="code-a",
            increment=2,
            min_value=1,
            max_value=100,
            pattern="SQP-{{seqValue}}",
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned
        assert state == {"scope": "scope-a", "code": "code-a"}
        # and a create request was sent without the startValue
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/sequences/scope-a"
        assert json.loads(request.content) == {
            "code": "code-a",
            "increment": 2,
            "minValue": 1,
            "maxValue": 100,
            "pattern": "SQP-{{seqValue}}",
        }

    def test_update_with_no_changes(self, respx_mock):
        # given an existing sequence
        respx_mock.get("/api/api/sequences/scope-a/code-a").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": {"scope": "scope-a", "code": "code-a"},
                    "increment": 2,
                    "startValue": 1,
                    "minValue": 1,
                    "maxValue": 100,
                    "pattern": "SQP-{{seqValue}}",
                },
            )
        )
        # and a desired with increment but everything else defaulted
        sut = sequence.SequenceResource(id="seq2", scope="scope-a", code="code-a", increment=2)
        old_state = SimpleNamespace(scope="scope-a", code="code-a")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is None
        assert state is None
        # and a read was made but no PUT

    def test_update_with_changes_throws(self, respx_mock):
        # given an existing sequence
        respx_mock.get("/api/api/sequences/scope-a/code-a").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": {"scope": "scope-b", "code": "code-b"},
                    "scope": "scope-a",
                    "code": "code-a",
                    "increment": 2,
                    "startValue": 1,
                    "minValue": 1,
                    "maxValue": 100,
                    "pattern": "SQP-{{seqValue}}",
                },
            )
        )
        # and a desired with a different increment
        sut = sequence.SequenceResource(id="seq2", scope="scope-a", code="code-a", increment=200)
        old_state = SimpleNamespace(scope="scope-a", code="code-a")
        # when we update it throws
        with pytest.raises(RuntimeError):
            sut.update(self.client, old_state)

    def test_delete_throws(self):
        # given a resource that exists in the remnte
        old_state = SimpleNamespace(scope="scope-b", code="code-b")
        # when we delete it throws
        with pytest.raises(RuntimeError):
            sequence.SequenceResource.delete(self.client, old_state)

    def test_deps(self):
        sut = sequence.SequenceResource(id="xyz", scope="scope-b", code="code-b")
        # it's deps are empty
        assert sut.deps() == []

    def test_dump(self):
        # given a sequence resource
        sut = sequence.SequenceResource(
            id="seq1",
            scope="test-scope",
            code="test-code",
            increment=2,
            min_value=1,
            max_value=100,
            start=10,
            cycle=True,
            pattern="SQP-{{seqValue}}"
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then it's correctly serialized
        assert result == {
            "scope": "test-scope",
            "code": "test-code",
            "increment": 2,
            "minValue": 1,
            "maxValue": 100,
            "start": 10,
            "cycle": True,
            "pattern": "SQP-{{seqValue}}"
        }

    def test_undump(self):
        # given dump data
        data = {
            "scope": "test-scope",
            "code": "test-code",
            "increment": 2,
            "minValue": 1,
            "maxValue": 100,
            "start": 10,
            "cycle": True,
            "pattern": "SQP-{{seqValue}}"
        }
        # when we undump it
        result = sequence.SequenceResource.model_validate(
            data, context={"style": "undump", "id": "seq1"}
        )
        # then it's correctly populated
        assert result.id == "seq1"
        assert result.scope == "test-scope"
        assert result.code == "test-code"
        assert result.increment == 2
        assert result.min_value == 1
        assert result.max_value == 100
        assert result.start == 10
        assert result.cycle is True
        assert result.pattern == "SQP-{{seqValue}}"
