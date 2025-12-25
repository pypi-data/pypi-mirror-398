import pathlib

from fbnconfig import Deployment, drive, lumi


def configure(env):
    deployment_name = getattr(env, "name", "lumi_example")

    lumi.ViewResource.Registration.wait_time = 30
    xlsx = "RandomSpreadsheet.xlsx"
    base_folder = drive.FolderResource(
        id="base_folder", name=f"fbnconfig-{deployment_name}", parent=drive.root
    )
    deployment_folder = drive.FolderResource(id="sub_folder", name=deployment_name, parent=base_folder)
    content_path = pathlib.Path(__file__).parent.resolve() / pathlib.Path(xlsx)
    spreadsheet = drive.FileResource(
        id="xslx", folder=deployment_folder, name=xlsx, content_path=content_path
    )
    xlsx_sql = f"""\
        -- Pull data from the spreadsheet
        @client_register_master = use Drive.Excel
        --file={spreadsheet.path()}
        enduse;

        select * from @client_register_master;
    """
    xls_view = lumi.ViewResource(
        id="xls-view",
        provider=f"Views.fbnconfig.{deployment_name}",
        description="Test view for fbnconfig reading a spreadsheet",
        sql=xlsx_sql,
        dependencies=[spreadsheet],
        use_dry_run=True,
    )
    vr_provider = f"Views.fbnconfig.{deployment_name}_vr"
    vr = lumi.ViewResource(
        id="lumi-example-view",
        provider=vr_provider,
        description="My resource test view",
        documentation_link="http://example.com/query4",
        variable_shape=False,
        use_dry_run=True,
        allow_execute_indirectly=False,
        distinct=True,
        sql="""
            select 2+#PARAMETERVALUE(p1)
            as   twelve

        """,
        parameters=[
            lumi.Parameter(
                name="p1",
                value=10,
                set_as_default_value=True,
                tooltip="a number, defaults to 10",
                type=lumi.ParameterType.Int,
            ),
            lumi.Parameter(
                name="p2",
                value="a default",
                set_as_default_value=True,
                tooltip="a string",
                type=lumi.ParameterType.Text,
            ),
            lumi.Parameter(
                name="no_tooltip",
                value="a default",
                set_as_default_value=True,
                type=lumi.ParameterType.Text,
            ),
        ],
        dependencies=[],
    )
    v2_provider = f"Views.fbnconfig.{deployment_name}_v2"
    v2 = lumi.ViewResource(
        id="lumi-dependent-view",
        provider=v2_provider,
        description="My resource test view",
        documentation_link="http://example.com/query4",
        variable_shape=False,
        use_dry_run=True,
        allow_execute_indirectly=False,
        distinct=True,
        sql=f"select twelve from {vr_provider}",
        parameters=[
            lumi.Parameter(
                name="num",
                value=10,
                set_as_default_value=False,
                tooltip="a number",
                type=lumi.ParameterType.Int,
            )
        ],
        dependencies=[vr],
    )
    seven = lumi.Variable(name="seven", type=lumi.VariableType.Table, sql="select 3 + 4")
    scalar_var = lumi.ViewResource(
        id="lumi-scalar-var-view",
        provider=f"Views.fbnconfig.{deployment_name}_scalar_var",
        description="View which takes a scalar variable",
        documentation_link="http://example.com/vars_query",
        use_dry_run=False,
        distinct=True,
        sql="select * from #PARAMETERVALUE(num)",
        variables=[seven],
        parameters=[
            lumi.Parameter(
                name="num",
                value=seven,
                is_mandatory=False,
                tooltip="this should be seven",
                type=lumi.ParameterType.Table,
            )
        ],
    )
    return Deployment(deployment_name, [vr, v2, xls_view, scalar_var])
