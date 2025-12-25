import hashlib
import json
import pathlib
from types import SimpleNamespace
from unittest import mock

import httpx
import pytest
from pydantic import ValidationError

from fbnconfig import drive


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeFolderRef:
    base_url = "https://foo.lusid.com"
    client = httpx.Client(base_url=base_url)

    def test_attach(self, respx_mock):
        respx_mock.post("/drive/api/search/").mock(
            return_value=httpx.Response(200, json={"values": [{"id": 23456}]})
        )
        ref = drive.FolderRef(id="a", folder_path="/robTest99")
        ref.attach(self.client)
        assert ref.drive_id == 23456

    def test_attach_root(self):
        # given a ref to the root path
        ref = drive.FolderRef(id="abc", folder_path="/")
        # when we attach it
        ref.attach(self.client)
        # then no http requests are made (you can't search for root with the api)
        # and the driveId is root
        assert ref.drive_id == "/"


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeFolder:
    base_url = "https://foo.lusid.com"
    client = httpx.Client(base_url=base_url)

    def test_ctor_invalid_parent(self):
        try:
            drive.FolderResource(id="id", name="name", parent=None)  # type: ignore
        except ValidationError:
            return
        assert False

    def test_ctor_with_root(self):
        f = drive.FolderResource(id="id", name="name", parent=drive.root)
        assert f

    def test_create_in_root(self, respx_mock):
        respx_mock.post("/drive/api/folders").mock(return_value=httpx.Response(200, json={"id": 23456}))
        client = self.client
        # given nothing really
        # when we create a folder at the root level
        sut = drive.FolderResource(id="anid", name="new_folder_name", parent=drive.root)
        state = sut.create(client)
        # then the state is returned
        assert state["name"] == "new_folder_name"
        assert state["driveId"] == 23456
        assert state["parentId"] == "/"
        assert str(sut.path()) == "/new_folder_name"
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == f"{self.base_url}/drive/api/folders"
        assert json.loads(request.content) == {"path": "/", "name": "new_folder_name"}

    def test_create_in_folder(self, respx_mock):
        client = self.client
        parent = drive.FolderResource(id="parentid", name="parentname", parent=drive.root)
        respx_mock.post("/drive/api/folders").mock(
            side_effect=[httpx.Response(200, json={"id": 1234}), httpx.Response(200, json={"id": 23456})]
        )
        parent.create(client)
        sut = drive.FolderResource(id="anid", name="new_folder_name", parent=parent)
        state = sut.create(client)
        assert state["name"] == "new_folder_name", "should have child name"
        assert state["driveId"] == 23456, "should get child driveId"
        assert state["parentId"] == 1234, "should capture parent driveId"
        assert str(sut.path()) == "/parentname/new_folder_name"
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == f"{self.base_url}/drive/api/folders"
        assert json.loads(request.content) == {"path": "/parentname", "name": "new_folder_name"}

    @pytest.fixture
    def existing_structure(self, respx_mock):
        # A structure which starts as
        # root/
        #    parentname/               [driveid: 1234]
        #       subfolder2             [driveid: 23456]
        #    other/                    [driveid: 7654]
        client = self.client
        respx_mock.post("/drive/api/folders").mock(
            side_effect=[
                httpx.Response(200, json={"id": "1234"}),
                httpx.Response(200, json={"id": "23456"}),
                httpx.Response(200, json={"id": "7654"}),
            ]
        )
        parent = drive.FolderResource(id="parentid", name="parentname", parent=drive.root)
        parent.create(client)
        folder = drive.FolderResource(id="anid", name="subfolder2", parent=parent)
        folder.create(client)
        other = drive.FolderResource(id="other", name="other", parent=drive.root)
        return SimpleNamespace(parent=parent, subfolder=folder, other=other)

    def test_delete(self, respx_mock, existing_structure):
        respx_mock.delete("/drive/api/folders/23456").mock(
            side_effect=[httpx.Response(200, json={"id": "23456"})]
        )

        # given an existing folder
        old_state = SimpleNamespace(id="anid", name="subfolder2", driveId="23456", parentId="1234")
        # when we delete it
        sut = drive.FolderResource(id="anid", name="subfolder2", parent=existing_structure.parent)
        sut.delete(self.client, old_state)
        # then a delete request is sent
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url == f"{self.base_url}/drive/api/folders/23456"

    def test_update_nochange(self, existing_structure):
        # given an existing state
        old_state = SimpleNamespace(id="anid", name="subfolder2", driveId="23456", parentId="1234")
        # when we update the folder with the same values as the state
        sut = drive.FolderResource(id="anid", name="subfolder2", parent=existing_structure.parent)
        new_state = sut.update(self.client, old_state)
        # then new  state is None indicating that no change was made
        assert new_state is None
        # and no http request was made (no mock!)

    def test_update_name(self, respx_mock, existing_structure):
        respx_mock.put("/drive/api/folders/23456").mock(
            side_effect=[httpx.Response(200, json={"id": "23456"})]
        )
        # given the folder exists with name 'another'
        old_state = SimpleNamespace(id="anid", name="subfolder2", driveId="23456", parentId="1234")
        # when it is updated with name subfolder2
        sut = drive.FolderResource(id="anid", name="anotherName", parent=existing_structure.parent)
        new_state = sut.update(self.client, old_state)
        # then a put request is made with the new name and the existing driveId
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url == f"{self.base_url}/drive/api/folders/23456"
        assert json.loads(request.content) == {"path": "/parentname", "name": "anotherName"}
        # and the new state is returned
        assert new_state == {"id": "anid", "name": "anotherName", "driveId": "23456", "parentId": "1234"}

    def test_update_parent(self, respx_mock, existing_structure):
        respx_mock.put("/drive/api/folders/23456").mock(
            side_effect=[httpx.Response(200, json={"id": "23456"})]
        )
        # given a state  /other/subfolder2     [other is id:7654]
        old_state = SimpleNamespace(id="anid", name="subfolder2", driveId="23456", parentId="7654")
        # when we update it's parent to be /parentname  [1234]
        sut = drive.FolderResource(id="anid", name="subfolder2", parent=existing_structure.parent)
        new_state = sut.update(self.client, old_state)
        # then a put request is made to move the subject
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url == f"{self.base_url}/drive/api/folders/23456"
        assert json.loads(request.content) == {"path": "/parentname", "name": "subfolder2"}
        # and the new state is returned
        assert new_state == {"id": "anid", "name": "subfolder2", "driveId": "23456", "parentId": "1234"}

    def test_dump_simple_folder(self):
        # given a simple folder resource
        sut = drive.FolderResource(
            id="dump-folder",
            name="DumpFolder",
            parent=drive.root
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
            "name": "DumpFolder",
            "parent": {"$ref": "drive_root"}
        }
        assert result == expected

    def test_dump_nested_folder(self):
        # given a nested folder structure
        parent_folder = drive.FolderResource(
            id="parent-folder",
            name="ParentFolder",
            parent=drive.root
        )
        sut = drive.FolderResource(
            id="child-folder",
            name="ChildFolder",
            parent=parent_folder
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then parent is referenced by $ref
        expected = {
            "name": "ChildFolder",
            "parent": {"$ref": "parent-folder"}
        }
        assert result == expected

    def test_undump_simple_folder(self):
        # given dump data
        data = {
            "name": "UndumpFolder",
            "parent": {"$ref": "drive_root"}
        }
        # mock the $refs context with root reference
        refs = {"drive_root": drive.root}
        # when we undump it with id from context
        result = drive.FolderResource.model_validate(
            data, context={"style": "dump", "id": "folder_id", "$refs": refs}
        )
        # then it's correctly populated including id from context
        assert result.id == "folder_id"
        assert result.name == "UndumpFolder"
        assert result.parent == drive.root

    def test_undump_nested_folder(self):
        # given dump data with parent folder reference
        data = {
            "name": "UndumpChildFolder",
            "parent": {"$ref": "parent-folder-id"}
        }
        # mock parent folder
        parent_folder = drive.FolderResource(
            id="parent-folder-id",
            name="ParentFolder",
            parent=drive.root
        )
        refs = {"parent-folder-id": parent_folder}
        # when we undump it
        result = drive.FolderResource.model_validate(
            data, context={"style": "dump", "id": "child_folder_id", "$refs": refs}
        )
        # then it's correctly populated
        assert result.id == "child_folder_id"
        assert result.name == "UndumpChildFolder"
        assert result.parent == parent_folder


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeFile:
    base_url = "https://foo.lusid.com"
    client = httpx.Client(base_url=base_url)

    def hashit(self, content):
        encoded = content.encode() if isinstance(content, str) else content
        return hashlib.sha256(encoded).hexdigest()

    @pytest.fixture
    def existing_structure(self, respx_mock):
        # A structure which starts as
        # root/
        #    parentname/               [driveid: 1234]
        #       subfolder2/            [driveid: 23456]
        #          afile.txt           [driveid: 6543]
        #    other/                    [driveid: 7654]
        client = self.client
        parent = drive.FolderResource(id="parentid", name="parentname", parent=drive.root)
        respx_mock.post("/drive/api/folders").mock(
            side_effect=[
                httpx.Response(200, json={"id": "1234"}),
                httpx.Response(200, json={"id": "23456"}),
                httpx.Response(200, json={"id": "7654"}),
            ]
        )
        parent.create(client)
        folder = drive.FolderResource(id="anid", name="subfolder2", parent=parent)
        folder.create(client)
        other = drive.FolderResource(id="other", name="other", parent=drive.root)
        other.create(client)
        file = drive.FileResource(id="afile", name="afile.txt", folder=folder, content="some content")
        return SimpleNamespace(parent=parent, subfolder=folder, other=other, file=file)

    def test_ctor_throws_with_non_folder(self):
        not_a_folder = {}
        with pytest.raises(ValidationError):
            drive.FileResource(id="id", name="name", folder=not_a_folder, content="content")  # type: ignore

    def test_ctor_works_with_folder(self):
        folder = drive.FolderResource(id="folder_id", name="folder", parent=drive.root)
        f = drive.FileResource(id="id", name="name", folder=folder, content="hello")
        assert f

    def test_delete(self, respx_mock, existing_structure):
        respx_mock.delete("/drive/api/files/6543").mock(side_effect=[httpx.Response(200, json={})])
        # given the existing file: afile.txt
        # when we delete it
        old_state = SimpleNamespace(id="afile", name="afile.txt", driveId="6543", parentId="123456")
        sut = drive.FileResource(
            id="afile", name="afile.txt", folder=existing_structure.subfolder, content="fake"
        )
        sut.delete(self.client, old_state)
        # then a delete request is made
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url == f"{self.base_url}/drive/api/files/6543"

    def test_create_str_content(self, respx_mock, existing_structure):
        respx_mock.post("/drive/api/files").mock(side_effect=[httpx.Response(200, json={"id": "8888"})])
        # given an existing folder, subfolder2 [23456]
        parent = existing_structure.subfolder
        # when we create a file with string content
        sut = drive.FileResource(id="bfile", name="poem.txt", folder=parent, content="banjo poem")
        new_state = sut.create(self.client)
        # then a post request is made
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == f"{self.base_url}/drive/api/files"
        assert request.headers["x-lusid-drive-filename"] == "poem.txt"
        assert request.headers["x-lusid-drive-path"] == "/parentname/subfolder2"
        assert request.headers["content-type"] == "application/octet-stream"
        # and the new state is created
        assert new_state == {
            "id": "bfile",
            "name": "poem.txt",
            "driveId": "8888",
            "parentId": "23456",
            "content_hash": self.hashit("banjo poem"),
        }

    def test_move_folders(self, respx_mock, existing_structure):
        respx_mock.put("/drive/api/files/6543").mock(side_effect=[httpx.Response(200, json={})])
        # given an existing file parentname/subfolder2/afile.txt
        old_parent = existing_structure.subfolder
        # when we change the parent to /other [id:7654]
        old_state = SimpleNamespace(
            id="cfile",
            name="afile.txt",
            driveId="6543",
            parentId=old_parent.id,
            content_hash=self.hashit("jam poem"),
        )
        sut = drive.FileResource(
            id="cfile", name="afile.txt", folder=existing_structure.other, content="jam poem"
        )
        new_state = sut.update(self.client, old_state)
        # then an out request is made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url == f"{self.base_url}/drive/api/files/6543"
        assert json.loads(request.content) == {"path": "/other", "name": "afile.txt"}
        # and the new state is created
        assert new_state == {
            "id": "cfile",
            "name": "afile.txt",
            "driveId": "6543",
            "parentId": "7654",
            "content_hash": self.hashit("jam poem"),
        }

    def test_rename_file(self, respx_mock, existing_structure):
        respx_mock.put("/drive/api/files/6543").mock(side_effect=[httpx.Response(200, json={})])
        # given an existing file parentname/subfolder2/afile.txt
        parent = existing_structure.subfolder
        # when we rename the file but retain the parent
        old_state = SimpleNamespace(
            id="cfile",
            name="afile.txt",
            driveId="6543",
            parentId=parent.id,
            content_hash=self.hashit("bear tail"),
        )
        sut = drive.FileResource(id="cfile", name="renamed.sql", folder=parent, content="bear tail")
        new_state = sut.update(self.client, old_state)
        # then a out request is made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url == f"{self.base_url}/drive/api/files/6543"
        assert json.loads(request.content) == {"path": "/parentname/subfolder2", "name": "renamed.sql"}
        # and the new state is created
        assert new_state == {
            "id": "cfile",
            "name": "renamed.sql",
            "driveId": "6543",
            "parentId": parent.drive_id,
            "content_hash": self.hashit("bear tail"),
        }

    def test_change_content(self, respx_mock, existing_structure):
        respx_mock.put("/drive/api/files/6543/contents").mock(side_effect=[httpx.Response(200, json={})])
        # given an existing file parentname/subfolder2/afile.txt
        parent = existing_structure.subfolder
        # when we update the content
        old_state = SimpleNamespace(
            id="cfile",
            name="afile.txt",
            driveId="6543",
            parentId=parent.drive_id,
            content_hash=self.hashit("cow bell"),
        )
        sut = drive.FileResource(id="cfile", name="afile.txt", folder=parent, content="pig ears")
        new_state = sut.update(self.client, old_state)
        # then a put request is made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url == f"{self.base_url}/drive/api/files/6543/contents"
        assert request.headers["content-type"] == "application/octet-stream"
        assert request.content == b"pig ears"
        # and the new state is created
        assert new_state == {
            "id": "cfile",
            "name": "afile.txt",
            "driveId": "6543",
            "parentId": parent.drive_id,
            "content_hash": self.hashit("pig ears"),
        }

    def test_ctor_with_file_content(self, existing_structure):
        mock_open = mock.mock_open(read_data=b"juicy\njuicy")
        with mock.patch("builtins.open", mock_open) as m:
            sut = drive.FileResource(
                id="from-file",
                name="tomato.txt",
                folder=existing_structure.parent,
                content_path=pathlib.PurePath("/foo.txt"),
            )
            assert sut.get_content() == b"juicy\njuicy"
        m.assert_called_with(pathlib.PurePosixPath("/foo.txt"), "rb")

    def test_create_with_file_content(self, respx_mock, existing_structure):
        respx_mock.post("/drive/api/files").mock(side_effect=[httpx.Response(200, json={"id": "999"})])
        mock_open = mock.mock_open(read_data=b"juicy\njuicy")
        with mock.patch("builtins.open", mock_open):
            sut = drive.FileResource(
                id="from-file",
                name="tomato.txt",
                folder=existing_structure.subfolder,
                content_path=pathlib.PurePath("/foo.txt"),
            )
            new_state = sut.create(self.client)
        # then a post request is made
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == f"{self.base_url}/drive/api/files"
        assert request.headers["x-lusid-drive-filename"] == "tomato.txt"
        assert request.headers["x-lusid-drive-path"] == "/parentname/subfolder2"
        assert request.headers["content-type"] == "application/octet-stream"
        assert request.content == b"juicy\njuicy"
        # and the new state is created
        assert new_state == {
            "id": "from-file",
            "name": "tomato.txt",
            "driveId": "999",
            "parentId": "23456",
            "content_hash": self.hashit(b"juicy\njuicy"),
        }

    def test_dump_simple_file(self):
        # given a simple file resource
        folder = drive.FolderResource(
            id="test-folder",
            name="TestFolder",
            parent=drive.root
        )
        sut = drive.FileResource(
            id="dump-file",
            name="DumpFile.txt",
            folder=folder,
            content="test content"
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
            "name": "DumpFile.txt",
            "content": "test content",
            "folder": {"$ref": "test-folder"}
        }
        assert result == expected

    def test_dump_file_bytes_content(self):
        # given a file resource with bytes content
        folder = drive.FolderResource(
            id="test-folder",
            name="TestFolder",
            parent=drive.root
        )
        sut = drive.FileResource(
            id="dump-file-bytes",
            name="DumpFile.bin",
            folder=folder,
            content=b"binary content"
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then bytes content is converted to string in json mode
        expected = {
            "name": "DumpFile.bin",
            "content": "binary content",
            "folder": {"$ref": "test-folder"}
        }
        assert result == expected

    def test_undump_simple_file(self):
        # given dump data
        data = {
            "name": "UndumpFile.txt",
            "content": "undump content",
            "folder": {"$ref": "test-folder-id"}
        }
        # mock folder reference
        folder = drive.FolderResource(
            id="test-folder-id",
            name="TestFolder",
            parent=drive.root
        )
        refs = {"test-folder-id": folder}
        # when we undump it with id from context
        result = drive.FileResource.model_validate(
            data, context={"style": "dump", "id": "file_id", "$refs": refs}
        )
        # then it's correctly populated including id from context
        assert result.id == "file_id"
        assert result.name == "UndumpFile.txt"
        assert result.content == "undump content"
        assert result.folder == folder

    def test_undump_file_bytes_content(self):
        # given dump data with bytes content
        data = {
            "name": "UndumpFile.bin",
            "content": b"undump binary content",
            "folder": {"$ref": "test-folder-id"}
        }
        # mock folder reference
        folder = drive.FolderResource(
            id="test-folder-id",
            name="TestFolder",
            parent=drive.root
        )
        refs = {"test-folder-id": folder}
        # when we undump it
        result = drive.FileResource.model_validate(
            data, context={"style": "dump", "id": "file_bytes_id", "$refs": refs}
        )
        # then it's correctly populated
        assert result.id == "file_bytes_id"
        assert result.name == "UndumpFile.bin"
        assert result.content == b"undump binary content"
        assert result.folder == folder
