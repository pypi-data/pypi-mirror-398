import functools
import json
import os

import click

from . import Deployment, deploy, dump_deployment, exceptions, undump_deployment
from . import log as deployment_log
from .deploy import load_vars
from .exceptions import api_exception_handler
from .http_client import create_client
from .load_module import load_module

help_footer = "environment defaults to $LUSID_ENV and token defaults to $FBN_ACCESS_TOKEN"


# decorator which applies a set of common options to the command
def common_options(fn):
    options = [
        click.option(
            "-e",
            "--environment",
            envvar="LUSID_ENV",
            required=True,
            help="Base url to the LUSID domain, eg https://foo.lusid.com. "
            "Defaults to env var $LUSID_ENV",
        ),
        click.option(
            "-t",
            "--access-token",
            type=str,
            envvar="FBN_ACCESS_TOKEN",
            required=True,
            help="A LUSID access token. Defaults to env var $FBN_ACCESS_TOKEN",
        ),
    ]
    to_wrap = fn
    for wrapper in options:
        wrapped = wrapper(to_wrap)
        to_wrap = wrapped
    return to_wrap


def cli_exception_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            raise click.ClickException(str(e))
        except exceptions.ApiError as e:
            raise click.ClickException(str(e))
        except exceptions.ApiStatusError as e:
            raise click.ClickException(str(e))

    return wrapper


@click.group()
@click.version_option(message="%(version)s")
def cli():
    pass  # base cli class


@cli.command(epilog=help_footer)
@common_options
@cli_exception_handler
@api_exception_handler
def setup(environment, access_token):
    """Perform initial setup of the environment"""
    client = create_client(environment, access_token)
    deployment_log.setup(client)


@cli.command(epilog=help_footer)
@common_options
@click.argument("deployments", type=click.STRING, nargs=-1, required=True)
@cli_exception_handler
@api_exception_handler
def teardown(environment, access_token, deployments):
    """Remove all resources from the named deployments"""
    for name in deployments:
        click.echo(f"Teardown: {name}")
        d = Deployment(name, [])
        deploy(d, environment, access_token)


@click.group()
def log():
    """Commands for interacting with the deployment log"""
    pass


@log.command(name="list", epilog=help_footer)
@common_options
@click.argument("deployment", type=click.STRING, default=None, required=0)
@cli_exception_handler
@api_exception_handler
def list_deployments(deployment, environment, access_token):
    """List deployments, or resources within a specified deployment.
    If no deployment id passed, returns all deployment ids ordered by last modified"""
    client = create_client(environment, access_token)
    if deployment:
        for line in deployment_log.list_resources_for_deployment(client, deployment_id=deployment):
            click.echo(deployment_log.format_log_line(line))
    else:
        for line in deployment_log.list_deployments(client):
            click.echo(f"   * {line}")


@log.command(epilog=help_footer)
@common_options
@click.argument("deployment", type=click.STRING)
@click.argument("resource_id", type=click.STRING)
@cli_exception_handler
@api_exception_handler
def get(environment, access_token, deployment, resource_id):
    """Get the logged state of a resource."""
    client = create_client(environment, access_token)
    for r in deployment_log.get_resource(client, deployment, resource_id):
        click.echo(f"    {r.resource_type}")
        click.echo(json.dumps(r.state.__dict__, indent=4))


@log.command(epilog=help_footer)
@common_options
@click.argument("deployment", type=click.STRING)
@click.argument("resource_id", type=click.STRING)
@cli_exception_handler
@api_exception_handler
def deps(deployment, resource_id, environment, access_token):
    """Show dependencies for this resource."""
    client = create_client(environment, access_token)
    (index, dependencies) = deployment_log.get_dependencies_map(client, deployment)
    deployment_log.print_tree(index, dependencies, resource_id, "=>")


@log.command(epilog=help_footer)
@common_options
@click.argument("deployment", type=click.STRING)
@click.argument("resource_id", type=click.STRING)
@cli_exception_handler
@api_exception_handler
def uses(deployment, resource_id, environment, access_token):
    """Show resources dependent on this resource."""
    client = create_client(environment, access_token)
    (index, rdeps) = deployment_log.get_dependents_map(client, deployment)
    deployment_log.print_tree(index, rdeps, resource_id, "<=")


@log.command(epilog=help_footer)
@common_options
@click.option(
    "-f",
    "--force",
    is_flag=True,
    required=False,
    default=False,
    show_default=True,
    help="Remove the entry even if there are dependencies on given resource id",
)
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    required=False,
    default=False,
    show_default=True,
    help="Remove the entry and any resources that  depend on it",
)
@click.argument("deployment", type=click.STRING)
@click.argument("resource_id", type=click.STRING)
@click.pass_context
@cli_exception_handler
@api_exception_handler
def rm(ctx, deployment, resource_id, force, recursive, environment, access_token):
    """Remove resources from a deployment."""
    client = create_client(environment, access_token)
    resource_log = deployment_log.get_resource(client, deployment, resource_id)
    if len(resource_log) == 0:
        ctx.fail(f"Resource {resource_id} not found in deployment {deployment}")
    _, dependents = deployment_log.get_dependents_map(client, deployment)
    resource_uses = dependents.get(resource_id, None)
    if resource_uses and force is False:
        ctx.fail(f"   Cannot remove entry for '{resource_id}' as {resource_uses} depends on it")
    elif recursive is True and resource_uses:
        for id in resource_uses:
            deployment_log.remove(client, deployment, id)
        deployment_log.remove(client, deployment, resource_id)
        click.echo(
            f"   Removed entry for '{resource_id}' in deployment '{deployment}' "
            f"and its dependencies {dependents}"
        )
    else:
        deployment_log.remove(client, deployment, resource_id)
        click.echo(f"   Removed entry for '{resource_id}' in deployment '{deployment}'")


cli.add_command(log)


@cli.command(epilog=help_footer)
@common_options
@click.option("-v", "--vars_file", type=click.File("r"))
@click.argument("script_path", type=click.Path(readable=True))
@cli_exception_handler
@api_exception_handler
def run(script_path, environment, vars_file, access_token):
    """Deploy the configuration

    Loads the configuration script from SCRIPT_PATH
    and runs against lusid.
    vars_file will be injected into the configure function
    """
    host_vars = load_vars(vars_file)
    try:
        module = load_module(script_path, os.path.basename(script_path))
        if getattr(module, "configure", None) is None:
            raise click.ClickException(
                f"Failed importing user config: [{script_path}]. Error : No configure function found"
            )

        d = module.configure(host_vars)
    except ImportError as e:
        raise click.ClickException(f"Failed importing user config: [{script_path}]. Error : \n{e}")
    deploy(d, environment, access_token)


@cli.command(epilog=help_footer, name="rundump")
@common_options
@click.argument("dumpfile", type=click.File("r"))
@cli_exception_handler
@api_exception_handler
def cmd_rundump(dumpfile, environment, access_token):
    """ Import a deployment from a json dump
        and run it
    """
    res = undump_deployment(dumpfile)
    # print(json.dumps(dump_deployment(res), indent=4))
    deploy(res, environment, access_token)


@cli.command(epilog=help_footer, name="dump")
@click.option("-v", "--vars_file", type=click.File("r"))
@click.argument("script_path", type=click.Path(readable=True))
@cli_exception_handler
@api_exception_handler
def cmd_dump(script_path, vars_file):
    """ Dump the configuration as json

        Loads the configuration script from SCRIPT_PATH
        injects the vars file and resolves them
        converts the deployment resources to json that can be run with rundump
    """
    host_vars = load_vars(vars_file)
    try:
        module = load_module(script_path, os.path.basename(script_path))
        if getattr(module, "configure", None) is None:
            raise click.ClickException(
                f"Failed importing user config: [{script_path}]. Error : No configure function found"
            )

        d = module.configure(host_vars)
    except ImportError as e:
        raise click.ClickException(f"Failed importing user config: [{script_path}]. Error : \n{e}")
    res = dump_deployment(d)
    print(json.dumps(res, indent=4))


if __name__ == "__main__":
    cli()
