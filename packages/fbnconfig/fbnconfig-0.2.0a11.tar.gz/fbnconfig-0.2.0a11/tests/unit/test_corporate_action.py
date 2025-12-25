import json
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig.corporate_action import CorporateActionSourceResource

TEST_BASE = "https://foo.lusid.com"


class DescribeCorporateActionSourceResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def get_hash(self, obj: CorporateActionSourceResource) -> str:
        desired = obj.model_dump(mode="json", exclude_none=True, by_alias=True)
        sorted_desired = json.dumps(desired, sort_keys=True)
        return sha256(sorted_desired.encode()).hexdigest()

    def test_create_minimal(self, respx_mock):
        respx_mock.post("/api/api/corporateactionsources").mock(
            return_value=httpx.Response(201, json={})
        )
        client = self.client
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source"
        )
        new_state = sut.create(client)
        post = respx_mock.calls[0]
        assert post.request.url == f"{TEST_BASE}/api/api/corporateactionsources"
        assert json.loads(post.request.content) == {
            "scope": "test",
            "code": "ca1",
            "displayName": "Test Corporate Action Source"
        }
        assert new_state == {"scope": "test", "code": "ca1", "content_hash": self.get_hash(sut)}

    def test_create_with_description_and_instrument_scopes(self, respx_mock):
        respx_mock.post("/api/api/corporateactionsources").mock(
            return_value=httpx.Response(201, json={})
        )
        client = self.client
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source",
            description="A test corporate action source",
            instrument_scopes=["default"]
        )
        new_state = sut.create(client)
        post = respx_mock.calls[0]
        assert json.loads(post.request.content) == {
            "scope": "test",
            "code": "ca1",
            "displayName": "Test Corporate Action Source",
            "description": "A test corporate action source",
            "instrumentScopes": ["default"]
        }
        assert new_state == {"scope": "test", "code": "ca1", "content_hash": self.get_hash(sut)}

    def test_instrument_scopes_validation_none_allowed(self):
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source",
            instrument_scopes=None
        )
        assert sut.instrument_scopes is None

    def test_instrument_scopes_validation_empty_list_allowed(self):
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source",
            instrument_scopes=[]
        )
        assert sut.instrument_scopes == []

    def test_instrument_scopes_validation_single_element_allowed(self):
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source",
            instrument_scopes=["default"]
        )
        assert sut.instrument_scopes == ["default"]

    def test_instrument_scopes_validation_multiple_elements_rejected(self):
        with pytest.raises(ValueError, match="instrument_scopes can have at most one element"):
            CorporateActionSourceResource(
                id="test_ca",
                scope="test",
                code="ca1",
                display_name="Test Corporate Action Source",
                instrument_scopes=["default", "test"]
            )

    def test_read(self, respx_mock):
        respx_mock.get("/api/api/corporateactionsources").mock(
            return_value=httpx.Response(200, json={
                "values": [{
                    "id": {"scope": "test", "code": "ca1"},
                    "displayName": "Test Corporate Action Source",
                    "instrumentScopes": ["default"]
                }]
            })
        )
        client = self.client
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source"
        )
        result = sut.read(client, SimpleNamespace(scope="test", code="ca1"))
        req = respx_mock.calls[0]
        assert req.request.url.path == "/api/api/corporateactionsources"
        assert req.request.url.query == b"filter=id.scope+eq+%27test%27+and+id.code+eq+%27ca1%27"
        assert result and result["id"]
        assert result["id"]["scope"] == "test"
        assert result["id"]["code"] == "ca1"

    def test_read_not_found(self, respx_mock):
        respx_mock.get("/api/api/corporateactionsources").mock(
            return_value=httpx.Response(200, json={"values": []})
        )
        client = self.client
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source"
        )
        result = sut.read(client, SimpleNamespace(scope="test", code="ca1"))
        assert result is None

    def test_delete(self, respx_mock):
        respx_mock.delete("/api/api/corporateactionsources/test/ca1").mock(
            return_value=httpx.Response(204, json={})
        )
        client = self.client
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source"
        )
        sut.delete(client, SimpleNamespace(scope="test", code="ca1"))
        req = respx_mock.calls[0]
        assert req.request.url == f"{TEST_BASE}/api/api/corporateactionsources/test/ca1"

    def test_update_no_change(self):
        client = self.client
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source"
        )
        remote_state = SimpleNamespace(scope="test", code="ca1", content_hash=self.get_hash(sut))
        new_state = sut.update(client, remote_state)
        assert not new_state

    def test_update_with_change(self, respx_mock):
        respx_mock.delete("/api/api/corporateactionsources/test/ca1").mock(
            return_value=httpx.Response(204, json={})
        )
        respx_mock.post("/api/api/corporateactionsources").mock(
            return_value=httpx.Response(201, json={})
        )
        client = self.client
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Updated Corporate Action Source",
            description="Updated description"
        )
        remote_state = SimpleNamespace(scope="test", code="ca1", content_hash="old_hash")
        new_state = sut.update(client, remote_state)
        delete_req = respx_mock.calls[0]
        assert delete_req.request.url == f"{TEST_BASE}/api/api/corporateactionsources/test/ca1"
        assert delete_req.request.method == "DELETE"
        create_req = respx_mock.calls[1]
        assert create_req.request.url == f"{TEST_BASE}/api/api/corporateactionsources"
        assert create_req.request.method == "POST"
        assert json.loads(create_req.request.content) == {
            "scope": "test",
            "code": "ca1",
            "displayName": "Updated Corporate Action Source",
            "description": "Updated description"
        }
        assert new_state == {"scope": "test", "code": "ca1", "content_hash": self.get_hash(sut)}

    def test_deps(self):
        sut = CorporateActionSourceResource(
            id="test_ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source"
        )
        assert sut.deps() == []

    def test_model_validation_from_dict_with_id_object(self):
        data = {
            "id": {"scope": "test", "code": "ca1"},
            "displayName": "Test Corporate Action Source",
            "description": "A test source",
            "instrumentScopes": ["default"]
        }
        sut = CorporateActionSourceResource.model_validate(data, context={"id": "test_ca"})
        assert sut.id == "test_ca"
        assert sut.scope == "test"
        assert sut.code == "ca1"
        assert sut.display_name == "Test Corporate Action Source"
        assert sut.description == "A test source"
        assert sut.instrument_scopes == ["default"]

    def test_dump_undump_with_id_context(self):
        sut = CorporateActionSourceResource(
            id="test-ca",
            scope="test",
            code="ca1",
            display_name="Test Corporate Action Source",
            description="A test corporate action source",
            instrument_scopes=["default"]
        )
        dumped = sut.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            round_trip=True,
            context={"style": "dump"}
        )
        assert "id" not in dumped
        assert dumped == {
            "scope": "test",
            "code": "ca1",
            "displayName": "Test Corporate Action Source",
            "description": "A test corporate action source",
            "instrumentScopes": ["default"]
        }
        result = CorporateActionSourceResource.model_validate(
            dumped, context={"style": "dump", "id": "context-ca"}
        )
        assert result.id == "context-ca"
        assert result.scope == "test"
        assert result.code == "ca1"
        assert result.display_name == "Test Corporate Action Source"
        assert result.description == "A test corporate action source"
        assert result.instrument_scopes == ["default"]
