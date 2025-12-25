import datetime as dt
import pathlib

from fbnconfig import Deployment, drive, lumi, property

"""
An example configuration for defining Luminesce views and inlined properties.
The script configures the following entities:
- Folder
- File
- View
- Inlined Properties

For more information on Folder and File resources, please refer to the `drive.py`
example.

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01767/
"""


def configure(env):
    lumi.ViewResource.Registration.wait_time = 30
    xlsx = "../data/example-spreadsheet.xlsx"
    base_folder = drive.FolderResource(id="base_folder", name="fbnconfig-folder", parent=drive.root)
    deployment_folder = drive.FolderResource(
        id="sub_folder", name="deployment-folder", parent=base_folder
    )
    content_path = pathlib.Path(__file__).parent.resolve() / pathlib.Path(xlsx)
    spreadsheet = drive.FileResource(
        id="xslx", folder=deployment_folder, name="example-spreadsheet.xlsx", content_path=content_path
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
        provider="Views.fbnconfig.ExampleProvider",
        description="Test view for fbnconfig reading a spreadsheet",
        sql=xlsx_sql,
        dependencies=[spreadsheet],
        use_dry_run=True,
    )
    vr_provider = "Views.fbnconfig.ExampleProvider_vr"
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
        ],
        dependencies=[],
    )
    v2_provider = "Views.fbnconfig.ExampleProvider_v2"
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
        provider="Views.fbnconfig.ExampleProvider_scalar_var",
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
    # Create inline properties resource
    test_property_ref = property.DefinitionRef(
        id="test-property-ref", domain=property.Domain.Transaction, scope="default", code="Custodian"
    )
    inline_properties = lumi.InlinePropertiesResource(
        id="test-inline-properties",
        provider="Lusid.Portfolio.Txn",
        provider_name_extension="Example",
        properties=[
            lumi.InlineProperty(
                key=test_property_ref,
                name="TestProperty",
                data_type=lumi.InlineDataType.Text,
                description="Test property for integration testing",
                is_main=True,
                as_at=dt.datetime(2025, 9, 20)
            )
        ],
    )
    return Deployment("luminesce_example", [vr, v2, xls_view, scalar_var, inline_properties])
