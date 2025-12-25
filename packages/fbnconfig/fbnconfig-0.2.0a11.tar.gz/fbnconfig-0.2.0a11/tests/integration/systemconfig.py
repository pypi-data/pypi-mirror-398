from fbnconfig import Deployment
from fbnconfig.configuration import SystemConfigResource


# Not adding a test for it as if this runs in QA it may break pipeline tests due to system config changes
def example_configure(env):
    validate_instruments = SystemConfigResource(
        id="validate-instr",
        code="TransactionBooking",
        key="ValidateInstruments",
        value="True",
        description="Test from fbnconfig",
        default_value=False,
    )

    validate_txn_types = SystemConfigResource(
        id="validate-txn-types",
        code="TransactionBooking",
        key="ValidateTransactionTypes",
        value="False",
        description="Test from fbnconfig",
        default_value=True,
    )

    return Deployment("systemconfigtest", [validate_instruments, validate_txn_types])
