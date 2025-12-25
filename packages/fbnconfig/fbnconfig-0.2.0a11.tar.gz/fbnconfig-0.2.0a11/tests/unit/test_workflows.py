import copy
import hashlib
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest
from polyfactory.factories.pydantic_factory import ModelFactory

from fbnconfig import identity, lumi, scheduler
from fbnconfig import workflows as wf
from fbnconfig.workflows import LuminesceView, SchedulerJob

TEST_BASE = "https://foo.lusid.com"

WORKER_CONFIGS = [
    (wf.Sleep(), {"type": "Sleep"}, "0"),
    (wf.Fail(), {"type": "Fail"}, "0"),
    (wf.HealthCheck(url="a.com"), {"type": "HealthCheck", "url": "a.com"}, "0"),
    (
        wf.LuminesceView(view=lumi.ViewRef(id="a", provider="Views.Unit.Something")),
        {"type": "LuminesceView", "name": "Views.Unit.Something"},
        "1",
    ),
    (
        wf.LuminesceView(
            view=lumi.ViewResource(
                id="my-view", provider="Views.Unit.Test", sql="select * from foo;", description="a view"
            )
        ),
        {"type": "LuminesceView", "name": "Views.Unit.Test"},
        "5c9205c16d8e2036aad15d4e827e7f0a6f2cbd159c2b2bf2cf7f7123a5ac0b65",
    ),
    (
        wf.SchedulerJob(job=scheduler.JobRef(id="A", scope="B", code="C")),
        {"type": "SchedulerJob", "jobId": {"scope": "B", "code": "C"}},
        "ABCD",
    ),
    (
        wf.SchedulerJob(
            job=scheduler.JobResource(
                id="A",
                scope="jobscope",
                code="jobcode",
                image=scheduler.ImageRef(id="img", dest_name="img-name", dest_tag="sometag"),
                name="A job",
                description="A",
            )
        ),
        {"type": "SchedulerJob", "jobId": {"scope": "jobscope", "code": "jobcode"}},
        "ce31cf3f48906e757c2daccfae062dc17d04bc7d66cfd04e8867c504eb4e8490",
    ),
]


class WorkerResourceFactory(ModelFactory[wf.WorkerResource]): ...


class TaskDefFactory(ModelFactory[wf.TaskDefinitionResource]): ...


class TaskDefRefFactory(ModelFactory[wf.TaskDefinitionRef]): ...


class UserFactory(ModelFactory[identity.UserResource]): ...


class EventHandlerFactory(ModelFactory[wf.EventHandlerResource]): ...


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeWorkerResource:
    base_url = TEST_BASE
    workers_url = "/workflow/api/workers"
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.mark.parametrize("worker_config, worker_config_json, version", WORKER_CONFIGS)
    def test_create_worker(self, respx_mock, worker_config, worker_config_json, version):
        # since tests modify the versions on the configs, copy in to allow parallel runs
        # deepcopy as changes are made to the underlying object rather than worker config itself
        config = copy.deepcopy(worker_config)
        # GIVEN Resource does not exist
        wr = wf.WorkerResource(
            id="wr1",
            scope="somescope",
            code="workercode",
            display_name="name",
            description="descriptions",
            worker_configuration=config,
        )
        if isinstance(config, wf.SchedulerJob) and isinstance(config.job, scheduler.JobRef):
            config.job._content_hash = "ABCD"
        if isinstance(config, LuminesceView) and isinstance(config.view, lumi.ViewRef):
            config.view._version = version
        respx_mock.post(self.workers_url).mock(
            side_effect=[
                httpx.Response(
                    status_code=201,
                    json={
                        "id": {"scope": "somescope", "code": "workercode"},
                        "displayName": "name",
                        "description": "descriptions",
                        "workerConfiguration": worker_config_json,
                        "version": {"asAtCreated": "somedate", "asAtVersionNumber": 1},
                        "parameters": [],
                        "resultFields": [],
                    },
                )
            ]
        )

        # WHEN Worker Resource is created
        new_state = wr.create(self.client)
        # THEN State returned as expected
        assert new_state == {
            "id": "wr1",
            "scope": "somescope",
            "code": "workercode",
            "worker_version": version,
        }

        request: httpx.Request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == self.workers_url
        assert f"https://{request.url.host}" == self.base_url
        assert json.loads(request.content) == {
            "id": {"scope": "somescope", "code": "workercode"},
            "displayName": "name",
            "description": "descriptions",
            "workerConfiguration": worker_config_json,
        }

    @pytest.mark.parametrize("worker_config, worker_config_json, version", WORKER_CONFIGS)
    def test_update_no_change(self, respx_mock, worker_config, worker_config_json, version):
        config = copy.deepcopy(worker_config)
        # GIVEN Resource exists
        respx_mock.get(f"{self.workers_url}/test/testWorker").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "id": {"scope": "test", "code": "testWorker"},
                        "displayName": "DoWork",
                        "description": "Worker that does some work",
                        "workerConfiguration": worker_config_json,
                        "version": {
                            "asAtCreated": "2023-10-09T12:48:27.6157190+00:00",
                            "asAtVersionNumber": 2,
                        },
                        "parameters": [],
                        "resultFields": [
                            {
                                "name": "AccountingMethod",
                                "type": "String",
                                "displayName": "Accounting Method",
                            }
                        ],
                        "links": [{"method": "GET"}],
                    },
                )
            ]
        )

        old_state = SimpleNamespace(id="wr1", scope="test", code="testWorker", worker_version=version)
        # AND No Change
        wr = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoWork",
            description="Worker that does some work",
            worker_configuration=config,
        )

        if isinstance(config, wf.LuminesceView) and isinstance(config.view, lumi.ViewRef):
            config.view._version = version

        if isinstance(config, wf.SchedulerJob) and isinstance(config.job, scheduler.JobRef):
            config.job._content_hash = version

        new_state = wr.update(self.client, old_state)
        # Then no actions
        assert new_state is None

    @pytest.mark.parametrize("worker_config, worker_config_json, version", WORKER_CONFIGS)
    def test_update_identifier(self, respx_mock, worker_config, worker_config_json, version):
        # GIVEN Worker exists
        # WHen updating scope or code
        # THEN Worker is deleted and recreated
        config = copy.deepcopy(worker_config)
        respx_mock.delete(f"{self.workers_url}/test/testWorker").mock(
            side_effect=[httpx.Response(200, json={"asAt": "asAt deleted"})]
        )

        respx_mock.post(self.workers_url).mock(
            side_effect=[
                httpx.Response(
                    status_code=201,
                    json={
                        "id": {"scope": "test2", "code": "testWorker2"},
                        "displayName": "DoWork",
                        "workerConfiguration": worker_config_json,
                    },
                )
            ]
        )
        old_state = SimpleNamespace(id="wr1", scope="test", code="testWorker", worker_version=version)
        wr = wf.WorkerResource(
            id="wr1",
            scope="test2",
            code="testWorker2",
            display_name="DoWork",
            worker_configuration=config,
        )

        if isinstance(config, wf.LuminesceView) and isinstance(config.view, lumi.ViewRef):
            config.view._version = version
        if isinstance(config, wf.SchedulerJob) and isinstance(config.job, scheduler.JobRef):
            config.job._content_hash = version
        new_state = wr.update(self.client, old_state)
        assert new_state == {
            "id": "wr1",
            "scope": "test2",
            "code": "testWorker2",
            "worker_version": version,
        }

        # and the post is made to create the job
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == {
            "id": {"scope": "test2", "code": "testWorker2"},
            "displayName": "DoWork",
            "workerConfiguration": worker_config_json,
        }

    def test_update_fields_locally(self, respx_mock):
        # GIVEN Worker exists, but it has not changed from local
        respx_mock.get(f"{self.workers_url}/test/testWorker").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "id": {"scope": "test", "code": "testWorker"},
                        "displayName": "DoWork",
                        "description": "some description",
                        "workerConfiguration": {
                            "type": "SchedulerJob",
                            "jobId": {"scope": "jobscope", "code": "jobcode"},
                        },
                        "version": {
                            "asAtCreated": "2023-10-09T12:48:27.6157190+00:00",
                            "asAtVersionNumber": 3,
                        },
                        "parameters": {},
                        "resultFields": {},
                        "links": {},
                    },
                )
            ]
        )

        respx_mock.put(f"{self.workers_url}/test/testWorker").mock(
            side_effect=[
                httpx.Response(
                    status_code=200,
                    json={
                        "displayName": "DoSomeDifferentWork",
                        "description": "New description",
                        "workerConfiguration": {
                            "type": "SchedulerJob",
                            "jobId": {"scope": "jobscope", "code": "jobcode"},
                        },
                        "version": {
                            "asAtCreated": "2023-10-09T12:48:27.6157190+00:00",
                            "asAtVersionNumber": 4,
                        },
                    },
                )
            ]
        )

        old_state = SimpleNamespace(
            id="wr1", scope="test", code="testWorker", worker_version="someworkerhash"
        )
        ref = scheduler.JobRef(id="A", scope="jobscope", code="jobcode")
        # WHEN The worker name and descriptions change
        # But not the worker config
        wr = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoSomeDifferentWork",
            description="New description",
            worker_configuration=wf.SchedulerJob(job=ref),
        )

        ref._content_hash = "ABCD"

        new_state = wr.update(self.client, old_state)
        # THEN local hash and remote version update, but worker config version stays the same
        assert new_state == {
            "id": "wr1",
            "scope": "test",
            "code": "testWorker",
            "worker_version": "ABCD",
        }

    def test_remote_updates_fields(self, respx_mock):
        # GIVEN Worker exists, but it has changed from local
        respx_mock.get(f"{self.workers_url}/test/testWorker").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "id": {"scope": "test", "code": "testWorker"},
                        "displayName": "DoSomeOtherWork",
                        "description": "SomeOtherDescription",
                        "workerConfiguration": {
                            "type": "SchedulerJob",
                            "jobId": {"scope": "jobscope", "code": "jobcode"},
                        },
                        "version": {
                            "asAtCreated": "2023-10-09T12:48:27.6157190+00:00",
                            "asAtVersionNumber": 4,
                        },
                        "parameters": {},
                        "resultFields": {},
                        "links": {},
                    },
                )
            ]
        )
        respx_mock.put(f"{self.workers_url}/test/testWorker").mock(
            side_effect=[
                httpx.Response(
                    status_code=200,
                    json={
                        "displayName": "Some name",
                        "description": "Some description",
                        "workerConfiguration": {
                            "type": "SchedulerJob",
                            "jobId": {"scope": "jobscope", "code": "jobcode"},
                        },
                        "version": {
                            "asAtCreated": "2023-10-09T12:48:27.6157190+00:00",
                            "asAtVersionNumber": 5,
                        },
                    },
                )
            ]
        )
        ref = lumi.ViewRef(id="A", provider="views.test.view1")
        ref._version = "1"
        old_state = SimpleNamespace(
            id="wr1", scope="test", code="testWorker", worker_version="someworkerhash"
        )

        # WHEN local has not changed but remote version has
        wr = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="Some name",
            description="Some description",
            worker_configuration=wf.LuminesceView(view=ref),
        )

        ref._version = "ABCD"
        new_state = wr.update(self.client, old_state)
        # THEN local hash and worker config version stays the same but remote version updates
        assert new_state == {
            "id": "wr1",
            "scope": "test",
            "code": "testWorker",
            "worker_version": "ABCD",
        }

    @pytest.mark.parametrize("worker_config, worker_config_json, version", WORKER_CONFIGS)
    def test_update_lumi_scheduler_worker_config(
        self, respx_mock, worker_config, worker_config_json, version
    ):
        config = copy.deepcopy(worker_config)
        respx_mock.get(f"{self.workers_url}/test/testWorker").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "id": {"scope": "test", "code": "testWorker"},
                        "displayName": "DoSomeOtherWork",
                        "description": "SomeOtherDescription",
                        "workerConfiguration": worker_config_json,
                        "version": {
                            "asAtCreated": "2023-10-09T12:48:27.6157190+00:00",
                            "asAtVersionNumber": 1,
                        },
                        "parameters": {},
                        "resultFields": {},
                        "links": {},
                    },
                )
            ]
        )

        respx_mock.put(f"{self.workers_url}/test/testWorker").mock(
            side_effect=[
                httpx.Response(
                    status_code=200,
                    json={
                        "displayName": "Some name",
                        "description": "Some description",
                        "workerConfiguration": worker_config_json,
                        "version": {
                            "asAtCreated": "2023-10-09T12:48:27.6157190+00:00",
                            "asAtVersionNumber": 5,
                        },
                    },
                )
            ]
        )
        old_state = SimpleNamespace(id="wr1", scope="test", code="testWorker", worker_version="abc")

        wr = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="Some name",
            description="Some description",
            worker_configuration=config,
        )

        if isinstance(config, LuminesceView) and isinstance(config.view, lumi.ViewRef):
            config.view._version = version
        if isinstance(config, SchedulerJob) and isinstance(config.job, scheduler.JobRef):
            config.job._content_hash = version

        new_state = wr.update(self.client, old_state)
        # THEN local hash and worker config version stays the same but remote version updates
        assert new_state == {
            "id": "wr1",
            "scope": "test",
            "code": "testWorker",
            "worker_version": version,
        }

    def test_delete(self, respx_mock):
        respx_mock.delete(f"{self.workers_url}/test/testWorker").mock(
            side_effect=[httpx.Response(200, json={"asAt": "asAt deleted"})]
        )

        old_state = SimpleNamespace(id="wr1", scope="test", code="testWorker")
        wr = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoSomeDifferentWork",
            description="New description",
            worker_configuration=wf.LuminesceView(
                view=lumi.ViewResource(
                    id="my-view",
                    provider="Views.Unit.Test",
                    sql="select * from foo;",
                    description="a view",
                )
            ),
        )
        assert wr.delete(self.client, old_state) is None

        request = respx_mock.calls.last.request
        assert request.method == "DELETE"

    @staticmethod
    def test_deps():
        job_ref = scheduler.JobRef(id="A", scope="B", code="C")
        job = scheduler.JobResource(
            id="A",
            scope="jobscope",
            code="jobcode",
            image=scheduler.ImageRef(id="img", dest_name="img-name", dest_tag="sometag"),
            name="A job",
            description="A",
        )

        view_ref = lumi.ViewRef(id="abc", provider="Views.Unit.Ref")

        view_resource = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="select * from foo;", description="a view"
        )

        wr_lumi_view = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoSomeDifferentWork",
            description="New description",
            worker_configuration=wf.LuminesceView(view=view_resource),
        )

        deps = wr_lumi_view.deps()
        assert deps == [view_resource]

        wr_lumi_ref = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoSomeDifferentWork",
            description="New description",
            worker_configuration=wf.LuminesceView(view=view_ref),
        )
        deps = wr_lumi_ref.deps()
        assert deps == [view_ref]

        wr_healthcheck = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoSomeDifferentWork",
            description="New description",
            worker_configuration=wf.HealthCheck(url="a.com"),
        )
        deps = wr_healthcheck.deps()
        assert deps == []

        wr_fail = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoSomeDifferentWork",
            description="New description",
            worker_configuration=wf.Fail(),
        )
        deps = wr_fail.deps()
        assert deps == []

        wr_sleep = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoSomeDifferentWork",
            description="New description",
            worker_configuration=wf.Sleep(),
        )
        deps = wr_sleep.deps()
        assert deps == []

        wr_job = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoSomeDifferentWork",
            description="New description",
            worker_configuration=wf.SchedulerJob(job=job),
        )
        deps = wr_job.deps()
        assert deps == [job]

        wr_job_ref = wf.WorkerResource(
            id="wr1",
            scope="test",
            code="testWorker",
            display_name="DoSomeDifferentWork",
            description="New description",
            worker_configuration=wf.SchedulerJob(job=job_ref),
        )
        deps = wr_job_ref.deps()
        assert deps == [job_ref]

    def test_dump_simple_worker(self):
        # given a simple worker resource
        sut = wf.WorkerResource(
            id="dump-worker",
            scope="test-scope",
            code="DumpWorker",
            display_name="Test Worker",
            description="A test worker for dumping",
            worker_configuration=wf.Sleep(),
        )
        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )
        # then all fields are included (no excludes)
        expected = {
            "scope": "test-scope",
            "code": "DumpWorker",
            "displayName": "Test Worker",
            "description": "A test worker for dumping",
            "workerConfiguration": {"type": "Sleep"},
        }
        assert result == expected

    def test_undump_simple_worker(self):
        # given dumped worker data with id context
        data = {
            "scope": "test-scope",
            "code": "DumpWorker",
            "displayName": "Test Worker",
            "description": "A test worker for undumping",
            "workerConfiguration": {"type": "Sleep"},
        }
        # when we undump it with id context
        result = wf.WorkerResource.model_validate(data, context={"id": "undump-worker"})
        # then the resource is properly constructed
        assert result.id == "undump-worker"
        assert result.scope == "test-scope"
        assert result.code == "DumpWorker"
        assert result.display_name == "Test Worker"
        assert result.description == "A test worker for undumping"
        assert isinstance(result.worker_configuration, wf.Sleep)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeWorkerRef:
    base_url = TEST_BASE
    workers_url = "/workflow/api/workers"
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get(f"{self.workers_url}/w1/w2").mock(
            side_effect=[httpx.Response(200, json={"id": {"scope": "w1", "code": "w2"}})]
        )

        sut = wf.WorkerRef(id="one", scope="w1", code="w2")
        # when we call attach
        sut.attach(self.client)
        # then a get request was made with the scope passed as a parameter
        req = respx_mock.calls.last.request
        assert req.url == f"{self.base_url + self.workers_url}/w1/w2"

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get(f"{self.workers_url}/w1/w2").mock(
            side_effect=[httpx.Response(404, json={"name": "WorkerNotFound"})]
        )
        sut = wf.WorkerRef(id="two", scope="w1", code="w2")

        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(self.client)

        assert "Worker w1/w2 does not exist" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get(f"{self.workers_url}/w1/w2").mock(side_effect=[httpx.Response(400, json={})])
        client = self.client
        sut = wf.WorkerRef(id="three", scope="w1", code="w2")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)

    def test_dump_simple_task_definition(self):
        # given a simple task definition resource
        sut = wf.TaskDefinitionResource(
            id="dump-task-def",
            scope="test-scope",
            code="DumpTaskDef",
            display_name="Test Task Definition",
            description="A test task definition for dumping",
            initial_state=wf.InitialState(name="Start"),
            states=[wf.TaskStateDefinition(name="Start"), wf.TaskStateDefinition(name="End")],
        )
        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )
        # then all fields are included (no excludes)
        expected = {
            "scope": "test-scope",
            "code": "DumpTaskDef",
            "displayName": "Test Task Definition",
            "description": "A test task definition for dumping",
            "initialState": {"name": "Start", "requiredFields": []},
            "states": [{"name": "Start"}, {"name": "End"}],
        }
        assert result == expected

    def test_undump_simple_task_definition(self):
        # given dumped task definition data with id context
        data = {
            "scope": "test-scope",
            "code": "DumpTaskDef",
            "displayName": "Test Task Definition",
            "description": "A test task definition for undumping",
            "initialState": {"name": "Start", "requiredFields": []},
            "states": [{"name": "Start"}, {"name": "End"}],
        }
        # when we undump it with id context
        result = wf.TaskDefinitionResource.model_validate(data, context={"id": "undump-task-def"})
        # then the resource is properly constructed
        assert result.id == "undump-task-def"
        assert result.scope == "test-scope"
        assert result.code == "DumpTaskDef"
        assert result.display_name == "Test Task Definition"
        assert result.description == "A test task definition for undumping"
        assert result.initial_state.name == "Start"
        assert len(result.states) == 2
        assert result.states[0].name == "Start"
        assert result.states[1].name == "End"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeTaskDefinitionRef:
    base_url = TEST_BASE
    task_defs_url = "/workflow/api/taskdefinitions"
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get(f"{self.task_defs_url}/t1/t2").mock(
            side_effect=[httpx.Response(200, json={"id": {"scope": "t1", "code": "t2"}})]
        )

        sut = wf.TaskDefinitionRef(id="one", scope="t1", code="t2")
        # when we call attach
        sut.attach(self.client)
        req = respx_mock.calls.last.request
        assert req.url == f"{self.base_url + self.task_defs_url}/t1/t2"

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get(f"{self.task_defs_url}/t1/t2").mock(
            side_effect=[httpx.Response(404, json={"name": "TaskDefinitionNotFound"})]
        )
        sut = wf.TaskDefinitionRef(id="two", scope="t1", code="t2")

        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(self.client)

        assert "Task definition t1/t2 does not exist" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get(f"{self.task_defs_url}/t1/t2").mock(side_effect=[httpx.Response(400, json={})])
        client = self.client
        sut = wf.TaskDefinitionRef(id="three", scope="t1", code="t2")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


class DescribeTaskDefinitionSerialization:
    @staticmethod
    def test_initial_state():
        ex = wf.InitialState(name="test")
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "test",
            "requiredFields": [],
        }
        ex = wf.InitialState(
            name=wf.TaskStateDefinition(name="test2"),
            required_fields=["a", wf.TaskFieldDefinition(name="b", type="String")],
        )
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "test2",
            "requiredFields": ["a", "b"],
        }

        ex = wf.InitialState(name="test", required_fields=None)
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {"name": "test"}

        ex = wf.InitialState(name="test", required_fields=[])
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True, exclude_defaults=True) == {
            "name": "test",
            "requiredFields": [],
        }

    @staticmethod
    def test_trigger_definition():
        ex = wf.TriggerDefinition(name="sometrigger", type="External")
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "sometrigger",
            "trigger": {"type": "External"},
        }

    @staticmethod
    def test_field_mapping():
        ex = wf.FieldMapping(map_from="something")
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {"mapFrom": "something"}

        ex = wf.FieldMapping(set_to="somethingelse")
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {"setTo": "somethingelse"}

    @staticmethod
    def test_create_child_tasks_action():
        user_ref = identity.UserRef(id="s", login="a")
        user_ref.user_id = "myrefuser"
        ex = wf.ActionDefinition(
            name="someaction",
            action_details=wf.CreateChildTasksAction(
                child_task_configurations=[
                    wf.ChildTaskConfiguration(
                        task_definition=wf.TaskDefinitionRef(id="1", scope="somescope", code="somecode")
                    )
                ]
            ),
            run_as_user_id=user_ref,
        )

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "someaction",
            "actionDetails": {
                "type": "CreateChildTasks",
                "childTaskConfigurations": [
                    {"taskDefinitionId": {"scope": "somescope", "code": "somecode"}}
                ],
            },
            "runAsUserId": "myrefuser",
        }

        ex = wf.ActionDefinition(
            name="someaction",
            action_details=wf.CreateChildTasksAction(
                child_task_configurations=[
                    wf.ChildTaskConfiguration(
                        task_definition=wf.TaskDefinitionRef(id="1", scope="somescope", code="somecode")
                    )
                ]
            ),
            run_as_user_id="myuserid",
        )

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "someaction",
            "actionDetails": {
                "type": "CreateChildTasks",
                "childTaskConfigurations": [
                    {"taskDefinitionId": {"scope": "somescope", "code": "somecode"}}
                ],
            },
            "runAsUserId": "myuserid",
        }
        usr = identity.UserResource(
            id="something",
            first_name="s",
            last_name="b",
            email_address="d",
            login="d",
            type=identity.UserType.SERVICE,
        )

        usr.user_id = "myserviceuserid"
        ex = wf.ActionDefinition(
            name="mysecondaction",
            action_details=wf.CreateChildTasksAction(
                child_task_configurations=[
                    wf.ChildTaskConfiguration(
                        task_definition=wf.TaskDefinitionRef(id="1", scope="somescope", code="somecode"),
                        task_definition_as_at="2018-01-01T00:00:00+00:00",
                        initial_trigger=wf.TriggerDefinition(name="sometrigger", type="External"),
                        child_task_fields={"somefield": wf.FieldMapping(map_from="somethingelse")},
                        map_stacking_key_from="somewhere_else",
                    ),
                    wf.ChildTaskConfiguration(
                        task_definition=wf.TaskDefinitionRef(
                            id="1", scope="somescope", code="somecode2"
                        ),
                        task_definition_as_at=datetime(year=2018, month=1, day=1, tzinfo=timezone.utc),
                        initial_trigger="sometrigger2",
                        child_task_fields={},
                    ),
                ]
            ),
            run_as_user_id=usr,
        )

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "mysecondaction",
            "actionDetails": {
                "type": "CreateChildTasks",
                "childTaskConfigurations": [
                    {
                        "taskDefinitionId": {"scope": "somescope", "code": "somecode"},
                        "taskDefinitionAsAt": "2018-01-01T00:00:00+00:00",
                        "initialTrigger": "sometrigger",
                        "childTaskFields": {"somefield": {"mapFrom": "somethingelse"}},
                        "mapStackingKeyFrom": "somewhere_else",
                    },
                    {
                        "taskDefinitionId": {"scope": "somescope", "code": "somecode2"},
                        "taskDefinitionAsAt": "2018-01-01T00:00:00+00:00",
                        "initialTrigger": "sometrigger2",
                        "childTaskFields": {},
                    },
                ],
            },
            "runAsUserId": "myserviceuserid",
        }

    @staticmethod
    def test_worker_status_triggers():
        trigger = wf.TriggerDefinition(name="mytrigger", type="External")
        ex = wf.WorkerStatusTriggers(
            started="trigger1",
            completed_with_results="trigger2",
            completed_no_results="trigger3",
            failed_to_start="trigger4",
            failed_to_complete="trigger5",
        )
        assert ex.model_dump(mode="json", by_alias=True) == {
            "started": "trigger1",
            "completedWithResults": "trigger2",
            "completedNoResults": "trigger3",
            "failedToStart": "trigger4",
            "failedToComplete": "trigger5",
        }

        ex = wf.WorkerStatusTriggers(
            started=trigger,
            completed_with_results=trigger,
            completed_no_results=trigger,
            failed_to_start=trigger,
            failed_to_complete=trigger,
        )

        assert ex.model_dump(mode="json", by_alias=True) == {
            "started": "mytrigger",
            "completedWithResults": "mytrigger",
            "completedNoResults": "mytrigger",
            "failedToStart": "mytrigger",
            "failedToComplete": "mytrigger",
        }

        ex = wf.WorkerStatusTriggers(completed_with_results="justonetrigger")
        assert ex.model_dump(mode="json", by_alias=True) == {
            "completedWithResults": "justonetrigger",
            "started": None,
            "completedNoResults": None,
            "failedToStart": None,
            "failedToComplete": None,
        }

    @staticmethod
    def test_resultant_child_task_configuration():
        child_task_config = wf.ChildTaskConfiguration(
            task_definition=wf.TaskDefinitionRef(id="1", scope="somescope", code="somecode"),
            child_task_fields={"somefield": wf.FieldMapping(map_from="somethingelse")},
        )
        ex = wf.ResultantChildTaskConfiguration(
            child_task_configuration=child_task_config, result_matching_pattern="something"
        )
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "taskDefinitionId": {"scope": "somescope", "code": "somecode"},
            "childTaskFields": {"somefield": {"mapFrom": "somethingelse"}},
            "resultMatchingPattern": {"filter": "something"},
        }

        ex = wf.ResultantChildTaskConfiguration(child_task_configuration=child_task_config)
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "taskDefinitionId": {"scope": "somescope", "code": "somecode"},
            "childTaskFields": {"somefield": {"mapFrom": "somethingelse"}},
        }

        field = wf.TaskFieldDefinition(name="somef", type=wf.TaskFieldDefinitionType.STRING)

        child_task_config = wf.ChildTaskConfiguration(
            task_definition=wf.TaskDefinitionRef(id="1", scope="somescope", code="somecode"),
            # Pyright thinks TaskFieldDefinition is unhashable
            child_task_fields={field: wf.FieldMapping(map_from=field)},  # pyright: ignore
        )

        ex = wf.ResultantChildTaskConfiguration(child_task_configuration=child_task_config)
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "taskDefinitionId": {"scope": "somescope", "code": "somecode"},
            "childTaskFields": {"somef": {"mapFrom": "somef"}},
        }

    @staticmethod
    def test_create_run_worker_action():
        worker = wf.WorkerResource(
            id="myworkerid", scope="a", code="b", display_name="b", worker_configuration=wf.Fail()
        )
        ex = wf.ActionDefinition(name="worker", action_details=wf.RunWorkerAction(worker=worker))

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "worker",
            "actionDetails": {"type": "RunWorker", "workerId": {"scope": "a", "code": "b"}},
        }
        ex = wf.ActionDefinition(
            name="worker",
            action_details=wf.RunWorkerAction(
                worker=worker, worker_as_at=datetime(year=2018, month=1, day=1, tzinfo=timezone.utc)
            ),
        )

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "worker",
            "actionDetails": {
                "type": "RunWorker",
                "workerAsAt": "2018-01-01T00:00:00+00:00",
                "workerId": {"scope": "a", "code": "b"},
            },
        }
        child_task_config = wf.ChildTaskConfiguration(
            task_definition=wf.TaskDefinitionRef(id="1", scope="somescope", code="somecode"),
            child_task_fields={"somefield": wf.FieldMapping(map_from="somethingelse")},
        )
        ex = wf.ActionDefinition(
            name="someworker",
            action_details=wf.RunWorkerAction(
                worker=worker,
                worker_as_at="2018-01-01T00:00:00+00:00",
                worker_parameters={"somefield": wf.FieldMapping(map_from="somethingelse")},
                worker_status_triggers=wf.WorkerStatusTriggers(started="something"),
                child_task_configurations=[
                    wf.ResultantChildTaskConfiguration(
                        child_task_configuration=child_task_config, result_matching_pattern="something"
                    )
                ],
            ),
        )
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "someworker",
            "actionDetails": {
                "type": "RunWorker",
                "workerAsAt": "2018-01-01T00:00:00+00:00",
                "workerId": {"scope": "a", "code": "b"},
                "workerParameters": {"somefield": {"mapFrom": "somethingelse"}},
                "workerStatusTriggers": {"started": "something"},
                "childTaskConfigurations": [
                    {
                        "taskDefinitionId": {"scope": "somescope", "code": "somecode"},
                        "childTaskFields": {"somefield": {"mapFrom": "somethingelse"}},
                        "resultMatchingPattern": {"filter": "something"},
                    }
                ],
            },
        }

    @staticmethod
    def test_task_field_definition():
        ex = wf.TaskFieldDefinition(name="somefield", type=wf.TaskFieldDefinitionType.STRING)
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "somefield",
            "type": "String",
        }

        ex = wf.TaskFieldDefinition(
            name="somefield",
            type="DateTime",
            read_only_states=wf.ReadOnlyStates(
                state_type=wf.ReadOnlyStateType.ALL_STATES,
                selected_states=["something", wf.TaskStateDefinition(name="somestate")],
            ),
            value_constraints=wf.ValueConstraints(
                constraint_type=wf.ValueConstraintType.SUGGESTED,
                value_source_type="AcceptableValues",
                acceptable_values=["something1"],
            ),
        )
        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "somefield",
            "type": "DateTime",
            "readOnlyStates": {"stateType": "AllStates", "selectedStates": ["something", "somestate"]},
            "valueConstraints": {
                "constraintType": "Suggested",
                "valueSourceType": "AcceptableValues",
                "acceptableValues": ["something1"],
            },
        }

    @staticmethod
    def test_trigger_parent_task_action():
        ex = wf.ActionDefinition(
            name="trigger", action_details=wf.TriggerParentTaskAction(trigger="sometrigger")
        )

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "trigger",
            "actionDetails": {"type": "TriggerParentTask", "trigger": "sometrigger"},
        }

        ex = wf.ActionDefinition(
            name="trigger",
            action_details=wf.TriggerParentTaskAction(
                trigger=wf.TriggerDefinition(name="sometrigger", type="External")
            ),
        )

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "name": "trigger",
            "actionDetails": {"type": "TriggerParentTask", "trigger": "sometrigger"},
        }

    @staticmethod
    def test_task_transition_definition():
        ex = wf.TaskTransitionDefinition(from_state="state1", to_state="state2", trigger="sometrigger")

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "fromState": "state1",
            "toState": "state2",
            "trigger": "sometrigger",
        }
        ex = wf.TaskTransitionDefinition(
            from_state="state1", to_state="state2", trigger="sometrigger", action="someaction"
        )

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "fromState": "state1",
            "toState": "state2",
            "trigger": "sometrigger",
            "action": "someaction",
        }

        ex = wf.TaskTransitionDefinition(
            from_state=wf.TaskStateDefinition(name="state1"),
            to_state=wf.TaskStateDefinition(name="state2"),
            trigger=wf.TriggerDefinition(name="sometrigger", type="External"),
            guard="someguard",
            action=wf.ActionDefinition(
                name="someaction", action_details=wf.TriggerParentTaskAction(trigger="sometrigger")
            ),
        )

        assert ex.model_dump(mode="json", by_alias=True, exclude_none=True) == {
            "fromState": "state1",
            "toState": "state2",
            "trigger": "sometrigger",
            "action": "someaction",
            "guard": "someguard",
        }


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeTaskDefinitionResource:
    base_url = TEST_BASE
    task_def_url = "/workflow/api/taskdefinitions"
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @staticmethod
    def get_version(td: wf.TaskDefinitionResource) -> str:
        dump = td.model_dump(mode="json", by_alias=True, exclude_none=True, exclude={"scope", "code"})
        return hashlib.sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()

    def test_create_task_definition(self, respx_mock):
        # GIVEN Resource does not exist
        state1 = wf.TaskStateDefinition(name="state1")
        state2 = wf.TaskStateDefinition(name="state2")
        tr = wf.TaskDefinitionResource(
            id="task1",
            scope="somescope",
            code="somecode",
            display_name="name",
            description="description",
            initial_state=wf.InitialState(name=state1),
            states=[state1],
            triggers=[wf.TriggerDefinition(name="sometrigger", type="External")],
            transitions=[
                wf.TaskTransitionDefinition(from_state=state1, to_state=state2, trigger="sometrigger")
            ],
            field_schema=[wf.TaskFieldDefinition(name="somefield", type="String")],
            actions=[
                wf.ActionDefinition(
                    name="someaction", action_details=wf.TriggerParentTaskAction(trigger="sometrigger")
                )
            ],
        )
        # and server returns a normal respnse
        respx_mock.post(self.task_def_url).mock(
            side_effect=[
                httpx.Response(
                    status_code=201,
                    json={
                        "id": {"scope": "somescope", "code": "somecode"},
                        "version": {
                            "asAtCreated": "2024-07-09T08:40:56.7836370+00:00",
                            "asAtVersionNumber": "1",
                        },
                        "displayName": "name",
                        "description": "descriptions",
                        "states": [{"name": "state1"}, {"name": "state2"}],
                        "initialState": {"name": "state1", "requiredFields": []},
                        "fieldSchema": [{"name": "somefield", "type": "String"}],
                        "triggers": [{"name": "sometrigger", "type": "External"}],
                        "actions": [
                            {
                                "name": "someaction",
                                "actionDetails": {"type": "TriggerParentTask", "trigger": "sometrigger"},
                            }
                        ],
                    },
                )
            ]
        )
        # WHEN Task definition Resource is created
        new_state = tr.create(self.client)
        # THEN State returned as expected
        assert new_state == {
            "id": "task1",
            "scope": "somescope",
            "code": "somecode",
            "source_version": "8830ca77423f70290a811bb30c37527e129dfd1c80529d5c58b5ce66e1db4c85",
            "remote_version": "1",
        }
        # and the expected post request was sent to create it
        request: httpx.Request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == self.task_def_url
        assert f"https://{request.url.host}" == self.base_url
        assert json.loads(request.content) == {
            "displayName": "name",
            "initialState": {"name": "state1", "requiredFields": []},
            "states": [{"name": "state1"}],
            "description": "description",
            "triggers": [{"name": "sometrigger", "trigger": {"type": "External"}}],
            "transitions": [{"fromState": "state1", "toState": "state2", "trigger": "sometrigger"}],
            "fieldSchema": [{"name": "somefield", "type": "String"}],
            "actions": [
                {
                    "name": "someaction",
                    "actionDetails": {"type": "TriggerParentTask", "trigger": "sometrigger"},
                }
            ],
            "id": {"scope": "somescope", "code": "somecode"},
        }

    @pytest.mark.parametrize("allow_none", [True, False])
    def test_update_no_change(self, respx_mock, allow_none: bool):
        class LocalFactory(ModelFactory[wf.TaskDefinitionResource]):
            # when set to False, factory will generate values for all fields
            # when set to True
            # factory will generate fields for required fields
            # and randomly assign either a value or None to optional fields
            # this test that update works for both cases
            __allow_none_optionals__ = allow_none

        task_def = LocalFactory.build()
        source_version = self.get_version(task_def)

        respx_mock.get(f"{self.task_def_url}/{task_def.scope}/{task_def.code}").mock(
            side_effect=[httpx.Response(200, json={"version": {"asAtVersionNumber": "1"}})]
        )

        old_state = SimpleNamespace(
            id=task_def.id,
            scope=task_def.scope,
            code=task_def.code,
            source_version=source_version,
            remote_version="1",
        )

        new_state = task_def.update(self.client, old_state)
        assert new_state is None

    def test_update_identifier(self, respx_mock):
        task_def = TaskDefFactory.build(scope="somethingelse", code="someothercode")
        old_state = SimpleNamespace(id="someid", scope="somescope", code="somecode")

        respx_mock.delete(f"{self.task_def_url}/{old_state.scope}/{old_state.code}").mock(
            side_effect=[httpx.Response(200, json={"asAt": "asAt deleted"})]
        )

        respx_mock.post(self.task_def_url).mock(
            side_effect=[httpx.Response(status_code=201, json={"version": {"asAtVersionNumber": "2"}})]
        )

        result = task_def.update(self.client, old_state)
        source_version = self.get_version(task_def)

        assert result == {
            "id": task_def.id,
            "scope": "somethingelse",
            "code": "someothercode",
            "source_version": source_version,
            "remote_version": "2",
        }

    def test_update_source_changes(self, respx_mock):
        existing_task_def = TaskDefFactory.build(
            scope="somethingelse", code="someothercode", display_name="something"
        )

        old_state = SimpleNamespace(
            id="someid",
            scope="somethingelse",
            code="someothercode",
            source_version=self.get_version(existing_task_def),
            remote_version="1",
        )

        new_task_def = TaskDefFactory.build(
            scope="somethingelse", code="someothercode", display_name="somethingelse"
        )

        respx_mock.get(f"{self.task_def_url}/{existing_task_def.scope}/{existing_task_def.code}").mock(
            side_effect=[httpx.Response(200, json={"version": {"asAtVersionNumber": "1"}})]
        )

        respx_mock.put(self.task_def_url + "/somethingelse/someothercode").mock(
            side_effect=[httpx.Response(status_code=201, json={"version": {"asAtVersionNumber": "2"}})]
        )

        new_state = new_task_def.update(self.client, old_state)

        assert new_state == {
            "id": new_task_def.id,
            "scope": "somethingelse",
            "code": "someothercode",
            "source_version": self.get_version(new_task_def),
            "remote_version": "2",
        }

        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == f"{self.task_def_url}/somethingelse/someothercode"
        assert json.loads(request.content) == new_task_def.model_dump(
            mode="json", by_alias=True, exclude_none=True, exclude={"scope", "code"}
        )

    def test_update_remote_changes(self, respx_mock):
        existing_task_def = TaskDefFactory.build(scope="somethingelse", code="someothercode")

        old_state = SimpleNamespace(
            id="someid",
            scope="somethingelse",
            code="someothercode",
            source_version=self.get_version(existing_task_def),
            remote_version="1",
        )

        respx_mock.get(f"{self.task_def_url}/{existing_task_def.scope}/{existing_task_def.code}").mock(
            side_effect=[httpx.Response(200, json={"version": {"asAtVersionNumber": "2"}})]
        )

        respx_mock.put(self.task_def_url + "/somethingelse/someothercode").mock(
            side_effect=[httpx.Response(status_code=201, json={"version": {"asAtVersionNumber": "3"}})]
        )

        new_state = existing_task_def.update(self.client, old_state)

        assert new_state == {
            "id": existing_task_def.id,
            "scope": "somethingelse",
            "code": "someothercode",
            "source_version": self.get_version(existing_task_def),
            "remote_version": "3",
        }

        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == f"{self.task_def_url}/somethingelse/someothercode"
        assert json.loads(request.content) == existing_task_def.model_dump(
            mode="json", by_alias=True, exclude_none=True, exclude={"scope", "code"}
        )

    def test_delete(self, respx_mock):
        respx_mock.delete(f"{self.task_def_url}/test/testcode").mock(
            side_effect=[httpx.Response(200, json={"asAt": "asAt deleted"})]
        )

        old_state = SimpleNamespace(id="tr1", scope="test", code="testcode")
        tr = TaskDefFactory.build()

        assert tr.delete(self.client, old_state) is None

        request = respx_mock.calls.last.request
        assert request.method == "DELETE"

    def test_dump_simple_task_definition(self):
        # given a simple task definition resource
        sut = wf.TaskDefinitionResource(
            id="dump-task-def",
            scope="test-scope",
            code="DumpTaskDef",
            display_name="Test Task Definition",
            description="A test task definition for dumping",
            initial_state=wf.InitialState(name="Start"),
            states=[wf.TaskStateDefinition(name="Start"), wf.TaskStateDefinition(name="End")],
        )
        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )
        # then all fields are included (no excludes)
        expected = {
            "scope": "test-scope",
            "code": "DumpTaskDef",
            "displayName": "Test Task Definition",
            "description": "A test task definition for dumping",
            "initialState": {"name": "Start", "requiredFields": []},
            "states": [{"name": "Start"}, {"name": "End"}],
        }
        assert result == expected

    def test_undump_simple_task_definition(self):
        # given dumped task definition data with id context
        data = {
            "scope": "test-scope",
            "code": "DumpTaskDef",
            "displayName": "Test Task Definition",
            "description": "A test task definition for undumping",
            "initialState": {"name": "Start", "requiredFields": []},
            "states": [{"name": "Start"}, {"name": "End"}],
        }
        # when we undump it with id context
        result = wf.TaskDefinitionResource.model_validate(data, context={"id": "undump-task-def"})
        # then the resource is properly constructed
        assert result.id == "undump-task-def"
        assert result.scope == "test-scope"
        assert result.code == "DumpTaskDef"
        assert result.display_name == "Test Task Definition"
        assert result.description == "A test task definition for undumping"
        assert result.initial_state.name == "Start"
        assert len(result.states) == 2
        assert result.states[0].name == "Start"
        assert result.states[1].name == "End"

    @staticmethod
    def test_deps():
        task_ref = TaskDefRefFactory.build()
        task_definition = TaskDefFactory.build()
        user = UserFactory.build()
        ct1 = wf.ChildTaskConfiguration(task_definition=task_ref)
        ct2 = wf.ChildTaskConfiguration(task_definition=task_definition)
        rt1 = wf.ResultantChildTaskConfiguration(child_task_configuration=ct1)
        rt2 = wf.ResultantChildTaskConfiguration(child_task_configuration=ct2)

        create_child_task_action1 = wf.CreateChildTasksAction(child_task_configurations=[ct1, ct2])
        assert create_child_task_action1.deps() == [task_ref, task_definition]
        create_child_task_action2 = wf.CreateChildTasksAction(child_task_configurations=[])
        assert create_child_task_action2.deps() == []

        # WHEN The worker name and descriptions change
        # But not the worker config
        wr = WorkerResourceFactory.build()
        job_ref = scheduler.JobRef(id="A", scope="jobscope", code="jobcode")
        wr.worker_configuration = wf.SchedulerJob(job=job_ref)
        worker_ref = wf.WorkerRef(id="wrkr", scope="PricingDemo", code="load_quotes")
        rwa = wf.RunWorkerAction(worker=wr, child_task_configurations=[rt1])
        rwa2 = wf.RunWorkerAction(worker=worker_ref, child_task_configurations=[rt1, rt2])

        assert rwa.deps() == [wr, task_ref]

        assert rwa2.deps() == [worker_ref, task_ref, task_definition]
        user_ref = identity.UserRef(id="a", login="b")

        action1 = wf.ActionDefinition(
            name="something", action_details=create_child_task_action1, run_as_user_id=user_ref
        )

        assert action1.deps() == [user_ref, task_ref, task_definition]

        action2 = wf.ActionDefinition(name="something", action_details=rwa2, run_as_user_id=user)

        assert action2.deps() == [user, worker_ref, task_ref, task_definition]

        action4 = wf.ActionDefinition(
            name="something", action_details=wf.TriggerParentTaskAction(trigger="something")
        )
        assert action4.deps() == []

        action3 = wf.ActionDefinition(name="something", action_details=rwa2, run_as_user_id=user)

        transition1 = wf.TaskTransitionDefinition(
            from_state="a", to_state="b", trigger="something", action=action3
        )
        assert transition1.deps() == [user, worker_ref, task_ref, task_definition]

        task_def = TaskDefFactory.build(transitions=[transition1], actions=[action3])
        target = task_def.deps()
        assert target == [user, worker_ref, task_ref, task_definition] + [
            user,
            worker_ref,
            task_ref,
            task_definition,
        ]

    def test_action_definition_deps(self):
        user = identity.UserRef(
            id="user1",
            login="some@example.com",
        )
        # given an action worker which has a user ref in it's run_as
        action = wf.ActionDefinition(
            name="test",
            action_details=wf.TriggerParentTaskAction(
                trigger="something-arbitrary"
            ),
            run_as_user_id=user
        )
        deps = action.deps()
        assert deps == [user]


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeEventHandlerRef:
    base_url = TEST_BASE
    eh_url = "/workflow/api/eventhandlers"
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get(f"{self.eh_url}/eh1/eh2").mock(
            side_effect=[httpx.Response(200, json={"id": {"scope": "w1", "code": "w2"}})]
        )

        sut = wf.EventHandlerRef(id="one", scope="eh1", code="eh2")
        # when we call attach
        sut.attach(self.client)
        # then a get request was made with the scope passed as a parameter
        req = respx_mock.calls.last.request
        assert req.url.path == f"{self.eh_url}/eh1/eh2"

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get(f"{self.eh_url}/eh1/eh2").mock(
            side_effect=[httpx.Response(404, json={"name": "EventHandlerNotFound"})]
        )
        sut = wf.EventHandlerRef(id="two", scope="eh1", code="eh2")

        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(self.client)

        assert "Event handler eh1/eh2 does not exist" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get(f"{self.eh_url}/eh1/eh2").mock(side_effect=[httpx.Response(400, json={})])
        client = self.client
        sut = wf.EventHandlerRef(id="three", scope="eh1", code="eh2")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeEventHandlerResource:
    base_url = TEST_BASE
    eh_url = "/workflow/api/eventhandlers"
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def test_create_event_handler(self, respx_mock):
        # GIVEN Resource does not exist
        respx_mock.post(self.eh_url).respond(
            status_code=201, json={"version": {"asAtVersionNumber": "1"}}
        )
        # when we create it with an event_matching_pattern
        eh = wf.EventHandlerResource(
            id="id1",
            scope="eh1",
            code="eh2",
            display_name="new name",
            description="something",
            status=wf.EventStatus.INACTIVE,
            event_matching_pattern=wf.EventMatchingPattern(
                event_type="FileCreated", filter="body.filePath startswith '/somedomain/quotes'"
            ),
            run_as_user_id=wf.EventHandlerMapping(map_from="header.userId"),
            task_definition=TaskDefFactory.build(scope="a", code="b"),
            task_activity=wf.CreateNewTaskActivity(
                correlation_ids=[wf.EventHandlerMapping(set_to="int-test")],
                task_fields={"abc": wf.FieldMapping(map_from="body.filePath")},
                initial_trigger=wf.TriggerDefinition(name="abc", type="External"),
            ),
        )
        new_state = eh.create(self.client)
        # THEN State returned as expected
        assert new_state == {
            "id": "id1",
            "scope": "eh1",
            "code": "eh2",
            "source_version": "699bfead44ca952993ea9fd271a602284dbf6e6818e295f94681e0d430804ced",
            "remote_version": "1",
        }
        # and the post request is sent
        request: httpx.Request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == self.eh_url
        assert f"https://{request.url.host}" == self.base_url
        assert json.loads(request.content) == {
            "description": "something",
            "displayName": "new name",
            "eventMatchingPattern": {
                "eventType": "FileCreated",
                "filter": "body.filePath startswith " "'/somedomain/quotes'",
            },
            "id": {"code": "eh2", "scope": "eh1"},
            "runAsUserId": {"mapFrom": "header.userId"},
            "status": "Inactive",
            "taskActivity": {
                "correlationIds": [{"setTo": "int-test"}],
                "initialTrigger": "abc",
                "taskFields": {"abc": {"mapFrom": "body.filePath"}},
                "type": "CreateNewTask",
            },
            "taskDefinitionId": {"code": "b", "scope": "a"},
        }

    def test_create_scheduled_handler(self, respx_mock):
        # GIVEN Resource does not exist
        respx_mock.post(self.eh_url).respond(
            status_code=201, json={"version": {"asAtVersionNumber": "1"}}
        )
        # when we create one with a schedule matching pattern
        eh = wf.EventHandlerResource(
            id="id1",
            scope="eh1",
            code="eh2",
            display_name="new name",
            description="something",
            status=wf.EventStatus.INACTIVE,
            schedule_matching_pattern=wf.ScheduleMatchingPattern(
                context=wf.ScheduleMatchingPatternContext(
                    time_zone="America/New_York",
                ),
                recurrence_pattern=wf.RecurrencePattern(
                    time_constraints=wf.TimeConstraints(
                        start_date="2024-01-01",
                        times_of_day=[
                            wf.SpecifiedTime(hours=6, minutes=30)
                        ]
                    ),
                    date_regularity=wf.WeekRegularity(
                        days_of_week=["Mon", "Fri"],
                        frequency=2
                    ),
                    business_day_adjustment="foo"
                )
            ),
            run_as_user_id=wf.EventHandlerMapping(map_from="header.userId"),
            task_definition=TaskDefFactory.build(scope="a", code="b"),
            task_activity=wf.CreateNewTaskActivity(
                correlation_ids=[wf.EventHandlerMapping(set_to="int-test")],
                task_fields={"abc": wf.FieldMapping(map_from="body.filePath")},
                initial_trigger=wf.TriggerDefinition(name="abc", type="External"),
            ),
        )
        new_state = eh.create(self.client)
        # THEN State returned as expected
        assert new_state == {
            "id": "id1",
            "scope": "eh1",
            "code": "eh2",
            "source_version": "1daef044ef5e1c9e792cc92fb33245f69340d7133c6aacfdababc947837e0acd",
            "remote_version": "1",
        }
        # and the post request is sent
        request: httpx.Request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == self.eh_url
        assert f"https://{request.url.host}" == self.base_url
        assert json.loads(request.content) == {
            "description": "something",
            "displayName": "new name",
            "scheduleMatchingPattern": {
                "context": {
                    "timeZone": "America/New_York",
                },
                "recurrencePattern": {
                    "businessDayAdjustment": "foo",
                    "dateRegularity": {
                        "daysOfWeek": [
                            "Mon",
                            "Fri",
                        ],
                        "frequency": 2,
                        "type": "Week",
                    },
                    "timeConstraints": {
                        "startDate": "2024-01-01",
                        "timesOfDay": [
                            {
                                "hours": 6,
                                "minutes": 30,
                                "type": "Specified",
                            },
                        ],
                    },
                },
            },
            "id": {"code": "eh2", "scope": "eh1"},
            "runAsUserId": {"mapFrom": "header.userId"},
            "status": "Inactive",
            "taskActivity": {
                "correlationIds": [{"setTo": "int-test"}],
                "initialTrigger": "abc",
                "taskFields": {"abc": {"mapFrom": "body.filePath"}},
                "type": "CreateNewTask",
            },
            "taskDefinitionId": {"code": "b", "scope": "a"},
        }

    @pytest.mark.parametrize(
        "scope_and_code", [("eh1", "newcode"), ("newscope", "newcode"), ("newscope", "eh2")]
    )
    def test_update_identifier(self, respx_mock, scope_and_code):
        scope, code = scope_and_code
        # GIVEN An existing event handler
        respx_mock.delete(f"{self.eh_url}/eh1/eh2").respond(200)
        respx_mock.post(self.eh_url).respond(201, json={"version": {"asAtVersionNumber": "2"}})
        old_state = SimpleNamespace(id="id1", scope="eh1", code="eh2")
        # WHEN scope or code are changed
        sut = EventHandlerFactory.build(scope=scope, code=code)
        new_state = sut.update(self.client, old_state)
        # THEN new state is correct
        assert new_state
        assert new_state["scope"] == scope
        assert new_state["code"] == code
        assert new_state["remote_version"] == "2"
        # and a delete and a post were made

    def test_update_source(self, respx_mock):
        # GIVEN event handler exists
        existing_eh = EventHandlerFactory.build(
            id="someid", scope="somethingelse", code="someothercode", display_name="something"
        )
        old_dump = existing_eh.model_dump(
            mode="json", exclude_none=True, by_alias=True, exclude={"event_handler_id", "scope", "code"}
        )
        source_version = hashlib.sha256(json.dumps(old_dump, sort_keys=True).encode()).hexdigest()
        old_state = SimpleNamespace(
            id="someid",
            scope="somethingelse",
            code="someothercode",
            source_version=source_version,
            remote_version="1",
        )
        # When local version changes
        new_eh = EventHandlerFactory.build(
            id="someid", scope="somethingelse", code="someothercode", display_name="somethingelse"
        )
        respx_mock.get(f"{self.eh_url}/{existing_eh.scope}/{existing_eh.code}").respond(
            status_code=200, json={"version": {"asAtVersionNumber": "1"}}
        )
        respx_mock.put(self.eh_url + "/somethingelse/someothercode").respond(
            status_code=201, json={"version": {"asAtVersionNumber": "2"}}
        )
        # and updated
        new_state = new_eh.update(self.client, old_state)
        # THEN the source_version is updated
        new_dump = new_eh.model_dump(
            mode="json", exclude_none=True, by_alias=True, exclude={"event_handler_id", "scope", "code"}
        )
        source_version = hashlib.sha256(json.dumps(new_dump, sort_keys=True).encode()).hexdigest()
        assert new_state == {
            "id": existing_eh.id,
            "scope": "somethingelse",
            "code": "someothercode",
            "source_version": source_version,
            "remote_version": "2",
        }
        # and a put request was made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == f"{self.eh_url}/somethingelse/someothercode"
        assert json.loads(request.content) == new_dump

    def test_update_remote(self, respx_mock):
        # GIVEN event handler exists
        eh = EventHandlerFactory.build(
            id="someid", scope="somethingelse", code="someothercode", display_name="something"
        )
        dump = eh.model_dump(
            mode="json", exclude_none=True, by_alias=True, exclude={"event_handler_id", "scope", "code"}
        )
        source_version = hashlib.sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()
        # with asAtVersion 2
        respx_mock.get(f"{self.eh_url}/{eh.scope}/{eh.code}").respond(
            status_code=200, json={"version": {"asAtVersionNumber": "2"}}
        )
        # and the log says we deployed version 1 last run
        old_state = SimpleNamespace(
            id="someid",
            scope="somethingelse",
            code="someothercode",
            source_version=source_version,
            remote_version="1",
        )
        # When we update with the same content again
        respx_mock.put(f"{self.eh_url}/{eh.scope}/{eh.code}").respond(
            status_code=201, json={"version": {"asAtVersionNumber": "3"}}
        )
        new_state = eh.update(self.client, old_state)
        # then an update is made
        assert new_state == {
            "id": eh.id,
            "scope": "somethingelse",
            "code": "someothercode",
            "source_version": source_version,
            "remote_version": "3",
        }
        # and the update request has the desired content from before
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content) == dump

    def test_delete(self, respx_mock):
        respx_mock.delete(f"{self.eh_url}/test/testcode").respond(200)
        # given an existing resource
        old_state = SimpleNamespace(id="tr1", scope="test", code="testcode")
        eh = EventHandlerFactory.build()
        # when it is deleted
        eh.delete(self.client, old_state)
        # then a delete request is made
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"

    @staticmethod
    def test_deps():
        # given a simple event handler resource using a string username
        task_def_ref = wf.TaskDefinitionRef(id="test-task-def", scope="test-scope", code="TestTaskDef")
        sut = wf.EventHandlerResource(
            id="dump-event-handler",
            scope="test-scope",
            code="DumpEventHandler",
            display_name="Test Event Handler",
            description="A test event handler for dumping",
            status=wf.EventStatus.ACTIVE,
            event_matching_pattern=wf.EventMatchingPattern(event_type="TestEvent"),
            run_as_user_id=wf.EventHandlerMapping(set_to="TestUser"),  # string here
            task_definition=task_def_ref,
            task_activity=wf.CreateNewTaskActivity(),
        )
        assert sut.deps() == [task_def_ref]

    @staticmethod
    def test_deps_with_user():
        # given a handler resource using a user reference
        task_def_ref = wf.TaskDefinitionRef(id="test-task-def", scope="test-scope", code="TestTaskDef")
        user_ref = identity.UserRef(id="user1", login="nobody@example.com")
        sut = wf.EventHandlerResource(
            id="dump-event-handler",
            scope="test-scope",
            code="DumpEventHandler",
            display_name="Test Event Handler",
            description="A test event handler for dumping",
            status=wf.EventStatus.ACTIVE,
            event_matching_pattern=wf.EventMatchingPattern(event_type="TestEvent"),
            run_as_user_id=wf.EventHandlerMapping(set_to=user_ref),  # string here
            task_definition=task_def_ref,
            task_activity=wf.CreateNewTaskActivity(),
        )
        # then it depends on the taskl definition and the user
        assert sut.deps() == [task_def_ref, user_ref]

    def test_dump_simple_event_handler(self):
        # given a simple event handler resource
        task_def_ref = wf.TaskDefinitionRef(id="test-task-def", scope="test-scope", code="TestTaskDef")
        sut = wf.EventHandlerResource(
            id="dump-event-handler",
            scope="test-scope",
            code="DumpEventHandler",
            display_name="Test Event Handler",
            description="A test event handler for dumping",
            status=wf.EventStatus.ACTIVE,
            event_matching_pattern=wf.EventMatchingPattern(event_type="TestEvent"),
            run_as_user_id=wf.EventHandlerMapping(set_to="TestUser"),
            task_definition=task_def_ref,
            task_activity=wf.CreateNewTaskActivity(),
        )
        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )
        # then all fields are included (no excludes)
        expected = {
            "scope": "test-scope",
            "code": "DumpEventHandler",
            "displayName": "Test Event Handler",
            "description": "A test event handler for dumping",
            "status": "Active",
            "eventMatchingPattern": {"eventType": "TestEvent"},
            "runAsUserId": {"setTo": "TestUser"},
            "taskDefinitionId": {"$ref": "test-task-def"},
            "taskActivity": {"type": "CreateNewTask"},
        }
        assert result == expected

    def test_undump_event_handler_with_create_new_task_activity(self):
        # given dumped event handler data with CreateNewTaskActivity
        data = {
            "scope": "test-scope",
            "code": "CreateNewTaskHandler",
            "displayName": "Create New Task Handler",
            "description": "Event handler that creates new tasks",
            "status": "Active",
            "eventMatchingPattern": {"eventType": "FileCreated"},
            "runAsUserId": {"setTo": "TestUser"},
            "taskDefinitionId": {"$ref": "test-task-def"},
            "taskActivity": {
                "type": "CreateNewTask",
                "correlationIds": [{"setTo": "test-correlation"}],
                "taskFields": {"fileName": {"mapFrom": "body.fileName"}},
                "initialTrigger": "Start",
            },
        }
        # when we undump it with $refs context
        task_def_ref = wf.TaskDefinitionRef(id="test-task-def", scope="test-scope", code="TestTaskDef")
        result = wf.EventHandlerResource.model_validate(
            data, context={"style": "dump", "$refs": {"test-task-def": task_def_ref},
                           "id": "create-task-event-handler"}
        )
        # then the resourceId is extracted from the context
        assert result.id == "create-task-event-handler"
        assert result.scope == "test-scope"
        assert result.code == "CreateNewTaskHandler"
        # the task def is wired up
        assert result.task_definition == task_def_ref
        # the task activity gets deserialized into the right type
        assert isinstance(result.task_activity, wf.CreateNewTaskActivity)
        assert result.task_activity.type == "CreateNewTask"

    def test_undump_event_handler_with_update_matching_tasks_activity(self):
        # given dumped event handler data with UpdateMatchingTasksActivity
        data = {
            "scope": "test-scope",
            "code": "UpdateTasksHandler",
            "displayName": "Update Tasks Handler",
            "description": "Event handler that updates matching tasks",
            "status": "Active",
            "eventMatchingPattern": {"eventType": "TaskUpdated"},
            "runAsUserId": {"mapFrom": "body.userId"},
            "taskDefinitionId": {"$ref": "test-task-def"},
            "taskActivity": {
                "type": "UpdateMatchingTasks",
                "correlationIds": [{"mapFrom": "body.correlationId"}],
                "taskFields": {"status": {"setTo": "Updated"}},
                "filter": "status eq 'InProgress'",
                "trigger": "UpdateComplete",
            },
        }
        # when we undump it with $refs context
        task_def_ref = wf.TaskDefinitionRef(id="test-task-def", scope="test-scope", code="TestTaskDef")
        result = wf.EventHandlerResource.model_validate(
            data, context={"style": "dump", "$refs": {"test-task-def": task_def_ref},
                           "id": "update-tasks-event-handler"}
        )
        # then the resourceId is extracted from the context
        assert result.id == "update-tasks-event-handler"
        assert result.scope == "test-scope"
        assert result.code == "UpdateTasksHandler"
        assert result.run_as_user_id
        assert result.run_as_user_id.map_from == "body.userId"
        # the task def is wired up
        assert result.task_definition == task_def_ref
        # and the task activity is the correct type
        assert isinstance(result.task_activity, wf.UpdateMatchingTasksActivity)
        assert result.task_activity.type == "UpdateMatchingTasks"
