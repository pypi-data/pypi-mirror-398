import json
from collections import defaultdict
from datetime import datetime
from types import SimpleNamespace
from typing import Dict, List, NamedTuple, Optional

from httpx import Client as httpxClient
from httpx import HTTPStatusError

from .resource_abc import Ref, Resource

log_entity = "deployment"

LogLine = NamedTuple(
    "LogLine",
    [
        ("entry_id", str),
        ("deployment", str),
        ("resource_id", str),
        ("state", str),
        ("dependencies", List[str]),
        ("resource_type", str),
        ("as_at", str),
    ],
)
DepList = Dict[str, List[str]]
Index = Dict[str, LogLine]


def record(client: httpxClient, deployment_id: str, resource: Resource | Ref, state: str):
    unique_deps = list(set([r.id for r in resource.deps()]))
    res = client.request(
        "post",
        f"/api/api/customentities/~{log_entity}",
        json={
            "displayName": resource.id,
            "description": "...",
            "identifiers": [
                {
                    "identifierScope": log_entity,
                    "identifierType": "resource",
                    "identifierValue": f"{deployment_id}_{resource.id}".replace("/", "_"),
                }
            ],
            "fields": [
                {"name": "deployment", "value": deployment_id},
                {"name": "resourceType", "value": type(resource).__name__},
                {"name": "dependencies", "value": unique_deps},
                {"name": "resource", "value": resource.id},
                {"name": "state", "value": json.dumps(state)},
            ],
        },
    )
    print("Logged changes to:", f"{deployment_id}_{resource.id}")
    return res.json()


def fetch_log_entries(client: httpxClient, params: Dict):
    page = None
    while True:
        pp = params | {"page": page} if page is not None else params
        res = client.get(f"/api/api/customentities/~{log_entity}", params=pp).json()
        for item in res["values"]:
            yield item
        if res.get("nextPage") is not None:
            page = res["nextPage"]
        else:
            break


def entry_to_logline(entry: Dict):
    indexed = {
        "identifiers": {i["identifierType"]: i["identifierValue"] for i in entry["identifiers"]},
        "fields": {f["name"]: f["value"] for f in entry["fields"]},
        "as_at": entry["version"]["asAtModified"],
    }
    parsed = {
        "entry_id": indexed["identifiers"]["resource"],
        "deployment": indexed["fields"]["deployment"],
        "resource_id": indexed["fields"]["resource"],
        "state": SimpleNamespace(**json.loads(indexed["fields"]["state"])),
        "dependencies": indexed["fields"]["dependencies"],
        "resource_type": indexed["fields"]["resourceType"],
        "as_at": indexed["as_at"],
    }
    return LogLine(**parsed)


def list_resources_for_deployment(client: httpxClient, deployment_id: str) -> List[LogLine]:
    lines = [
        entry_to_logline(e)
        for e in fetch_log_entries(client, {"filter": f"fields[deployment] eq '{deployment_id}'"})
    ]
    lines.sort(key=lambda line: datetime.fromisoformat(line.as_at), reverse=True)
    return lines


def list_deployments(client: httpxClient) -> List[str]:
    log_lines = [entry_to_logline(e) for e in fetch_log_entries(client, {})]
    log_lines.sort(key=lambda line: datetime.fromisoformat(line.as_at), reverse=True)
    seen = []
    # get sorted set of deployments
    for line in log_lines:
        if line.deployment not in seen:
            seen.append(line.deployment)
    return seen


def get_resource(client: httpxClient, deployment_id: str, resource_id: str) -> List[LogLine]:
    list_filter = f"fields[deployment] eq '{deployment_id}' and fields[resource] eq '{resource_id}'"
    log_lines = [entry_to_logline(e) for e in fetch_log_entries(client, {"filter": list_filter})]
    return log_lines


# index of dependencies (key resource needs values to exist)
def entry_deps(log: List[LogLine]) -> DepList:
    return {e.resource_id: e.dependencies for e in log}


# entries indexed by resource id
def entry_index(log: List[LogLine]) -> Index:
    return {e.resource_id: e for e in log}


# index of dependants (value resources need key resource to exist)
def entry_rdeps(log: List[LogLine]) -> DepList:
    reverse_deps = defaultdict(list)
    for e in log:
        for d in e.dependencies:
            reverse_deps[d].append(e.resource_id)
    return reverse_deps


def print_tree(index: Dict[str, LogLine], deps: DepList, start_at: str, marker: str) -> None:
    leader = "    "

    def resolve_type(i: Dict[str, LogLine], r_id: str) -> str:
        return f"({i[r_id].resource_type})" if i.get(r_id, None) else "Unknown Type"

    def helper(resource_id, depth):
        if depth == 0:
            print(resource_id, resolve_type(index, resource_id))
        else:
            print(
                leader * depth,
                marker if depth > 0 else "",
                resource_id,
                resolve_type(index, resource_id),
            )

        for d in deps.get(resource_id, {}):
            if d:
                helper(d, depth + 1)
            else:
                helper(resource_id, 0)

    # resource does not exist
    if start_at not in index.keys():
        return

    helper(start_at, 0)


def get_dependencies_map(client: httpxClient, deployment_id: str) -> tuple[Index, DepList]:
    resources: List[LogLine] = list_resources_for_deployment(client, deployment_id)

    return entry_index(resources), entry_deps(resources)


def get_dependents_map(client: httpxClient, deployment_id: str) -> tuple[Index, DepList]:
    resources: List[LogLine] = list_resources_for_deployment(client, deployment_id)

    return entry_index(resources), entry_rdeps(resources)


def remove(client: httpxClient, deployment_id: str, resource_id: str) -> str:
    identifier_value = f"{deployment_id}_{resource_id}".replace("/", "_")
    res = client.delete(
        f"/api/api/customentities/~{log_entity}/resource/{identifier_value}",
        params={"identifierScope": log_entity})
    print("Removed log for:", f"{deployment_id}_{resource_id}")
    return res.json()


def format_log_line(line: LogLine) -> str:
    return f"id: {line.resource_id} | type: {line.resource_type} | {line.dependencies}"


def identifier_create(client: httpxClient) -> Optional[Dict]:
    try:
        res = client.request(
            "post",
            "/api/api/propertydefinitions",
            json={
                "domain": "CustomEntity",
                "scope": "deployment",
                "code": "resource",
                "displayName": "Deployment Resource",
                "dataTypeId": {"scope": "system", "code": "string"},
                "lifeTime": "Perpetual",
                "constraintStyle": "Identifier",
                "description": "To identify resources in a deployment",
            },
        )
        print("Created identifier", res.json()["key"])
        return res.json()
    except HTTPStatusError as e:
        if e.response.status_code == 400 and e.response.json().get("name") == "PropertyAlreadyExists":
            print("   Identifier already exists")
            return None
        raise e


entity_definition = {
    "displayName": "Deploy Resource",
    "description": "Deploy Resource v2.1",
    "fieldSchema": [
        {
            "name": "dependencies",
            "lifetime": "Perpetual",
            "type": "String",
            "collectionType": "Array",
            "required": True,
            "description": "IDs of resource this one depends on",
        },
        {
            "name": "deployment",
            "lifetime": "Perpetual",
            "type": "String",
            "required": True,
            "description": "the deployment this resource is in",
        },
        {
            "name": "resource",
            "lifetime": "Perpetual",
            "type": "String",
            "required": True,
            "description": "ID of the resource within the deployment",
        },
        {
            "name": "resourceType",
            "lifetime": "Perpetual",
            "type": "String",
            "required": True,
            "description": "Class that manages this resource",
        },
        {
            "name": "state",
            "lifetime": "Perpetual",
            "type": "String",
            "required": True,
            "description": "Current state resource within the deployment",
        },
    ],
}


def entity_def_get(client: httpxClient) -> Optional[Dict]:
    try:
        res = client.get(f"/api/api/customentitytypes/~{log_entity}")
        return res.json()
    except HTTPStatusError as e:
        if (
            e.response.status_code == 404
            and e.response.json().get("name") == "CustomEntityDefinitionNotFound"
        ):
            return None
        raise e


def entity_def_create(client: httpxClient) -> Dict:
    body = {"entityTypeName": log_entity} | entity_definition
    res = client.request("post", "/api/api/customentitytypes", json=body)
    return res.json()


def entity_def_update(client: httpxClient) -> Dict:
    res = client.request("put", f"/api/api/customentitytypes/~{log_entity}", json=entity_definition)
    return res.json()


def entity_def_upsert(client: httpxClient) -> None:
    existing_entity_def = entity_def_get(client)

    if existing_entity_def is not None:
        existing_entity_def.pop("href", None)
        existing_entity_def.pop("entityType", None)
        existing_entity_def.pop("version", None)
        existing_entity_def.pop("entityTypeName", None)

        if existing_entity_def == entity_definition:
            print("   Entity already exists")
        else:
            update = entity_def_update(client)
            print(update)
    else:
        create = entity_def_create(client)
        print(f"Created entity definition: {create['displayName']}")


def setup(client: httpxClient) -> None:
    """Set up the CustomEntity defintion where deployment logs are stored

    Example
    -------
        >>> from fbnconfig
        >>> client = fbnconfig.create_client(lusid_env, token)
        >>> fbnconfig.setup(client)

    Attributes
    ----------
    client : httpx.Client
        Authenticated httpx client
    """
    identifier_create(client)
    entity_def_upsert(client)
