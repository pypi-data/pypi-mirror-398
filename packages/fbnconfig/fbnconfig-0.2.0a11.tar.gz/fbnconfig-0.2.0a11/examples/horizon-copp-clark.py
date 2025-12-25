from fbnconfig import Deployment, horizon, property


def configure(_):
    instance = horizon.IntegrationInstanceResource(
        id="copp-clark-instance",
        integration_type="copp-clark",
        name="cc2",
        description="my modified cc",
        enabled=True,
        triggers=[
            horizon.Trigger(
                type="time",
                cron_expression="0 13 0 ? * *",
                time_zone="Europe/London",
            )
        ],
        details={
            "paymentSystemsCalendar": {
                "currencyFilter": [
                  "GBP"
                ],
                "importUnqualified": False
            }
        }
    )
    prop1 = property.DefinitionRef(
        id="p1",
        domain=property.Domain.Instrument,
        scope="default",
        code="Status"
    )
    props = horizon.OptionalPropsResource(
        id="copp-clark-props",
        instance=instance,
        props=[
            horizon.OptionalProp(
                property=prop1,
                display_name_override="status3",
                description_override="renamed it",
            )
        ]
    )

    return Deployment("example-copp-clark", [props, instance])
