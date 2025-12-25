from __future__ import annotations

import hashlib
from pathlib import PurePath, PurePosixPath
from typing import Annotated, Any, Optional, Union

import httpx
from pydantic import BaseModel, BeforeValidator, Field, model_validator
from pydantic.functional_serializers import PlainSerializer

from .resource_abc import Ref, Resource, register_resource


@register_resource()
class FolderRef(BaseModel, Ref):
    """Reference to a drive directory."""

    id: str = Field(exclude=True, init=True)
    drive_id: str = Field("/", exclude=True, init=False)
    folder_path: str

    def attach(self, client):
        if self.folder_path == "/":
            self.drive_id = "/"
            return
        p = PurePosixPath(self.folder_path)
        search = client.post("/drive/api/search/", json={"withPath": str(p.parent), "name": str(p.name)})
        values = search.json()["values"]
        if len(values) != 1:
            raise RuntimeError(
                "Expected to find exactly one match path for PathRef but found " + str(len(values))
            )
        self.drive_id = values[0]["id"]

    def path(self):
        return PurePosixPath(self.folder_path)


root = FolderRef(id="drive_root", folder_path="/")


@register_resource()
class FolderResource(BaseModel, Resource):
    """Resource describing a Drive folder

    Creates if it doesn't exist and updates if it has changed:
        - When name is changed, the reference for the folder will be maintained
        - When parent is changed, the folder will be moved under new parent

    Example
    -------
        >>> from fbnconfig import drive, Deployment
        >>> f1 = drive.FolderResource(id="base_folder", name="first_level", parent=drive.root)
        >>> f2 = drive.FolderResource(id="base_folder", name="second_level", parent=f1)
        >>> Deployment("myDeployment", [f1,f2])

    Notes
    -----
    If the folder is the parent of another resource, all dependents need to be deleted before this one

    Attributes
    ----------
    id : str
        resource identifier; this will be used in the log to reference the folder resource

    name : str
        folder name that will be displayed in Drive UI

    parent:  Union[FolderKey, RootFolder]
        Folder reference to the parent folder; if it is in root, use 'drive.root'
    """

    id: str = Field(exclude=True)
    drive_id: str | None = Field(None, exclude=True, init=False)
    name: str
    parent: FolderKey

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info):
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return {"id": info.context["id"]} | data
        return data

    def read(self, client, old_state):
        pass  # not needed

    def create(self, client: httpx.Client):
        body = {"path": str(self.parent.path()), "name": self.name}
        res = client.request("POST", "/drive/api/folders", json=body)
        self.drive_id = res.json()["id"]
        return {
            "id": self.id,
            "driveId": self.drive_id,
            "name": self.name,
            "parentId": self.parent.drive_id,
        }

    def update(self, client: httpx.Client, old_state):
        self.drive_id = old_state.driveId
        if self.name != old_state.name or self.parent.drive_id != old_state.parentId:
            body = {"path": str(self.parent.path()), "name": self.name}
            client.request("PUT", "/drive/api/folders/" + old_state.driveId, json=body)
            return {
                "id": self.id,
                "driveId": self.drive_id,
                "name": self.name,
                "parentId": self.parent.drive_id,
            }
        return None

    @staticmethod
    def delete(client, old_state):
        client.request("DELETE", "/drive/api/folders/" + old_state.driveId)

    def deps(self):
        return [self.parent] if self.parent else []

    def path(self):
        return self.parent.path() / PurePosixPath(self.name)


def ser_folder_key(value, info):
    if info.context and info.context.get("style", "api") == "dump":
        return {"$ref": value.id}
    return value


def des_folder_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


FolderKey = Annotated[
    FolderResource | FolderRef,
    BeforeValidator(des_folder_key), PlainSerializer(ser_folder_key)
]


@register_resource()
class FileResource(BaseModel, Resource):
    """Resource describing a Drive file.

    Creates if it doesn't exist and updates if content changes.

    Example
    -------
        >>> from fbnconfig import drive, Deployment
        >>> import pathlib
        >>> f1 = drive.FolderResource(id="base_folder", name="first_level", parent=drive.root)
        >>> content_path = pathlib.Path(__file__).parent.resolve() / pathlib.Path("myfile1.txt")
        >>> ff_with_path =
        >>> drive.FileResource(id="file1", folder=f1, name="myfile1.txt", content_path=content_path)
        >>> ff_with_content =
        >>> drive.FileResource(id="file2", folder=f1, name="myfile2.txt", content="Content of my file")
        >>> Deployment("myDeployment", [f1, ff_with_path, ff_with_content])

    Notes
    -----
    Can only supply a path to content or the content itself, but not both

    Attributes
    ----------
    id : str
      resource identifier; this will be used in the log to reference the file resource
    name : str
      file name that will be displayed in Drive UI
    content: Optional[Union[str, bytes]]
        file content
    content_path: Optional[PurePath]
        Path to the content of the file
    folder: FolderResource
      Folder reference to the parent folder; if it is in root, use 'drive.root'
    """

    id: str = Field(exclude=True)
    drive_id: str | None = Field(None, exclude=True, init=False)
    name: str
    content: Optional[Union[str, bytes]] = None
    content_path: Optional[PurePath] = None
    folder: FolderKey
    content_hash: str | None = Field(None, exclude=True, init=False)

    _drive_path = "/drive/api/files"

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info):
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return {"id": info.context["id"]} | data
        return data

    def read(self, client, old_state) -> None:
        pass  # not needed

    @model_validator(mode="after")
    def validate_content(self):
        if self.content_path is not None:
            if self.content is not None:
                raise RuntimeError(
                    "Only one of content and content_path should be specified in FileResource"
                )
            if not self.content_path.is_absolute():
                raise RuntimeError("content_path should be an absolute path")
            with open(self.content_path, "rb") as ff:
                content = ff.read()
            self.content_hash = hashlib.sha256(content).hexdigest()
        elif self.content is not None:
            encoded = self.content.encode() if isinstance(self.content, str) else self.content
            self.content_hash = hashlib.sha256(encoded).hexdigest()
        else:
            raise RuntimeError("Either content or content_path should be specified in FileResource")
        return self

    def get_content(self) -> str | bytes | None:
        """Get the content of the file."""
        if self.content_path is not None:
            with open(self.content_path, "rb") as ff:
                return ff.read()
        return self.content

    def create(self, client):
        path = str(self.folder.path())
        res = client.request(
            "POST",
            self._drive_path,
            headers={
                "x-lusid-drive-filename": self.name,
                "x-lusid-drive-path": path,
                "content-type": "application/octet-stream",
            },
            content=self.get_content(),
        )
        self.drive_id = res.json()["id"]
        return {
            "id": self.id,
            "driveId": self.drive_id,
            "name": self.name,
            "parentId": self.folder.drive_id,
            "content_hash": self.content_hash,
        }

    def update(self, client, old_state):
        self.drive_id = old_state.driveId
        if (
            self.name == old_state.name
            and self.folder.drive_id == old_state.parentId
            and self.content_hash == old_state.content_hash
        ):
            return None

        if self.content_hash != old_state.content_hash:
            assert self.drive_id is not None
            client.request(
                "put",
                "/drive/api/files/" + self.drive_id + "/contents",
                headers={"content-type": "application/octet-stream"},
                content=self.get_content(),
            )
        if self.name != old_state.name or self.folder.drive_id != old_state.parentId:
            json = {"path": str(self.folder.path()), "name": self.name}
            client.request("PUT", self._drive_path + "/" + old_state.driveId, json=json)
        return {
            "id": self.id,
            "driveId": self.drive_id,
            "name": self.name,
            "parentId": self.folder.drive_id,
            "content_hash": self.content_hash,
        }

    @staticmethod
    def delete(client, old_state):
        client.request("DELETE", "/drive/api/files/" + old_state.driveId)

    def deps(self):
        return [self.folder]

    def path(self):
        return self.folder.path() / PurePosixPath(self.name)
