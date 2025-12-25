import os
from types import SimpleNamespace

from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
from fbnconfig import custodian_accounts, datatype, property
from fbnconfig.properties import PropertyValue
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
client = fbnconfig.create_client(lusid_env, token)


@fixture()
def deployment_name():
    return gen("custodian_acc")


@fixture()
def legal_entity_identifier_prop(deployment_name):
    """Create a legal entity identifier property definition."""
    identifier_property = {
        "domain": "LegalEntity",
        "scope": deployment_name,
        "code": "ClientInternal",
        "displayName": "Client Internal Identifier",
        "dataTypeId": {"scope": "system", "code": "string"},
        "lifeTime": "Perpetual",
        "constraintStyle": "Identifier",
    }

    try:
        client.post("/api/api/propertydefinitions", json=identifier_property)
    except HTTPStatusError as e:
        if e.response.status_code != 409:  # Already exists
            raise

    yield f"LegalEntity/{deployment_name}/ClientInternal"

    # Cleanup
    try:
        client.delete(f"/api/api/propertydefinitions/LegalEntity/{deployment_name}/ClientInternal")
    except HTTPStatusError:
        pass


@fixture()
def legal_entities(deployment_name, legal_entity_identifier_prop):
    """Create legal entities for custodians."""
    entity_codes = ["CUST-FIFO", "CUST-LIFO", "CUST-AVGCOST"]
    legal_entities_data = [
        {
            "identifiers": {
                legal_entity_identifier_prop: {
                    "key": legal_entity_identifier_prop,
                    "value": {"labelValue": code},
                }
            },
            "displayName": f"{code} Custodian Entity",
        }
        for code in entity_codes
    ]

    for entity in legal_entities_data:
        try:
            client.post("/api/api/legalentities", json=entity)
        except HTTPStatusError as e:
            if e.response.status_code != 409:  # Already exists
                raise
    yield entity_codes

    # Cleanup
    for code in entity_codes:
        try:
            client.delete(f"/api/api/legalentities/{deployment_name}/ClientInternal/{code}")
        except HTTPStatusError:
            pass


@fixture()
def portfolio(deployment_name, legal_entities):
    """Create a transaction portfolio for custodian accounts."""
    portfolio_code = "MAIN-PORTFOLIO"
    portfolio_request = {
        "displayName": "Test Portfolio for Custodian Accounts",
        "description": "Integration test portfolio",
        "code": portfolio_code,
        "created": "2020-01-01T00:00:00.0000000+00:00",
        "baseCurrency": "USD",
    }

    try:
        client.post(f"/api/api/transactionportfolios/{deployment_name}", json=portfolio_request)
    except HTTPStatusError as e:
        if e.response.status_code != 409:  # Already exists
            raise

    yield {"scope": deployment_name, "code": portfolio_code}

    # Cleanup
    try:
        client.delete(f"/api/api/portfolios/{deployment_name}/{portfolio_code}")
    except HTTPStatusError:
        pass


@fixture()
def setup_deployment(deployment_name, base_resources):
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Cleanup custodian account deployment state
    try:
        fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
    except Exception:
        pass


@fixture()
def base_resources(deployment_name, portfolio):
    """Create base custodian account resources."""
    # Create property definitions
    rating_prop = property.DefinitionResource(
        id="custodian-rating",
        domain=property.Domain.CustodianAccount,
        scope=deployment_name,
        code="CreditRating",
        display_name="Custodian Credit Rating",
        data_type_id=datatype.DataTypeRef(id="default_str_rating", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="Credit rating of the custodian institution",
        life_time=property.LifeTime.Perpetual,
    )

    tier_prop = property.DefinitionResource(
        id="custodian-tier",
        domain=property.Domain.CustodianAccount,
        scope=deployment_name,
        code="ServiceTier",
        display_name="Service Tier",
        data_type_id=datatype.DataTypeRef(id="default_str_tier", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="Service tier level",
        life_time=property.LifeTime.Perpetual,
    )

    # Create custodian accounts
    fifo_account = custodian_accounts.CustodianAccountResource(
        id="fifo-account",
        portfolio_scope=portfolio["scope"],
        portfolio_code=portfolio["code"],
        scope=deployment_name,
        code="FIFO-ACCOUNT",
        account_number="ACC-001",
        account_name="FIFO Test Account",
        accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
        currency="USD",
        custodian_identifier=custodian_accounts.CustodianIdentifier(
            id_type_scope=deployment_name, id_type_code="ClientInternal", code="CUST-FIFO"
        ),
        account_type=custodian_accounts.AccountTypeEnum.Margin,
        properties=[
            PropertyValue(property_key=rating_prop, label_value="AAA"),
            PropertyValue(property_key=tier_prop, label_value="Premium"),
        ],
    )

    lifo_account = custodian_accounts.CustodianAccountResource(
        id="lifo-account",
        portfolio_scope=portfolio["scope"],
        portfolio_code=portfolio["code"],
        scope=deployment_name,
        code="LIFO-ACCOUNT",
        account_number="ACC-002",
        account_name="LIFO Test Account",
        accounting_method=custodian_accounts.AccountingMethodEnum.LastInFirstOut,
        currency="GBP",
        custodian_identifier=custodian_accounts.CustodianIdentifier(
            id_type_scope=deployment_name, id_type_code="ClientInternal", code="CUST-LIFO"
        ),
        account_type=custodian_accounts.AccountTypeEnum.Cash,
    )

    avgcost_account = custodian_accounts.CustodianAccountResource(
        id="avgcost-account",
        portfolio_scope=portfolio["scope"],
        portfolio_code=portfolio["code"],
        scope=deployment_name,
        code="AVGCOST-ACCOUNT",
        account_number="ACC-003",
        account_name="Average Cost Account",
        accounting_method=custodian_accounts.AccountingMethodEnum.AverageCost,
        currency="EUR",
        custodian_identifier=custodian_accounts.CustodianIdentifier(
            id_type_scope=deployment_name, id_type_code="ClientInternal", code="CUST-AVGCOST"
        ),
        account_type=custodian_accounts.AccountTypeEnum.Swap,
        properties=[PropertyValue(property_key=rating_prop, label_value="AA")],
    )

    return [rating_prop, tier_prop, fifo_account, lifo_account, avgcost_account]


def test_create(setup_deployment, base_resources):
    """Test creating custodian accounts."""
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    # Verify the FIFO account was created with properties
    fifo_account = client.get(
        f"/api/api/transactionportfolios/{setup_deployment.name}/MAIN-PORTFOLIO/"
        f"custodianaccounts/{setup_deployment.name}/FIFO-ACCOUNT",
        params={
            "propertyKeys": [
                f"CustodianAccount/{setup_deployment.name}/CreditRating",
                f"CustodianAccount/{setup_deployment.name}/ServiceTier",
            ]
        },
    )
    assert fifo_account.status_code == 200
    fifo_data = fifo_account.json()
    assert fifo_data["accountName"] == "FIFO Test Account"
    assert fifo_data["accountNumber"] == "ACC-001"
    assert fifo_data["accountingMethod"] == "FirstInFirstOut"
    assert fifo_data["currency"] == "USD"
    assert fifo_data["accountType"] == "Margin"
    assert fifo_data["status"] == "Active"

    # Verify FIFO account has properties
    assert "properties" in fifo_data
    property_keys = list(fifo_data["properties"].keys())
    assert any("CreditRating" in key for key in property_keys)
    assert any("ServiceTier" in key for key in property_keys)

    # Verify the LIFO account was created
    lifo_account = client.get(
        f"/api/api/transactionportfolios/{setup_deployment.name}/MAIN-PORTFOLIO/"
        f"custodianaccounts/{setup_deployment.name}/LIFO-ACCOUNT"
    )
    assert lifo_account.status_code == 200
    lifo_data = lifo_account.json()
    assert lifo_data["accountName"] == "LIFO Test Account"
    assert lifo_data["accountingMethod"] == "LastInFirstOut"
    assert lifo_data["currency"] == "GBP"
    assert lifo_data["accountType"] == "Cash"

    # Verify the Average Cost account was created
    avgcost_account = client.get(
        f"/api/api/transactionportfolios/{setup_deployment.name}/MAIN-PORTFOLIO/"
        f"custodianaccounts/{setup_deployment.name}/AVGCOST-ACCOUNT"
    )
    assert avgcost_account.status_code == 200
    avgcost_data = avgcost_account.json()
    assert avgcost_data["accountName"] == "Average Cost Account"
    assert avgcost_data["accountingMethod"] == "AverageCost"
    assert avgcost_data["accountType"] == "Swap"


def test_nochange(setup_deployment, base_resources):
    """Test that redeploying without changes shows nochange."""
    # Given we have deployed the base case
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    # When we apply it again
    update = fbnconfig.deployex(deployment, lusid_env, token)

    # Then custodian accounts show no change
    custodian_account_changes = [a.change for a in update if a.type == "CustodianAccountResource"]
    assert all(change == "nochange" for change in custodian_account_changes)


def test_update(setup_deployment, base_resources, portfolio):
    """Test updating custodian accounts with actual changes."""
    deployment_name = setup_deployment.name

    # Given we have deployed the base case
    initial = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(initial, lusid_env, token)

    # When we update resources
    rating_prop = property.DefinitionResource(
        id="custodian-rating",
        domain=property.Domain.CustodianAccount,
        scope=deployment_name,
        code="CreditRating",
        display_name="Custodian Credit Rating",
        data_type_id=datatype.DataTypeRef(id="default_str_rating", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="Credit rating of the custodian institution",
        life_time=property.LifeTime.Perpetual,
    )

    tier_prop = property.DefinitionResource(
        id="custodian-tier",
        domain=property.Domain.CustodianAccount,
        scope=deployment_name,
        code="ServiceTier",
        display_name="Service Tier",
        data_type_id=datatype.DataTypeRef(id="default_str_tier", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="Service tier level",
        life_time=property.LifeTime.Perpetual,
    )

    # Update FIFO account with changed values
    updated_fifo = custodian_accounts.CustodianAccountResource(
        id="fifo-account",
        portfolio_scope=portfolio["scope"],
        portfolio_code=portfolio["code"],
        scope=deployment_name,
        code="FIFO-ACCOUNT",
        account_number="ACC-001-MODIFIED",  # Changed
        account_name="FIFO Test Account - Updated",  # Changed
        accounting_method=custodian_accounts.AccountingMethodEnum.FirstInFirstOut,
        currency="USD",
        custodian_identifier=custodian_accounts.CustodianIdentifier(
            id_type_scope=deployment_name, id_type_code="ClientInternal", code="CUST-FIFO"
        ),
        account_type=custodian_accounts.AccountTypeEnum.Margin,
        properties=[
            PropertyValue(property_key=rating_prop, label_value="AA+"),  # Changed
            PropertyValue(property_key=tier_prop, label_value="Gold"),  # Changed
        ],
    )

    # And deploy it
    updated_deployment = fbnconfig.Deployment(deployment_name, [rating_prop, tier_prop, updated_fifo])
    update = fbnconfig.deployex(updated_deployment, lusid_env, token)

    # Then we expect the custodian account to change
    custodian_account_changes = [a.change for a in update if a.type == "CustodianAccountResource"]
    assert "update" in custodian_account_changes

    # And it has the new values
    updated_account = client.get(
        f"/api/api/transactionportfolios/{deployment_name}/MAIN-PORTFOLIO/"
        f"custodianaccounts/{deployment_name}/FIFO-ACCOUNT",
        params={
            "propertyKeys": [
                f"CustodianAccount/{deployment_name}/CreditRating",
                f"CustodianAccount/{deployment_name}/ServiceTier",
            ]
        },
    )
    assert updated_account.status_code == 200
    updated_data = updated_account.json()
    assert updated_data["accountName"] == "FIFO Test Account - Updated"
    assert updated_data["accountNumber"] == "ACC-001-MODIFIED"

    # Verify the property values changed
    property_key_rating = f"CustodianAccount/{deployment_name}/CreditRating"
    property_key_tier = f"CustodianAccount/{deployment_name}/ServiceTier"
    assert property_key_rating in updated_data["properties"]
    assert updated_data["properties"][property_key_rating]["value"]["labelValue"] == "AA+"
    assert property_key_tier in updated_data["properties"]
    assert updated_data["properties"][property_key_tier]["value"]["labelValue"] == "Gold"


def test_teardown(setup_deployment, base_resources):
    """Test deleting custodian accounts."""
    deployment_name = setup_deployment.name

    # Given we have deployed the base case
    deployment = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    # When we remove all the resources
    empty = fbnconfig.Deployment(deployment_name, [])
    update = fbnconfig.deployex(empty, lusid_env, token)

    # Then resources are removed
    custodian_account_changes = [a.change for a in update if a.type == "CustodianAccountResource"]
    assert custodian_account_changes.count("remove") == 3  # All 3 accounts removed

    # And the accounts were soft deleted (status should be Inactive)
    fifo_account = client.get(
        f"/api/api/transactionportfolios/{deployment_name}/MAIN-PORTFOLIO/"
        f"custodianaccounts/{deployment_name}/FIFO-ACCOUNT"
    )
    assert fifo_account.status_code == 200
    assert fifo_account.json()["status"] == "Inactive"

    lifo_account = client.get(
        f"/api/api/transactionportfolios/{deployment_name}/MAIN-PORTFOLIO/"
        f"custodianaccounts/{deployment_name}/LIFO-ACCOUNT"
    )
    assert lifo_account.status_code == 200
    assert lifo_account.json()["status"] == "Inactive"


def test_property_dependencies(setup_deployment, base_resources):
    """Test that property definitions are created before custodian accounts."""
    deployment_name = setup_deployment.name
    deployment = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    # Verify property definitions were created
    rating_prop = client.get(
        f"/api/api/propertydefinitions/CustodianAccount/{deployment_name}/CreditRating"
    )
    assert rating_prop.status_code == 200

    tier_prop = client.get(
        f"/api/api/propertydefinitions/CustodianAccount/{deployment_name}/ServiceTier"
    )
    assert tier_prop.status_code == 200

    # Verify custodian account references these properties
    fifo_account = client.get(
        f"/api/api/transactionportfolios/{deployment_name}/MAIN-PORTFOLIO/"
        f"custodianaccounts/{deployment_name}/FIFO-ACCOUNT",
        params={
            "propertyKeys": [
                f"CustodianAccount/{deployment_name}/CreditRating",
                f"CustodianAccount/{deployment_name}/ServiceTier",
            ]
        },
    )
    assert fifo_account.status_code == 200
    fifo_data = fifo_account.json()

    # Check that properties are present with correct values
    assert "properties" in fifo_data
    property_key_rating = f"CustodianAccount/{deployment_name}/CreditRating"
    property_key_tier = f"CustodianAccount/{deployment_name}/ServiceTier"
    assert property_key_rating in fifo_data["properties"]
    assert fifo_data["properties"][property_key_rating]["value"]["labelValue"] == "AAA"
    assert property_key_tier in fifo_data["properties"]
    assert fifo_data["properties"][property_key_tier]["value"]["labelValue"] == "Premium"


def test_list_custodian_accounts(setup_deployment, base_resources):
    """Test listing all custodian accounts for a portfolio."""
    deployment_name = setup_deployment.name
    deployment = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)

    # List all custodian accounts
    accounts_list = client.get(
        f"/api/api/transactionportfolios/{deployment_name}/MAIN-PORTFOLIO/custodianaccounts"
    )
    assert accounts_list.status_code == 200
    accounts_data = accounts_list.json()

    # Should have all three accounts
    assert "values" in accounts_data
    account_codes = [acc["custodianAccountId"]["code"] for acc in accounts_data["values"]]
    assert "FIFO-ACCOUNT" in account_codes
    assert "LIFO-ACCOUNT" in account_codes
    assert "AVGCOST-ACCOUNT" in account_codes
