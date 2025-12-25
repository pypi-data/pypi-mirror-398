from fbnconfig import Deployment, customentity, datatype, property

"""
An example configuration for a custom entity.
The script configures the following entities:
- Entity Type

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01750/en-us
"""


def configure(env):
    # entity type
    ce_type = customentity.EntityTypeResource(
        id="ce1",
        entity_type_name="entity-type-name",
        display_name="Example Custom Entity",
        description="An example custom entity",
        field_schema=[
            customentity.FieldDefinition(
                name="Field1",
                lifetime=customentity.LifeTime.PERPETUAL,
                type=customentity.FieldType.STRING,
                collection_type=customentity.CollectionType.SINGLE,
                required=True,
            ),
            customentity.FieldDefinition(
                name="Field2",
                lifetime=customentity.LifeTime.TIMEVARIANT,
                type=customentity.FieldType.STRING,
                required=True,
            ),
        ],
    )
    # data type
    string = datatype.DataTypeRef(
        id="systemstring",
        scope="system",
        code="string",
    )
    # identifier
    identifier_type = property.DefinitionResource(
        id="exid",
        domain=property.Domain.CustomEntity,
        scope="ce-example",
        code="ce-example-id",
        display_name="Example Custom Entity ID",
        data_type_id=string,
        life_time=property.LifeTime.Perpetual,
        constraint_style=property.ConstraintStyle.Identifier,
    )
    property_definition = property.DefinitionResource(
        id="propid",
        domain=property.Domain.CustomEntity,
        scope="ce-example",
        code="ce-example-prop",
        display_name="Example Property on a CE",
        data_type_id=string,
        life_time=property.LifeTime.Perpetual,
        constraint_style=property.ConstraintStyle.Property,
    )
    # entity instance with properties
    ce_instance = customentity.EntityResource(
        id="ce1-instance",
        entity_type=ce_type,
        description="An example custom entity instance",
        display_name="Example Instance",
        identifiers=[
            customentity.EntityIdentifier(
                identifier_type=identifier_type,
                identifier_value="ce-exmaple-one",
            )
        ],
        fields=[
            customentity.EntityField(
                name="Field1",
                value="Example Value 1",
            ),
            customentity.EntityField(
                name="Field2",
                value="Example Value 2",
            )
        ],
        properties=[customentity.PropertyValue(
            property_key=property_definition,
            label_value="banjo",
        )]
    )
    return Deployment("custom_entity_example", [ce_type, ce_instance, identifier_type])
