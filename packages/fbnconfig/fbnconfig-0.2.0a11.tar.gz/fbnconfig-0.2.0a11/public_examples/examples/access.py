from fbnconfig import Deployment, access

"""
An example configuration for defining Access related entities.
The script configures the following entities:
- Id Selector
- Policy
- Role

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01659/
https://support.lusid.com/knowledgebase/article/KA-01908/
"""


def configure(env):
    selector = access.IdSelector(
        name="ExampleId",
        description="Example ID selector",
        identifier={"scope": "sc1", "code": "cd1"},
        actions=[access.ActionId(scope="sc1", activity="execute", entity="Feature")],
    )

    policy = access.PolicyResource(
        id="ExamplePolicy",
        code="cd1",
        description="Example policy",
        applications=["Scheduler"],
        grant=access.Grant.ALLOW,
        selectors=[selector],
        when=access.WhenSpec(activate="2020-01-01T00:00:00.0000000+00:00"),
    )

    role = access.RoleResource(
        id="ExampleRole",
        code="cd1",
        description="Example role",
        resource=access.RoleResourceRequest(
            policy_id_role_resource=access.PolicyIdRoleResource(policies=[policy])
        ),
        when=access.WhenSpec(activate="2020-01-01T00:00:00.0000000+00:00"),
        permission=access.Permission.READ,
    )

    selector = access.IdSelector(
        name="ExampleId",
        description="Example ID selector",
        identifier={"scope": "sc1", "code": "cd1"},
        actions=[access.ActionId(scope="sc1", activity="execute", entity="Feature")],
    )

    templated_selector = access.TemplatedSelector(
        application="Scheduler",
        tag="Data",
        selector=selector
    )

    policy_template = access.PolicyTemplateResource(
        id="ExamplePolicyTemplate",
        display_name="display_name",
        code="cd2",
        description="Example description",
        templated_selectors=[templated_selector]
    )

    return Deployment("access_example", [role, policy_template])
