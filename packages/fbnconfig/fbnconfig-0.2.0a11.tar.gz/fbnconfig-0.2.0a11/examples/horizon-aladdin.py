from fbnconfig import Deployment, horizon


def configure(_):
    instance = horizon.IntegrationInstanceResource(
        id="instance",
        integration_type="blackrock-aladdin",
        name="example_aladdin_Int96",
        description="my first aladdin",
        enabled=False,
        triggers=[],
        details={
            "sourceFileLocation": "/sftp",
            "onboardingDate": "2022-01-01",
            "localTimeZone": "Australia/Melbourne",
            "unpackFromArchive": False,
            "archiveFileMask": "",
            "isFxNdfAllowed": True,
            "int29AnalyticsFileType": "NotApplicable",
            "allowCoreFieldUpdates": "Never",
            "blackRockAladdinInterfaceSelections": [{
                "interfaceNumber": "Int96",
                "fileMask": "^ATOM_R_newcash96_daily.*_*.xml$",
                "localCutTime": "00:00"
            }]

        }
    )
    return Deployment("example-aladdin", [instance])
