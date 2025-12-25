from fbnconfig import Deployment, access, drive, identity, scheduler

company = "robert.byrnemail.org"
service_user_login = "exports"
schedule_scope = "export_jobs"
drive_scope = "exports"
start_date = "2024-02-18T00:00:00.0000000+00:00"
role_name = "export_job_service"


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
    # create role to allow the service user to be used as principal for the schedule
    # allow use of drive and luminesce
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
        code="export_service_feature_policy",
        description="Grant access to honeycomb and drive features",
        applications=["Honeycomb", "Drive", "Website"],
        grant=access.Grant.ALLOW,
        selectors=feature_selectors,
        when=access.WhenSpec(activate=start_date),
    )
    # allow it to write to the target folder in drive
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
        code="grant_export_data_folder",
        description="Grant access to exports folder",
        applications=["Drive"],
        grant=access.Grant.ALLOW,
        selectors=data_selectors,
        when=access.WhenSpec(activate=start_date),
    )
    # identity role
    identity_role = identity.IdentityRoleResource(
        id="identity_role", name=role_name, description="export_jobs"
    )
    # access role with name matching the identity role
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
    # give the role to the user
    assign = identity.RoleAssignment(id="role_assignment", user=export_user, role=identity_role)
    #
    # create the folder
    #
    exports_folder = drive.FolderResource(id="exports_folder", name=drive_scope, parent=drive.root)
    #
    # create the schedule
    #
    # reference existing query runner job
    job = scheduler.JobRef(id="query_runner", scope="default", code="QueryRunner")
    # create a schedule for the job that is runAs the export user
    schedule = scheduler.ScheduleResource(
        id="portfolio_export_schedule",
        name="portfolio-export-schedule",
        scope=schedule_scope,
        code="portfolio_export",
        expression="0 0/5 * * * ?",
        timezone="Europe/London",
        job=job,
        description="Exports portfolios",
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
        "scheduled_export",
        [export_user, identity_role, access_role, assign, exports_folder, job, schedule],
    )
