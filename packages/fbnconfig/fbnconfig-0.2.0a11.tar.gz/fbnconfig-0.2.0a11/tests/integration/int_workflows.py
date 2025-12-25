import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import identity, scheduler
from fbnconfig import workflows as wf
from tests.integration.generate_test_name import gen


@fixture(scope="module")
def lusid_env():
    if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
        raise (
            RuntimeError("FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
        )

    env = os.environ["LUSID_ENV"]
    token = os.environ["FBN_ACCESS_TOKEN"]
    return SimpleNamespace(env=env, token=token)


@fixture(scope="module")
def client(lusid_env):
    return fbnconfig.create_client(lusid_env.env, lusid_env.token)


@fixture(scope="module")
def deployment_name():
    return gen("workflows")


def resources(deployment_name):
    tag = "v5.0"
    image = scheduler.ImageResource(
        id="img1",
        source_image="harbor.finbourne.com/ceng/fbnconfig-pipeline:0.1",
        dest_name="beany",
        dest_tag=tag,
    )
    job = scheduler.JobResource(
        id="job1",
        scope=deployment_name,
        code="jobwf",
        image=image,
        name="wfjob",
        description="something nice",
        min_cpu="1",
        max_cpu="2",
        argument_definitions={},
    )
    worker = wf.WorkerResource(
        id="wr3-example",
        scope=deployment_name,
        code="wr3",
        display_name="I am worker3",
        worker_configuration=wf.SchedulerJob(job=job),
    )
    pending_state = wf.TaskStateDefinition(name="pending")
    in_progress_state = wf.TaskStateDefinition(name="inprogress")
    end_state = wf.TaskStateDefinition(name="end")
    start_trigger = wf.TriggerDefinition(name="start", type="External")
    end_trigger = wf.TriggerDefinition(name="end", type="External")
    some_field = wf.TaskFieldDefinition(name="imafield", type=wf.TaskFieldDefinitionType.STRING)
    do_something_action = wf.ActionDefinition(
        name="start-something-worker",
        action_details=wf.RunWorkerAction(
            worker=worker,
            worker_parameters={},
            worker_status_triggers=wf.WorkerStatusTriggers(completed_with_results=end_trigger),
        ),
    )
    task_def = wf.TaskDefinitionResource(
        id="integrationtest-task-definition",
        scope=deployment_name,
        code="DoSomething",
        display_name="Does something",
        description="Task description",
        states=[pending_state, in_progress_state, end_state],
        field_schema=[some_field],
        initial_state=wf.InitialState(name=pending_state),
        triggers=[start_trigger, end_trigger],
        transitions=[
            wf.TaskTransitionDefinition(
                from_state=pending_state,
                to_state=in_progress_state,
                trigger=start_trigger,
                action=do_something_action,
            ),
            wf.TaskTransitionDefinition(
                from_state=in_progress_state, to_state=end_state, trigger=end_trigger
            ),
        ],
        actions=[do_something_action],
    )
    event_handler = wf.EventHandlerResource(
        id="integrationtest-eventhandler",
        scope=deployment_name,
        code="testeventhandler",
        display_name="new name",
        description="something",
        status=wf.EventStatus.INACTIVE,
        event_matching_pattern=wf.EventMatchingPattern(
            event_type="FileCreated",
            filter="body.filePath startswith '/somedomain/quotes'"),
        run_as_user_id=wf.EventHandlerMapping(
            map_from="header.userId"
        ),
        task_definition=task_def,
        task_activity=wf.CreateNewTaskActivity(
            correlation_ids=[wf.EventHandlerMapping(set_to="int-test")],
            task_fields={
                some_field: wf.FieldMapping(map_from="body.filePath")  # pyright: ignore
            },
            initial_trigger=start_trigger
        )
    )
    current_user = identity.CurrentUserRef(
        id="me-user"
    )
    schedule_handler = wf.EventHandlerResource(
        id="integrationtest-schedule-handler",
        scope=deployment_name,
        code="testschedulehandler",
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
                    days_of_week=["Monday"],
                    frequency=2
                ),
                business_day_adjustment="None"
            )
        ),
        run_as_user_id=wf.EventHandlerMapping(
            set_to=current_user
        ),
        task_definition=task_def,
        task_activity=wf.CreateNewTaskActivity(
            correlation_ids=[wf.EventHandlerMapping(set_to="int-test")],
            task_fields={
                some_field: wf.FieldMapping(set_to="aconstant")  # pyright: ignore
            },
            initial_trigger=start_trigger
        )
    )
    return {
        "image": image,
        "job": job,
        "worker": worker,
        "task_def": task_def,
        "event_handler": event_handler,
        "schedule_handler": schedule_handler
    }


@fixture()
def deployment(deployment_name, lusid_env):
    res = resources(deployment_name)
    print(f"\nRunning for deployment {deployment_name}...")
    yield fbnconfig.Deployment(deployment_name, list(res.values()))
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env.env, lusid_env.token)


def test_teardown(deployment, client, lusid_env):
    # create first
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    fbnconfig.deployex(fbnconfig.Deployment(deployment.id, []), lusid_env.env, lusid_env.token)
    result = client.get(f"/workflow/api/workers?filter=id.scope eq '{deployment.id}'")
    # no response returned
    assert len(result.json()["values"]) == 0


def test_create(deployment, client, lusid_env):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    workers = client.get(f"/workflow/api/workers?filter=id.scope eq '{deployment.id}'")
    task_defs = client.get(f"/workflow/api/taskdefinitions?filter=id.scope eq '{deployment.id}'")
    event_handlers = client.get(
        f"/workflow/api/eventhandlers?filter=id.scope eq '{deployment.id}'"
    )
    assert len(workers.json()["values"]) == 1
    assert len(task_defs.json()["values"]) == 1
    assert len(event_handlers.json()["values"]) == 2


def test_update_nochange(deployment, client, lusid_env):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    actions = fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    assert {a.change for a in actions} == {"nochange", "attach"}
    workers = client.get(f"/workflow/api/workers?filter=id.scope eq '{deployment.id}'")
    task_defs = client.get(f"/workflow/api/taskdefinitions?filter=id.scope eq '{deployment.id}'")
    event_handlers = client.get(
        f"/workflow/api/eventhandlers?filter=id.scope eq '{deployment.id}'"
    )
    assert len(workers.json()["values"]) == 1
    assert len(task_defs.json()["values"]) == 1
    assert len(event_handlers.json()["values"]) == 2
