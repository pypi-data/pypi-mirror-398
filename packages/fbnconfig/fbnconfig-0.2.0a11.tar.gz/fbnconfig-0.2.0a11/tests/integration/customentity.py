from fbnconfig import Deployment, customentity


def configure(env):
    deployment_name = getattr(env, "name", "entitytype_example")
    ce = customentity.EntityTypeResource(
        id="ce2",
        entity_type_name=deployment_name,
        display_name="Takeaway menu",
        description="A menu",
        field_schema=[
            customentity.FieldDefinition(
                name="venueId",
                lifetime=customentity.LifeTime.PERPETUAL,
                type=customentity.FieldType.STRING,
                collection_type=customentity.CollectionType.SINGLE,
                required=True,
            ),
            customentity.FieldDefinition(
                name="venueOwner",
                lifetime=customentity.LifeTime.TIMEVARIANT,
                type=customentity.FieldType.STRING,
                required=True,
            ),
        ],
    )
    return Deployment(deployment_name, [ce])


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
