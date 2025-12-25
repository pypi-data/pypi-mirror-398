import json
from typing import Dict

import httpx
import pytest

from fbnconfig import http_client, log

log_entity = "deployment"


# region test helpers
def build_field(
    name: str = "aname",
    field_description: str = "somed escription",
    is_collection: bool = False,
    lifetime: str = "Perpetual",
    field_type: str = "String",
    required: bool = True,
) -> Dict:
    """
    Helper for testing different values for a FieldSchema object

    :return: a FieldSchema object for a custom entity

    """

    if is_collection:
        return {
            "name": name,
            "lifetime": lifetime,
            "type": field_type,
            "required": required,
            "description": field_description,
            "collectionType": "Array",
        }

    return {
        "name": name,
        "lifetime": lifetime,
        "type": field_type,
        "required": required,
        "description": field_description,
    }


def build_entity_definition(
    name: str = "Deploy Resource", description: str = "Deploy Resource v2.1", fields=None
) -> Dict:
    """
    Returns a CustomEntityDefinition; Defaults to look like the definition set in `log.py`
    """

    return {
        "displayName": name,
        "description": description,
        "fieldSchema": fields
        if fields is not None
        else [
            build_field("dependencies", "IDs of resource this one depends on", True),
            build_field("deployment", "the deployment this resource is in"),
            build_field("resource", "ID of the resource within the deployment"),
            build_field("resourceType", "Class that manages this resource"),
            build_field("state", "Current state resource within the deployment"),
        ],
    }


# endregion


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeSetup:
    @staticmethod
    def response_hook(response: httpx.Response) -> None:
        if response.is_error:
            response.read()
            response.raise_for_status()

    base_url = "https://foo.lusid.com"

    client = http_client.create_client(lusid_url=base_url, token="token")

    def test_setup_from_scratch(self, respx_mock, capsys):
        respx_mock.post("/api/api/propertydefinitions").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "href": "https://example.lusid.com/api/properties/demo-scope/demo-code",
                        "key": "identifier/key/something",
                    },
                )
            ]
        )

        respx_mock.post("/api/api/customentitytypes").mock(
            side_effect=[httpx.Response(200, json={"displayName": "something", "anotherKey": "else"})]
        )
        respx_mock.get(f"/api/api/customentitytypes/~{log_entity}").mock(
            side_effect=[httpx.Response(404, json={"name": "CustomEntityDefinitionNotFound"})]
        )
        client = self.client
        # given nothing exists yet
        # when we call setup
        log.setup(client)
        # then it creates a property definition for the identifier
        identifier = respx_mock.calls[0].request
        assert identifier.method == "POST"
        assert identifier.url == f"{self.base_url}/api/api/propertydefinitions"
        # and a custom entity type with entity typename
        entity = respx_mock.calls.last.request
        assert entity.method == "POST"
        assert entity.url == f"{self.base_url}/api/api/customentitytypes"
        assert json.loads(entity.content)["entityTypeName"] == log_entity

        captured = capsys.readouterr()
        assert (
            captured.out
            == "Created identifier identifier/key/something\nCreated entity definition: something\n"
        )

    def test_setup_when_identifier_exists(self, respx_mock):
        respx_mock.post("/api/api/propertydefinitions").mock(
            side_effect=[httpx.Response(400, json={"name": "PropertyAlreadyExists"})]
        )

        respx_mock.post("/api/api/customentitytypes").mock(
            side_effect=[httpx.Response(200, json={"displayName": "something", "anotherKey": "else"})]
        )
        respx_mock.get(f"/api/api/customentitytypes/~{log_entity}").mock(
            side_effect=[httpx.Response(404, json={"name": "CustomEntityDefinitionNotFound"})]
        )
        client = self.client
        # given the identifier exists but the entity does not
        # when we call setup
        log.setup(client)
        # then it creates a property definition for the identifier and handles the error
        identifier = respx_mock.calls[0].request
        assert identifier.method == "POST"
        assert identifier.url == f"{self.base_url}/api/api/propertydefinitions"
        # and a custom entity type
        entity = respx_mock.calls.last.request
        assert entity.method == "POST"
        assert entity.url == f"{self.base_url}/api/api/customentitytypes"

    def test_setup_when_identifier_call_fails(self, respx_mock):
        respx_mock.post("/api/api/propertydefinitions").mock(
            side_effect=[httpx.Response(400, json={"name": "SomeOtherError"})]
        )
        client = self.client
        # given the identifier exists but the entity does not
        # when we call setup it throws
        with pytest.raises(httpx.HTTPStatusError) as error:
            log.setup(client)
        assert error.value.response.status_code == 400
        assert error.value.response.json()["name"] == "SomeOtherError"

    def test_setup_when_entity_exists_with_same_fields(self, respx_mock):
        respx_mock.post("/api/api/propertydefinitions").mock(
            side_effect=[httpx.Response(400, json={"name": "PropertyAlreadyExists"})]
        )

        respx_mock.get(f"/api/api/customentitytypes/~{log_entity}").mock(
            side_effect=[httpx.Response(200, json=build_entity_definition())]
        )
        client = self.client

        # given the identifier and the entity exist and the entity is upto date
        # when we call setup
        log.setup(client)
        # then it creates a property definition for the identifier (and handles the error)
        identifier = respx_mock.calls[0].request
        assert identifier.method == "POST"
        assert identifier.url == f"{self.base_url}/api/api/propertydefinitions"
        # and it does not update the entity

    @pytest.mark.parametrize(
        "test_input",
        [
            build_entity_definition(description="something else"),
            build_entity_definition(name="something else"),
            build_entity_definition(fields=[]),
            build_entity_definition(fields=[build_field(name="different")]),
            build_entity_definition(fields=[build_field(field_description="different")]),
            build_entity_definition(fields=[build_field(is_collection=False)]),
            build_entity_definition(fields=[build_field(lifetime="Something else")]),
            build_entity_definition(fields=[build_field(field_type="Something else")]),
            build_entity_definition(fields=[build_field(required=False)]),
        ],
    )
    def test_setup_when_entity_exists_with_different_fields(self, respx_mock, test_input):
        respx_mock.post("/api/api/propertydefinitions").mock(
            side_effect=[httpx.Response(400, json={"name": "PropertyAlreadyExists"})]
        )

        respx_mock.put(f"/api/api/customentitytypes/~{log_entity}").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        respx_mock.get(f"/api/api/customentitytypes/~{log_entity}").mock(
            side_effect=[httpx.Response(200, json=test_input)]
        )
        client = self.client
        # given the identifier and the entity exist, but the entity is an old version
        # when we call setup
        log.setup(client)
        # then it creates a property definition for the identifier (and handles the error)
        identifier = respx_mock.calls[0].request
        assert identifier.method == "POST"
        assert identifier.url == f"{self.base_url}/api/api/propertydefinitions"
        # and it updates the entity
        # and a custom entity type
        entity = respx_mock.calls.last.request
        assert entity.method == "PUT"
        assert entity.url == f"{self.base_url}/api/api/customentitytypes/~{log_entity}"

    @pytest.mark.parametrize("status_code", [404, 401, 403])
    def test_setup_when_get_entity_fails(self, respx_mock, status_code):
        respx_mock.post("/api/api/propertydefinitions").mock(
            side_effect=[httpx.Response(400, json={"name": "PropertyAlreadyExists"})]
        )

        respx_mock.get(f"/api/api/customentitytypes/~{log_entity}").mock(
            side_effect=[httpx.Response(status_code, json={"Exception": "somexception"})]
        )

        client = self.client
        with pytest.raises(httpx.HTTPStatusError) as ex:
            log.setup(client)
        assert ex.value.response.status_code == status_code


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeList:
    @staticmethod
    def response_hook(response: httpx.Response) -> None:
        if response.is_error:
            response.read()
            response.raise_for_status()

    base_url = "https://foo.lusid.com"
    client = httpx.Client(base_url=base_url, event_hooks={"response": [response_hook]})

    def test_list_deployments_pages_results(self, respx_mock):
        def get_entry(date, id):
            return {
                "description": "...",
                "displayName": "...",
                "fields": [
                    {"name": "deployment", "value": id},
                    {"name": "resourceType", "value": "FileResource"},
                    {"name": "dependencies", "value": []},
                    {"name": "resource", "value": "something"},
                    {"name": "state", "value": '{"some_variable": "some"}'},
                ],
                "identifiers": [
                    {
                        "identifierScope": log_entity,
                        "identifierType": "resource",
                        "identifierValue": "whatever_one",
                    }
                ],
                "version": {"asAtModified": date},
            }

        # given four entries in the log
        existing_values = [
            get_entry("2021-02-20T15:39:58.1008350+00:00", "4"),
            get_entry("2023-02-20T15:39:58.1008350+00:00", "2"),
            get_entry("2024-02-20T15:39:58.1008350+00:00", "1"),
            get_entry("2022-02-20T15:39:58.1008350+00:00", "3"),
        ]
        # and the api returns them in pages of two
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            side_effect=[
                httpx.Response(200, json={"values": existing_values[0:2], "nextPage": "2"}),
                httpx.Response(200, json={"values": existing_values[2:]}),
            ]
        )
        # when we list them
        logs = log.list_deployments(self.client)
        # Then all four are returned in order
        assert ["1", "2", "3", "4"] == logs
        # and the second call requests page 2
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == f"/api/api/customentities/~{log_entity}"
        assert dict(request.url.params) == {"page": "2"}

    def test_list_when_no_entries(self, respx_mock):
        # given there are not entries
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            side_effect=[httpx.Response(200, json={"values": []})]
        )
        # when we list them
        logs = log.list_deployments(self.client)
        # we get an empty list
        assert logs == []

    def test_list_deployments_returns_in_order(self, respx_mock):
        def get_entry(date, id):
            return {
                "description": "...",
                "displayName": "...",
                "fields": [
                    {"name": "deployment", "value": id},
                    {"name": "resourceType", "value": "FileResource"},
                    {"name": "dependencies", "value": []},
                    {"name": "resource", "value": "something"},
                    {"name": "state", "value": '{"some_variable": "some"}'},
                ],
                "identifiers": [
                    {
                        "identifierScope": log_entity,
                        "identifierType": "resource",
                        "identifierValue": "whatever_one",
                    }
                ],
                "version": {"asAtModified": date},
            }

        existing_values = [
            get_entry("2021-02-20T15:39:58.1008350+00:00", "4"),
            get_entry("2023-02-20T15:39:58.1008350+00:00", "2"),
            get_entry("2024-02-20T15:39:58.1008350+00:00", "1"),
            get_entry("2022-02-20T15:39:58.1008350+00:00", "3"),
        ]

        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(200, json={"values": existing_values})
        )

        # Returned in asAt order
        assert ["1", "2", "3", "4"] == log.list_deployments(self.client)

    def test_list_returns_resources_in_order(self, respx_mock):
        def get_entry(date, id):
            return {
                "description": "...",
                "displayName": "...",
                "fields": [
                    {"name": "deployment", "value": "mydeployment"},
                    {"name": "resourceType", "value": "FileResource"},
                    {"name": "dependencies", "value": []},
                    {"name": "resource", "value": id},
                    {"name": "state", "value": '{"some_variable": "some"}'},
                ],
                "identifiers": [
                    {
                        "identifierScope": log_entity,
                        "identifierType": "resource",
                        "identifierValue": "whatever_one",
                    }
                ],
                "version": {"asAtModified": date},
            }

        # given four log entrues for mydeployment
        existing_values = [
            get_entry("2021-02-20T15:39:58.1008350+00:00", "4"),
            get_entry("2023-02-20T15:39:58.1008350+00:00", "2"),
            get_entry("2024-02-20T15:39:58.1008350+00:00", "1"),
            get_entry("2022-02-20T15:39:58.1008350+00:00", "3"),
        ]
        # and the api returns them in pages of two
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            side_effect=[
                httpx.Response(200, json={"values": existing_values[0:2], "nextPage": "page2"}),
                httpx.Response(200, json={"values": existing_values[2:]}),
            ]
        )
        # The entries are returned in asAt order
        assert ["1", "2", "3", "4"] == [
            line.resource_id for line in log.list_resources_for_deployment(self.client, "mydeployment")
        ]
        # and the filter was sent on both page requests
        request1 = respx_mock.calls[0].request
        assert dict(request1.url.params) == {"filter": "fields[deployment] eq 'mydeployment'"}
        request2 = respx_mock.calls[1].request
        assert dict(request2.url.params) == {
            "filter": "fields[deployment] eq 'mydeployment'",
            "page": "page2",
        }

    def test_get_returns_resource(self, respx_mock):
        response = {
            "description": "...",
            "displayName": "...",
            "fields": [
                {"name": "deployment", "value": "deployment1"},
                {"name": "resourceType", "value": "FileResource"},
                {"name": "dependencies", "value": []},
                {"name": "resource", "value": "something"},
                {"name": "state", "value": '{"some_variable": "some"}'},
            ],
            "identifiers": [
                {
                    "identifierScope": log_entity,
                    "identifierType": "resource",
                    "identifierValue": "whatever_3",
                }
            ],
            "version": {"asAtModified": "2021-02-20T15:39:58.1008350+00:00"},
        }

        filter = "fields[deployment] eq 'deployment1' and fields[resource] eq 'whatever_3'"
        respx_mock.get(f"/api/api/customentities/~{log_entity}", params={"filter": filter}).mock(
            return_value=httpx.Response(200, json={"values": [response]})
        )

        resource = log.get_resource(self.client, "deployment1", "whatever_3")
        assert len(resource) == 1

    def test_get_when_no_resources(self, respx_mock):
        filter = "fields[deployment] eq 'deployment1' and fields[resource] eq 'whatever_3'"

        respx_mock.get(f"/api/api/customentities/~{log_entity}", params={"filter": filter}).mock(
            return_value=httpx.Response(200, json={"values": []})
        )

        resource = log.get_resource(self.client, "deployment1", "whatever_3")
        assert len(resource) == 0

    def test_get_dependencies_returns_correctly(self, respx_mock):
        response = {
            "description": "...",
            "displayName": "...",
            "fields": [
                {"name": "deployment", "value": "deployment1"},
                {"name": "resourceType", "value": "FileResource"},
                {"name": "dependencies", "value": ["a", "b", "c"]},
                {"name": "resource", "value": "whatever_1"},
                {"name": "state", "value": '{"some_variable": "some"}'},
            ],
            "identifiers": [
                {
                    "identifierScope": log_entity,
                    "identifierType": "resource",
                    "identifierValue": "deployment1_whatever_1",
                }
            ],
            "version": {"asAtModified": "2021-02-20T15:39:58.1008350+00:00"},
        }
        respx_mock.get(
            f"/api/api/customentities/~{log_entity}",
            params={"filter": "fields[deployment] eq 'deployment1'"},
        ).mock(return_value=httpx.Response(200, json={"values": [response]}))

        _, resource = log.get_dependencies_map(self.client, "deployment1")
        assert resource["whatever_1"] == ["a", "b", "c"]

    def test_get_dependent_returns_correctly(self, respx_mock):
        def get_entry(deployment, id, deps):
            return {
                "description": "...",
                "displayName": "...",
                "fields": [
                    {"name": "deployment", "value": deployment},
                    {"name": "resourceType", "value": "FileResource"},
                    {"name": "dependencies", "value": deps},
                    {"name": "resource", "value": id},
                    {"name": "state", "value": '{"some_variable": "some"}'},
                ],
                "identifiers": [
                    {
                        "identifierScope": log_entity,
                        "identifierType": "resource",
                        "identifierValue": id,
                    }
                ],
                "version": {"asAtModified": "2021-02-20T15:39:58.1008350+00:00"},
            }

        # A -> B,C
        # B -> E
        # D -> F
        # E <- B
        # F <- D
        # Z no deps

        respx_mock.get(
            f"/api/api/customentities/~{log_entity}",
            params={"filter": "fields[deployment] eq 'deployment1'"},
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "values": [
                        get_entry("deployment1", "a", ["b", "c"]),
                        get_entry("deployment1", "b", ["e"]),
                        get_entry("deployment1", "d", ["f"]),
                        get_entry("deployment1", "f", []),
                        get_entry("deployment1", "e", []),
                        get_entry("deployment1", "z", []),
                    ]
                },
            )
        )

        _, uses_map = log.get_dependents_map(self.client, "deployment1")
        assert uses_map["e"] == ["b"]
        assert uses_map["f"] == ["d"]
        assert uses_map["z"] == []

    @pytest.mark.parametrize(
        "deployment_id,resource_id",
        [("clean", "clean"), ("dir/ty", "clean"), ("clean", "dir/ty"), ("dir/ty", "dir/ty")],
    )
    def test_remove_replaces_slashes_url(self, respx_mock, deployment_id, resource_id):
        client = self.client

        identifier = f"{deployment_id}_{resource_id}".replace("/", "_")
        respx_mock.delete(
            f"/api/api/customentities/~{log_entity}/resource/{identifier}",
            params={"identifierScope": log_entity},
        ).mock(return_value=httpx.Response(200, json={"asAt": "2018-03-05T10:10:10.0000000+00:00"}))

        response = log.remove(client, deployment_id, resource_id)

        assert response == {"asAt": "2018-03-05T10:10:10.0000000+00:00"}

        request = respx_mock.calls.last.request
        assert request.url.path == f"/api/api/customentities/~{log_entity}/resource/{identifier}"
