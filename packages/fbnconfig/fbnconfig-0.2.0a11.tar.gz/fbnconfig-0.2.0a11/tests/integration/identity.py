from fbnconfig import Deployment, identity


def configure(env):
    admin = identity.IdentityRoleRef(id="admin", name="instrument-administrator")
    operator = identity.IdentityRoleResource(
        id="role1", description="scheduler-operators", name="robTest_role2"
    )
    user = identity.UserResource(
        id="user_jane3",
        first_name="robTestJane",
        last_name="robTestSmith",
        email_address="robtest_jane@robert.byrnemail.org",
        login="robtest_jane3@robtest.com",
        type=identity.UserType.SERVICE,
    )
    assignment1 = identity.RoleAssignment(id="jane3_operator", user=user, role=operator)
    assignment2 = identity.RoleAssignment(id="jane3_admin", user=user, role=admin)
    return Deployment("identity", [assignment1, assignment2, user, operator])


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
