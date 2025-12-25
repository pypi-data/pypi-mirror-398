import json
from io import StringIO
from types import SimpleNamespace
from typing import Annotated, Sequence
from unittest import mock
from unittest.mock import patch

import httpx
import pytest
from pydantic import BaseModel, BeforeValidator, PlainSerializer, computed_field

import fbnconfig.resource_abc
from fbnconfig import create_client
from fbnconfig.deploy import Action, Deployment, dump_deployment, run, undump_deployment
from fbnconfig.resource_abc import CamelAlias, Resource, get_resource_class, register_resource

TEST_BASE = "https://foo.lusid.com"

log_entity = "deployment"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeWithNoRemoteResources:
    client = create_client(TEST_BASE, "xyz")

    def test_handles_429_on_get(self, respx_mock):
        # given the server returns a 429 before returning the real response
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            side_effect=[
                httpx.Response(429, json={}, headers={"retry-after": "0"}),
                httpx.Response(200, json={"values": []}),
            ]
        )
        # when we run an empty deployment
        deployment = Deployment("whatever", [])
        run(self.client, deployment)
        # then the 429 gets retried and we continue
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        assert request.url.params._dict == {"filter": ["fields[deployment] eq 'whatever'"]}
        # but no other http requests are made

    def test_run_with_empty_deploy_does_nothing(self, respx_mock):
        # given there are no resources in the log
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": []})
        )
        # when we run an empty deployment
        deployment = Deployment("whatever", [])
        actions = run(self.client, deployment)
        # then the log is searched
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        assert request.url.params._dict == {"filter": ["fields[deployment] eq 'whatever'"]}
        # but no other http requests are made
        # and an empty actions list is returned
        assert actions == []

    def test_run_with_one_resource_creates_it(self, respx_mock):
        # given there are no resources in the log
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": []})
        )
        respx_mock.post(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={})
        )
        # when we run a deployment with one resource
        resource = mock.Mock(spec=Resource)
        resource.deps = mock.Mock(return_value=[])
        resource.id = "23"
        resource.create = mock.Mock(return_value={"some_variable": "x"})
        deployment = Deployment("whatever", [resource])
        actions = run(self.client, deployment)
        # then the create method on the resource is called
        resource.create.assert_called_once_with(self.client)
        # and the create is recorded in the log
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        assert json.loads(request.content) == {
            "description": "...",
            "displayName": "23",
            "fields": [
                {"name": "deployment", "value": "whatever"},
                {"name": "resourceType", "value": "Mock"},
                {"name": "dependencies", "value": []},
                {"name": "resource", "value": "23"},
                {"name": "state", "value": '{"some_variable": "x"}'},
            ],
            "identifiers": [
                {
                    "identifierScope": log_entity,
                    "identifierType": "resource",
                    "identifierValue": "whatever_23",
                }
            ],
        }
        # and the create is in the actions
        assert actions == [Action(id="23", type="Mock", change="create")]

    def test_run_with_one_resource_empty_state(self, respx_mock):
        # given there are no resources in the log
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": []})
        )
        respx_mock.post(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={})
        )
        # when we run a deployment with one resource
        resource = mock.Mock(spec=Resource)
        resource.deps = mock.Mock(return_value=[])
        resource.id = "23"
        # and the new state value is an empty dict
        resource.create = mock.Mock(return_value={})
        deployment = Deployment("whatever", [resource])
        actions = run(self.client, deployment)
        # then the create method on the resource is called
        resource.create.assert_called_once_with(self.client)
        # and the create is recorded in the log
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        assert json.loads(request.content) == {
            "description": "...",
            "displayName": "23",
            "fields": [
                {"name": "deployment", "value": "whatever"},
                {"name": "resourceType", "value": "Mock"},
                {"name": "dependencies", "value": []},
                {"name": "resource", "value": "23"},
                {"name": "state", "value": "{}"},
            ],
            "identifiers": [
                {
                    "identifierScope": log_entity,
                    "identifierType": "resource",
                    "identifierValue": "whatever_23",
                }
            ],
        }
        # and the action is to create
        assert actions == [Action(id="23", type="Mock", change="create")]

    def test_run_with_two_resources(self, respx_mock):
        # given there are no resources in the log
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": []})
        )
        respx_mock.post(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={})
        )
        # and desired resources one and two are independent
        resource1 = mock.Mock(spec=Resource)
        resource1.deps = mock.Mock(return_value=[])
        resource1.id = "one"
        resource1.create = mock.Mock(return_value={"some_variable": "x"})
        resource2 = mock.Mock(spec=Resource)
        resource2.deps = mock.Mock(return_value=[])
        resource2.id = "two"
        resource2.create = mock.Mock(return_value={"some_variable": "y"})
        # when we run a deployment with one and two
        deployment = Deployment("whatever", [resource1, resource2])
        actions = run(self.client, deployment)
        # then the create methods are called on both
        resource1.create.assert_called_once_with(self.client)
        resource2.create.assert_called_once_with(self.client)
        # and the create is recorded in the log for both in the order they were
        # added to the deployment
        request = respx_mock.calls[-2].request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        assert json.loads(request.content)["displayName"] == "one"
        request = respx_mock.calls[-1].request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        assert json.loads(request.content)["displayName"] == "two"
        # and they appear in order in the actions
        assert actions == [
            Action(id="one", type="Mock", change="create"),
            Action(id="two", type="Mock", change="create"),
        ]

    def test_run_logs_unique_dependencies(self, respx_mock):
        # given there are no resources in the log
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": []})
        )
        respx_mock.post(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={})
        )
        # and resources "one" and "two" where "two" depends on "one"
        # twice
        resource1 = mock.Mock(spec=Resource)
        resource1.deps = mock.Mock(return_value=[])
        resource1.id = "one"
        resource1.create = mock.Mock(return_value={"some_variable": "x"})
        resource2 = mock.Mock(spec=Resource)
        resource2.deps = mock.Mock(return_value=[resource1, resource1])  # double dependency
        resource2.id = "two"
        resource2.create = mock.Mock(return_value={"some_variable": "x"})
        # when we deploy
        deployment = Deployment("whatever", [resource1, resource2])
        run(self.client, deployment)
        # then the create method on each of them is called
        resource1.create.assert_called_once_with(self.client)
        resource2.create.assert_called_once_with(self.client)
        # and the create is recorded in the log for both in dependency order
        request = respx_mock.calls[-2].request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        assert json.loads(request.content)["displayName"] == "one"
        request = respx_mock.calls[-1].request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        two_log = json.loads(request.content)
        assert two_log["displayName"] == "two"
        # and resource two has uniquely recorded dependency on resource one
        assert next(
            field["value"] for field in two_log["fields"] if field["name"] == "dependencies"
        ) == ["one"]

    def test_run_with_one_resource_and_dependency(self, respx_mock):
        # given there are no resources in the log
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": []})
        )
        respx_mock.post(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={})
        )
        # and resources "one" and "two" where "two" depends on "one"
        resource1 = mock.Mock(spec=Resource)
        resource1.deps = mock.Mock(return_value=[])
        resource1.id = "one"
        resource1.create = mock.Mock(return_value={"some_variable": "x"})
        resource2 = mock.Mock(spec=Resource)
        resource2.deps = mock.Mock(return_value=[resource1])
        resource2.id = "two"
        resource2.create = mock.Mock(return_value={"some_variable": "x"})
        # when we deploy "two" only
        deployment = Deployment("whatever", [resource2])
        actions = run(self.client, deployment)
        # then the create method on each of them is called
        resource1.create.assert_called_once_with(self.client)
        resource2.create.assert_called_once_with(self.client)
        # and the create is recorded in the log for both in dependency order
        request = respx_mock.calls[-2].request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        assert json.loads(request.content)["displayName"] == "one"
        request = respx_mock.calls[-1].request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        two_log = json.loads(request.content)
        assert two_log["displayName"] == "two"
        # and resource two has recorded a dependency on resource one
        assert next(f["value"] for f in two_log["fields"] if f["name"] == "dependencies") == ["one"]
        # and they appear in order in the actions
        assert actions == [
            Action(id="one", type="Mock", change="create"),
            Action(id="two", type="Mock", change="create"),
        ]

    def test_run_with_deuplicate_resourcei_ids(self, respx_mock):
        # given two resources using the same resource id and a dependency between them
        resource1 = mock.Mock(spec=Resource)
        resource1.deps = mock.Mock(return_value=[])
        resource1.id = "duplicate-id"
        resource1.create = mock.Mock(return_value={"some_variable": "x"})
        resource2 = mock.Mock(spec=Resource)
        resource2.deps = mock.Mock(return_value=[resource1])
        resource2.id = "duplicate-id"
        resource2.create = mock.Mock(return_value={"some_variable": "x"})
        # when we deploy resource2
        deployment = Deployment("whatever", [resource2])
        # then an error is raised because resource2 depends on resource1
        # but they have the same resource id
        with pytest.raises(RuntimeError) as ex:
            run(self.client, deployment)
        assert "duplicate-id has been used on more than one resource" in str(ex.value)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeWithExistingResources:
    client = httpx.Client(base_url=TEST_BASE)

    @pytest.fixture
    def existing_resource(self):
        return {
            "description": "...",
            "displayName": "one",
            "fields": [
                {"name": "deployment", "value": "whatever"},
                {"name": "resourceType", "value": "FileResource"},
                {"name": "dependencies", "value": []},
                {"name": "resource", "value": "one"},
                {"name": "state", "value": '{"some_variable": "x"}'},
            ],
            "identifiers": [
                {
                    "identifierScope": log_entity,
                    "identifierType": "resource",
                    "identifierValue": "whatever_one",
                }
            ],
            "version": {"asAtModified": "2024-02-20T15:39:58.1008350+00:00"},
        }

    @pytest.fixture
    def dependent_resource(self):
        # this resource "two" depends on resource "one"
        return {
            "description": "...",
            "displayName": "two",
            "fields": [
                {"name": "deployment", "value": "whatever"},
                {"name": "resourceType", "value": "FileResource"},
                {"name": "dependencies", "value": ["one"]},
                {"name": "resource", "value": "two"},
                {"name": "state", "value": '{"other_variable": "x"}'},
            ],
            "identifiers": [
                {
                    "identifierScope": log_entity,
                    "identifierType": "resource",
                    "identifierValue": "whatever_two",
                }
            ],
            "version": {"asAtModified": "2024-02-20T15:39:58.1008350+00:00"},
        }

    def test_run_existing_resource_calls_update_no_change(self, respx_mock, existing_resource):
        # given that resource "one" already exists in the log
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": [existing_resource]})
        )
        # and the desired resource one
        resource1 = mock.Mock(spec=Resource)
        resource1.deps = mock.Mock(return_value=[])
        resource1.id = "one"
        resource1.__name__ = "FileResource"
        # and it is the same as the remote
        resource1.update = mock.Mock(return_value=None)
        # when we deploy "one"
        deployment = Deployment("whatever", [resource1])
        actions = run(self.client, deployment)
        # then the update method is called with the log state
        resource1.update.assert_called_once_with(self.client, SimpleNamespace(some_variable="x"))
        # and the log is not updated
        # but nochange is in the actions
        assert actions == [Action(id="one", type="Mock", change="nochange")]

    def test_run_existing_resource_calls_update_new_state(self, respx_mock, existing_resource):
        # given that resource "one" already exists in the log
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": [existing_resource]})
        )
        respx_mock.post(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={})
        )
        # and a desired resource "one"
        resource1 = mock.Mock(spec=Resource)
        resource1.deps = mock.Mock(return_value=[])
        resource1.id = "one"
        resource1.__name__ = "FileResource"
        # and it is different to the remote state (it returns not None)
        resource1.update = mock.Mock(return_value={"some_variable": "abcdefg"})
        # when we deploy "one"
        deployment = Deployment("whatever", [resource1])
        actions = run(self.client, deployment)
        # then the update method is called with the remote log state
        resource1.update.assert_called_once_with(self.client, SimpleNamespace(some_variable="x"))
        # and the state returned by update is recorded in the log
        request = respx_mock.calls[-1].request
        assert request.method == "POST"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        content = json.loads(request.content)
        assert content["displayName"] == "one"
        new_state = next(field["value"] for field in content["fields"] if field["name"] == "state")
        assert json.loads(new_state) == {"some_variable": "abcdefg"}
        # and the action is update
        assert actions == [Action(id="one", type="Mock", change="update")]

    def test_run_existing_resource_gets_deleted_when_not_desired(self, respx_mock, existing_resource):
        # given that resource "one" already exists in the log
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": [existing_resource]})
        )
        respx_mock.delete(
            f"/api/api/customentities/~{log_entity}/resource/whatever_one?identifierScope={log_entity}"
        ).mock(return_value=httpx.Response(200, json={}))
        # and "one" is not in the deployment
        deployment = Deployment("whatever", [])
        from fbnconfig import drive

        mock_resource = mock.Mock(spec=drive.FileResource)
        mock_resource.delete = mock.Mock(return_value=None)
        with mock.patch(
            "fbnconfig.resource_abc.RESOURCE_REGISTRY", {"FileResource": {"class": mock_resource}}
        ):
            actions = run(self.client, deployment)
            # then the FileResource.delete function is called (the patched one for this test)
            mock_resource.delete.assert_called_once_with(self.client, SimpleNamespace(some_variable="x"))
            # and the log record is deleted
            request = respx_mock.calls[-1].request
            assert request.method == "DELETE"
            # and the url matches the one mocked above
            # and the action is update
            assert actions == [Action(id="one", type="FileResource", change="remove")]

    def test_run_implicit_resource_does_not_get_deleted(
        self, respx_mock, existing_resource, dependent_resource
    ):
        # given that resource "one" and "two already exists in the log and "two" depends on "one"
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": [existing_resource, dependent_resource]})
        )
        # and desired resources "one" and "two" match what has been deployed
        #    where "two" depends on "one"
        resource1 = mock.Mock(spec=Resource)
        resource1.deps = mock.Mock(return_value=[])
        resource1.id = "one"
        resource1.update = mock.Mock(return_value=None)
        resource2 = mock.Mock(spec=Resource)
        resource2.deps = mock.Mock(return_value=[resource1])  # two depends on one
        resource2.id = "two"
        resource2.update = mock.Mock(return_value=None)
        # and "two" is explicitly in the deployment but "one" is only implicity
        # because two depends on "one"
        deployment = Deployment("whatever", [resource2])
        from fbnconfig import drive

        mock_resource = mock.Mock(spec=drive.FileResource)
        mock_resource.delete = mock.Mock(return_value=None)
        with mock.patch(
            "fbnconfig.resource_abc.RESOURCE_REGISTRY", {"FileResource": {"class": mock_resource}}
        ):
            run(self.client, deployment)
            # then no delete calls are made because we should keep both resources
            assert mock_resource.delete.mock_calls == []

    def test_run_dependent_resources_get_deleted_in_order(
        self, respx_mock, existing_resource, dependent_resource
    ):
        # given resources "one" and "two" where "two"depends on "one"
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": [dependent_resource, existing_resource]})
        )
        respx_mock.delete(
            f"/api/api/customentities/~{log_entity}/resource/whatever_one?identifierScope={log_entity}",
            name="delete_one",
        ).mock(return_value=httpx.Response(200, json={}))
        respx_mock.delete(
            f"/api/api/customentities/~{log_entity}/resource/whatever_two?identifierScope={log_entity}",
            name="delete_two",
        ).mock(return_value=httpx.Response(200, json={}))
        # and the deployment is empty
        deployment = Deployment("whatever", [])
        from fbnconfig import drive

        mock_resource = mock.Mock(spec=drive.FileResource)
        mock_resource.delete = mock.Mock(return_value=None)
        with mock.patch(
            "fbnconfig.resource_abc.RESOURCE_REGISTRY", {"FileResource": {"class": mock_resource}}
        ):
            run(self.client, deployment)
            # then the FileResource.delete function is called for both, dependent resource first
            assert mock_resource.delete.mock_calls == [
                mock.call(self.client, SimpleNamespace(other_variable="x")),
                mock.call(self.client, SimpleNamespace(some_variable="x")),
            ]
            # and the log record for two is deleted
            request = respx_mock.calls[-2].request
            assert request.method == "DELETE"
            assert request.url.path == f"/api/api/customentities/~{log_entity}/resource/whatever_two"
            # before the log record for one is deleted last
            request = respx_mock.calls[-1].request
            assert request.method == "DELETE"
            assert request.url.path == f"/api/api/customentities/~{log_entity}/resource/whatever_one"
            # and the url matches the one mocked above


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeResourceRegistry:
    client = create_client(TEST_BASE, "xyz")

    @pytest.fixture()
    def stub_resource_class(self):
        class StubResource(Resource):
            id: str

            def read(self, client, old_state):
                return None

            def create(self, client):
                return None

            def update(self, client, old_state):
                return None

            @staticmethod
            def delete(client, old_state):
                pass

            def deps(self):
                return []

        return StubResource

    @staticmethod
    def test_resource_registry_returns_expected_registrations(stub_resource_class):
        with patch.dict("fbnconfig.resource_abc.RESOURCE_REGISTRY", {}, clear=True) as registry:
            # GIVEN Two resources are registered
            @register_resource()
            class KlassResource(stub_resource_class):
                pass

            @register_resource(type_name="DifferentName")
            class MyOtherKlassResource(stub_resource_class):
                pass

            # THEN the resource registry is populated with the expected resources
            assert len(registry) == 2
            assert registry == {
                "KlassResource": {"class": KlassResource},
                "DifferentName": {"class": MyOtherKlassResource},
            }

    @staticmethod
    def test_get_resource_class_when_unregistered_resource_fails():
        with pytest.raises(RuntimeError) as ex:
            get_resource_class("UnregisteredResource")

        assert "Resource type 'UnregisteredResource' not found in registry" in str(ex.value)

    @staticmethod
    def test_get_resource_type_defaults_to_name():
        resource1 = mock.Mock(spec=Resource)
        resource1.__name__ = "something"
        type = fbnconfig.resource_abc.get_resource_type(resource1)
        assert type == "Mock"


class StubResource(CamelAlias, BaseModel, Resource):
    id: str
    data: str = "default"

    def read(self, client, old_state):
        return None

    def create(self, client):
        return None

    def update(self, client, old_state):
        return None

    @staticmethod
    def delete(client, old_state):
        pass

    def deps(self):
        return []


def ser_stub_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return value


def des_stub_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


StubKey = Annotated[
    StubResource,
    BeforeValidator(des_stub_key), PlainSerializer(ser_stub_key)
]


class FakeResource(BaseModel, CamelAlias, Resource):
    id: str
    with_alias: int | None = None
    depends_on: Sequence[StubKey] | None

    @computed_field(alias="computed")
    def computed(self) -> str:
        return self.id + "computed"

    def read(self, client, old_state):
        return None

    def create(self, client):
        return None

    def update(self, client, old_state):
        return None

    @staticmethod
    def delete(client, old_state):
        pass

    def deps(self):
        return self.depends_on if self.depends_on else []


class TestDumpDeployment:

    def test_dump_one(self):
        # given a resource with an aliased field and a computed one
        # and no dependencies
        fkr = FakeResource(id="one", with_alias=99, depends_on=None)
        deployment = Deployment("dep1", [fkr])
        # when it's dumpted
        serialized = dump_deployment(deployment)
        # then the alias is respected, the computed is omitted
        # and the id is extracted as resourceId
        assert serialized == {
            "deploymentId": "dep1",
            "resources": [{
                "resourceId": "one",
                "resourceType": "FakeResource",
                "dependencies": [],
                "value": {
                    "withAlias": 99,
                }
            }]
        }

    def test_dump_dependents(self):
        stub = StubResource(id="stub-id", data="stubdata")
        fkr = FakeResource(id="fake-id", with_alias=99, depends_on=[stub])
        deployment = Deployment("dep1", [stub, fkr])
        # when it's dumpted
        serialized = dump_deployment(deployment)
        # the dependent resource is first
        assert serialized == {
            "deploymentId": "dep1",
            "resources": [{
                "resourceId": "stub-id",
                "resourceType": "StubResource",
                "dependencies": [],
                "value": {
                    "data": "stubdata",
                }
            }, {
                "resourceId": "fake-id",
                "resourceType": "FakeResource",
                "dependencies": ["stub-id"],
                "value": {
                    "withAlias": 99,
                    "dependsOn": [{"$ref": "stub-id"}]
                }
            }]
        }

    def test_dump_empty_deployment(self):
        # given an empty deployment
        deployment = Deployment("empty-deployment", [])
        # when we dump it
        result = dump_deployment(deployment)
        # then the dump matches expected structure
        expected = {"deploymentId": "empty-deployment", "resources": []}
        assert result == expected

    def test_undump_deployment_with_single_resource(self):
        # given a dumped deployment with one resource
        dump_data = {
            "deploymentId": "test-deployment",
            "resources": [
                {
                    "resourceType": "StubResource",
                    "resourceId": "test-resource",
                    "value": {"data": "test-value"},
                    "dependencies": [],
                }
            ],
        }
        dump_file = StringIO(json.dumps(dump_data))
        # when we undump it
        with patch.dict(
            "fbnconfig.resource_abc.RESOURCE_REGISTRY", {"StubResource": {"class": StubResource}}
        ):
            result = undump_deployment(dump_file)
        # then we get a deployment with the correct id and resources
        assert result.id == "test-deployment"
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert resource.id == "test-resource"
        assert isinstance(resource, StubResource)
        assert resource.data == "test-value"

    def test_undump_deployment_with_dependent_resources(self):
        # given a dumped deployment with dependent resources
        dump_data = {
            "deploymentId": "test-deployment",
            "resources": [
                {
                    "resourceType": "StubResource",
                    "resourceId": "resource-1",
                    "value": {"data": "value1"},
                    "dependencies": [],
                },
                {
                    "resourceType": "FakeResource",
                    "resourceId": "resource-2",
                    "value": {
                        "withAlias": 87,
                        "dependsOn": [{"$ref": "resource-1"}]
                    },
                    "dependencies": ["resource-1"],
                },
            ],
        }
        dump_file = StringIO(json.dumps(dump_data))
        # when we undump it
        with patch.dict(
            "fbnconfig.resource_abc.RESOURCE_REGISTRY", {
                "StubResource": {"class": StubResource},
                "FakeResource": {"class": FakeResource},
            }
        ):
            result = undump_deployment(dump_file)
        # then we get a deployment with both resources
        assert result.id == "test-deployment"
        assert len(result.resources) == 2
        # resources should be ordered by dependencies (resource-1 first)
        assert result.resources[0].id == "resource-1"
        assert isinstance(result.resources[0], StubResource)
        assert result.resources[0].data == "value1"
        assert isinstance(result.resources[1], FakeResource)
        assert result.resources[1].id == "resource-2"
        assert result.resources[1].with_alias == 87
        # and the stub is wired up to the fake
        assert result.resources[1].depends_on
        assert result.resources[1].depends_on[0] == result.resources[0]

    def test_undump_deployment_with_empty_resources(self):
        # given a dumped deployment with no resources
        dump_data = {"deploymentId": "empty-deployment", "resources": []}
        dump_file = StringIO(json.dumps(dump_data))
        # when we undump it
        result = undump_deployment(dump_file)
        # then we get an empty deployment
        assert result.id == "empty-deployment"
        assert result.resources == []

    def test_undump_deployment_round_trip(self):
        # given a deployment with resources
        original_resource = StubResource(id="test-resource", data="test-data")
        original_deployment = Deployment("round-trip-test", [original_resource])
        # when we dump and then undump it
        dumped = dump_deployment(original_deployment)
        dump_file = StringIO(json.dumps(dumped))
        with patch.dict(
            "fbnconfig.resource_abc.RESOURCE_REGISTRY", {"StubResource": {"class": StubResource}}
        ):
            result = undump_deployment(dump_file)
        # then we get back the same deployment
        assert result.id == "round-trip-test"
        assert len(result.resources) == 1
        assert result.resources[0].id == "test-resource"
        assert isinstance(result.resources[0], StubResource)
        assert result.resources[0].data == "test-data"
