import json
from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import httpx
import pytest

from fbnconfig import configuration as cfg
from fbnconfig import scheduler
from fbnconfig.identity import UserRef, UserResource, UserType


def response_hook(response: httpx.Response) -> None:
    if response.is_error:
        response.read()
        response.raise_for_status()


def mock_upload_response_aws(dest_name, dest_tag):
    return {
        "dockerLoginCommand":
            "docker login -u AWS -p TOK1 foo.lusid.com",
        "buildVersionedDockerImageCommand":
            f"docker build -t foo/{dest_name}:{dest_tag} . --platform=linux/amd64",
        "tagVersionedDockerImageCommand":
            f"docker tag foo/{dest_name}:{dest_tag} foo.lusid.com/foo/{dest_name}:{dest_tag}",
        "pushVersionedDockerImageCommand":
            f"docker push foo.lusid.com/foo/{dest_name}:{dest_tag}",
        "tagLatestDockerImageCommand":
            f"docker tag foo/{dest_name}:{dest_tag} foo.lusid.com/foo/{dest_name}:latest",
        "pushLatestDockerImageCommand":
            f"docker push foo.lusid.com/foo/{dest_name}:latest",
        "expiryTime": "2024-01-30T17:15:58.6730000+00:00",
    }


def mock_upload_response_az(dest_name, dest_tag):
    return {
      "dockerLoginCommand":
          "docker login -u fbn-rob-az-token -p TOK1 fbnciaz.azurecr.io",
      "buildVersionedDockerImageCommand":
          f"docker build -t foo/{dest_name}:{dest_tag} . --platform=linux/amd64",
      "tagVersionedDockerImageCommand":
          f"docker tag foo/{dest_name}:{dest_tag} fbnciaz.azurecr.io/foo/{dest_name}:{dest_tag}",
      "pushVersionedDockerImageCommand":
          f"docker push fbnciaz.azurecr.io/foo/{dest_name}:{dest_tag}",
      "tagLatestDockerImageCommand":
          f"docker tag foo/{dest_name}:{dest_tag} fbnciaz.azurecr.io/foo/{dest_name}:latest",
      "pushLatestDockerImageCommand":
          f"docker push fbnciaz.azurecr.io/foo/{dest_name}:latest",
       "expiryTime": "2024-01-30T17:15:58.6730000+00:00",
}


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeImageRef:
    base_url = "https://foo.lusid.com"
    client = httpx.Client(base_url=base_url, event_hooks={"response": [response_hook]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote image exists with the required tag
        respx_mock.get("/scheduler2/api/images/repository/myimage").mock(
            return_value=httpx.Response(
                200,
                json={
                    "values": [
                        {
                            "name": "myimage",
                            "tags": [{"name": "0.1.0"}, {"name": "0.1.1"}, {"name": "latest"}],
                        }
                    ]
                },
            )
        )
        sut = scheduler.ImageRef(id="img1", dest_name="myimage", dest_tag="0.1.1")
        # when we call attach
        sut.attach(self.client)
        # then a get request was made and no exception raised

    def test_attach_when_missing_tag(self, respx_mock):
        # given the remote image exists but not with the required tag
        respx_mock.get("/scheduler2/api/images/repository/myimage").mock(
            return_value=httpx.Response(
                200,
                json={"values": [{"name": "myimage", "tags": [{"name": "0.1.0"}, {"name": "latest"}]}]},
            )
        )
        sut = scheduler.ImageRef(id="img1", dest_name="myimage", dest_tag="0.1.1")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(self.client)
        assert "Image with name myimage and tag 0.1.1 not found" in str(ex.value)

    def test_attach_when_http_not_found(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/scheduler2/api/images/repository/myimage").mock(
            return_value=httpx.Response(404, json={})
        )
        sut = scheduler.ImageRef(id="img1", dest_name="myimage", dest_tag="0.1.1")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(self.client)
        assert "Image with name myimage and tag 0.1.1 not found" in str(ex.value)


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeImage:
    base_url = "https://foo.lusid.com"
    client = httpx.Client(base_url=base_url)

    @staticmethod
    def test_read():
        img = scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        img.read(httpx.Client(), SimpleNamespace())
        assert img.id == "image1"

    def test_delete(self):
        old_state = {
            "id": "image1",
            "source_image": "docker.io/alpine:5",
            "dest_name": "dest_alpine",
            "dest_tag": "v1",
        }
        # delete does nothing because we can't delete an image that's been uploaded
        sut = scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        sut.delete(self.client, old_state)

    @staticmethod
    def test_commands():
        sut = scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        user = "AWS"
        password = "TOK1"
        reghost = "foo.lusid.com"
        downstream_tag = "foo.lusid.com/foo/beany:v1"
        source_image = "docker.io/alpine:5"
        commands = (
            sut._pull_commands(source_image)
            + sut._tag_commands(downstream_tag)
            + sut._push_commands(downstream_tag, user, password, reghost)
        )
        assert commands == [
            ["docker", "pull", "--platform", "linux/amd64", "-q", "docker.io/alpine:5"],
            ["docker", "tag", "docker.io/alpine:5", "foo.lusid.com/foo/beany:v1"],
            ["docker", "login", "-u", "AWS", "--password", "TOK1", "foo.lusid.com"],
            ["docker", "push", "-q", "foo.lusid.com/foo/beany:v1"],
        ]

    @patch("subprocess.run")
    def test_create_no_matching_downstream_aws(self, mock_run, respx_mock):
        # given we have not pushed this image to an AWS lusid before
        def process_mock(args, **kwargs):
            if args[1] == "inspect":
                ret = MagicMock()
                ret.stdout = '["alpine@sha256:aaabbbccc"]'
                return ret
            return MagicMock()

        mock_run.side_effect = process_mock
        upload = mock_upload_response_aws("dest_alpine", "not_the_real_tag")
        respx_mock.post("/scheduler2/api/images").mock(side_effect=[httpx.Response(200, json=upload)])
        # when we create it
        sut = scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        new_state = sut.create(self.client)
        # then the new state is correct
        assert new_state == {
            "id": "image1",
            "source_image": "docker.io/alpine:5",
            "dest_name": "dest_alpine",
            "dest_tag": "v1",
        }
        # and the post method on scheduler gets the stock commands
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == f"{self.base_url}/scheduler2/api/images"
        # and docker pull was called on the upstream
        assert len(mock_run.call_args_list) == 5
        pull_args = next(a[0][0] for a in mock_run.call_args_list if a[0][0][1] == "pull")
        assert pull_args == ["docker", "pull", "--platform", "linux/amd64", "-q", "docker.io/alpine:5"]
        # and the upstream was tagged with the downstream image
        tag_args = next(a[0][0] for a in mock_run.call_args_list if a[0][0][1] == "tag")
        assert tag_args == ["docker", "tag", "docker.io/alpine:5", "foo.lusid.com/foo/dest_alpine:v1"]
        # and docker push was called on the downstream image
        push_args = next(a[0][0] for a in mock_run.call_args_list if a[0][0][1] == "push")
        assert push_args == ["docker", "push", "-q", "foo.lusid.com/foo/dest_alpine:v1"]

    @patch("subprocess.run")
    def test_create_no_matching_downstream_az(self, mock_run, respx_mock):
        # given we have not pushed this image to an azure lusid before
        def process_mock(args, **kwargs):
            if args[1] == "inspect":
                ret = MagicMock()
                ret.stdout = '["alpine@sha256:aaabbbccc"]'
                return ret
            return MagicMock()

        mock_run.side_effect = process_mock
        # the az variant of the commands response
        upload = mock_upload_response_az("dest_alpine", "not_the_real_tag")
        respx_mock.post("/scheduler2/api/images").mock(side_effect=[httpx.Response(200, json=upload)])
        # when we create it
        sut = scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        new_state = sut.create(self.client)
        # then the new state is correct
        assert new_state == {
            "id": "image1",
            "source_image": "docker.io/alpine:5",
            "dest_name": "dest_alpine",
            "dest_tag": "v1",
        }
        # and the post method on scheduler gets the stock commands
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == f"{self.base_url}/scheduler2/api/images"
        # and docker pull was called on the upstream
        assert len(mock_run.call_args_list) == 5
        pull_args = next(a[0][0] for a in mock_run.call_args_list if a[0][0][1] == "pull")
        assert pull_args == ["docker", "pull", "--platform", "linux/amd64", "-q", "docker.io/alpine:5"]
        # and the upstream was tagged with the downstream image which uses the container registry
        # host instead of the lusid domain
        tag_args = next(a[0][0] for a in mock_run.call_args_list if a[0][0][1] == "tag")
        assert tag_args == [
            "docker",
            "tag",
            "docker.io/alpine:5",
            "fbnciaz.azurecr.io/foo/dest_alpine:v1"
        ]
        # and docker push was called on the downstream image
        push_args = next(a[0][0] for a in mock_run.call_args_list if a[0][0][1] == "push")
        assert push_args == ["docker", "push", "-q", "fbnciaz.azurecr.io/foo/dest_alpine:v1"]

    @patch("subprocess.run")
    def test_create_no_matching_downstream_no_pull(self, mock_run, respx_mock):
        # given we have not pushed this image to lusid before
        def process_mock(args, **kwargs):
            if args[1] == "inspect":
                ret = MagicMock()
                ret.stdout = '["alpine@sha256:aaabbbccc"]'
                return ret
            return MagicMock()

        mock_run.side_effect = process_mock
        upload = mock_upload_response_aws("dest_alpine", "not_the_tag")
        respx_mock.post("/scheduler2/api/images").mock(side_effect=[httpx.Response(200, json=upload)])
        # given a new image with no pull so we upload the local image
        sut = scheduler.ImageResource(
            id="image1",
            source_image="alpine:5",
            dest_name="dest_alpine",
            dest_tag="v1",
            pull_upstream=False,
        )
        # when we create it
        new_state = sut.create(self.client)
        # then the new state is correct
        assert new_state == {
            "id": "image1",
            "source_image": "alpine:5",
            "dest_name": "dest_alpine",
            "dest_tag": "v1",
        }
        # and the post method on scheduler gets the stock commands
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == f"{self.base_url}/scheduler2/api/images"
        # and docker pull was NOT called to fetch the usptream
        pull_args = [a[0][0] for a in mock_run.call_args_list if a[0][0][1] == "pull"]
        assert len(pull_args) == 0
        # and the existing local image was tagged with the downstream name
        tag_args = next(a[0][0] for a in mock_run.call_args_list if a[0][0][1] == "tag")
        assert tag_args == ["docker", "tag", "alpine:5", "foo.lusid.com/foo/dest_alpine:v1"]
        # and docker push was called on the upstream image
        assert len(mock_run.call_args_list) == 4
        push_args = next(a[0][0] for a in mock_run.call_args_list if a[0][0][1] == "push")
        assert push_args == ["docker", "push", "-q", "foo.lusid.com/foo/dest_alpine:v1"]

    @patch("subprocess.run")
    def test_create_image_already_exists_downstream(self, mock_run, respx_mock):
        # given we have pushed this image to lusid but it's not in the old_state
        # (maybe we deleted the state but the image can't be deleted)
        def process_mock(args, **kwargs):
            if args[1] == "inspect":
                ret = MagicMock()
                ret.stdout = (
                    '["alpine@sha256:aaabbbccc", "foo.lusid.com/foo/dest_alpine@sha256:123456abcdef"]'
                )
                return ret
            return MagicMock()

        mock_run.side_effect = process_mock
        # the api gives us the commands
        upload = mock_upload_response_aws("dest_alpine", "not_the_tag")
        respx_mock.post("/scheduler2/api/images").mock(side_effect=[httpx.Response(200, json=upload)])
        # the image exists in the downstream repo
        respx_mock.get("/scheduler2/api/images/repository/dest_alpine").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {"digest": "sha256:7654321", "tags": [{"name": "not_mine"}]},
                            {"digest": "sha256:123456abcdef", "tags": [{"name": "v3"}, {"name": "v1"}]},
                        ]
                    },
                )
            ]
        )
        # given a new image
        sut = scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        # when we call create
        new_state = sut.create(self.client)
        # then the new state is correct
        assert new_state == {
            "id": "image1",
            "source_image": "docker.io/alpine:5",
            "dest_name": "dest_alpine",
            "dest_tag": "v1",
        }
        # the image with matching digest and tag in ecr is detected so
        #     we didn't upload the image with push
        #     we didn't call the post image endpoint
        assert len(mock_run.call_args_list) == 3

    @staticmethod
    def test_deps():
        # given an image
        sut = scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        # it doesn't have any dependencies
        assert sut.deps() == []

    def test_update_no_change(self):
        # given an existing job
        old_state = SimpleNamespace(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        # when we update with the same options
        sut = scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        new_state = sut.update(self.client, old_state)
        # then the state is None indicating no change
        assert new_state is None

    @patch("subprocess.run")
    def test_update_new_tag(self, mock_run, respx_mock):
        upload = mock_upload_response_aws("dest_alpine", "not_the_tag")
        respx_mock.post("/scheduler2/api/images").mock(side_effect=[httpx.Response(200, json=upload)])

        # given docker inspect will not return a downstream tag
        def process_mock(args, **kwargs):
            if args[1] == "inspect":
                ret = MagicMock()
                ret.stdout = '["alpine@sha256:aaabbbccc"]'
                return ret
            return MagicMock()

        mock_run.side_effect = process_mock
        # given an existing job using v0 of the image
        old_state = SimpleNamespace(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v0"
        )
        # when we update to v1
        sut = scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )
        # then the new state is v1
        new_state = sut.update(self.client, old_state)
        assert new_state == {
            "id": "image1",
            "source_image": "docker.io/alpine:5",
            "dest_name": "dest_alpine",
            "dest_tag": "v1",
        }
        # and v1 gets pushed
        mock_run.assert_called_with(["docker", "push", "-q", "foo.lusid.com/foo/dest_alpine:v1"])

    def test_dump(self):
        # given an image resource
        sut = scheduler.ImageResource(
            id="img1", source_image="docker.io/alpine:3.16.7", dest_name="myimage", dest_tag="3.16.7"
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )
        # then the dumped state is correct
        assert dumped == {
            "id": "img1",
            "sourceImage": "docker.io/alpine:3.16.7",
            "destName": "myimage",
            "destTag": "3.16.7",
        }

    def test_undump(self):
        # given a dumped image state
        dumped = {
            "id": "img1",
            "sourceImage": "docker.io/alpine:3.16.7",
            "destName": "myimage",
            "destTag": "3.16.7",
        }
        # when we undump it
        sut = scheduler.ImageResource.model_validate(
            dumped, context={"style": "dump", "$refs": {}, "id": "img1"}
        )
        # then the id has been extracted from the context
        assert sut.id == "img1"
        assert sut.source_image == "docker.io/alpine:3.16.7"
        assert sut.dest_name == "myimage"
        assert sut.dest_tag == "3.16.7"
        assert sut.pull_upstream is True  # default value


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeJobRef:
    base_url = "https://foo.lusid.com"
    client = httpx.Client(base_url=base_url)

    def test_attach_when_remote_exists(self, respx_mock):
        # given that a job is returned from the list call
        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(200, json={"values": [{"name": "job name", "argumentDefinitions": {}}]})
            ]
        )
        # when we create a JobRef
        sut = scheduler.JobRef(id="10", scope="scope_a", code="code_a")
        sut.attach(self.client)
        # then no exception

    def test_attach_when_remote_exists_with_argument_definition(self, respx_mock):
        # given that a job is returned from the list call
        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {
                                "name": "job name",
                                "argumentDefinitions": {
                                    "someargument": {
                                        "dataType": "String",
                                        "required": True,
                                        "description": "my argument",
                                        "order": 1,
                                        "constraints": "None",
                                        "passedAs": "CommandLine",
                                        "defaultValue": "somedefaultvalue",
                                    }
                                },
                            }
                        ]
                    },
                )
            ]
        )

        # when we create a JobRef
        sut = scheduler.JobRef(id="10", scope="scope_a", code="code_a")
        sut.attach(self.client)
        # then no exception

    def test_attach_when_no_remote(self, respx_mock):
        # given that a job is returned from the list call
        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[httpx.Response(200, json={"values": []})]
        )
        # when we create a JobRef
        with pytest.raises(RuntimeError):
            sut = scheduler.JobRef(id="10", scope="scope_a", code="code_a")
            sut.attach(self.client)
            # then an exception is thrown


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeJob:
    def setup_class(self):
        scheduler.JobResource.ScanTimeoutParameters.tries = 3
        scheduler.JobResource.ScanTimeoutParameters.wait_time = 0

    base_url = "https://foo.lusid.com"
    jobs_url = "/scheduler2/api/jobs"

    client = httpx.Client(base_url=base_url, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def existing_image(self):
        return scheduler.ImageResource(
            id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
        )

    @pytest.fixture
    def image_scan_stub(self):
        return self.image_scan_value("dest_alpine", "v1", "COMPLETE")

    @pytest.fixture
    def config_item_ref(self):
        set = cfg.SetRef(id="set", scope="cfgscope", code="cfgcode", type=cfg.SetType.PERSONAL)
        item = cfg.ItemRef(id="item", set=set, key="itemkey")
        # fake the item being attached
        item.ref = "config://123"
        return item

    def test_create_with_config_arg(self, respx_mock, existing_image, config_item_ref, image_scan_stub):
        respx_mock.get(f"/scheduler2/api/images/repository/{existing_image.dest_name}").mock(
            side_effect=httpx.Response(200, json={"values": [image_scan_stub]})
        )
        # given an existing image
        # and a config item that's already got a ref
        # when we create a job using the config item as a default arg value
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={
                "myargument1": scheduler.EnvironmentArg(
                    data_type="String",
                    required=True,
                    description="a description",
                    order=1,
                    default_value=config_item_ref,
                ),
                "myargument2": scheduler.CommandlineArg(
                    data_type="Int",
                    required=False,
                    description="other description",
                    order=2,
                    default_value="3",
                ),
            },
        )
        respx_mock.post("/scheduler2/api/jobs").mock(
            side_effect=[httpx.Response(200, json={"name": "job name"})]
        )
        new_state = sut.create(self.client)
        # the state is created
        assert new_state == {"id": "job1", "scope": "scope1", "code": "code1"}
        # and the post is made to create the job passing the config
        # item ref in the argument
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == f"{self.base_url}/scheduler2/api/jobs"
        assert json.loads(request.content) == {
            "jobId": {"scope": "scope1", "code": "code1"},
            "imageName": "dest_alpine",
            "imageTag": "v1",
            "name": "job name",
            "description": "a job",
            "argumentDefinitions": {
                "myargument1": {
                    "dataType": "String",
                    "required": True,
                    "description": "a description",
                    "order": 1,
                    "passedAs": "EnvironmentVariable",
                    "defaultValue": "config://123",
                },
                "myargument2": {
                    "dataType": "Int",
                    "required": False,
                    "description": "other description",
                    "order": 2,
                    "passedAs": "CommandLine",
                    "defaultValue": "3",
                },
            },
        }

    def test_create(self, respx_mock, existing_image, image_scan_stub):
        respx_mock.get(f"/scheduler2/api/images/repository/{existing_image.dest_name}").mock(
            side_effect=httpx.Response(200, json={"values": [image_scan_stub]})
        )

        # given an existing image
        # when we create a job
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={
                "myargument1": scheduler.EnvironmentArg(
                    data_type="String",
                    required=True,
                    description="a description",
                    order=1,
                    default_value=None,
                ),
                "myargument2": scheduler.CommandlineArg(
                    data_type="Int",
                    required=False,
                    description="other description",
                    order=2,
                    default_value="3",
                ),
            },
        )

        respx_mock.post("/scheduler2/api/jobs").mock(
            side_effect=[httpx.Response(200, json={"name": "job name"})]
        )

        new_state = sut.create(self.client)
        # the state is created
        assert new_state == {"id": "job1", "scope": "scope1", "code": "code1"}

        # and the post is made to create the job
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == f"{self.base_url}/scheduler2/api/jobs"
        assert json.loads(request.content) == {
            "jobId": {"scope": "scope1", "code": "code1"},
            "imageName": "dest_alpine",
            "imageTag": "v1",
            "name": "job name",
            "description": "a job",
            "argumentDefinitions": {
                "myargument1": {
                    "dataType": "String",
                    "required": True,
                    "description": "a description",
                    "order": 1,
                    "passedAs": "EnvironmentVariable",
                },
                "myargument2": {
                    "dataType": "Int",
                    "required": False,
                    "description": "other description",
                    "order": 2,
                    "passedAs": "CommandLine",
                    "defaultValue": "3",
                },
            },
        }

    def test_update_no_change(self, respx_mock, existing_image):
        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {
                                "name": "job name",
                                "jobId": {},
                                "dockerImage": "dest_alpine:v1",
                                "description": "a job",
                                "minCpu": "1",
                                "maxCpu": "2",
                                "dateCreated": "2023-01-02",
                                "requiredResources": {
                                    "lusidApis": [],
                                    "lusidFileSystem": [],
                                    "externalCalls": [],
                                },
                                "commandLineArgumentSeparator": " ",
                                "author": "bob",
                                "argumentDefinitions": {
                                    "arg1": {
                                        "dataType": "String",
                                        "required": True,
                                        "description": "some",
                                        "order": 1,
                                        "constraints": "None",
                                        "passedAs": "CommandLine",
                                    }
                                },
                            }
                        ]
                    },
                )
            ]
        )
        old_state = SimpleNamespace(id="job1", scope="scope1", code="code1")
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={
                "arg1": scheduler.CommandlineArg(
                    data_type="String", required=True, description="some", order=1
                )
            },
        )
        new_state = sut.update(self.client, old_state)
        assert new_state is None

    def test_update_leaves_default_fields(self, respx_mock, existing_image):
        # given a job with an author (a field which is defaulted by the api)
        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {
                                "name": "job name",
                                "jobId": {},
                                "author": "somebody",
                                "dockerImage": "dest_alpine:v1",
                                "description": "a job",
                                "requiredResources": {
                                    "lusidApis": [],
                                    "lusidFileSystem": [],
                                    "externalCalls": [],
                                },
                                "commandLineArgumentSeparator": " ",
                                "argumentDefinitions": {},
                            }
                        ]
                    },
                )
            ]
        )
        # when we update and leave the author blank
        old_state = SimpleNamespace(id="job1", scope="scope1", code="code1")
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
        )
        new_state = sut.update(self.client, old_state)
        # then no request is made so we preserve the default
        assert new_state is None

    def test_update_modify_default_field(self, respx_mock, existing_image, image_scan_stub):
        # given a job with an author (a field which is defaulted by the api)
        respx_mock.get(f"/scheduler2/api/images/repository/{existing_image.dest_name}").mock(
            side_effect=httpx.Response(200, json={"values": [image_scan_stub]})
        )

        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {
                                "name": "job name",
                                "jobId": {},
                                "author": "somebody",
                                "dockerImage": "dest_alpine:v1",
                                "description": "a job",
                                "requiredResources": {
                                    "lusidApis": [],
                                    "lusidFileSystem": [],
                                    "externalCalls": [],
                                },
                                "commandLineArgumentSeparator": " ",
                                "argumentDefinitions": {},
                            }
                        ]
                    },
                )
            ]
        )
        respx_mock.put("/scheduler2/api/jobs/scope1/code1").mock(
            side_effect=[httpx.Response(200, json={"name": "different job name"})]
        )
        # when we provide a value for author
        old_state = SimpleNamespace(id="job1", scope="scope1", code="code1")
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            author="someone else",
        )
        new_state = sut.update(self.client, old_state)
        # then the new state the same as the old one
        assert new_state == {"id": "job1", "scope": "scope1", "code": "code1"}
        # and a request is made to change the author
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content)["author"] == "someone else"

    def test_update_default_field_same_value(self, respx_mock, existing_image):
        # given a job with an author (a field which is defaulted by the api)
        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {
                                "name": "job name",
                                "jobId": {},
                                "author": "somebody",
                                "dockerImage": "dest_alpine:v1",
                                "description": "a job",
                                "requiredResources": {
                                    "lusidApis": [],
                                    "lusidFileSystem": [],
                                    "externalCalls": [],
                                },
                                "commandLineArgumentSeparator": " ",
                                "argumentDefinitions": {},
                            }
                        ]
                    },
                )
            ]
        )
        # when the desired author is specified but is the same as the remote
        old_state = SimpleNamespace(id="job1", scope="scope1", code="code1")
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            author="somebody",
        )
        new_state = sut.update(self.client, old_state)
        # then the new state is None because no modification is required
        assert new_state is None
        # and no put request is made to change

    def test_update_change_name(self, respx_mock, existing_image, image_scan_stub):
        # given an existing job with name 'a job'
        respx_mock.get(f"/scheduler2/api/images/repository/{existing_image.dest_name}").mock(
            side_effect=httpx.Response(200, json={"values": [image_scan_stub]})
        )

        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {
                                "name": "job name",
                                "jobId": {},
                                "author": "bob",
                                "dockerImage": "dest_alpine:v1",
                                "description": "a job",
                                "requiredResources": {
                                    "lusidApis": [],
                                    "lusidFileSystem": [],
                                    "externalCalls": [],
                                },
                                "commandLineArgumentSeparator": " ",
                                "argumentDefinitions": {},
                            }
                        ]
                    },
                )
            ]
        )
        respx_mock.put("/scheduler2/api/jobs/scope1/code1").mock(
            side_effect=[httpx.Response(200, json={"name": "different job name"})]
        )
        # when we update to 'different job name'
        old_state = SimpleNamespace(id="job1", scope="scope1", code="code1")
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="different job name",
            description="a job",
        )
        new_state = sut.update(self.client, old_state)
        # then the new state is created
        assert new_state == {"id": "job1", "scope": "scope1", "code": "code1"}
        # and the post is made to create the job
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url == f"{self.base_url}/scheduler2/api/jobs/scope1/code1"
        assert json.loads(request.content) == {
            "argumentDefinitions": {},
            "description": "a job",
            "name": "different job name",
            "imageName": "dest_alpine",
            "imageTag": "v1",
        }

    def test_update_changed_argument_names(self, respx_mock, existing_image, image_scan_stub):
        # given an existing job arg1 only
        respx_mock.get(f"/scheduler2/api/images/repository/{existing_image.dest_name}").mock(
            side_effect=httpx.Response(200, json={"values": [image_scan_stub]})
        )
        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {
                                "name": "job name",
                                "jobId": {},
                                "author": "bob",
                                "dockerImage": "dest_alpine:v1",
                                "description": "a job",
                                "requiredResources": {
                                    "lusidApis": [],
                                    "lusidFileSystem": [],
                                    "externalCalls": [],
                                },
                                "commandLineArgumentSeparator": " ",
                                "argumentDefinitions": {
                                    "arg1": {
                                        "dataType": "String",
                                        "required": True,
                                        "description": "some",
                                        "order": 1,
                                        "constraints": "None",
                                        "passedAs": "CommandLine",
                                    }
                                },
                            }
                        ]
                    },
                )
            ]
        )
        respx_mock.put("/scheduler2/api/jobs/scope1/code1").mock(
            side_effect=[httpx.Response(200, json={"name": "different job name"})]
        )
        old_state = SimpleNamespace(id="job1", scope="scope1", code="code1")
        # when we update with a desired state where arg1 is removed and arg2 is added
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={
                "arg2": scheduler.EnvironmentArg(
                    data_type="Configuration", required=True, description="some", order=1
                )
            },
        )
        # then it is detected as a change and arg2 is sent
        new_state = sut.update(self.client, old_state)
        assert new_state == {"id": "job1", "scope": "scope1", "code": "code1"}
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url == f"{self.base_url}/scheduler2/api/jobs/scope1/code1"
        assert json.loads(request.content) == {
            "argumentDefinitions": {
                "arg2": {
                    "dataType": "Configuration",
                    "required": True,
                    "description": "some",
                    "order": 1,
                    "passedAs": "EnvironmentVariable",
                }
            },
            "description": "a job",
            "name": "job name",
            "imageName": "dest_alpine",
            "imageTag": "v1",
        }

    def test_update_when_removing_default_value(self, respx_mock, existing_image, image_scan_stub):
        respx_mock.get(f"/scheduler2/api/images/repository/{existing_image.dest_name}").mock(
            side_effect=httpx.Response(200, json={"values": [image_scan_stub]})
        )
        # given an existing job with arg1 that has a default value
        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {
                                "name": "job name",
                                "jobId": {},
                                "author": "bob",
                                "dockerImage": "dest_alpine:v1",
                                "description": "a job",
                                "requiredResources": {
                                    "lusidApis": [],
                                    "lusidFileSystem": [],
                                    "externalCalls": [],
                                },
                                "commandLineArgumentSeparator": " ",
                                "argumentDefinitions": {
                                    "arg1": {
                                        "dataType": "String",
                                        "required": True,
                                        "description": "some",
                                        "order": 1,
                                        "constraints": "None",
                                        "passedAs": "EnvironmentVariable",
                                        "defaultValue": "somevalue",
                                    }
                                },
                            }
                        ]
                    },
                )
            ]
        )

        respx_mock.put("/scheduler2/api/jobs/scope1/code1").mock(
            side_effect=[httpx.Response(200, json={"name": "different job name"})]
        )
        old_state = SimpleNamespace(id="job1", scope="scope1", code="code1")
        # when we update with a desired state where arg1 default value is removed
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={
                "arg1": scheduler.EnvironmentArg(
                    data_type="String", required=True, description="some", order=1
                )
            },
        )
        # then it is detected as a change and arg1 is sent
        new_state = sut.update(self.client, old_state)
        assert new_state == {"id": "job1", "scope": "scope1", "code": "code1"}
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url == f"{self.base_url}/scheduler2/api/jobs/scope1/code1"
        assert json.loads(request.content) == {
            "argumentDefinitions": {
                "arg1": {
                    "dataType": "String",
                    "required": True,
                    "description": "some",
                    "order": 1,
                    "passedAs": "EnvironmentVariable",
                }
            },
            "description": "a job",
            "name": "job name",
            "imageName": "dest_alpine",
            "imageTag": "v1",
        }

    def test_update_merges_args(self, respx_mock, existing_image, image_scan_stub):
        # given an existing job
        respx_mock.get(f"/scheduler2/api/images/repository/{existing_image.dest_name}").mock(
            side_effect=httpx.Response(200, json={"values": [image_scan_stub]})
        )

        respx_mock.get("/scheduler2/api/jobs").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            {
                                "name": "job name",
                                "jobId": {},
                                "author": "bob",
                                "dockerImage": "dest_alpine:v1",
                                "description": "a job",
                                "requiredResources": {
                                    "lusidApis": [],
                                    "lusidFileSystem": [],
                                    "externalCalls": [],
                                },
                                "commandLineArgumentSeparator": " ",
                                "argumentDefinitions": {
                                    "arg1": {
                                        "dataType": "String",
                                        "required": True,
                                        "description": "some",
                                        "order": 1,
                                        "constraints": "None",
                                        "passedAs": "CommandLine",
                                    }
                                },
                            }
                        ]
                    },
                )
            ]
        )
        respx_mock.put("/scheduler2/api/jobs/scope1/code1").mock(
            side_effect=[httpx.Response(200, json={"name": "different job name"})]
        )
        old_state = SimpleNamespace(id="job1", scope="scope1", code="code1")
        # when we update with a field inside the argument changed (required=False)
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={
                "arg1": scheduler.CommandlineArg(
                    data_type="String", required=False, description="some", order=1
                )
            },
        )
        # then it is detected as a change and the modified arg is sent
        new_state = sut.update(self.client, old_state)
        assert new_state == {"id": "job1", "scope": "scope1", "code": "code1"}
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url == f"{self.base_url}/scheduler2/api/jobs/scope1/code1"
        assert json.loads(request.content) == {
            "argumentDefinitions": {
                "arg1": {
                    "dataType": "String",
                    "required": False,
                    "description": "some",
                    "order": 1,
                    "passedAs": "CommandLine",
                }
            },
            "description": "a job",
            "name": "job name",
            "imageName": "dest_alpine",
            "imageTag": "v1",
        }

    def test_deps(self, existing_image):
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="different job name",
            description="a job",
        )
        assert sut.deps() == [existing_image]

    def test_deps_with_config_item(self, existing_image, config_item_ref):
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="different job name",
            description="a job",
            argument_definitions={
                "myargument1": scheduler.EnvironmentArg(
                    data_type="String",
                    required=True,
                    description="a description",
                    order=1,
                    default_value=config_item_ref,
                )
            },
        )
        assert sut.deps() == [existing_image, config_item_ref]

    @staticmethod
    def image_scan_value(name: str, tag: str, scan_status: str) -> Dict[Any, Any]:
        return {
            "name": name,
            "pushTime": "2024-11-22T15:11:39.9570000+00:00",
            "digest": "sha256:0e5733c4ffc5317a24dcd10adbe5dbe0499f641a3b13a74a118ac5059385f605",
            "size": 586206179,
            "tags": [
                {
                    "name": tag,
                    "pullTime": "0001-01-01T00:00:00.0000000+00:00",
                    "pushTime": "0001-01-01T00:00:00.0000000+00:00",
                    "signed": False,
                    "immutable": False,
                },
                {
                    "name": "00000",
                    "pullTime": "0001-01-01T00:00:00.0000000+00:00",
                    "pushTime": "0001-01-01T00:00:00.0000000+00:00",
                    "signed": False,
                    "immutable": False,
                },
            ],
            "scanStatus": scan_status,
            "scanSummary": {},
        }

    def test_vulnerability_scan_multiple_fail(self, respx_mock, existing_image):
        # given: there are mutliple images in the repository.
        # An old one which # was scanned ok,
        # the one this job is referencing which failed the scan
        dest_name = existing_image.dest_name
        dest_tag = existing_image.dest_tag
        respx_mock.get("/scheduler2/api/images/repository/dest_alpine").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            self.image_scan_value(dest_name, dest_tag, "FAILED"),
                            self.image_scan_value(dest_name, "other_tag", "COMPLETE"),
                        ]
                    },
                )
            ]
        )
        # when we check the scan
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={},
        )
        # then it fails because the image/tag combination this job uses has failed the scan
        with pytest.raises(RuntimeError, match="Image vulnerability scan failed."):
            sut._wait_for_vulnerability_scan(self.client)

    def test_vulnerability_scan_multiple_success(self, respx_mock, existing_image):
        # given: there are mutliple images in the repository. An old one which
        # failed the scan, and the one this job is referencing which completes
        dest_name = existing_image.dest_name
        respx_mock.get("/scheduler2/api/images/repository/dest_alpine").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            self.image_scan_value(dest_name, existing_image.dest_tag, "COMPLETE"),
                            self.image_scan_value(dest_name, "other_tag", "FAILED"),
                        ]
                    },
                )
            ]
        )
        # when we check the scan
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={},
        )
        # then it completes because the referenced image is ok
        sut._wait_for_vulnerability_scan(self.client)

    def test_vulnerability_scan_waits_for_complete(self, respx_mock, existing_image):
        # given the scan is in progress at the time the job is created
        # and then completes with a successful scan
        respx_mock.get("/scheduler2/api/images/repository/dest_alpine").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            self.image_scan_value(existing_image.dest_name, existing_image.dest_tag, "")
                        ]
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "values": [
                            self.image_scan_value(
                                existing_image.dest_name, existing_image.dest_tag, "IN_PROGRESS"
                            )
                        ]
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "values": [
                            self.image_scan_value(
                                existing_image.dest_name, existing_image.dest_tag, "COMPLETE"
                            )
                        ]
                    },
                ),
            ]
        )
        # when we check the scan
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={},
        )
        # then it is successful because the final state of the scan is COMPLETE
        sut._wait_for_vulnerability_scan(self.client)

    @pytest.mark.parametrize(
        "terminal_state",
        ["FAILED", "UNSUPPORTED_IMAGE", "SCAN_ELIGIBILITY_EXPIRED", "FINDINGS_UNAVAILABLE"],
    )
    def test_wait_for_vulnerability_scan_failure(self, respx_mock, existing_image, terminal_state):
        # given the scan is in progress when the job is created and results
        # in any of the failure states
        respx_mock.get("/scheduler2/api/images/repository/dest_alpine").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            self.image_scan_value(existing_image.dest_name, existing_image.dest_tag, "")
                        ]
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "values": [
                            self.image_scan_value(
                                existing_image.dest_name, existing_image.dest_tag, "IN_PROGRES"
                            )
                        ]
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "values": [
                            self.image_scan_value(
                                existing_image.dest_name, existing_image.dest_tag, terminal_state
                            )
                        ]
                    },
                ),
            ]
        )
        # when we check the scan
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={},
        )
        # then an exception is raised which causes the job update to fail
        with pytest.raises(RuntimeError, match="Image vulnerability scan failed."):
            sut._wait_for_vulnerability_scan(self.client)

    def test_wait_for_vulnerability_scan_timeout(self, respx_mock, existing_image):
        # given the scan is in progress and stays in progress for 4 requests
        # where our scan tries is 3
        respx_mock.get("/scheduler2/api/images/repository/dest_alpine").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "values": [
                            self.image_scan_value(
                                existing_image.dest_name, existing_image.dest_tag, "IN_PROGRESS"
                            )
                        ]
                    },
                )
            ]
            * 4
        )
        # when we wait for the scan
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={},
        )
        # then a timeout exception is raised because the scan did not complete in time
        with pytest.raises(RuntimeError, match="Image vulnerability scan timed out."):
            sut._wait_for_vulnerability_scan(self.client)

    def test_dump_with_config_arg(self, existing_image, config_item_ref):
        # given a resource
        sut = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=existing_image,
            name="job name",
            description="a job",
            argument_definitions={
                "myargument1": scheduler.EnvironmentArg(
                    data_type="String",
                    required=True,
                    description="a description",
                    order=1,
                    default_value=config_item_ref,
                ),
                "myargument2": scheduler.CommandlineArg(
                    data_type="Int",
                    required=False,
                    description="other description",
                    order=2,
                    default_value="3",
                ),
            },
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True, exclude_none=True, round_trip=True, context={"style": "dump"}
        )
        # then:
        assert dumped == {
            "scope": "scope1",  # it has scope/code instead of jobId
            "code": "code1",
            "image": {"$ref": existing_image.id},  # the image is a $ref
            "name": "job name",
            "description": "a job",
            "argumentDefinitions": {
                "myargument1": {
                    "dataType": "String",
                    "required": True,
                    "description": "a description",
                    "order": 1,
                    "passedAs": "EnvironmentVariable",
                    "defaultValue": {"$ref": config_item_ref.id},  # config item is $ref
                },
                "myargument2": {
                    "dataType": "Int",
                    "required": False,
                    "description": "other description",
                    "order": 2,
                    "passedAs": "CommandLine",
                    "defaultValue": "3",
                },
            },
        }

    def test_undump(self, existing_image, config_item_ref):
        # given a dumped resource
        dumped = {
            "scope": "scope1",
            "code": "code1",
            "image": {"$ref": existing_image.id},
            "name": "job name",
            "description": "a job",
            "argumentDefinitions": {
                "myargument1": {
                    "dataType": "String",
                    "required": True,
                    "description": "a description",
                    "order": 1,
                    "passedAs": "EnvironmentVariable",
                    "defaultValue": {"$ref": config_item_ref.id},
                },
                "myargument2": {
                    "dataType": "Int",
                    "required": False,
                    "description": "other description",
                    "order": 2,
                    "passedAs": "CommandLine",
                    "defaultValue": "3",
                },
            },
        }
        # when we undump it
        sut = scheduler.JobResource.model_validate(
            dumped,
            context={
                "style": "dump",
                "id": "job1",
                "$refs": {existing_image.id: existing_image, config_item_ref.id: config_item_ref},
            },
        )
        # then scope/code are read
        assert sut.scope == dumped["scope"]
        assert sut.code == dumped["code"]
        # the image is wired up to the resource
        assert sut.image == existing_image
        # the id field has been extracted from the context
        assert sut.id == "job1"
        # the config $ref has been wired up to the config item provided
        assert sut.argument_definitions["myargument1"].default_value == config_item_ref
        assert sut.name == dumped["name"]
        assert sut.description == dumped["description"]

    def test_parse_api_format_list_response(self, existing_image, config_item_ref):
        # given a job in the same format as list jobs returns (jobId.scope and jobId.code)
        # and "dockerImage" as a single item
        # but with refs for the related objects
        resp = {
            "jobId": {"scope": "scope1", "code": "code1"},
            "dockerImage": {"$ref": existing_image.id},
            "name": "job name",
            "description": "a job",
            "argumentDefinitions": {
                "myargument1": {
                    "dataType": "String",
                    "required": True,
                    "description": "a description",
                    "order": 1,
                    "passedAs": "EnvironmentVariable",
                    "defaultValue": {"$ref": config_item_ref.id},
                },
                "myargument2": {
                    "dataType": "Int",
                    "required": False,
                    "description": "other description",
                    "order": 2,
                    "passedAs": "CommandLine",
                    "defaultValue": "3",
                },
            },
        }
        # when we parse it
        sut = scheduler.JobResource.model_validate(
            resp,
            context={
                "$refs": {existing_image.id: existing_image, config_item_ref.id: config_item_ref},
                "id": "job1",
            },
        )
        # then the scope and code are from the jobId
        assert sut.scope == "scope1"
        assert sut.code == "code1"
        # and the first argument is an env var
        first_arg = sut.argument_definitions["myargument1"]
        assert isinstance(first_arg, scheduler.EnvironmentArg)
        assert isinstance(first_arg.default_value, cfg.ItemRef)
        # with the config ref resolved
        assert first_arg.default_value.id == config_item_ref.id
        # and the second is a commandline
        assert isinstance(sut.argument_definitions["myargument2"], scheduler.CommandlineArg)


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeSchedule:
    base_url = "https://foo.lusid.com"
    schedules_url = "/scheduler2/api/schedules"

    client = httpx.Client(base_url=base_url, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def existing_job(self):
        return scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=scheduler.ImageResource(
                id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
            ),
            name="job name",
            description="a job",
            argument_definitions={
                "myarg1": scheduler.CommandlineArg(data_type="String", description="test", order=1)
            },
        )

    @pytest.fixture
    def config_item_ref(self):
        set = cfg.SetRef(id="set", scope="cfgscope", code="cfgcode", type=cfg.SetType.PERSONAL)
        item = cfg.ItemRef(id="item", set=set, key="itemkey")
        # fake the item being attached
        item.ref = "config://123"
        return item

    def test_read_given_schedule_exists(self, respx_mock, existing_job: scheduler.JobResource):
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="name",
            scope="schedulescope",
            code="schedulecode",
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="description",
        )
        old_state = SimpleNamespace(scope="scope1", code="code1")
        respx_mock.get(f"{self.schedules_url}/{old_state.scope}/{old_state.code}").mock(
            side_effect=[
                httpx.Response(
                    200, json={"somefield": "myschedule", "scheduleIdentifier": "somethingelse"}
                )
            ]
        )
        # when read is called
        # the remote is populated but scheduleIdentifier is not included
        assert schedule.read(client=self.client, old_state=old_state) == {"somefield": "myschedule"}

    def test_create_with_config_arg(self, respx_mock, existing_job, config_item_ref):
        # given the schedule does not exists in the remote
        respx_mock.post(self.schedules_url).mock(
            side_effect=[httpx.Response(201, json={"some": "response"})]
        )
        # and the desired schedule references a config item
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope="scopes",
            code="codes",
            expression="somecron",
            job=existing_job,
            description="some description",
            arguments={"arg1": config_item_ref},
        )
        # when we create it
        schedule.create(self.client)
        # then the config item is turned into it's ref
        request = respx_mock.calls.last.request
        assert json.loads(request.content) == {
            "scheduleId": {"scope": "scopes", "code": "codes"},
            "jobId": {"scope": existing_job.scope, "code": existing_job.code},
            "trigger": {"timeTrigger": {"expression": "somecron"}},
            "name": "testname",
            "description": "some description",
            "arguments": {"arg1": "config://123"},
        }

    def test_update_with_config_arg(self, respx_mock, existing_job, config_item_ref):
        # GIVEN a remote schedule which does not use a config
        respx_mock.get(f"{self.schedules_url}/scope1/code1").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "scheduleIdentifier": "somethingelse",
                        "enabled": False,
                        "author": "default",
                        "owner": "default",
                        "useAsAuth": "default",
                        "notifications": "default",
                        "arguments": {"arg1": "astring"},
                    },
                )
            ]
        )
        respx_mock.put(f"{self.schedules_url}/scope1/code1").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        # and the desired schedule references a config item
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope="scope1",
            code="code1",
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="some description",
            arguments={"arg1": config_item_ref},
        )
        # when we update it
        old_state = SimpleNamespace(scope="scope1", code="code1")
        new_state = schedule.update(self.client, old_state)
        # then the config item is turned into it's ref in the put request
        request = respx_mock.calls.last.request
        assert json.loads(request.content) == {
            "jobId": {"scope": existing_job.scope, "code": existing_job.code},
            "trigger": {"timeTrigger": {"expression": "somecron", "timeZone": "Europe/London"}},
            "name": "testname",
            "description": "some description",
            "arguments": {"arg1": "config://123"},
        }
        # and a new state is returned
        assert new_state is not None

    @pytest.mark.parametrize(
        "user_resource",
        [
            UserResource(
                id="id",
                first_name="name",
                last_name="last",
                email_address="email",
                login="login",
                type=UserType.SERVICE,
            ),
            UserRef(id="id", login="login"),
        ],
    )
    def test_create_given_schedule_has_defaults(
        self, respx_mock, existing_job: scheduler.JobResource, user_resource
    ):
        schedule_scope = "testscope"
        schedule_code = "testcode"
        user = user_resource
        user.user_id = "someuserid"
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope=schedule_scope,
            code=schedule_code,
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="some description",
            author="custom author",
            use_as_auth=user,
        )

        expected_post = {
            "scheduleId": {"scope": schedule_scope, "code": schedule_code},
            "jobId": {"scope": existing_job.scope, "code": existing_job.code},
            "trigger": {"timeTrigger": {"expression": "somecron", "timeZone": "Europe/London"}},
            "name": "testname",
            "author": "custom author",
            "description": "some description",
            "useAsAuth": "someuserid",
        }

        respx_mock.post(self.schedules_url).mock(
            side_effect=[httpx.Response(201, json={"some": "response"})]
        )

        response = schedule.create(client=self.client)

        assert (
            response
            == scheduler.ScheduleState(
                id="myschedule", scope=schedule_scope, code=schedule_code, argKeys=[]
            ).model_dump()
        )

        request = respx_mock.calls.last.request
        assert json.loads(request.content) == expected_post

    def test_update_given_id_is_changed_then_fails(self, existing_job: scheduler.JobResource):
        # GIVEN some schedule state
        schedule_scope = "testscope"
        schedule_code = "testcode"
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope=schedule_scope,
            code=schedule_code,
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="some description",
        )

        def assert_result(scope: str, code: str):
            # WHEN the old state ID is different from current state
            old_state = SimpleNamespace(scope=scope, code=code)

            # THEN Update fails
            with pytest.raises(RuntimeError) as ex:
                schedule.update(client=self.client, old_state=old_state)
            assert f"{schedule_scope}/{schedule_code}" in str(ex.value)
            assert f"{old_state.scope}/{old_state.code}" in str(ex.value)

        # just the code is different
        assert_result(scope=schedule_scope, code="someothercode")
        # just the scope is different
        assert_result(scope="someotherscope", code=schedule_code)
        # scope and code are both different
        assert_result(scope="someotherscope", code="someothercode")

    def test_update_given_no_defaults_provided_then_handles_correctly(
        self, respx_mock, existing_job: scheduler.JobResource
    ):
        schedule_scope = "testscope"
        schedule_code = "testcode"

        old_state = SimpleNamespace(scope=schedule_scope, code=schedule_code)

        # GIVEN a remote state containing the defaults
        respx_mock.get(f"{self.schedules_url}/{old_state.scope}/{old_state.code}").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "scheduleIdentifier": "somethingelse",
                        "enabled": False,
                        "author": "default",
                        "owner": "default",
                        "useAsAuth": "default",
                        "notifications": "default",
                    },
                )
            ]
        )
        json = {
            "description": "some description",
            "jobId": {"code": existing_job.code, "scope": existing_job.scope},
            "name": "testname",
            "trigger": {"timeTrigger": {"expression": "somecron", "timeZone": "Europe/London"}},
        }
        respx_mock.put(f"{self.schedules_url}/{schedule_scope}/{schedule_code}", json=json).mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "somefield": "myschedule",
                        "scheduleIdentifier": "somethingelse",
                        "enabled": False,
                        "author": "default",
                        "owner": "default",
                        "useAsAuth": "default",
                    },
                )
            ]
        )

        # AND a resource without the defaults and some changed fields
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope=schedule_scope,
            code=schedule_code,
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="some description",
        )
        # WHEN Calling update
        # THEN Updated as expected
        state = schedule.update(client=self.client, old_state=old_state)
        assert state is not None
        assert state["id"] == "myschedule"

    def test_update_remove_argument(self, respx_mock, existing_job):
        # GIVEN A remote with two arguments
        respx_mock.get(f"{self.schedules_url}/scope1/code1").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "scheduleIdentifier": {"scope": "scop1", "code": "code1"},
                        "jobId": {"scope": existing_job.scope, "code": existing_job.code},
                        "trigger": {
                            "timeTrigger": {"expression": "somecron", "timeZone": "Europe/London"}
                        },
                        "name": "testname",
                        "author": "custom author",
                        "description": "some description",
                        "arguments": {"arg1": "argvalue1", "arg2": "argvalue2"},
                    },
                )
            ]
        )
        # and desired is the same but has removed one arg
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope="scope1",
            code="code1",
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="some description",
            arguments={"arg1": "argvalue1"},
        )
        # when it gets updated
        respx_mock.put(f"{self.schedules_url}/scope1/code1").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        old_state = SimpleNamespace(scope="scope1", code="code1", argKeys=["arg1", "arg2"])
        new_state = schedule.update(self.client, old_state)
        # then the change is detected and a state is returned
        assert new_state is not None
        assert new_state["argKeys"] == ["arg1"]

    @pytest.mark.parametrize(
        "user_resource",
        [
            UserResource(
                id="id",
                first_name="name",
                last_name="last",
                email_address="email",
                login="login",
                type=UserType.SERVICE,
            ),
            UserRef(id="id", login="login"),
        ],
    )
    def test_update_given_all_defaults_provided_then_handles_correctly(
        self, respx_mock, existing_job, user_resource
    ):
        schedule_scope = "testscope"
        schedule_code = "testcode"
        auth_user = user_resource
        auth_user.user_id = "notdefaultuser"

        old_state = SimpleNamespace(scope=schedule_scope, code=schedule_code)
        # GIVEN A remote state with all defaults set
        respx_mock.get(f"{self.schedules_url}/{old_state.scope}/{old_state.code}").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "somefield": "myschedule",
                        "scheduleIdentifier": "somethingelse",
                        "enabled": True,
                        "author": "notdefault",
                        "owner": "notdefault",
                        "useAsAuth": "notdefault",
                        "notifications": "some",
                        "arguments": {"myarg1": "myvalue1"},
                    },
                )
            ]
        )

        expected_update = {
            "description": "some description",
            "jobId": {"code": existing_job.code, "scope": existing_job.scope},
            "name": "testname",
            "trigger": {"timeTrigger": {"expression": "somecron", "timeZone": "Europe/London"}},
            "arguments": {"myarg2": "myvalue2"},
            "author": "notdefaultauthor",
            "owner": "notdefaultowner",
            "useAsAuth": "notdefaultuser",
        }

        respx_mock.put(
            f"{self.schedules_url}/{schedule_scope}/{schedule_code}", json=expected_update
        ).mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "somefield": "myschedule",
                        "scheduleIdentifier": "somethingelse",
                        "enabled": False,
                        "author": "default",
                        "owner": "default",
                        "useAsAuth": "default",
                    },
                )
            ]
        )

        # AND A resource with all the defaults set and they are different
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope=schedule_scope,
            code=schedule_code,
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="some description",
            arguments={"myarg2": "myvalue2"},
            author="notdefaultauthor",
            owner="notdefaultowner",
            use_as_auth=auth_user,
        )

        # WHEN Calling update
        state = schedule.update(client=self.client, old_state=old_state)
        assert state is not None
        assert state["id"] == "myschedule"

    def test_update_given_no_change_then_no_action(self, respx_mock):
        schedule_scope = "testscope"
        schedule_code = "testcode"
        user = UserRef(id="id", login="login")
        user.user_id = "notdefault"

        job = scheduler.JobResource(
            id="job1",
            scope="scope1",
            code="code1",
            image=scheduler.ImageResource(
                id="image1", source_image="docker.io/alpine:5", dest_name="dest_alpine", dest_tag="v1"
            ),
            name="job name",
            description="a job",
            argument_definitions={
                "myarg1": scheduler.CommandlineArg(data_type="String", description="test", order=1),
                "jobdefaultarg": scheduler.CommandlineArg(
                    data_type="String",
                    description="test",
                    order=1,
                    required=False,
                    default_value="somedefaultvalue",
                ),
            },
        )

        old_state = SimpleNamespace(
            scope=schedule_scope, code=schedule_code, argKeys=["myarg1", "jobdefaultarg"]
        )

        # GIVEN A remote that matches the resource
        respx_mock.get(f"{self.schedules_url}/{old_state.scope}/{old_state.code}").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "scheduleIdentifier": "somethingelse",
                        "description": "some description",
                        "jobId": {"code": job.code, "scope": job.scope},
                        "name": "testname",
                        "enabled": True,
                        "author": "notdefault",
                        "owner": "notdefault",
                        "useAsAuth": "notdefault",
                        "notifications": "some",
                        "trigger": {
                            "timeTrigger": {"expression": "somecron", "timeZone": "Europe/London"}
                        },
                        "arguments": {"myarg1": "myvalue1", "jobdefaultarg": "somedefaultvalue"},
                    },
                )
            ]
        )
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope=schedule_scope,
            code=schedule_code,
            expression="somecron",
            timezone="Europe/London",
            job=job,
            description="some description",
            arguments={"myarg1": "myvalue1", "jobdefaultarg": "somedefaultvalue"},
            author="notdefault",
            owner="notdefault",
            use_as_auth=user,
        )

        # WHEN Calling Update
        result = schedule.update(client=self.client, old_state=old_state)
        # Then None is returned
        assert result is None

    def test_delete_given_schedule_exists(self, respx_mock, existing_job):
        schedule_scope = "testscope"
        schedule_code = "testcode"
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope=schedule_scope,
            code=schedule_code,
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="something",
        )

        old_state = SimpleNamespace(scope=schedule_scope, code=schedule_code)

        # GIVEN Delete returns 204
        respx_mock.delete(f"{self.schedules_url}/{schedule_scope}/{schedule_code}").mock(
            side_effect=[httpx.Response(204)]
        )

        # THEN Calling delete does not raise an exception
        schedule.delete(client=self.client, old_state=old_state)

    def test_delete_given_schedule_does_not_exist(self, respx_mock, existing_job):
        schedule_scope = "testscope"
        schedule_code = "testcode"
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope=schedule_scope,
            code=schedule_code,
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="something",
        )

        old_state = SimpleNamespace(scope=schedule_scope, code=schedule_code)

        # GIVEN Delete returns 404 with name ValidationError
        # AND title Schedule could not be found
        respx_mock.delete(f"{self.schedules_url}/{schedule_scope}/{schedule_code}").mock(
            side_effect=[
                httpx.Response(
                    404, json={"name": "ValidationError", "title": "Schedule could not be found"}
                )
            ]
        )

        # THEN Calling delete does not raise an exception
        schedule.delete(client=self.client, old_state=old_state)

    def test_delete_given_failure_then_raises(self, respx_mock, existing_job):
        schedule_scope = "testscope"
        schedule_code = "testcode"
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope=schedule_scope,
            code=schedule_code,
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="something",
        )

        old_state = SimpleNamespace(scope=schedule_scope, code=schedule_code)

        # GIVEN Delete returns 404 with some name or error title other than not found
        respx_mock.delete(f"{self.schedules_url}/{schedule_scope}/{schedule_code}").mock(
            side_effect=[
                httpx.Response(404, json={"name": "notavalidationerror", "title": "Something else"})
            ]
        )

        # THEN Calling delete does raise an exception
        with pytest.raises(httpx.HTTPStatusError) as error:
            schedule.delete(client=self.client, old_state=old_state)

        assert error.value.response.status_code == 404
        assert error.value.response.json()["name"] == "notavalidationerror"

    @staticmethod
    @pytest.mark.parametrize(
        "user",
        [
            UserResource(
                id="id",
                first_name="name",
                last_name="last",
                email_address="email",
                login="login",
                type=UserType.SERVICE,
            ),
            UserRef(id="id", login="login"),
        ],
    )
    def test_deps_with_config_and_user(config_item_ref, existing_job, user):
        # given a schedule which references a config item in its arguments
        schedule = scheduler.ScheduleResource(
            id="myschedule",
            name="testname",
            scope="scopes",
            code="codes",
            expression="somecron",
            timezone="Europe/London",
            job=existing_job,
            description="some description",
            arguments={"arg1": config_item_ref},
            use_as_auth=user,
        )
        # when we get the dependencies
        deps = schedule.deps()
        # then the deps includes the config item and the job
        assert deps == [existing_job, config_item_ref, user]

    def test_dump(self, existing_job):
        # given a simple schedule
        sut = scheduler.ScheduleResource(
            id="schedule1",
            name="Test Schedule",
            scope="scope1",
            code="code1",
            expression="0 9 * * *",
            timezone="Europe/London",
            job=existing_job,
            description="A test schedule",
            enabled=True,
            author="test-author",
            owner="test-owner",
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True,
            round_trip=True,  # excludes computeds
            exclude_none=True,
            context={"style": "dump"},
        )
        # then the dumped state is correct
        assert dumped == {
            "name": "Test Schedule",
            "description": "A test schedule",
            "scope": "scope1",  # scope/code are used instead of jobId
            "code": "code1",
            "expression": "0 9 * * *",
            "timezone": "Europe/London",
            "job": {"$ref": existing_job.id},
            "enabled": True,
            "author": "test-author",
            "owner": "test-owner",
        }

    def test_dump_with_config(self, existing_job, config_item_ref):
        # given an existing schedule with config arguments
        sut = scheduler.ScheduleResource(
            id="schedule1",
            name="Test Schedule",
            scope="scope1",
            code="code1",
            expression="0 9 * * *",
            timezone="Europe/London",
            job=existing_job,
            description="A test schedule",
            arguments={"myarg": config_item_ref, "stringarg": "test-value"},
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True,
            round_trip=True,  # excludes computeds
            exclude_none=True,
            context={"style": "dump"},
        )
        # then:
        assert dumped == {
            "scope": "scope1",
            "code": "code1",
            "name": "Test Schedule",
            "description": "A test schedule",
            "expression": "0 9 * * *",
            "timezone": "Europe/London",
            "job": {"$ref": existing_job.id},  # the job is a $ref
            "arguments": {
                "myarg": {"$ref": config_item_ref.id},  # the config item is a $ref
                "stringarg": "test-value",
            },
        }

    def test_undump_with_config_arg(self, existing_job, config_item_ref):
        # given a dumped schedule state
        dumped = {
            "scope": "scope1",
            "code": "code1",
            "name": "Test Schedule",
            "expression": "0 9 * * *",
            "timezone": "Europe/London",
            "description": "A test schedule",
            "job": {"$ref": existing_job.id},
            "enabled": True,
            "author": "test-author",
            "owner": "test-owner",
            "arguments": {"myarg": {"$ref": config_item_ref.id}, "stringarg": "test-value"},
        }
        # when we undump it
        sut = scheduler.ScheduleResource.model_validate(
            dumped,
            context={
                "style": "undump",
                "$refs": {existing_job.id: existing_job, config_item_ref.id: config_item_ref},
                "id": "schedule1",
            },
        )
        # then the id has been extracted from the context
        assert sut.id == "schedule1"
        assert sut.name == "Test Schedule"
        assert sut.description == "A test schedule"
        # and the job ref has been wired up
        assert sut.job == existing_job
        assert sut.enabled is True
        assert sut.author == "test-author"
        assert sut.owner == "test-owner"
        # and the config item ref has been wired up
        assert sut.arguments
        assert sut.arguments["myarg"] == config_item_ref
        assert sut.arguments["stringarg"] == "test-value"


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeScheduleRef:
    base_url = "https://foo.lusid.com"
    client = httpx.Client(base_url=base_url, event_hooks={"response": [response_hook]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote schedule exists
        respx_mock.get("/scheduler2/api/schedules/testscope/testcode").mock(
            return_value=httpx.Response(200, json={"name": "Test Schedule"})
        )
        sut = scheduler.ScheduleRef(id="sched1", scope="testscope", code="testcode")
        # when we call attach
        sut.attach(self.client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote schedule does not exist
        respx_mock.get("/scheduler2/api/schedules/testscope/testcode").mock(
            return_value=httpx.Response(404, json={})
        )
        sut = scheduler.ScheduleRef(id="sched1", scope="testscope", code="testcode")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(self.client)
        assert "Schedule testscope/testcode not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/scheduler2/api/schedules/testscope/testcode").mock(
            return_value=httpx.Response(500, json={})
        )
        sut = scheduler.ScheduleRef(id="sched1", scope="testscope", code="testcode")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPStatusError):
            sut.attach(self.client)
