from fbnconfig import Deployment
from fbnconfig.configuration import SystemConfigResource

"""
An example configuration for defining system configuration entities.
The script configures the following entities:
- System configuration

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01768/
https://support.lusid.com/knowledgebase/article/KA-01799/
"""


def configure(env):
    validate_instruments = SystemConfigResource(
        id="validate-instruments",
        code="TransactionBooking",
        key="ValidateInstruments",
        value="True",
        description="Sets validation that instruments exist when booking transactions",
        default_value=False,
    )

    validate_txn_types = SystemConfigResource(
        id="validate-txn-types",
        code="TransactionBooking",
        key="ValidateTransactionTypes",
        value="False",
        description="Sets validation that transaction types exist when booking transactions",
        default_value=True,
    )

    return Deployment("system-configuration", [validate_instruments, validate_txn_types])
