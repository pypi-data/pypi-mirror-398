from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field, model_validator

from fbnconfig.fund_accounting import AccountKey, ChartOfAccountsKey

from .resource_abc import CamelAlias, Ref, Resource, register_resource


class PostingModuleRule(CamelAlias, BaseModel):
    rule_id: str
    general_ledger_account_code: AccountKey
    rule_filter: str


@register_resource()
class PostingModuleRef(CamelAlias, BaseModel, Ref):
    """Reference a posting module

    Example
    -------
    >>> from fbnconfig.posting_module import PostingModuleRef
    ...
    >>> post_mod = PostingModuleRef(
    >>> id="posting_module_example",
    >>> scope="scope_example",
    >>> code="code_example",
    >>> posting_module_code="post_mod_code_example")
    """

    id: str = Field(exclude=True, init=True)
    scope: str
    code: str
    posting_module_code: str

    def attach(self, client):
        scope = self.scope
        code = self.code
        module = self.posting_module_code

        request_url = f"/api/api/chartofaccounts/{scope}/{code}/postingmodules/{module}"
        try:
            client.request("get", request_url)
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Posting Module {self.posting_module_code} not found")
            else:
                raise ex


@register_resource()
class PostingModuleResource(CamelAlias, BaseModel, Resource):
    """Define a Posting Module in Chart of Accounts in LUSID"""

    id: str = Field(exclude=True)
    chart_of_accounts: ChartOfAccountsKey
    code: str
    display_name: str
    description: str | None = None
    rules: List[PostingModuleRule] | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}

        return data

    def __get_content_hash__(self) -> str:
        dump = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        return sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()

    def read(self, client: httpx.Client, old_state) -> None | Dict[str, Any]:
        scope = old_state.scope
        code = old_state.code
        module = old_state.module_code
        request_url = f"/api/api/chartofaccounts/{scope}/{code}/postingmodules/{module}"
        response = client.get(request_url).json()

        # Remove unnecessary fields
        response.pop("href", None)
        response.pop("links", None)
        response.pop("status", None)
        response.pop("version", None)

        return response

    def create(self, client: httpx.Client) -> Optional[Dict[str, Any]]:
        desired = self.model_dump(
            mode="json",
            exclude_none=True,
            by_alias=True,
            exclude={"chart_of_accounts"}
        )

        scope = self.chart_of_accounts.scope
        code = self.chart_of_accounts.code

        request_url = f"/api/api/chartofaccounts/{scope}/{code}/postingmodules"
        response = client.post(request_url, json=desired).json()

        # Remove unnecessary fields
        response.pop("href", None)
        response.pop("version", None)
        response.pop("status", None)
        response.pop("links", None)

        return {
            "module_code": self.code,
            "scope": scope,
            "code": code,
            "source_version": self.__get_content_hash__(),
            "remote_version": sha256(json.dumps(response, sort_keys=True).encode()).hexdigest(),
        }

    def update(self, client: httpx.Client, old_state) -> Union[None, Dict[str, Any]]:
        scope = self.chart_of_accounts.scope
        code = self.chart_of_accounts.code

        if self.code != old_state.module_code:
            self.delete(client, old_state)
            return self.create(client)

        if old_state.code != code:
            raise (RuntimeError("Cannot change the code of the chart of account on an posting module"))

        if old_state.scope != scope:
            raise (RuntimeError("Cannot change the scope of the chart of account on an posting module"))

        source_hash = self.__get_content_hash__()
        remote = self.read(client, old_state)
        remote_hash = sha256(json.dumps(remote, sort_keys=True).encode()).hexdigest()

        if remote_hash == old_state.remote_version and source_hash == old_state.source_version:
            return None

        self.delete(client, old_state)
        return self.create(client)

    @staticmethod
    def delete(client: httpx.Client, old_state) -> None:
        scope = old_state.scope
        code = old_state.code
        module = old_state.module_code
        client.delete(f"/api/api/chartofaccounts/{scope}/{code}/postingmodules/{module}")

    def deps(self):
        # Adds chart of accounts
        deps = [self.chart_of_accounts]

        if self.rules is None:
            return deps

        # Adds accounts from rules
        accounts = [rule.general_ledger_account_code for rule in self.rules]
        deps += accounts

        return deps
