from __future__ import annotations

import csv
import hashlib
import json
import sys
import textwrap
import time
from datetime import datetime
from enum import StrEnum
from io import StringIO
from types import SimpleNamespace
from typing import Annotated, Any, Dict, List, Sequence, Union

import httpx
from httpx import Client as httpxClient
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    field_serializer,
    field_validator,
    model_validator,
)

from . import exceptions
from .backoff_handler import BackoffHandler
from .property import PropertyKey
from .resource_abc import CamelAlias, Ref, Resource, register_resource


# from the sdk
class TaskStatus(StrEnum):
    CREATED = "Created"
    WAITING_FOR_ACTIVATION = "WaitingForActivation"
    WAITING_TO_RUN = "WaitingToRun"
    RUNNING = "Running"
    WAITING_FOR_CHILDREN_TO_COMPLETE = "WaitingForChildrenToComplete"
    RAN_TO_COMPLETION = "RanToCompletion"
    CANCELED = "Canceled"
    FAULTED = "Faulted"


def start_query(client: httpx.Client, sql: str) -> str:
    return client.put(
        "/honeycomb/api/SqlBackground", content=sql, headers={"Content-type": "text/plain"}
    ).json()["executionId"]


def wait_for_background(client, execution_id) -> bool:
    status_resp = get_status(client, execution_id)
    status = status_resp["status"]
    match status:
        case TaskStatus.FAULTED | TaskStatus.CANCELED:
            raise exceptions.QueryError(status, status_resp)
        case (
            TaskStatus.CREATED
            | TaskStatus.WAITING_FOR_ACTIVATION
            | TaskStatus.WAITING_TO_RUN
            | TaskStatus.WAITING_FOR_CHILDREN_TO_COMPLETE
        ):
            return False
        case TaskStatus.RUNNING:
            return False
        case TaskStatus.RAN_TO_COMPLETION:
            return True
        case _:
            raise RuntimeError("Unknown status: " + status + ". Execution id: " + execution_id)


def fetch(client, execution_id):
    res = client.get(f"/honeycomb/api/SqlBackground/{execution_id}/jsonproper")
    return res.json()


def get_status(client: httpx.Client, execution_id: str) -> Dict[str, Any]:
    """Get the status of the query in Luminesce

    Returns:
        Dict: status response message
    """
    return client.get(f"/honeycomb/api/SqlBackground/{execution_id}").json()


def query(client: httpx.Client, sql: str, backoff_handler: BackoffHandler) -> Dict[Any, Any]:
    execution_id: str = start_query(client, sql)
    progress = False
    while True:
        if progress is False:
            backoff_handler.sleep()
            progress = wait_for_background(client, execution_id)
        else:
            #  Pause after the last wait_for_background_call, otherwise increased chances of 429s
            backoff_handler.sleep()
            return fetch(client, execution_id)


class ParameterType(StrEnum):
    BigInt = "BigInt"
    Boolean = "Boolean"
    Date = "Date"
    DateTime = "DateTime"
    Decimal = "Decimal"
    Double = "Double"
    Int = "Int"
    Table = "Table"
    Text = "Text"


class VariableType(StrEnum):
    Scalar = "@@"
    Table = "@"


class Variable(BaseModel):
    name: str
    type: VariableType
    sql: str

    def init_str(self):
        #  eg @scalar = select 2 + 2
        return f"{self.type.value}{self.name} = {self.sql}"

    def with_str(self):
        return f"{self.type.value}{self.name}"


class Parameter(BaseModel, CamelAlias):
    name: str
    type: ParameterType
    value: Any
    set_as_default_value: bool = True
    is_mandatory: bool = True
    tooltip: str | None = None

    # return in the same format that sys.file stores it in
    def metadata(self):
        base: Dict[str, Any] = {"Name": self.name, "Type": self.type.value, "Description": self.tooltip}
        if self.set_as_default_value and self.type != ParameterType.Table:
            base["DefaultValue"] = self.value
        if self.type == ParameterType.Table:
            if self.is_mandatory:
                base["ConditionUsage"] = 2
            else:
                base["ConditionUsage"] = 0
        return base


def lumi_fmt(value: Any) -> str:
    """ escaping parameters which act like commandline args and use " for strings """
    if value is None:
        return "null"
    if isinstance(value, Variable):
        return f"{value.type.value}{value.name}"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return '"' + value.replace('"', '""') + '"'


def lumi_sql(value: Any) -> str:
    """ escape a sql value """
    if value is None:
        return "null"
    if isinstance(value, Variable):
        return f"{value.type.value}{value.name}"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return "'" + str(value) + "'"
    return "'" + value.replace("'", "''") + "'"


@register_resource()
class ViewRef(BaseModel, Ref):
    """Reference an existing view


    Example
    ----------
    >>> from fbnconfig import lumi
    >>> lumi.ViewRef(
    ...  id="lumi-example-ref",
    ...  provider="Views.fbnconfig.existing_view")


    Attributes
    ----------
    id : str
         Resource identifier.
    provider : str
        Name of the view referenced. This is assumed to exist
    """

    id: str = Field(exclude=True)
    provider: str
    _backoff_handler = BackoffHandler()
    _version: str | None = None

    def attach(self, client) -> None:
        res = query(
            client,
            textwrap.dedent(f"""\
                select r.Version from sys.registration as r
                where name = '{self.provider}'
                order by r.Version asc
                limit 1
            """),
            backoff_handler=self._backoff_handler,
        )
        if len(res) != 1:
            raise RuntimeError(f"Failed to attach ref to {self.provider}, the view might not exist")
        self._version = res[0]


@register_resource()
class ViewResource(BaseModel, Resource):
    """Create and manage a Luminesce view

    Example
    ----------
    >>> from fbnconfig import lumi
    >>> lumi.ViewResource(
    ...  id="lumi-example-view",
    ...  provider="Views.fbnconfig.example",
    ...  description="My resource test view",
    ...  documentation_link="http://example.com/query",
    ...  variable_shape=False,
    ...  use_dry_run=True,
    ...  allow_execute_indirectly=False,
    ...  distinct=True,
    ...  sql='select 2+#PARAMETERVALUE(p1)   as   twelve',
    ...  parameters=[
    ...      lumi.Parameter(
    ...          name="p1",
    ...          value=10,
    ...          set_as_default_value=True,
    ...          tooltip="a number",
    ...          type=lumi.ParameterType.INT
    ...      )

    Attributes
    ----------
    id : str
         Resource identifier.
    provider : str
        Name of the view managed by this resource
    description : str
        View description
    sql: str
        The query string for the view
    parameters : list of `Parameter`, optional
        List of parameters for the view
    dependencies : list of dependencies, optional
        This can be another view or any other resource
    documentation_link: str, optional
        Displays one or more hyperlinks in the summary dialog for the view
    variable_shape: bool, optional
        This is useful if data returned is likely to vary in shape between queries. Defaults to false.
    allow_execute_indirectly : bool, optional
        Allows end users to query providers within the view even if they are not entitled to use those
        providers directly.
        Defaults to false.
    limit: int, optional
        Test option when developing view, does not have an effect on a published view. Defaults to None
    group_by: str, optional
        Test option when developing view, does not have an effect on a published view. Defaults to None
    filter: str, optional
        Test option when developing view, does not have an effect on a published view. Defaults to None
    offset: int, optional
        Test option when developing view, does not have an effect on a published view. Defaults to None
    distinct: bool, optional
        Test option when developing view, does not have an effect on a published view. Defaults to None
    use_dry_run: bool, optional
        Intended for automatic deployment of views. See docs for more details. Defaults to false
    variables: List of `Variable`, optional
        A table variable that can be passed into the view by an end user or in code

    See Also
    --------
    `https://support.lusid.com/knowledgebase/article/KA-01767/en-us`__
    """

    id: str = Field(exclude=True)
    provider: str = Field(serialization_alias="Provider")
    description: str = Field(serialization_alias="Description")
    sql: str
    parameters: List[Parameter] = []
    dependencies: List | None = None
    documentation_link: str | None = None
    variable_shape: bool | None = None
    allow_execute_indirectly: bool | None = None
    limit: int | None = None
    group_by: str | None = None
    filter: str | None = None
    offset: int | None = None
    distinct: bool | None = None
    use_dry_run: bool | None = None
    variables: List[Variable] = []

    _backoff_handler = BackoffHandler()

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info):
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    @field_validator("dependencies", mode="before")
    @classmethod
    def des_dependencies(cls, data: Any, info) -> List[Resource | Ref]:
        if data is None:
            return data
        if info.context and info.context.get("$refs"):
            return [
                info.context["$refs"][d["$ref"]] if isinstance(d, dict) else d
                for d in data
            ]
        return data

    class Registration:
        tries = 10
        wait_time = 1

    _saved_options = {  # maps from sys.file metadata to view option names
        "Description": "Description",
        "DocumentationLink": "documentationLink",
        "IsWithinDirectProviderView": "variableShape",
        "IsWithinViewAllowingIndirectExecute": "allowExecuteIndirectly",
    }
    _test_options = ["distinct", "filter", "groupby", "limit", "offset", "preamble", "useDryRun"]

    def read(self, client, old_state) -> Dict[str, Any]:
        path = old_state.provider.replace(".", "/")
        res = query(
            client,
            textwrap.dedent(f"""\
                select f.Content, r.Version from sys.file as f
                join sys.registration as r on r.Name = '{old_state.provider}'
                where path = 'databaseproviders/{path}.sql'
                order by r.Version asc
                limit 1
            """),
            self._backoff_handler)
        if len(res) != 1:
            raise RuntimeError(f"{self.id}: expected to find exactly one instance of "
                f"{old_state.provider} in sys.registration but found {len(res)}")

        def strip_column_description(kv: Dict) -> Dict:
            if kv["Type"] == "Table":
                kv["Description"] = kv["Description"].split("\nAvailable columns")[0]

            return kv

        parts = res[0]["Content"].split("--- MetaData ---")
        sql = parts[0]
        metadata = json.loads(parts[1])

        parameters = [strip_column_description(p) for p in metadata["Parameters"]]
        props = {
            v: metadata[k] for k, v in self._saved_options.items() if metadata.get(k, None) is not None
        }
        return {"sql": sql, "version": res[0]["Version"], "parameters": parameters} | props

    @staticmethod
    def registration_version(client, view_name, backoff_handler: BackoffHandler) -> int | None:
        content = textwrap.dedent(f"""\
            select Version from sys.registration where Name='{view_name}'
            order by Version asc
            limit 1
        """)
        rows = query(client, content, backoff_handler)
        return int(rows[0]["Version"]) if len(rows) > 0 else None

    @staticmethod
    def format_option(option, value):
        if isinstance(value, bool) and value:
            return f"--{option}"
        if isinstance(value, (int, float)):
            return f"--{option}={value}"
        # we run self.dump by alias, these two have a serialization alias on the dto
        # which ends up as the option, which should be lower
        if option == "Provider" or option == "Description":
            option = option.lower()
        return f"--{option}={lumi_fmt(value)}"

    def get_variables(self):
        param_variables = [param.value for param in self.parameters if isinstance(param.value, Variable)]
        seen = set()
        return [
            value
            for value in self.variables + param_variables
            if value.name not in seen and not seen.add(value.name)
        ]

    def template(self, desired):
        options = [
            self.format_option(option, desired[option])
            for option in ["Provider"] + self._test_options + list(self._saved_options.values())
            if desired.get(option) is not None
        ]

        tpl = textwrap.dedent("""\
            {preamble}@x = use Sys.Admin.SetupView{with_clause}
            {options}{params}
            ----
            {sql}
            enduse;
            select * from @x;
        """)
        params = [
            f"{p.name},{p.type.value},{lumi_fmt(p.value)},{lumi_fmt(p.is_mandatory)}"
            + (f',"{p.tooltip}"' if p.tooltip is not None else "")
            if p.type == ParameterType.Table
            else f"{p.name},{p.type.value},{lumi_fmt(p.value)},{lumi_fmt(p.set_as_default_value)}"
            + (f',"{p.tooltip}"' if p.tooltip is not None else "")
            for p in self.parameters
        ]
        param_clause = "\n--parameters\n{0}".format("\n".join(params)) if len(params) > 0 else ""
        variables = self.get_variables()
        preamble = ";\n".join([v.init_str() for v in variables]) + ";\n" if len(variables) > 0 else ""
        with_clause = (
            " with " + ", ".join([v.with_str() for v in variables]) if len(variables) > 0 else ""
        )
        sql = tpl.format(
            options="\n".join(options),
            params=param_clause,
            sql=desired["sql"],
            with_clause=with_clause,
            preamble=preamble,
        )
        return sql

    def _get_content_hash(self) -> str:
        desired = self.model_dump(exclude_none=True, by_alias=True)
        sql = self.template(desired)
        return hashlib.sha256(sql.encode()).hexdigest()

    def create(self, client) -> Dict[str, Any]:
        desired = self.model_dump(exclude_none=True, by_alias=True)
        sql = self.template(desired)
        query(client, sql, self._backoff_handler)
        for i in range(1, self.Registration.tries + 1):
            if self.registration_version(client, self.provider, self._backoff_handler) is not None:
                break
            else:
                if i == self.Registration.tries:
                    sys.stderr.write(
                        f"warning: no view registration after {i} tries for {self.provider}"
                    )
                else:
                    time.sleep(self.Registration.wait_time)
        return {"provider": self.provider}

    def update(self, client, old_state):
        if self.provider != old_state.provider:
            self.delete(client, old_state)
            self.create(client)
            return {"provider": self.provider}
        desired = self.model_dump(exclude_none=True, by_alias=True, exclude=set(self._test_options))
        raw_remote = self.read(client, old_state)
        remote_props = {
            k.lower(): v
            for k, v in raw_remote.items()
            if k in self._saved_options.values() and v is not None
        }
        desired_props = {
            k.lower(): v
            for k, v in desired.items()
            if k in self._saved_options.values() and v is not None
        }
        remote_params = raw_remote["parameters"]
        desired_params = [p.metadata() for p in self.parameters]
        effective_params = [
            (remote_params[i] | desired_params[i])
            if i < len(remote_params) and remote_params[i]["Name"] == desired_params[i]["Name"]
            else desired_params[i]
            for i, _ in enumerate(desired_params)
        ]
        remote_sql = textwrap.dedent(raw_remote["sql"].rstrip())
        remote_version = raw_remote["version"]
        desired_sql = textwrap.dedent(self.sql.rstrip())
        if (
            desired_sql == remote_sql
            and remote_props | desired_props == remote_props
            and effective_params == remote_params
        ):
            return None
        sql = self.template(desired)
        query(client, sql, self._backoff_handler)
        for i in range(1, self.Registration.tries + 1):
            version: int | None = self.registration_version(client, self.provider, self._backoff_handler)
            if version is not None and remote_version < version:
                break
            else:
                if i == self.Registration.tries:
                    sys.stderr.write(
                        f"warning: no view registration after {i} tries for {self.provider}"
                    )
                else:
                    time.sleep(self.Registration.wait_time)
        return {"provider": self.provider}

    def deps(self):
        return self.dependencies if self.dependencies else []

    @staticmethod
    def delete(client, old_state):
        sql = textwrap.dedent(f"""\
        @x = use Sys.Admin.SetupView
        --provider={old_state.provider}
        --deleteProvider
        ----
        select 1 as deleting
        enduse;
        select * from @x;
        """)
        backoff = BackoffHandler()
        query(client, textwrap.dedent(sql), backoff_handler=backoff)
        for i in range(1, ViewResource.Registration.tries + 1):
            if (
                ViewResource.registration_version(
                    client=client, view_name=old_state.provider, backoff_handler=backoff
                )
                is None
            ):
                break
            else:
                if i == ViewResource.Registration.tries:
                    sys.stderr.write(
                        f"warning: no view deregistration after {i} tries for {old_state.provider}"
                    )
                else:
                    time.sleep(ViewResource.Registration.wait_time)


def ser_key_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return value.provider


def des_key_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


ViewKey = Annotated[
    ViewResource | ViewRef,
    BeforeValidator(des_key_key), PlainSerializer(ser_key_key)
]


class InlineDataType(StrEnum):
    Text = "Text"
    Decimal = "Decimal"
    DateTime = "DateTime"
    Date = "Date"
    Boolean = "Boolean"
    Identifier = "_identifier"


class InlineProperty(CamelAlias, BaseModel):
    """A property that can be set inline in a view """
    key: PropertyKey | None = None  # set for properties not custom entities
    field: str | None = None        # set for structured properties and CEs, not scalars
    name: str
    description: str = ""
    data_type: InlineDataType | None = None
    is_main: None | bool = None
    as_at: None | datetime = None

    @field_serializer("as_at", when_used="always")
    def as_at_serializer(self, value: datetime | None) -> str | None:
        """Serialize the as_at datetime to a string in ISO 8601 format"""
        if value is None:
            return None
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def prop_key(self):
        # key is set for a scalar property, key and field for a structured property
        # only field if we inlining a custom entity
        if self.key is not None and self.field is not None:
            return "/".join([self.key.domain, self.key.scope, self.key.code]) + "." + self.field
        elif self.key is not None:
            return "/".join([self.key.domain, self.key.scope, self.key.code])
        else:
            return self.field

    def sql_values(self):
        # key is set for a scalar property, key and field for a structured property
        # only field if we inlining a custom entity
        prop_key = self.prop_key()
        return [
            lumi_sql(prop_key),
            lumi_sql(self.name),
            lumi_sql(self.data_type),
            lumi_sql(self.description),
            lumi_sql(self.is_main),
            lumi_sql(self.as_at),
        ]


@register_resource()
class InlinePropertiesResource(BaseModel, Resource):
    id: str = Field(exclude=True)
    provider: str
    provider_name_extension: str | None = None
    properties: Sequence[InlineProperty]

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data: Any, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context and info.context.get("id"):
            return data | {"id": info.context.get("id")}
        return data

    @model_validator(mode="after")
    def validate_no_ext_custom(self):
        parts = self.provider.split(".")
        if len(parts) == 3 and parts[1].lower() == "customentity":
            if self.provider_name_extension is not None:
                raise KeyError(f"{self.id} Cannot set use a provider name extension when creating "
                "a custom entity provider")
        return self

    @staticmethod
    def _convert_provider_name_to_path(provider, provider_name_extension) -> str:
        """Convert a provider name to a path format used in sys.file"""
        str_builder = ""
        if provider_name_extension:
            str_builder += f"{provider_name_extension.lower()}_"
        parts = provider.split(".")
        if len(parts) == 3 and parts[1].lower() == "customentity":
            str_builder += (
                parts[2] + "customentity"
            )
        else:
            str_builder += (
                provider.replace(".", "").lower().replace("lusid", "").replace("txn", "transaction")
            )
        return str_builder

    def _check_extension(self) -> str:
        """Check if the provider name extension is set and return the appropriate SQL clause"""
        if self.provider_name_extension:
            return f"and ProviderNameExtension = '{self.provider_name_extension}'"
        return ""

    def read(self, client: httpxClient, old_state: SimpleNamespace) -> None | Dict[str, Any]:
        # create backoff handler
        backoff = BackoffHandler()
        # run query to get the inline properties
        path = self._convert_provider_name_to_path(old_state.provider, old_state.extension)
        sql = textwrap.dedent(f"""\
            select Content from Sys.File
                where Path = 'config/lusid/factories/{path}providerfactory.csv'
            ;
        """)
        res = query(client, sql, backoff_handler=backoff)
        # If no results found, return None (properties don't exist yet)
        if not res:
            return None
        remote = self.parse_content(res)
        return remote

    def generate_sql(self):
        if len(self.properties) == 0:
            return textwrap.dedent(f"""\
                select * from Sys.Admin.Lusid.Provider.Configure
                    where Provider = '{self.provider}'
                    and WriteAction = 'Set'
                    {self._check_extension()}
                ;
            """)
        # build the values sql from the properties
        keys_right = ["(" + ", ".join(prop.sql_values()) + ")" for prop in self.properties]
        values_str = ",".join(keys_right)
        # build the columns clause
        columns_str = "column1 as [Key], column2 as Name, column3 as DataType, column4 as Description, "\
            "column5 as IsMain, column6 as AsAt"
        # set the inline properties of the provider to these values overwriting any existing ones
        return textwrap.dedent(f"""\
            @keysToCatalog = values
                {values_str}
            ;
            @config = select
                {columns_str}
                from @keysToCatalog
            ;
            select * from Sys.Admin.Lusid.Provider.Configure
                where Provider = '{self.provider}'
                and Configuration = @config
                and WriteAction = 'Set'
                {self._check_extension()}
            ;
        """)

    def parse_content(self, rows):
        csv_str = rows[0]["Content"]
        reader = csv.DictReader(StringIO(csv_str))
        data = [row for row in reader]
        # convert to a dictionary, sorted by key so we get consistent hashing
        return {
            prop["Key"]: {
                "Name": prop["Name"],
                "DataType": prop["DataType"],
                "Description": prop["Description"],
                "IsMain": prop.get("IsMain", None),
                "AsAt": prop.get("AsAt", None),
            }
            for prop in sorted(data, key=lambda x: x["Name"])
        }

    def create(self, client: httpxClient) -> None | Dict[str, Any]:
        # lumi query to create or update the provider columns
        backoff = BackoffHandler()
        sql = self.generate_sql()
        rows = query(client, sql, backoff_handler=backoff)
        if len(rows) > 0 and rows[0]["Error"]:
            raise RuntimeError(f"{self.id} Failed to inline:" + rows[0]["Error"] + "\n" + sql)
        # parse the result
        properties_dict = self.parse_content(rows)
        remote_version = hashlib.sha256(json.dumps(properties_dict, sort_keys=True).encode()).hexdigest()
        # desired hash
        desired = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        source_version = hashlib.sha256(json.dumps(desired, sort_keys=True).encode()).hexdigest()
        return {
            "provider": self.provider,
            "extension": self.provider_name_extension,
            "source_version": source_version,
            "remote_version": remote_version,
        }

    def update(self, client: httpxClient, old_state) -> Union[None, Dict[str, Any]]:
        # if the identity has changed, delete and recreate
        if self.provider != old_state.provider or self.provider_name_extension != old_state.extension:
            self.delete(client, old_state)
            return self.create(client)
        # check for changes
        remote = self.read(client, old_state)
        if remote is None:
            raise RuntimeError(f"Updating {self.id}: expected to read inline of {old_state.provider} "
                f"{old_state.extension} from sys.registration but found none")
        remote_version = hashlib.sha256(json.dumps(remote, sort_keys=True).encode()).hexdigest()
        desired = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        source_version = hashlib.sha256(json.dumps(desired, sort_keys=True).encode()).hexdigest()
        if source_version == old_state.source_version and remote_version == old_state.remote_version:
            return None
        return self.create(client)

    @staticmethod
    def delete(client: httpxClient, old_state) -> None:
        pne = f"and ProviderNameExtension = '{old_state.extension}'" if old_state.extension else ""
        backoff = BackoffHandler()
        sql = textwrap.dedent(f"""\
            select *
                from Sys.Admin.Lusid.Provider.Configure
                where Provider = '{old_state.provider}'
                and WriteAction = 'Reset'
                {pne}
            ;
        """)
        query(client, sql, backoff_handler=backoff)

    def deps(self) -> Sequence["Resource|Ref"]:
        deps = []
        for v in self.properties:
            if v.key:  # custom entity has no key
                deps.append(v.key)
        return deps
