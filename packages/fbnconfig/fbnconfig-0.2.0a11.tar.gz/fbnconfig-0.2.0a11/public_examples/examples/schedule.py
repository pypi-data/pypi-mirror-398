from fbnconfig import Deployment, scheduler

"""
An example configuration for defining scheduler related entities.
The script configures the following entities:
- Image
- Job
- Schedule

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01698/
https://support.lusid.com/knowledgebase/article/KA-02048/
https://support.lusid.com/knowledgebase/article/KA-02049/
"""


def configure(env):
    tag = "s17"

    image = scheduler.ImageResource(
        id="img1", source_image="docker.io/alpine:latest", dest_name="schedule-example", dest_tag=tag
    )

    job = scheduler.JobResource(
        id="job1",
        scope="sc1",
        code="job",
        image=image,
        name="Example Job",
        description="Example job resource",
        min_cpu="1",
        max_cpu="2",
        argument_definitions={
            "arg1": scheduler.EnvironmentArg(
                data_type="String",
                required=False,
                description="Example argument",
                order=1,
                default_value="default-value",
            )
        },
    )

    schedule = scheduler.ScheduleResource(
        id="sch1",
        name="schedule",
        scope="sc1",
        code="python-schedule",
        expression="0 30 4 * * ? *",
        timezone="Europe/London",
        job=job,
        description="Example schedule",
        arguments={"arg1": "none-default-value"},
        enabled=False,
    )

    return Deployment("scheduler_example", [image, job, schedule])
