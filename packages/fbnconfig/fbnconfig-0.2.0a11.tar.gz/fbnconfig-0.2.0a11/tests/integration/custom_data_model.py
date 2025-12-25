from fbnconfig import Deployment, custom_data_model, datatype, property
from fbnconfig.coretypes import ResourceId


def configure(env):
    deployment_name = getattr(env, "name", "custom_data_model")

    # Create a property definition to use in the custom data model
    rating_prop = property.DefinitionResource(
        id="rating",
        domain=property.Domain.Instrument,
        scope=deployment_name,
        code="Rating",
        display_name="Credit Rating",
        data_type_id=datatype.DataTypeRef(id="default_str_rating", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="Credit rating for instruments",
        life_time=property.LifeTime.Perpetual,
    )

    maturity_prop = property.DefinitionResource(
        id="maturity",
        domain=property.Domain.Instrument,
        scope=deployment_name,
        code="MaturityDate",
        display_name="Maturity Date",
        data_type_id=datatype.DataTypeRef(id="default_str_maturity", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="Maturity date for instruments",
        life_time=property.LifeTime.TimeVariant,
    )

    # Create a base custom data model
    base_model = custom_data_model.CustomDataModelResource(
        id="base_instrument_model",
        entity_type="Instrument",
        resource_id=ResourceId(scope=deployment_name, code="BaseInstrumentModel"),
        display_name="Base Instrument Model",
        description="Base model for all instruments",
        conditions="InstrumentDefinition.InstrumentType eq 'Bond'",
        properties=[custom_data_model.DataModelProperty(property_key=rating_prop, required=True)],
    )

    # Create a child model that inherits from base
    bond_model = custom_data_model.CustomDataModelResource(
        id="bond_model",
        entity_type="Instrument",
        resource_id=ResourceId(scope=deployment_name, code="BondModel"),
        display_name="Bond Data Model",
        description="Validation model for bond instruments",
        parent_data_model=base_model,
        conditions="InstrumentDefinition.InstrumentType eq 'Bond'",
        properties=[custom_data_model.DataModelProperty(property_key=maturity_prop, required=True)],
        identifier_types=[
            custom_data_model.IdentifierType(identifier_key="Instrument/default/Isin", required=True)
        ],
        attribute_aliases=[
            custom_data_model.AttributeAlias(
                attribute_name=f"Properties[Instrument/{deployment_name}/MaturityDate]",
                attribute_alias="maturity",
            )
        ],
        recommended_sort_by=[
            custom_data_model.RecommendedSortBy(
                attribute_name=f"Properties[Instrument/{deployment_name}/MaturityDate]",
                sort_order=custom_data_model.SortOrder.ASC,
            )
        ],
    )

    return Deployment(deployment_name, [rating_prop, maturity_prop, base_model, bond_model])


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
