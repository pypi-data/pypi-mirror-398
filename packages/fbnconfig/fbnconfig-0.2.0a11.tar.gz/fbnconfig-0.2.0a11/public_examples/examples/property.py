from fbnconfig import Deployment, datatype, property

"""
An example configuration for defining property related entities.
The script configures the following entities:
- Property definition


More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01855/
"""


def configure(env):
    dom_ccy = property.DefinitionRef(
        id="dfdomccy", domain=property.Domain.Holding, scope="default", code="DfDomCcy"
    )

    nominal = property.DefinitionRef(
        id="nominal", domain=property.Domain.Holding, scope="default", code="Nominal"
    )

    rating = property.DefinitionResource(
        id="rating",
        domain=property.Domain.Instrument,
        scope="sc1",
        code="rating",
        display_name="Rating",
        data_type_id=datatype.DataTypeRef(id="default_str", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Collection,
        property_description="Example property representing a rating",
        life_time=property.LifeTime.Perpetual,
        collection_type=property.CollectionType.Array,
    )

    instrument_property_definition = property.DefinitionResource(
        id="pd1",
        domain=property.Domain.Instrument,
        scope="sc1",
        code="pd1",
        display_name="Property definition example",
        data_type_id=property.ResourceId(scope="system", code="number"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="Example property definition",
        life_time=property.LifeTime.Perpetual,
        collection_type=None,
    )

    pv_nominal = property.DefinitionResource(
        id="derived",
        domain=property.Domain.Holding,
        data_type_id=property.ResourceId(scope="system", code="number"),
        scope="sc1",
        code="PVNominal",
        property_description="Example derived property",
        display_name="DF Nominal",
        derivation_formula=property.Formula("{x} * {y}", x=dom_ccy, y=nominal),
    )

    derived_property = property.DefinitionResource(
        id="derived_property",
        domain=property.Domain.Holding,
        data_type_id=property.ResourceId(scope="system", code="number"),
        scope="sc1",
        code="derived_property",
        property_description="pd1 x df x nominal",
        display_name="DF Nominal pd1",
        derivation_formula=property.Formula(
            "{x} * {y}",
            x=pv_nominal,
            y=instrument_property_definition
        ),
    )

    return Deployment(
        "property_example",
        [instrument_property_definition, dom_ccy, nominal, pv_nominal, derived_property, rating],
    )
