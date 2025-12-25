import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import workspace

TEST_BASE = "https://foo.lusid.com"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeWorkspaceResource:
    client = httpx.Client(
        base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]}
    )

    def test_create(self, respx_mock):
        respx_mock.post("/api/api/workspaces/personal").mock(return_value=httpx.Response(200, json={}))
        # given no workspace exists
        sut = workspace.WorkspaceResource(
            id="wk1",
            visibility=workspace.Visibility.PERSONAL,
            description="a test workspace",
            name="workspace1",
        )
        # when we call create
        new_state = sut.create(self.client)
        # then a post request is made
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/workspaces/personal"
        assert json.loads(request.content) == {
            "name": "workspace1",
            "description": "a test workspace",
        }
        # and the new state is returned
        assert new_state == {
            "visibility": "personal",
            "name": "workspace1",
            "content_hash": "55b0645f9146503f4bf66d88b85603a2ea8081b1272f2a1c1fb7bae84a0c209d",
        }

    def test_create_conflict(self, respx_mock):
        respx_mock.post("/api/api/workspaces/personal").mock(return_value=httpx.Response(429, json={}))
        # given a workspace with this name already exists
        sut = workspace.WorkspaceResource(
            id="wk1",
            visibility=workspace.Visibility.PERSONAL,
            description="a test workspace",
            name="workspace1",
        )
        # when we call create we get an exception
        with pytest.raises(httpx.HTTPError):
            sut.create(self.client)

    def test_delete(self, respx_mock):
        respx_mock.delete("/api/api/workspaces/personal/workspace1").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        # given an existing workspace
        # when we delete it
        old_state = SimpleNamespace(visibility="personal", name="workspace1", content_hash="xxxx")
        workspace.WorkspaceResource.delete(self.client, old_state)
        # then a delete request is made
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/api/api/workspaces/personal/workspace1"

    def test_deps(self):
        # given a workspace
        sut = workspace.WorkspaceResource(
            id="wk1",
            visibility=workspace.Visibility.PERSONAL,
            description="a test workspace",
            name="workspace1",
        )
        # it has no deps
        assert sut.deps() == []

    def test_read_exists(self, respx_mock):
        # given the workspace exists
        respx_mock.get("/api/api/workspaces/shared/workspace1").mock(
            return_value=httpx.Response(200, json={
                "name": "workspace1",
                "description": "a test workspace",
                "version": {"stuff": 1},
                "links": {"stuff": 2},
            })
        )
        sut = workspace.WorkspaceResource(
            id="wk1",
            visibility=workspace.Visibility.PERSONAL,
            description="not the same",
            name="workspace1",
        )
        # when we read it
        old_state = SimpleNamespace(visibility="shared", name="workspace1")
        res = sut.read(self.client, old_state)
        # then the links and version fields are removed
        assert res == {
            "name": "workspace1",
            "description": "a test workspace",
        }

    def test_update_same_hash(self):
        # given the desired resource has not changed (same hash as last time)
        sut = workspace.WorkspaceResource(
            id="wk1",
            visibility=workspace.Visibility.PERSONAL,
            description="a test workspace",
            name="workspace1",
        )
        old_state = SimpleNamespace(
            visibility="personal",
            name="workspace1",
            content_hash="55b0645f9146503f4bf66d88b85603a2ea8081b1272f2a1c1fb7bae84a0c209d",
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then the hash check matches, no request is made and None is returned
        assert new_state is None

    def test_update_description(self, respx_mock):
        respx_mock.put("/api/api/workspaces/personal/workspace1").mock(
            return_value=httpx.Response(200, json={})
        )
        # given the desired resource has modified only the description
        sut = workspace.WorkspaceResource(
            id="wk1",
            visibility=workspace.Visibility.PERSONAL,
            description="a new description",
            name="workspace1",
        )
        old_state = SimpleNamespace(
            visibility="personal",
            name="workspace1",
            content_hash="55b0645f9146503f4bf66d88b85603a2ea8081b1272f2a1c1fb7bae84a0c209d",
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then a put request is made to update the description
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/api/api/workspaces/personal/workspace1"
        assert json.loads(request.content) == {
            "name": "workspace1",
            "description": "a new description",
        }
        # and the new state is returned with a new hash
        assert new_state == {
            "visibility": "personal",
            "name": "workspace1",
            "content_hash": "c69f472de0c5e825760d4b216e321454028433fe9ee41d584f171b5a7ea3b1c2",
        }

    def test_update_name(self, respx_mock):
        respx_mock.delete("/api/api/workspaces/personal/workspace1").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        respx_mock.post("/api/api/workspaces/personal").mock(
            return_value=httpx.Response(200, json={})
        )
        # given the desired name has changed from workspace1 to workspace2
        sut = workspace.WorkspaceResource(
            id="wk1",
            visibility=workspace.Visibility.PERSONAL,
            description="a test workspace",
            name="workspace2",
        )
        old_state = SimpleNamespace(
            visibility="personal",
            name="workspace1",
            content_hash="55b0645f9146503f4bf66d88b85603a2ea8081b1272f2a1c1fb7bae84a0c209d",
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then a post request creates the workspace with a new name
        request1 = respx_mock.calls[0].request
        assert request1.method == "POST"
        assert request1.url.path == "/api/api/workspaces/personal"
        assert json.loads(request1.content) == {
            "name": "workspace2",
            "description": "a test workspace",
        }
        # and a delete request is made to remove the existing name
        request2 = respx_mock.calls[1].request
        assert request2.method == "DELETE"
        assert request2.url.path == "/api/api/workspaces/personal/workspace1"
        # and the new state is returned with a new hash
        assert new_state == {
            "visibility": "personal",
            "name": "workspace2",
            "content_hash": "8a6fee24a682ea3d6995a93fdc1f2caabcc0b2e0bb9bcc90195aef036ff8406e",
        }

    def test_update_visibility(self, respx_mock):
        respx_mock.delete("/api/api/workspaces/personal/workspace1").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        respx_mock.post("/api/api/workspaces/shared").mock(
            return_value=httpx.Response(200, json={})
        )
        # given the desired visibility has changed from personal to shared
        sut = workspace.WorkspaceResource(
            id="wk1",
            visibility=workspace.Visibility.SHARED,
            description="a test workspace",
            name="workspace1",
        )
        old_state = SimpleNamespace(
            visibility="personal",
            name="workspace1",
            content_hash="55b0645f9146503f4bf66d88b85603a2ea8081b1272f2a1c1fb7bae84a0c209d",
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then a post request creates the workspace in shared
        request1 = respx_mock.calls[0].request
        assert request1.method == "POST"
        assert request1.url.path == "/api/api/workspaces/shared"
        assert json.loads(request1.content) == {
            "name": "workspace1",
            "description": "a test workspace",
        }
        # then a delete request is made to remove the existing name
        request2 = respx_mock.calls[1].request
        assert request2.method == "DELETE"
        assert request2.url.path == "/api/api/workspaces/personal/workspace1"
        # and the new state is returned with the same hash because content hasn't changed
        assert new_state == {
            "visibility": "shared",
            "name": "workspace1",
            "content_hash": "55b0645f9146503f4bf66d88b85603a2ea8081b1272f2a1c1fb7bae84a0c209d",
        }

    def test_dump_simple_workspace(self):
        # given a simple workspace resource
        sut = workspace.WorkspaceResource(
            id="dump-workspace",
            visibility=workspace.Visibility.PERSONAL,
            name="DumpWorkspace",
            description="A test workspace for dumping"
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then all fields are included (no excludes)
        expected = {
            "visibility": "personal",
            "name": "DumpWorkspace",
            "description": "A test workspace for dumping"
        }
        assert result == expected

    def test_undump_simple_workspace(self):
        # given dump data
        data = {
            "visibility": "shared",
            "name": "UndumpWorkspace",
            "description": "A test workspace for undumping"
        }
        # when we undump it with id from context
        result = workspace.WorkspaceResource.model_validate(
            data, context={"style": "dump", "id": "workspace_id"}
        )
        # then it's correctly populated including id from context
        assert result.id == "workspace_id"
        assert result.visibility == workspace.Visibility.SHARED
        assert result.name == "UndumpWorkspace"
        assert result.description == "A test workspace for undumping"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeWorkspaceRef:
    client = httpx.Client(
        base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]}
    )

    def test_attach_when_present(self, respx_mock):
        # given that the remote exists
        respx_mock.get("/api/api/workspaces/shared/workspace1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = workspace.WorkspaceRef(
            id="wk1",
            visibility=workspace.Visibility.SHARED,
            name="workspace1",
        )
        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/api/api/workspaces/shared/workspace1").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        sut = workspace.WorkspaceRef(
            id="wk1",
            visibility=workspace.Visibility.SHARED,
            name="workspace1",
        )
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Workspace shared/workspace1 not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/api/api/workspaces/shared/workspace1").mock(
            return_value=httpx.Response(400, json={})
        )
        client = self.client
        sut = workspace.WorkspaceRef(
            id="wk1",
            visibility=workspace.Visibility.SHARED,
            name="workspace1",
        )
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeWorkspaceItemRef:
    client = httpx.Client(
        base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]}
    )

    def test_attach_with_workspace_resource(self, respx_mock):
        # given that the remote exists
        respx_mock.get("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        wksp = workspace.WorkspaceResource(
            id="wk1",
            visibility=workspace.Visibility.SHARED,
            name="workspace1",
            description="a test workspace",
        )
        sut = workspace.WorkspaceItemRef(
            id="wk1",
            name="item1",
            group="group1",
            workspace=wksp,
        )
        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_with_workspace_ref(self, respx_mock):
        # given that the remote exists
        respx_mock.get("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        wksp = workspace.WorkspaceRef(
            id="wk1",
            visibility=workspace.Visibility.SHARED,
            name="workspace1",
        )
        sut = workspace.WorkspaceItemRef(
            id="wk1",
            name="item1",
            group="group1",
            workspace=wksp,
        )
        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        wksp = workspace.WorkspaceRef(
            id="wk1",
            visibility=workspace.Visibility.SHARED,
            name="workspace1",
        )
        sut = workspace.WorkspaceItemRef(
            id="wk1",
            name="item1",
            group="group1",
            workspace=wksp,
        )
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Workspace item shared/workspace1/items/group1/item1 not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            return_value=httpx.Response(400, json={})
        )
        client = self.client
        wksp = workspace.WorkspaceRef(
            id="wk1",
            visibility=workspace.Visibility.SHARED,
            name="workspace1",
        )
        sut = workspace.WorkspaceItemRef(
            id="wk1",
            name="item1",
            group="group1",
            workspace=wksp,
        )
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeWorkspaceItemResource:
    client = httpx.Client(
        base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]}
    )

    @pytest.fixture
    def workspace1(self):
        return workspace.WorkspaceRef(
            id="wk1",
            visibility=workspace.Visibility.SHARED,
            name="workspace1",
        )

    @pytest.fixture
    def workspace2(self):
        return workspace.WorkspaceRef(
            id="wk1",
            visibility=workspace.Visibility.PERSONAL,
            name="workspace2",
        )

    def test_create(self, respx_mock, workspace1):
        respx_mock.post("/api/api/workspaces/shared/workspace1/items").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a workspace but no item1
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace1,
            type="type1",
            group="group1",
            format=2,
            description="a test item",
            name="item1",
            content={"key1": "value1", "key2": True, "key3": 42}
        )
        # when we call create
        new_state = sut.create(self.client)
        # then a post request is made
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/workspaces/shared/workspace1/items"
        assert json.loads(request.content) == {
            "name": "item1",
            "description": "a test item",
            "format": 2,
            "group": "group1",
            "content": {"key1": "value1", "key2": True, "key3": 42},
            "type": "type1",
        }
        # and the new state is returned
        assert new_state == {
            "visibility": "shared",
            "name": "item1",
            "group": "group1",
            "workspace_name": "workspace1",
            "content_hash": "d7875024b7d17597c4779da2097b221b73fd30d86891376f3762b7433ecbedfa",
        }

    def test_create_conflict(self, respx_mock, workspace1):
        # given an item already exists
        respx_mock.post("/api/api/workspaces/shared/workspace1/items").mock(
            return_value=httpx.Response(429, json={})
        )
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace1,
            type="type1",
            group="group1",
            format=2,
            description="a test item",
            name="item1",
            content={"key1": "value1", "key2": True, "key3": 42}
        )
        # when we call create we get an exception
        with pytest.raises(httpx.HTTPError):
            sut.create(self.client)

    def test_delete(self, respx_mock):
        respx_mock.delete("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        # given an existing item
        old_state = SimpleNamespace(
            name="item1",
            group="group1",
            visibility="shared",
            workspace_name="workspace1",
            content_hash="xxxx"
        )
        # when we delete it
        workspace.WorkspaceItemResource.delete(self.client, old_state)
        # then a delete request is made
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/api/api/workspaces/shared/workspace1/items/group1/item1"

    def test_deps_ref(self):
        # given an item that depends on a workspace ref
        ref = workspace.WorkspaceRef(
            id="ref1",
            visibility=workspace.Visibility.PERSONAL,
            name="ref1",
        )
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=ref,
            type="type1",
            group="group1",
            format=2,
            description="a test item",
            name="item1",
            content={"key1": "value1", "key2": True, "key3": 42}
        )
        # it's deps include the workspace
        assert sut.deps() == [ref]

    def test_deps_workspace(self, workspace1):
        # given an item that depends on a workspace
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace1,
            type="type1",
            group="group1",
            format=2,
            description="a test item",
            name="item1",
            content={"key1": "value1", "key2": True, "key3": 42}
        )
        # it's deps include the workspace
        assert sut.deps() == [workspace1]

    def test_read_exists(self, respx_mock, workspace2):
        # given the workspace tem exists
        respx_mock.get("/api/api/workspaces/personal/workspace2/items/group1/item1").mock(
            return_value=httpx.Response(200, json={
                "name": "item1",
                "group": "group1",
                "format": 2,
                "content": {},
                "description": "a test item",
                "version": {"stuff": 1},
                "links": {"stuff": 2},
            })
        )
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace2,
            type="type1",
            group="group1",
            format=2,
            description="a test item",
            name="item1",
            content={}
        )
        # when we read it
        old_state = SimpleNamespace(
            visibility="personal",
            name="item1",
            workspace_name="workspace2",
            group="group1",
        )
        res = sut.read(self.client, old_state)
        # then the links and version fields are removed
        assert res == {
            "name": "item1",
            "group": "group1",
            "description": "a test item",
            "format": 2,
            "content": {},
        }

    def test_update_same_hash(self, workspace1):
        # given the desired resource has not changed (same hash as last time)
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace1,
            type="type1",
            description="a test item",
            name="item1",
            group="group1",
            format=3,
            content={"key1": "value1", "key2": True, "key3": 42},
        )
        old_state = SimpleNamespace(
            visibility=workspace1.visibility,
            name="item1",
            group="group1",
            workspace_name=workspace1.name,
            content_hash="21368e5f74f8fa8651d55f88d48ba651e3e8f0c105eb674e1151358921b7abaa",
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then the hash check matches, no request is made and None is returned
        assert new_state is None

    def test_update_move_workspace(self, respx_mock, workspace2):
        respx_mock.delete("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/api/api/workspaces/personal/workspace2/items").mock(
            return_value=httpx.Response(200, json={})
        )
        # given the desired resource changes from workspace1 to workspace2
        # but the item has not changed
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace2,
            type="type1",
            description="a test item",
            name="item1",
            group="group1",
            format=3,
            content={"key1": "value1", "key2": True, "key3": 42},
        )
        old_state = SimpleNamespace(
            visibility="shared",
            name="item1",
            group="group1",
            workspace_name="workspace1",
            content_hash="21368e5f74f8fa8651d55f88d48ba651e3e8f0c105eb674e1151358921b7abaa",
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then a new one is created
        request1 = respx_mock.calls[0].request
        assert json.loads(request1.content) == {
            "name": "item1",
            "description": "a test item",
            "format": 3,
            "group": "group1",
            "content": {"key1": "value1", "key2": True, "key3": 42},
            "type": "type1",
        }
        # and the existing item is deleted
        request2 = respx_mock.calls[1].request
        assert request2.method == "DELETE"
        assert request2.url.path == "/api/api/workspaces/shared/workspace1/items/group1/item1"
        # and the new state is returned with the same hash
        assert new_state == {
            "visibility": "personal",
            "name": "item1",
            "workspace_name": "workspace2",
            "group": "group1",
            "content_hash": "21368e5f74f8fa8651d55f88d48ba651e3e8f0c105eb674e1151358921b7abaa",
        }

    def test_update_move_workspace_failure(self, respx_mock, workspace2):
        # given we need to move the item to another workspace
        # but creation of the new one fails
        respx_mock.post("/api/api/workspaces/personal/workspace2/items").mock(
            return_value=httpx.Response(400, json={})
        )
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace2,
            type="type1",
            description="a test item",
            name="item1",
            group="group1",
            format=3,
            content={"key1": "value1", "key2": True, "key3": 42},
        )
        old_state = SimpleNamespace(
            visibility="shared",
            name="item1",
            group="group1",
            workspace_name="workspace1",
            content_hash="21368e5f74f8fa8651d55f88d48ba651e3e8f0c105eb674e1151358921b7abaa",
        )
        # when we call update it raises and no delete call is made
        with pytest.raises(httpx.HTTPError):
            sut.update(self.client, old_state)

    def test_update_rename_item(self, respx_mock, workspace1):
        respx_mock.delete("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/api/api/workspaces/shared/workspace1/items").mock(
            return_value=httpx.Response(200, json={})
        )
        # given the desired resource changes it's name
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace1,
            type="type1",
            description="a test item",
            name="item_renamed",
            group="group1",
            format=3,
            content={"key1": "value1", "key2": True, "key3": 42},
        )
        old_state = SimpleNamespace(
            visibility="shared",
            name="item1",
            group="group1",
            workspace_name="workspace1",
            content_hash="21368e5f74f8fa8651d55f88d48ba651e3e8f0c105eb674e1151358921b7abaa",
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then a new one is created
        request1 = respx_mock.calls[0].request
        assert json.loads(request1.content) == {
            "name": "item_renamed",
            "description": "a test item",
            "format": 3,
            "group": "group1",
            "content": {"key1": "value1", "key2": True, "key3": 42},
            "type": "type1",
        }
        # and the existing item is deleted
        request2 = respx_mock.calls[1].request
        assert request2.method == "DELETE"
        assert request2.url.path == "/api/api/workspaces/shared/workspace1/items/group1/item1"
        # and the new state is returned with a new hash
        assert new_state == {
            "visibility": "shared",
            "name": "item_renamed",
            "workspace_name": "workspace1",
            "group": "group1",
            "content_hash": "715e9305b154ce58b460f848ac0e65f7fc25657e0375c28b7a7843381c1df638",
        }

    def test_update_change_group(self, respx_mock, workspace1):
        respx_mock.delete("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/api/api/workspaces/shared/workspace1/items").mock(
            return_value=httpx.Response(200, json={})
        )
        # given the desired resource is in a different group
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace1,
            type="type1",
            description="a test item",
            name="item_renamed",
            group="group2",
            format=3,
            content={"key1": "value1", "key2": True, "key3": 42},
        )
        old_state = SimpleNamespace(
            visibility="shared",
            name="item1",
            group="group1",
            workspace_name="workspace1",
            content_hash="21368e5f74f8fa8651d55f88d48ba651e3e8f0c105eb674e1151358921b7abaa",
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then a new one is created
        request1 = respx_mock.calls[0].request
        assert json.loads(request1.content) == {
            "name": "item_renamed",
            "description": "a test item",
            "format": 3,
            "group": "group2",
            "content": {"key1": "value1", "key2": True, "key3": 42},
            "type": "type1",
        }
        # and the existing item is deleted
        request2 = respx_mock.calls[1].request
        assert request2.method == "DELETE"
        assert request2.url.path == "/api/api/workspaces/shared/workspace1/items/group1/item1"
        # and the new state is returned with a new hash
        assert new_state == {
            "visibility": "shared",
            "name": "item_renamed",
            "workspace_name": "workspace1",
            "group": "group2",
            "content_hash": "e348d17261f9b7d35c52e15f3b40d7aa220b0fd23d56415651721c269c088fd5",
        }

    def test_update_change_content(self, respx_mock, workspace1):
        respx_mock.put("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            return_value=httpx.Response(200, json={})
        )
        # given the desired resource changes the content of the item
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace1,
            type="type1",
            description="a test item",
            name="item1",
            group="group1",
            format=3,
            content={"key1": "value_changed", "key2": True, "key3": 42},
        )
        old_state = SimpleNamespace(
            visibility="shared",
            name="item1",
            group="group1",
            workspace_name="workspace1",
            content_hash="21368e5f74f8fa8651d55f88d48ba651e3e8f0c105eb674e1151358921b7abaa",
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then the existing item is updated
        request1 = respx_mock.calls[0].request
        assert json.loads(request1.content) == {
            "name": "item1",
            "description": "a test item",
            "format": 3,
            "group": "group1",
            "content": {"key1": "value_changed", "key2": True, "key3": 42},
            "type": "type1",
        }
        # and the new state is returned with a new hash
        assert new_state == {
            "visibility": "shared",
            "name": "item1",
            "workspace_name": "workspace1",
            "group": "group1",
            "content_hash": "39a57eb19bae4c013829d9cc5be72d9796a44edbd2b15d4044b691321ee6e5a7",
        }

    def test_update_no_hash_on_existing(self, respx_mock, workspace1):
        respx_mock.put("/api/api/workspaces/shared/workspace1/items/group1/item1").mock(
            return_value=httpx.Response(200, json={})
        )
        # given the desired resource is the same as the remote
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace1,
            type="type1",
            description="a test item",
            name="item1",
            group="group1",
            format=3,
            content={"key1": "value1", "key2": True, "key3": 42},
        )
        # but the remote is from an old version without hashing
        old_state = SimpleNamespace(
            visibility="shared",
            name="item1",
            group="group1",
            workspace_name="workspace1"
        )
        # when we call update
        new_state = sut.update(self.client, old_state)
        # then the existing item is updated
        request1 = respx_mock.calls[0].request
        assert json.loads(request1.content) == {
            "name": "item1",
            "description": "a test item",
            "format": 3,
            "group": "group1",
            "content": {"key1": "value1", "key2": True, "key3": 42},
            "type": "type1",
        }
        # and the new state is returned with a new hash
        assert new_state == {
            "visibility": "shared",
            "name": "item1",
            "workspace_name": "workspace1",
            "group": "group1",
            "content_hash": "21368e5f74f8fa8651d55f88d48ba651e3e8f0c105eb674e1151358921b7abaa",
        }

    def test_dump_item(self, workspace1):
        # given an item resource referencing a workspace resource
        sut = workspace.WorkspaceItemResource(
            id="item1",
            workspace=workspace1,
            type="type1",
            description="a test item",
            name="item1",
            group="group1",
            format=3,
            content={"key1": "value1", "key2": True, "key3": 42},
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then the dumped has the workspace as a $ref
        assert dumped == {
            "name": "item1",
            "workspace": {"$ref": "wk1"},
            "type": "type1",
            "description": "a test item",
            "group": "group1",
            "format": 3,
            "content": {"key1": "value1", "key2": True, "key3": 42},
        }

    def test_undump_item(self):
        workspace_ref = workspace.WorkspaceRef(
            id="wrkref",
            visibility=workspace.Visibility.SHARED,
            name="workspace5"
        )
        # given the dumped form of an item
        dumped = {
            "name": "item1",
            "workspace": {"$ref": "wrkref"},
            "type": "type1",
            "description": "a test item",
            "group": "group1",
            "format": 3,
            "content": {"key1": "value1", "key2": True, "key3": 42},
        }
        # when we deserialize it
        result = workspace.WorkspaceItemResource.model_validate(
            dumped,
            context={
                "style": "dump",
                "$refs": {
                    "wrkref": workspace_ref
                },
                "id": "item_id"
            }
        )
        # then the workspace is connected
        assert result.workspace == workspace_ref
        # and the resource id gets set
        assert result.id == "item_id"
