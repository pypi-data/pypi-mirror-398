from fbnconfig import Deployment, access, identity, workspace


def configure(_):
    start_date = "2024-01-01T00:00:00.0000000+00:00"
    #
    # UK Trading Shared workspace
    #
    uk_trading_wksp = workspace.WorkspaceResource(
        id="workspace",
        visibility=workspace.Visibility.SHARED,
        name="example_trading_uk",
        description="workspace for UK Trading dashboards",
    )
    #
    # workspace Administrator
    #
    # this selector grants full control of the workspaces because action Any
    # includes ReadItem and WriteItem
    admin_selectors = [
        access.IdSelector(
            name="data_any_workspace_example_trading_uk",
            identifier={"visibility": "shared", "name": "example_trading_uk"},
            actions=[
                access.ActionId(scope="default", activity="Any", entity="Workspace"),
            ],
        )
    ]
    # policy to allow admin
    admin_data_policy = access.PolicyResource(
        id="admin_policy",
        code="data_admin_example_trading_uk",
        applications=["LUSID"],
        grant=access.Grant.ALLOW,
        selectors=admin_selectors,
        when=access.WhenSpec(activate=start_date),
        description="Allow full admin access to the UK trading workspace and items within",
    )
    # access role for admin to hold the permissions
    admin_access_role = access.RoleResource(
        id="admin_access_role",
        code="data_admin_example_trading_uk",
        resource=access.RoleResourceRequest(policy_id_role_resource=access.PolicyIdRoleResource(policies=[admin_data_policy])),
        when=access.WhenSpec(activate=start_date),
        permission=access.Permission.EXECUTE,
    )
    # identity role for admin to hold the users. Adding this role to a user will make them an admin
    admin_identity_role = identity.IdentityRoleResource(
        id="admin_identity_role",
        name="data_admin_example_trading_uk",
        description="irole workspace_data",
    )
    #
    # Workspace reader
    #
    # this selector grants read access to the workspace and read to the items
    # inside
    read_selectors = [
        access.IdSelector(
            name="data_read_workspace_example_trading_uk",
            identifier={"visibility": "shared", "name": "example_trading_uk"},
            actions=[
                access.ActionId(scope="default", activity="Read", entity="Workspace"),
                access.ActionId(scope="default", activity="ReadItem", entity="Workspace"),
            ],
        )
    ]
    # policy to allow read
    read_data_policy = access.PolicyResource(
        id="read_policy",
        code="data_read_example_trading_uk",
        applications=["LUSID"],
        grant=access.Grant.ALLOW,
        selectors=read_selectors,
        when=access.WhenSpec(activate=start_date),
        description="Allow read access to UK trading workspace and items",
    )
    # access role for read permissions
    read_access_role = access.RoleResource(
        id="read_access_role",
        code="data_read_example_trading_uk",
        resource=access.RoleResourceRequest(policy_id_role_resource=access.PolicyIdRoleResource(policies=[read_data_policy])),
        when=access.WhenSpec(activate=start_date),
        permission=access.Permission.EXECUTE,
    )
    # identity role for read. Adding this role to a user will allow them to read workspace items
    read_identity_role = identity.IdentityRoleResource(
        id="read_identity_role",
        name="data_read_example_trading_uk",
        description="Allow read access to UK trading workspace and items",
    )
    #
    # Deployment
    #
    return Deployment("workspace_example", [
        uk_trading_wksp,
        admin_data_policy, admin_access_role, admin_identity_role,
        read_data_policy, read_access_role, read_identity_role,

    ])
