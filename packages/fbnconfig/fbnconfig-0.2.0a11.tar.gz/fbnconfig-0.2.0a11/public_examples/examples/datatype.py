from fbnconfig import Deployment, datatype, property

"""
An example configuration for data types.
The script configures the following entities:
- Data type

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01743/
"""


def configure(env):
    strategy_type = datatype.DataTypeResource(
        id="datatype-example",
        scope="sc1",
        code="cd1",
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
        id="strategy-property",
        domain=property.Domain.Portfolio,
        scope="sc1",
        code="strategy",
        display_name="Example portfolio strategy",
        data_type_id=strategy_type,
        constraint_style=property.ConstraintStyle.Property,
        property_description="Example strategy datatype property",
        life_time=property.LifeTime.Perpetual,
    )

    priority_type = datatype.DataTypeResource(
        id="priority",
        scope="sc1",
        code="priority",
        type_value_range=datatype.TypeValueRange.CLOSED,
        display_name="Priority datatype example",
        description="A datatype for Priority values",
        value_type=datatype.ValueType.STRING,
        acceptable_values=["High", "Medium", "Low"],
    )

    return Deployment("datatype_example", [strategy_type, strategy_prop, priority_type])
