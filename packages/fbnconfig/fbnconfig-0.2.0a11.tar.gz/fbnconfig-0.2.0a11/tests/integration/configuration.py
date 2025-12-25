import click

import fbnconfig
from fbnconfig import Deployment, configuration, scheduler


def configure(env):
    deployment_name = getattr(env, "name", "configuration")

    #
    # create a set and some items inside
    #
    cs = configuration.SetResource(
        id="set1",
        scope=f"set1-{deployment_name}",
        code="rbCode",
        type=configuration.SetType.PERSONAL,
        description="lovely",
    )
    username = configuration.ItemResource(
        id="user",
        set=cs,
        key="username",
        value="my-bobby-login",
        value_type=configuration.ValueType.TEXT,
        is_secret=False,
        description="whatever user",
    )
    passwd = configuration.ItemResource(
        id="pass",
        set=cs,
        key="password",
        value="my-bobby-password",
        value_type=configuration.ValueType.TEXT,
        is_secret=False,
        description="whatever pass",
    )
    #
    # add another set
    #
    set_ref = configuration.SetResource(
        id="setref",
        scope=f"shared-{deployment_name}",
        code="testref2",
        type=configuration.SetType.SHARED,
        description="something nice",
    )
    ins_item = configuration.ItemResource(
        id="item-in-ref",
        set=set_ref,
        key="user",
        value="lucy-login",
        value_type=configuration.ValueType.TEXT,
        is_secret=False,
        description="Lucy test",
    )
    #
    # create a scheduler job that uses the config for username and leaves password empty
    #
    image = scheduler.ImageResource(
        id="img1",
        source_image="harbor.finbourne.com/ceng/fbnconfig-pipeline:0.1",
        dest_name="configexample",
        dest_tag="v1",
    )
    job = scheduler.JobResource(
        id="job1",
        scope=deployment_name,
        code="configexample",
        image=image,
        name="configexample",
        description="example of a job using a config item",
        min_cpu="1",
        max_cpu="1",
        argument_definitions={
            "username": scheduler.EnvironmentArg(
                data_type="Configuration",
                required=False,
                description="A secret",
                order=1,
                default_value=username,
            ),
            "password": scheduler.EnvironmentArg(
                data_type="Configuration", required=False, description="A secret", order=1
            ),
        },
    )
    #
    # a schedule that uses config store for the password
    #
    schedule = scheduler.ScheduleResource(
        id="sch1",
        job=job,
        name="config-example",
        scope=deployment_name,
        code="config-sched",
        expression="0 30 4 * * ? *",
        timezone="Europe/London",
        description="testing config store example",
        arguments={"username": username, "password": passwd},
    )

    return Deployment(deployment_name, [schedule, job, ins_item, cs, username, passwd])


if __name__ == "__main__":
    import os

    import click

    import fbnconfig

    @click.command()
    @click.argument("lusid_url", envvar="LUSID_ENV", type=str)
    @click.option("-v", "--vars_file", type=click.File("r"))
    def cli(lusid_url, vars_file):
        host_vars = fbnconfig.load_vars(vars_file)
        d = configure(host_vars)
        fbnconfig.deployex(d, lusid_url, os.environ["FBN_ACCESS_TOKEN"])

    cli()
