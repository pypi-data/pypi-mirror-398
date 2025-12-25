from __future__ import annotations

import json
import string
from enum import StrEnum
from hashlib import sha256
from typing import Sequence

import httpx
from pydantic import BaseModel, Field, model_validator

from .properties import MetricValue, PropertyValue, PropertyValueDict
from .resource_abc import CamelAlias, Ref, Resource, register_resource
from .urlfmt import Urlfmt

# force these to be exported
_ = [PropertyValue, MetricValue]

url: string.Formatter = Urlfmt("api/api/transactionportfolios")
CREATE_CUSTODIAN_ACCOUNTS_URL = "{base}/{portfolio_scope}/{portfolio_code}/custodianaccounts"
CUSTODIAN_ACCOUNT_URL = "{base}/{portfolio_scope}/{portfolio_code}/custodianaccounts/{scope}/{code}"
DELETE_CUSTODIAN_ACCOUNTS_URL = "{base}/{portfolio_scope}/{portfolio_code}/custodianaccounts/$delete"


class AccountingMethodEnum(StrEnum):
    Default = "Default"
    AverageCost = "AverageCost"
    FirstInFirstOut = "FirstInFirstOut"
    LastInFirstOut = "LastInFirstOut"
    HighestCostFirst = "HighestCostFirst"
    LowestCostFirst = "LowestCostFirst"
    ProRateByUnits = "ProRateByUnits"
    ProRateByCost = "ProRateByCost"
    ProRateByCostPortfolioCurrency = "ProRateByCostPortfolioCurrency"
    IntraDayThenFirstInFirstOut = "IntraDayThenFirstInFirstOut"
    LongTermHighestCostFirst = "LongTermHighestCostFirst"
    LongTermHighestCostFirstPortfolioCurrency = "LongTermHighestCostFirstPortfolioCurrency"
    HighestCostFirstPortfolioCurrency = "HighestCostFirstPortfolioCurrency"
    LowestCostFirstPortfolioCurrency = "LowestCostFirstPortfolioCurrency"
    MaximumLossMinimumGain = "MaximumLossMinimumGain"
    MaximumLossMinimumGainPortfolioCurrency = "MaximumLossMinimumGainPortfolioCurrency"


class AccountTypeEnum(StrEnum):
    Margin = "Margin"
    Cash = "Cash"
    Swap = "Swap"


class CustodianIdentifier(CamelAlias, BaseModel):
    """Identifier for the custodian entity (legal entity or person) already mastered in LUSID."""

    id_type_scope: str
    id_type_code: str
    code: str


@register_resource()
class CustodianAccountRef(CamelAlias, BaseModel, Ref):
    """Reference to an existing custodian account."""

    id: str = Field(exclude=True)
    portfolio_scope: str
    portfolio_code: str
    scope: str
    code: str

    def attach(self, client):
        """Verify that the custodian account exists."""
        formatted_url = url.format(
            CUSTODIAN_ACCOUNT_URL,
            portfolio_scope=self.portfolio_scope,
            portfolio_code=self.portfolio_code,
            scope=self.scope,
            code=self.code,
        )
        try:
            client.get(formatted_url)
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(
                    f"CustodianAccount {self.scope}/{self.code} not found in portfolio "
                    f"{self.portfolio_scope}/{self.portfolio_code}"
                )
            else:
                raise ex


@register_resource()
class CustodianAccountResource(CamelAlias, BaseModel, Resource):
    """
    Manages custodian accounts for transaction portfolios.

    Custodian accounts allow you to segregate holdings and track which custodian
    holds specific assets within a portfolio.
    """

    id: str = Field(exclude=True)
    # Parent portfolio identifier
    portfolio_scope: str
    portfolio_code: str
    # Custodian account identifier
    scope: str
    code: str
    # Account details
    account_number: str
    account_name: str
    accounting_method: AccountingMethodEnum
    currency: str
    custodian_identifier: CustodianIdentifier
    account_type: AccountTypeEnum | None = None
    # Optional properties
    properties: PropertyValueDict | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info):
        """Handle deserialization from stored state."""
        if not isinstance(data, dict):
            return data

        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        """Read current state of a custodian account from LUSID."""
        formatted_url = url.format(
            CUSTODIAN_ACCOUNT_URL,
            portfolio_scope=old_state.portfolio_scope,
            portfolio_code=old_state.portfolio_code,
            scope=old_state.scope,
            code=old_state.code,
        )

        # Fetch properties
        property_keys = []
        if self.properties:
            for prop_value in self.properties:
                prop_key = prop_value.property_key
                full_key = f"{prop_key.domain.value}/{prop_key.scope}/{prop_key.code}"
                property_keys.append(full_key)

        # Pass params as dict with list value (not list of tuples)
        params = {"propertyKeys": property_keys} if property_keys else {}
        response = client.get(formatted_url, params=params)
        return response.json()

    def create(self, client):
        """Create a new custodian account using the Upsert endpoint."""
        desired = self.model_dump(
            mode="json",
            exclude_none=True,
            exclude={"id", "portfolio_scope", "portfolio_code"},
            by_alias=True,
        )

        # Upsert endpoint expects an array of custodian accounts
        request_body = [desired]

        # Calculate content hash for change detection
        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode("utf-8")).hexdigest()

        formatted_url = url.format(
            CREATE_CUSTODIAN_ACCOUNTS_URL,
            portfolio_scope=self.portfolio_scope,
            portfolio_code=self.portfolio_code,
        )

        client.post(formatted_url, json=request_body)

        return {
            "portfolio_scope": self.portfolio_scope,
            "portfolio_code": self.portfolio_code,
            "scope": self.scope,
            "code": self.code,
            "content_hash": content_hash,
        }

    def update(self, client, old_state):
        """Update an existing custodian account if it has changed."""
        # Check if the identifier has changed (requires delete + recreate)
        if (
            self.portfolio_scope != old_state.portfolio_scope
            or self.portfolio_code != old_state.portfolio_code
            or self.scope != old_state.scope
            or self.code != old_state.code
        ):
            self.delete(client, old_state)
            return self.create(client)

        # Calculate content hash to detect changes
        desired = self.model_dump(
            mode="json",
            exclude_none=True,
            exclude={"id", "portfolio_scope", "portfolio_code"},
            by_alias=True,
        )
        sorted_desired = json.dumps(desired, sort_keys=True)
        desired_hash = sha256(sorted_desired.encode("utf-8")).hexdigest()

        # No changes needed
        if desired_hash == old_state.content_hash:
            return None

        # Upsert the updated account
        request_body = [desired]
        formatted_url = url.format(
            CREATE_CUSTODIAN_ACCOUNTS_URL,
            portfolio_scope=self.portfolio_scope,
            portfolio_code=self.portfolio_code,
        )

        client.post(formatted_url, json=request_body)

        return {
            "portfolio_scope": self.portfolio_scope,
            "portfolio_code": self.portfolio_code,
            "scope": self.scope,
            "code": self.code,
            "content_hash": desired_hash,
        }

    @staticmethod
    def delete(client, old_state):
        """Delete a custodian account (soft or hard delete)."""
        formatted_url = url.format(
            DELETE_CUSTODIAN_ACCOUNTS_URL,
            portfolio_scope=old_state.portfolio_scope,
            portfolio_code=old_state.portfolio_code,
        )

        # Request body contains the custodian accounts to delete
        request_body = [{"scope": old_state.scope, "code": old_state.code}]

        # Default deleteMode is "Soft" which sets status to Inactive
        # Can also use "Hard" to permanently delete
        params = {"deleteMode": "Soft"}

        client.post(formatted_url, json=request_body, params=params)

    def deps(self) -> Sequence[Resource | Ref]:
        """Return dependencies (property definitions if any)."""
        deps = []
        if self.properties:
            deps.extend([prop.property_key for prop in self.properties])
        return deps
