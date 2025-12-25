from fbnconfig import Deployment, scheduler


def configure(env) -> Deployment:
    deployment_name = getattr(env, "name", "schedule")
    tag = "v5.0"
    i = scheduler.ImageResource(
        id="img1",
        source_image="harbor.finbourne.com/ceng/fbnconfig-pipeline:0.1",
        dest_name="beany",
        dest_tag=tag,
    )
    j = scheduler.JobResource(
        id="job1",
        scope=deployment_name,
        code="job",
        image=i,
        name="RobsJob",
        description="something nice",
        min_cpu="1",
        max_cpu="2",
        argument_definitions={
            "arg1": scheduler.EnvironmentArg(
                data_type="String",
                required=False,
                description="My argument",
                order=1,
                default_value="mydefaultvalue",
            )
        },
    )
    s = scheduler.ScheduleResource(
        id="sch1",
        name="my-schedule",
        scope=deployment_name,
        code="python-sched",
        expression="0 30 4 * * ? *",
        timezone="Europe/London",
        job=j,
        description="my awesome schedule",
        arguments={"arg1": "mynotdefaultvalue"},
    )
    return Deployment(deployment_name, [i, j, s])
