from fbnconfig import Deployment, access, drive, identity, scheduler

#
# Creates a scheduled query that writes the current set of Luminesce view names to
# a file in Drive.
#
# This example shows how to create a scheduled job that runs as a service user.
# The service user is granted specific permissions required to query the data and write to a
# destination folder in Drive
company = "example.com"
service_user_login = "exports"
schedule_scope = "user_roles_schedule_example"
drive_scope = "user_roles_schedule_example"
start_date = "2024-02-18T00:00:00.0000000+00:00"
role_name = "user_roles_sche_service"


def configure(host_vars):
    #
    # add a new service user
    #
    export_user = identity.UserResource(
        id="user2",
        first_name="Export",
        last_name="ServiceAccount",
        email_address=f"exports@{company}",
        login=f"exports@{company}",
        type=identity.UserType.SERVICE,
    )
    #
    # create policies to allow the service user to access the API endpoints
    # allow use of drive and luminesce APIs and the drive UI (optional)
    #
    feature_selectors = [
        access.IdSelector(
            name="Execute * on honeycomb",
            description="Execute * on honeycomb",
            identifier={"scope": "Honeycomb", "code": "*"},
            actions=[access.ActionId(scope="Honeycomb", activity="Execute", entity="Feature")],
        ),
        access.IdSelector(
            name="Execute * on drive",
            description="Execute * on drive",
            identifier={"scope": "Drive", "code": "*"},
            actions=[access.ActionId(scope="LUSID", activity="Execute", entity="Feature")],
        ),
        access.IdSelector(
            name="Use drive on the web",
            identifier={"scope": "data-management", "code": "drive"},
            actions=[access.ActionId(scope="default", activity="view", entity="data-management")],
        ),
    ]
    feature_policy = access.PolicyResource(
        id="feature-policy",
        code="user_roles_sch_policy",
        description="Grant access to honeycomb and drive features",
        applications=["Honeycomb", "Drive", "Website"],
        grant=access.Grant.ALLOW,
        selectors=feature_selectors,
        when=access.WhenSpec(activate=start_date),
    )
    #
    # create data policies to allow the user to access the folder in Drive
    # and write the files
    #
    # allow to write to the target folder in drive
    data_selectors = [
        # allow read access on the root means you can see all the top level folders
        access.IdSelector(
            identifier={"path": "/"},
            actions=[access.ActionId(scope="default", activity="Read", entity="Folder")],
        ),
        # allow read access to the export folder itself
        access.IdSelector(
            identifier={"path": "/", "name": drive_scope},
            actions=[access.ActionId(scope="default", activity="Any", entity="Folder")],
        ),
        # allow creation of files inside the exports folder
        access.IdSelector(
            identifier={"name": "*", "path": f"/{drive_scope}"},
            actions=[access.ActionId(scope="default", activity="Any", entity="File")],
        ),
        # allow creation of folders inside the exports folder
        access.IdSelector(
            identifier={"name": "*", "path": f"/{drive_scope}"},
            actions=[access.ActionId(scope="default", activity="Any", entity="Folder")],
        ),
    ]
    data_policy = access.PolicyResource(
        id="data-policy",
        code="user_roles_sche_datapolicy",
        description="Grant access to exports folder",
        applications=["Drive"],
        grant=access.Grant.ALLOW,
        selectors=data_selectors,
        when=access.WhenSpec(activate=start_date),
    )
    #
    # Create roles for the policies
    #
    # identity role which can be attached to the user
    identity_role = identity.IdentityRoleResource(
        id="identity_role", name=role_name, description="export_jobs"
    )
    # access role which holds the policies
    access_role = access.RoleResource(
        id="access_role",
        code=role_name,
        description="Grants access to the export folder",
        resource=access.RoleResourceRequest(
            policy_id_role_resource=access.PolicyIdRoleResource(policies=[feature_policy, data_policy])
        ),
        when=access.WhenSpec(activate=start_date),
        permission=access.Permission.READ,
    )
    #
    # Assign the role to our service user
    #
    assign = identity.RoleAssignment(id="role_assignment", user=export_user, role=identity_role)
    #
    # create the folder
    #
    exports_folder = drive.FolderResource(id="exports_folder", name=drive_scope, parent=drive.root)
    #
    # create the schedule
    #
    # reference the existing (built-in) query runner job
    job = scheduler.JobRef(id="query_runner", scope="default", code="QueryRunner")
    # create a schedule for the job that is runAs the export user
    schedule = scheduler.ScheduleResource(
        id="portfolio_export_schedule",
        name="portfolio-export-schedule",
        scope=schedule_scope,
        code="user_roles_sche_export",
        expression="0 0/5 * * * ?",
        timezone="Europe/London",
        job=job,
        description="Exports luminesce",
        use_as_auth=export_user,
        arguments={
            "QUERY_01": f"""
            @data = select distinct TableName from Sys.Field order by 1;
            @@ts = select strftime('%Y%m%d_%H%M%S');
            @x = use Drive.SaveAs with @data, @@ts
            --path=/{drive_scope}
            --type=CSV
            --fileNames=export1_{{@@ts}}.csv
            enduse;
            select * from @x
        """
        },
    )
    #
    # create the deployment
    #
    return Deployment(
        "user_roles_schedule_example",
        [export_user, identity_role, access_role, assign, exports_folder, job, schedule],
    )
