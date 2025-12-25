from fbnconfig import Deployment, datatype, property

# https://support.lusid.com/knowledgebase/article/KA-01743/


def configure(env):
    deployment_name = getattr(env, "name", "datatype_example2")
    strategy_type = datatype.DataTypeResource(
        id="robtest_strategy",
        scope=deployment_name,
        code="robtest_strategy",
        type_value_range=datatype.TypeValueRange.CLOSED,
        display_name="Portfolio Strategy Test",
        description="A test datatype modified",
        value_type=datatype.ValueType.STRING,
        reference_data=datatype.ReferenceData(
            field_definitions=[
                datatype.FieldDefinition(key="description", is_required=True, is_unique=False),
                datatype.FieldDefinition(key="commission", is_required=True, is_unique=False),
            ],
            values=[
                datatype.FieldValue(
                    value="I", fields={"description": "Investment Portfolio", "commission": "0.01"}
                ),
                datatype.FieldValue(
                    value="H", fields={"description": "Hedging Portfolio", "commission": "0.05"}
                ),
                datatype.FieldValue(
                    value="C", fields={"description": "Client Portfolio", "commission": "0.10"}
                ),
            ],
        ),
    )
    strategy_prop = property.DefinitionResource(
        id="robtest_strategt_prop",
        domain=property.Domain.Portfolio,
        scope=deployment_name,
        code="strategy",
        display_name="robtest portfolio strategy ",
        data_type_id=strategy_type,
        constraint_style=property.ConstraintStyle.Property,
        property_description="robTest strategy datatype property",
        life_time=property.LifeTime.Perpetual,
    )
    priority_type = datatype.DataTypeResource(
        id="robtest_priority",
        scope=deployment_name,
        code="robtest_priority",
        type_value_range=datatype.TypeValueRange.CLOSED,
        display_name="Priority Test",
        description="A test datatype for Priority",
        value_type=datatype.ValueType.STRING,
        acceptable_values=["High", "Medium", "Low"],
    )
    return Deployment(deployment_name, [strategy_type, strategy_prop, priority_type])


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
        client = fbnconfig.http_client.create_client(lusid_url, os.environ["FBN_ACCESS_TOKEN"])
        print(client.get("/api/api/datatypes/datatype_example2/robtest_strategy").json())

    cli()
