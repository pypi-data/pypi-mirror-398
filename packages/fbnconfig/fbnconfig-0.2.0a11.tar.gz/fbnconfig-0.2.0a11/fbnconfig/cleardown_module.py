import json
import string
from hashlib import sha256
from typing import List

from pydantic import BaseModel, Field, model_validator

from fbnconfig import fund_accounting as fa
from fbnconfig.resource_abc import CamelAlias, Resource, register_resource
from fbnconfig.urlfmt import Urlfmt

url: string.Formatter = Urlfmt("api/api/chartofaccounts")
CREATE_CLEARDOWN_MODULE_URL = ("{base}/{scope}/{code}/cleardownmodules")
CLEARDOWN_MODULE_URL = ("{base}/{scope}/{code}/cleardownmodules/{cleardown_module_code}")
CLEARDOWN_RULES_URL = ("{base}/{scope}/{code}/cleardownmodules/{cleardown_module_code}/cleardownrules")


class CleardownModuleRule(CamelAlias, BaseModel):
    general_ledger_account_code: str
    rule_filter: str
    rule_id: str


@register_resource()
class CleardownModuleResource(Resource, BaseModel):
    id: str = Field(exclude=True)
    chart_of_accounts: fa.ChartOfAccountsKey
    # Body
    cleardown_module_code: str
    display_name: str | None = None
    description: str | None = None
    rules: List[CleardownModuleRule] | None
    status: str = Field(default="Active", exclude=True)

    @property
    def scope(self):
        return self.chart_of_accounts.scope

    @property
    def code(self):
        return self.chart_of_accounts.code

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info):
        if not isinstance(data, dict):
            return data
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def read(self, client, old_state):
        scope, code = old_state.scope, old_state.code
        cleardown_module_code = old_state.cleardown_module_code
        formatted_url = url.format(
            CLEARDOWN_MODULE_URL,
            scope=scope,
            code=code,
            cleardown_module_code=cleardown_module_code
        )
        return client.get(formatted_url).json()

    def create(self, client):
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
                                  exclude={"scope", "code", "id", "chart_of_accounts"})
        cleardown_module_code = desired.pop("cleardownModuleCode", None)
        if cleardown_module_code is None:
            raise ValueError("cleardown_module_code must be provided")
        desired.update({"code": cleardown_module_code})

        sorted_desired = json.dumps(desired, sort_keys=True)
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        formatted_url = url.format(CREATE_CLEARDOWN_MODULE_URL, scope=self.scope, code=self.code)
        client.request("POST", formatted_url, json=desired)

        # Serialize rules to dict for JSON storage
        rules_data = None
        if self.rules:
            rules_data = [rule.model_dump(mode="json", by_alias=True) for rule in self.rules]

        return {
            "scope": self.scope,
            "code": self.code,
            "cleardown_module_code": self.cleardown_module_code,
            "display_name": self.display_name,
            "description": self.description,
            "status": self.status,
            "rules": rules_data,
            "content_hash": content_hash
        }

    def update(self, client, old_state):
        if (
            (self.scope, self.code, self.cleardown_module_code) !=
            (old_state.scope, old_state.code, old_state.cleardown_module_code)
        ):
            self.delete(client, old_state)
            return self.create(client)

        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True,
                                  exclude={"scope", "code", "id", "chart_of_accounts"})

        cleardown_module_code = desired.pop("cleardownModuleCode", None)
        if cleardown_module_code is None:
            raise ValueError("cleardown_module_code must be provided")
        desired.update({"code": cleardown_module_code})

        sorted_desired = json.dumps(desired, sort_keys=True)
        desired_hash = sha256(sorted_desired.encode()).hexdigest()

        if desired_hash == old_state.content_hash:
            return None

        details_changed = (
            self.display_name != getattr(old_state, "display_name", None) or
            self.description != getattr(old_state, "description", None) or
            self.status != getattr(old_state, "status", None)
        )

        # Compare rules - old_state.rules are dicts, self.rules are CleardownModuleRule objects
        old_rules = getattr(old_state, "rules", None)
        current_rules_data = None
        if self.rules:
            current_rules_data = [rule.model_dump(mode="json", by_alias=True) for rule in self.rules]
        rules_changed = current_rules_data != old_rules

        if details_changed and rules_changed:
            self.update_details(client, desired_hash)
            return self.update_rules(client, desired_hash)

        if details_changed and not rules_changed:
            return self.update_details(client, desired_hash)

        if rules_changed and not details_changed:
            return self.update_rules(client, desired_hash)

        # If we get here, hash changed but we can't detect what changed
        # Fall back to recreating the resource
        self.delete(client, old_state)
        return self.create(client)

    @staticmethod
    def delete(client, old_state):
        scope, code = old_state.scope, old_state.code
        cleardown_module_code = old_state.cleardown_module_code
        formatted_url = url.format(
            CLEARDOWN_MODULE_URL,
            scope=scope,
            code=code,
            cleardown_module_code=cleardown_module_code
        )
        client.request("DELETE", formatted_url)

    def deps(self):
        deps = []

        # Always add chart of accounts dependency
        deps.append(self.chart_of_accounts)

        # Add account dependencies if rules exist
        if self.rules:
            # Get unique account codes from rules
            account_codes = set()
            for rule in self.rules:
                if rule.general_ledger_account_code:
                    account_codes.add(rule.general_ledger_account_code)

            # Create account references for each unique account code
            for account_code in account_codes:
                account_ref = fa.AccountRef(
                    id=f"account_{account_code}",
                    account_code=account_code,
                    chart_of_accounts=self.chart_of_accounts
                )
                deps.append(account_ref)

        return deps

    def update_details(self, client, desired_hash):
        metadata_json = {
            "displayName": self.display_name,
            "description": self.description,
            "status": self.status
        }
        try:
            client.request("PUT", url.format(
                CLEARDOWN_MODULE_URL,
                scope=self.scope,
                code=self.code,
                cleardown_module_code=self.cleardown_module_code
            ), json=metadata_json)
        except Exception as e:
            print(f"Error updating cleardown module metadata: {e}")
            raise e

        # Serialize rules to dict for JSON storage
        rules_data = None
        if self.rules:
            rules_data = [rule.model_dump(mode="json", by_alias=True) for rule in self.rules]

        return {
                "scope": self.scope,
                "code": self.code,
                "cleardown_module_code": self.cleardown_module_code,
                "display_name": self.display_name,
                "description": self.description,
                "status": self.status,
                "rules": rules_data,
                "content_hash": desired_hash
            }

    def update_rules(self, client, desired_hash):
        rules_data = []
        if self.rules:
            for rule in self.rules:
                rules_data.append(rule.model_dump(mode="json", by_alias=True))

        try:
            client.request("PUT", url.format(
                CLEARDOWN_RULES_URL,
                scope=self.scope,
                code=self.code,
                cleardown_module_code=self.cleardown_module_code
            ), json=rules_data)
        except Exception as e:
            print(f"Error updating cleardown rules: {e}")
            raise e

        # Serialize rules to dict for JSON storage
        rules_data = None
        if self.rules:
            rules_data = [rule.model_dump(mode="json", by_alias=True) for rule in self.rules]

        return {
                "scope": self.scope,
                "code": self.code,
                "cleardown_module_code": self.cleardown_module_code,
                "display_name": self.display_name,
                "description": self.description,
                "status": self.status,
                "rules": rules_data,
                "content_hash": desired_hash
            }
