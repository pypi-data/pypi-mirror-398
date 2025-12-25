from fbnconfig import Deployment, access


def configure(env):
    deployment_name = getattr(env, "name", "policies")

    ids = access.IdSelector(
        name="banjo",
        description="whatever",
        identifier={"scope": f"w_{deployment_name}", "code": "y"},
        actions=[access.ActionId(scope=deployment_name, activity="execute", entity="Feature")],
    )
    idp = access.PolicyResource(
        id="polly",
        code=f"policy-{deployment_name}",
        description="Policy with an Id selector",
        applications=["Scheduler"],
        grant=access.Grant.ALLOW,
        selectors=[ids],
        when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
    )

    r = access.RoleResource(
        id="role-1",
        code=f"role-{deployment_name}",
        description="Role with an Id selector",
        resource=access.RoleResourceRequest(
            policy_id_role_resource=access.PolicyIdRoleResource(policies=[idp])
        ),
        when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
        permission=access.Permission.READ,
    )

    malls = access.MatchAllSelector(
        name="banana",
        description="match all selector",
        actions=[access.ActionId(scope=deployment_name, activity="execute", entity="Feature")],
    )
    mallp = access.PolicyResource(
        id="match-all-polly",
        code=f"policy-matchall-{deployment_name}",
        description="Policy with a match all selector",
        applications=["Scheduler"],
        grant=access.Grant.ALLOW,
        selectors=[malls],
        when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
    )
    policy_selector = access.PolicySelector(
        name="policy-banana",
        description="a policy selector",
        actions=[access.ActionId(scope=deployment_name, activity="execute", entity="Feature")],
    )
    multi_policy = access.PolicyResource(
        id="multi-polly",
        code=f"multi-polly{deployment_name}",
        description="Policy with a policy selector and a match all selector",
        applications=["Scheduler"],
        grant=access.Grant.ALLOW,
        selectors=[policy_selector, malls],
        when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
    )
    support_pol = access.PolicyRef(
        id="support", scope="support", code="support-access-to-drive-website-feature"
    )
    collection1 = access.PolicyCollectionResource(
        id="polly-collection-inner",
        code=f"robtest-innercol-{deployment_name}",
        policies=[idp, support_pol],
    )
    collection = access.PolicyCollectionResource(
        id="polly-collection",
        code=f"robtest-col-4-{deployment_name}",
        policies=[idp, mallp],
        policy_collections=[collection1],
    )
    collection_role = access.RoleResource(
        id="role-2",
        code=f"role-coll-{deployment_name}",
        description="Role with a policy collection",
        resource=access.RoleResourceRequest(
            policy_id_role_resource=access.PolicyIdRoleResource(policy_collections=[collection])
        ),
        when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
        permission=access.Permission.READ,
    )
    temp_selector = access.TemplatedSelector(
        application="example_application",
        tag="Data",
        selector=ids
    )
    policy_template = access.PolicyTemplateResource(
        id="polly-template",
        display_name="updated-policy-template",
        code=f"policy-template-{deployment_name}",
        description="Example policy template for a policy that grants access to some resource",
        templated_selectors=[temp_selector],
    )

    return Deployment(deployment_name, [collection_role, r, mallp, multi_policy, policy_template])


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
