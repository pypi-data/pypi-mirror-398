from fbnconfig import Deployment, identity

"""
An example configuration for defining Identity related entities.
The script configures the following entities:
- Role
- User

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01653/
https://support.lusid.com/knowledgebase/article/KA-01794/
"""


def configure(env):
    admin = identity.IdentityRoleRef(id="admin-ref", name="instrument-administrator")
    operator = identity.IdentityRoleResource(id="role1", description="scheduler-operators", name="role1")

    # ! WARNING: this will create a user in your domain, please remove the following UserResource if you
    # do not wish for that to happen.
    user = identity.UserResource(
        id="user1",
        first_name="Example",
        last_name="User",
        email_address="example_user@example.org",
        login="example_service_user@example.com",
        type=identity.UserType.SERVICE,
    )
    assignment1 = identity.RoleAssignment(id="operator", user=user, role=operator)
    assignment2 = identity.RoleAssignment(id="admin", user=user, role=admin)

    application = identity.ApplicationResource(
        id="example",
        client_id="example-id",
        display_name="Example",
        type=identity.ApplicationType.NATIVE,
    )

    return Deployment("identity_example", [assignment1, assignment2, user, operator, application])
