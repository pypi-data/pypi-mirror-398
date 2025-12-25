import csv
import os

from fbnconfig import Deployment, property


def configure(env):
    deployment_name = getattr(env, "name", "propertiesFromCsv")
    properties = []

    csv_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "..", "data", "property_definitions.csv"
    )

    # Read the CSV file
    with open(csv_path, mode="r", newline="") as file:
        reader = csv.DictReader(file)

        # Parse each row and create Property instances
        for row in reader:
            domain = row["Domain"]
            scope = row["PropertyScope"]
            code = row["PropertyCode"]
            property_definition = property.DefinitionResource(
                id=f"property-{domain}-{scope}-{code}",
                domain=property.Domain[domain],
                scope=scope,
                code=code,
                display_name=row["DisplayName"],
                data_type_id=property.ResourceId(scope=row["DataTypeScope"], code=row["DataTypeCode"]),
                constraint_style=property.ConstraintStyle[row["ConstraintStyle"]],
                property_description=row["Description"],
                life_time=property.LifeTime[row["Lifetime"]],
                collection_type=None,
            )
            properties.append(property_definition)

    return Deployment(deployment_name, properties)
