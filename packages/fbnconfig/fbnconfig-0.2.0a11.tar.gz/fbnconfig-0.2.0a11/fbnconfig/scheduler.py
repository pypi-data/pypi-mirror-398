import hashlib
import json
import subprocess
import time
from collections import defaultdict
from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional

import httpx
from httpx import Client, HTTPStatusError
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
)

from . import configuration as cfg
from . import identity
from .resource_abc import CamelAlias, Ref, Resource, register_resource


@register_resource()
class ImageRef(BaseModel, Ref):
    """Reference an existing image
    Example
    -------
    >>> from fbnconfig.scheduler import ImageRef
    >>> image_ref = ImageRef(dest_name="myimage", dest_tag="0.1.1")
    """

    id: str
    dest_name: str
    dest_tag: str

    def attach(self, client):
        # we only need to check it exists
        try:
            res = client.get(f"/scheduler2/api/images/repository/{self.dest_name}").json()
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Image with name {self.dest_name} and tag {self.dest_tag} not found")
            else:
                raise ex
        for img in res["values"]:
            names = {tag["name"] for tag in img["tags"]}
            if self.dest_tag in names:
                return
        raise RuntimeError(f"Image with name {self.dest_name} and tag {self.dest_tag} not found")


@register_resource()
class ImageResource(BaseModel, Resource):
    """Define an image

    Example
    -------
    >>> from fbnconfig.scheduler import ImageResource
    >>> image = ImageResource(
            id="img1",
            source_image="docker.io/alpine:3.16.7",
            dest_name="myimage",
            dest_tag="3.16.7")
    """

    id: str
    source_image: str
    dest_name: str
    dest_tag: str
    pull_upstream: bool | None = Field(default=True, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        pass  # not needed

    def create(self, client):
        # create a unique tag so scheduler will give us commands and not complain about
        # reusing an existing one. We want to check hashes not tags
        body = {"imageName": f"{self.dest_name}:{time.time()}"}
        upload = client.post("/scheduler2/api/images", json=body).json()
        auth_cmd = upload["dockerLoginCommand"].split(" ")
        user = auth_cmd[3]
        password = auth_cmd[5]
        reghost = auth_cmd[6]
        tag_cmd = upload["tagVersionedDockerImageCommand"].split(" ")
        # combine the repo from the api with the real tag we want
        downstream_repo = tag_cmd[3].split(":")[0]
        downstream_image = ":".join([downstream_repo, self.dest_tag])
        # pull from the upstream and apply the downstream tag
        pull_cmd = self._pull_commands(self.source_image) if self.pull_upstream else []
        tag_cmd = self._tag_commands(downstream_image)
        for cmd in pull_cmd + tag_cmd:
            subprocess.run(cmd).check_returncode()
        # get local and downstream digests to see if they match
        local_digest = self._get_local_digest(downstream_image)
        # check if the local hash matches the remote hash. If so skip the rest
        if local_digest is not None:
            downstream_images = self.get_remote_tags(client, self.dest_name, local_digest)
            matching_tag = next((tag for tag in downstream_images if tag["name"] == self.dest_tag), None)
            if matching_tag is not None:  # this image/tag combo already exists
                print("image already exists in the remote with the same digest")
                return {
                    "id": self.id,
                    "source_image": self.source_image,
                    "dest_name": self.dest_name,
                    "dest_tag": self.dest_tag,
                }
        # push the tag we actually want to have using the auth from scheduler
        push_commands = self._push_commands(downstream_image, user, password, reghost)
        for cmd in push_commands:
            subprocess.run(cmd).check_returncode()
        return {
            "id": self.id,
            "source_image": self.source_image,
            "dest_name": self.dest_name,
            "dest_tag": self.dest_tag,
        }

    @staticmethod
    def get_remote_tags(client, dest_name, local_digest):
        repo = client.get(f"/scheduler2/api/images/repository/{dest_name}")
        # todo: this could be paged
        return next((img["tags"] for img in repo.json()["values"] if img["digest"] == local_digest), [])

    @staticmethod
    def _get_local_digest(tag):
        inspect = subprocess.run(
            ["docker", "inspect", "--format", "{{json .RepoDigests}}", tag],
            capture_output=True,
            text=True,
        )
        inspect.check_returncode()
        # inspect returns:
        #   [alpine@sha256:a8cb.. fbn-qa.lusid.com/fbn-qa/beany@sha256:b797...]
        repo = tag.split(":")[0]
        return next(
            (
                digest.split("@")[1]
                for digest in json.loads(inspect.stdout)
                if digest.split("@")[0] == repo
            ),
            None,
        )

    @staticmethod
    def _push_commands(downstream_image, user, password, reghost):
        return [
            ["docker", "login", "-u", user, "--password", password, reghost],
            ["docker", "push", "-q", downstream_image],
        ]

    def _pull_commands(self, source_image):
        return [["docker", "pull", "--platform", "linux/amd64", "-q", source_image]]

    def _tag_commands(self, tag):
        return [["docker", "tag", self.source_image, tag]]

    def update(self, client, old_state):
        if (
            [self.source_image, self.dest_name, self.dest_tag] ==
            [old_state.source_image, old_state.dest_name, old_state.dest_tag]
        ):
            return None
        else:
            return self.create(client)

    @staticmethod
    def delete(client, old_state):
        # no delete for images
        pass

    def deps(self):
        return []


def ser_image_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return value


def des_image_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


ImageKey = Annotated[
    ImageResource | ImageRef,
    BeforeValidator(des_image_key), PlainSerializer(ser_image_key)
]


class CommandlineArg(BaseModel, CamelAlias):
    """Define a commandline ArgumentDefinition for a JobResource"""

    data_type: Literal["String", "Int"]
    required: Optional[bool] = False
    description: str
    order: int
    passed_as: Literal["CommandLine"] = "CommandLine"
    default_value: None | str = None


class EnvironmentArg(BaseModel, CamelAlias):
    """Define a environment ArgumentDefinition for a JobResource"""

    data_type: Literal["String", "Int", "SecureString", "Configuration"]
    required: Optional[bool] = False
    description: str
    order: int
    passed_as: Literal["EnvironmentVariable"] = "EnvironmentVariable"
    default_value: None | str | cfg.ItemRef | cfg.ItemResource = None

    @field_serializer("default_value", when_used="always")
    def ser_value(self, value, info) -> Dict[str, str] | str | None:
        style = info.context.get("style", "api") if info.context else "api"
        if style == "dump":
            if isinstance(value, (cfg.ItemRef, cfg.ItemResource)):
                return {"$ref": value.id}
            return value
        # api style print is as config:abc
        if value is None:
            return None
        if isinstance(value, (cfg.ItemRef, cfg.ItemResource)):
            return value.ref
        return value

    @field_validator("default_value", mode="before")
    @classmethod
    def des_value(cls, value, info):
        if info.context and info.context.get("$refs"):
            if isinstance(value, dict) and value.get("$ref"):
                return info.context["$refs"][value["$ref"]]
        return value


JobArgument = Annotated[CommandlineArg | EnvironmentArg, Field(discriminator="passed_as")]


@register_resource()
class JobRef(BaseModel, Ref):
    """Reference an existing scheduler job"""

    id: str = Field(exclude=True)
    scope: str
    code: str

    _content_hash: str | None = None

    def attach(self, client):
        # just check it exists
        search = client.get(
            "/scheduler2/api/jobs",
            params={"filter": f"jobId.scope eq '{self.scope}' and jobId.code eq '{self.code}'"},
        )

        current = next((job for job in search.json()["values"]), None)
        if current is None:
            raise RuntimeError(
                f"Failed to attach JobRef to job with scope={self.scope} and code={self.code}"
            )

        self._content_hash = hashlib.sha256(json.dumps(current, sort_keys=True).encode()).hexdigest()


class JobState(BaseModel):
    id: str
    scope: str
    code: str


@register_resource()
class JobResource(BaseModel, Resource):
    """Manage a JobDefinition"""

    id: str = Field(exclude=True)
    scope: str = Field(exclude=False, init=True)
    code: str = Field(exclude=False, init=True)
    image: ImageKey
    name: str
    author: Optional[str] = None
    date_created: Optional[datetime] = None
    description: str
    ttl: Optional[int] = None
    min_cpu: Optional[str] = None
    max_cpu: Optional[str] = None
    min_memory: Optional[str] = None
    max_memory: Optional[str] = None
    argument_definitions: Dict[str, JobArgument] = {}
    command_line_argument_separator: Optional[str] = None

    class ScanTimeoutParameters:
        tries = 120
        wait_time = 1

    @computed_field
    def job_id(self) -> Dict[str, str]:
        return {"scope": self.scope, "code": self.code}

    @computed_field
    def image_name(self) -> str:
        return self.image.dest_name

    @computed_field
    def image_tag(self) -> str:
        return self.image.dest_tag

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Dict[str, Any], info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # handle the list api returning dockerImage instead of image
        if data.get("dockerImage", None):
            data = data | {"image": data["dockerImage"]}
            data.pop("dockerImage")
        # Handle API list response format (jobIdd.scope and jobIdd.code)
        if isinstance(data.get("jobId", None), dict):
            data = data | data["jobId"]
            data.pop("jobId")
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    @field_validator("image", mode="before")
    @classmethod
    def des_image(cls, image, info) -> ImageResource | ImageRef:
        if info.context and info.context.get("$refs"):
            return info.context["$refs"][image["$ref"]]
        return image

    def read(self, client: Client, old_state):
        search = client.get(
            "/scheduler2/api/jobs",
            params={
                "filter": f"jobId.scope eq '{old_state.scope}' and jobId.code eq '{old_state.code}'"
            },
        )
        current = next(job for job in search.json()["values"])
        # normalise the current values
        current.pop("jobId")
        current.pop("requiredResources")
        current["imageName"] = current["dockerImage"].split(":")[
            0
        ]  # we get dockerImage but have to send separately :(
        current["imageTag"] = current["dockerImage"].split(":")[1]
        current.pop("dockerImage")
        return current

    def _wait_for_vulnerability_scan(self, client):
        tries = self.ScanTimeoutParameters.tries
        while True:
            values = client.get(f"/scheduler2/api/images/repository/{self.image_name}").json()["values"]

            filtered_images = [v for v in values if self.image_tag in [tag["name"] for tag in v["tags"]]]

            if any(v["scanStatus"] == "COMPLETE" for v in filtered_images):
                break
            if any(
                (
                    v["scanStatus"]
                    in (
                        "FAILED",
                        "UNSUPPORTED_IMAGE",
                        "SCAN_ELIGIBILITY_EXPIRED",
                        "FINDINGS_UNAVAILABLE",
                    )
                    for v in filtered_images
                )
            ):
                raise RuntimeError("Image vulnerability scan failed.")
            time.sleep(self.ScanTimeoutParameters.wait_time)
            tries -= 1
            if tries < 1:
                raise RuntimeError("Image vulnerability scan timed out.")

    def create(self, client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
                                  exclude={"scope", "code", "image"})
        self._wait_for_vulnerability_scan(client)
        client.post("/scheduler2/api/jobs", json=desired)
        new_state = JobState(id=self.id, scope=self.scope, code=self.code)
        return new_state.model_dump()

    def update(self, client: Client, old_state):
        if self.scope != old_state.scope or self.code != old_state.code:
            raise (RuntimeError("Cannot change identifier on job. Create a new one"))

        remote = self.read(client, old_state)
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
                                  exclude={"job_id", "scope", "code", "image"})
        effective = remote | desired
        remote_args = remote["argumentDefinitions"]
        effective_args: dict[str, dict] = defaultdict(None)
        for arg_key, arg_value in desired["argumentDefinitions"].items():
            v: dict[str, str] = remote_args.get(arg_key, {}) | arg_value
            # if desired state does not have a default value, remove it from effective
            if arg_value.get("defaultValue", None) is None:
                v.pop("defaultValue", None)
            effective_args[arg_key] = v

        effective["argumentDefinitions"] = effective_args
        if effective == remote:
            return None
        self._wait_for_vulnerability_scan(client)
        client.put(f"/scheduler2/api/jobs/{self.scope}/{self.code}", json=desired)
        new_state = JobState(id=self.id, scope=self.scope, code=self.code)
        return new_state.model_dump()

    @staticmethod
    def delete(client: Client, old_state):
        client.delete(f"/scheduler2/api/jobs/{old_state.scope}/{old_state.code}")

    def cleanup(self, client, old_state):
        if self.scope != old_state.scope or self.code != old_state.code:
            return self.delete(client, old_state)
        return None

    def deps(self):
        config_args: List[cfg.ItemRef | cfg.ItemResource] = [
            arg.default_value
            for arg in self.argument_definitions.values()
            if isinstance(arg.default_value, (cfg.ItemRef, cfg.ItemResource))
        ]
        return [self.image] + config_args


def ser_job_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return {"scope": value.scope, "code": value.code}


def des_job_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


JobKey = Annotated[
    JobResource | JobRef,
    BeforeValidator(des_job_key), PlainSerializer(ser_job_key)
]


class ScheduleState(BaseModel):
    id: str
    scope: str
    code: str
    # Suppress to keep backwards comp with existing state
    argKeys: List[str]  # noqa: N815


@register_resource()
class ScheduleResource(BaseModel, Resource):
    """Manage a ScheduleDefinition"""

    id: str = Field(exclude=True)
    name: str
    scope: str
    code: str
    expression: str
    timezone: Optional[str] = None
    job: JobKey
    description: str
    author: Optional[str] = None
    owner: Optional[str] = None
    arguments: None | Dict[str, str | cfg.ItemKey] = None
    enabled: Optional[bool] = None
    use_as_auth: identity.UserKey | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # Handle API list response format (jobIdd.scope and jobIdd.code)
        if isinstance(data.get("scheduleIdentifier", None), dict):
            data = data | data["scheduleIdentifier"]
            data.pop("scheduleIdentifier")
        # api list format uses jobId.scope and jobId.code, we want job
        if isinstance(data.get("jobId", None), dict):
            data = data | {"job": data["jobId"]}
            data.pop("jobId")
        # promote the trigger fields up to the top and change case in timeZone
        if isinstance(data.get("trigger", None), dict):
            time_trigger = data["trigger"]["timeTrigger"]
            data = data | {
                "expression": time_trigger["expression"],
                "timezone": time_trigger["timeZone"]
            }
            data.pop("trigger")
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    @computed_field
    def job_id(self) -> Dict[str, str]:
        """Return the job identifier as a dictionary"""
        return {"scope": self.job.scope, "code": self.job.code}

    @computed_field
    def schedule_id(self) -> Dict[str, str]:
        return {"scope": self.scope, "code": self.code}

    @computed_field
    def trigger(self) -> Dict[str, Dict[str, str]]:
        time_trigger = {"timeTrigger": {"expression": self.expression}}

        if self.timezone is not None:
            time_trigger["timeTrigger"]["timeZone"] = self.timezone

        return time_trigger

    def read(self, client, old_state):
        get = client.get(f"/scheduler2/api/schedules/{old_state.scope}/{old_state.code}")
        current = get.json()
        # note scheduleId for create scheduleIdentifier for read :(
        current.pop("scheduleIdentifier")
        return current

    def create(self, client):
        body = self.model_dump(mode="json", exclude_none=True, by_alias=True,
           exclude={"job", "scope", "code", "expression", "timezone"}
        )
        client.post("/scheduler2/api/schedules", json=body)
        arg_keys = list(self.arguments.keys()) if self.arguments else []
        return ScheduleState(id=self.id, scope=self.scope, code=self.code, argKeys=arg_keys).model_dump()

    def update(self, client, old_state):
        if self.scope != old_state.scope or self.code != old_state.code:
            from_id = f"{old_state.scope}/{old_state.code}"
            to_id = f"{self.scope}/{self.code}"
            raise (RuntimeError(f"Cannot change schedule identifier. From: '{from_id}', to: '{to_id}'"))

        remote = self.read(client, old_state)
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
          exclude={"schedule_id", "job", "scope", "code", "expression", "timezone"}
        )
        effective = remote | desired
        # On read the schedule will contain schedule args and args from the job.
        # Only update if the user specified args are different to the remote
        effective["arguments"] = remote.get("arguments", {}) | desired.get("arguments", {})
        arg_keys = list(self.arguments.keys()) if self.arguments else []
        if effective == remote and arg_keys == getattr(old_state, "argKeys", []):
            return None
        client.put(f"/scheduler2/api/schedules/{self.scope}/{self.code}", json=desired)
        return ScheduleState(id=self.id, scope=self.scope, code=self.code, argKeys=arg_keys).model_dump()

    @staticmethod
    def delete(client, old_state):
        try:
            client.delete(f"/scheduler2/api/schedules/{old_state.scope}/{old_state.code}")
        except HTTPStatusError as ex:
            content = ex.response.json()
            if (
                ex.response.status_code == 404
                and content.get("name", None) == "ValidationError"
                and content.get("title", None) == "Schedule could not be found"
            ):
                pass  # don't throw if schedule was already deleted
            else:
                raise ex

    def deps(self):
        config_args: List[cfg.ItemRef | cfg.ItemResource] = (
            [
                value
                for value in self.arguments.values()
                if isinstance(value, (cfg.ItemRef, cfg.ItemResource))
            ]
            if self.arguments
            else []
        )

        return [self.job] + config_args + ([self.use_as_auth] if self.use_as_auth is not None else [])


@register_resource()
class ScheduleRef(BaseModel, Ref):
    """Used to reference an existing schedule """

    id: str = Field(exclude=True)
    scope: str
    code: str

    def attach(self, client):
        scope, code = self.scope, self.code
        try:
            client.get(f"/scheduler2/api/schedules/{scope}/{code}")
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Schedule {scope}/{code} not found")
            else:
                raise ex
