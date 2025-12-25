import datetime as dt
import json
from hashlib import sha256
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import httpx
import pytest

from fbnconfig import fund_accounting, property

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeChartOfAccountsRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = fund_accounting.ChartOfAccountsRef(
            id="chart_example",
            code="testCode",
            scope="testScope"
        )

        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        sut = fund_accounting.ChartOfAccountsRef(
            id="chart_example",
            code="testCode",
            scope="testScope"
        )
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Chart of Accounts testScope/testCode not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode").mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        sut = fund_accounting.ChartOfAccountsRef(
            id="chart_example",
            code="testCode",
            scope="testScope"
        )
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeChartOfAccounts:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def stock_chart_of_account_resource(self):
        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.ChartOfAccounts, scope="sc1", code="cd4"
        )

        perp_prop = fund_accounting.PropertyValue(
            property_key=property_example,
            label_value="Hello"
        )

        return fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
            properties=[perp_prop]
        )

    def test_read(self, respx_mock, stock_chart_of_account_resource):
        respx_mock.get("/api/api/chartofaccounts/oldScope/oldCode/properties").mock(
            return_value=httpx.Response(200, json={},))
        respx_mock.get("/api/api/chartofaccounts/oldScope/oldCode").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": {
                        "scope": "oldScope",
                        "code": "oldCode"
                    },
                    "displayName": "different_example_display_name",
                    "description": "different_example_description",
                    "properties": {}
                    },
            )
        )
        sut = stock_chart_of_account_resource
        old_state = SimpleNamespace(scope="oldScope", code="oldCode")
        result = sut.read(self.client, old_state)
        assert result is not None
        assert result["id"]["scope"] == "oldScope"
        assert result["id"]["code"] == "oldCode"

    def test_create_without_properties(self, respx_mock):
        respx_mock.post("/api/api/chartofaccounts/testScope").mock(
            return_value=httpx.Response(200, json={
                "version": {
                    "effectiveFrom": "2019-08-24T14:15:22Z",
                    "asAtDate": "2019-08-24T14:15:22Z",
                    "asAtCreated": "2019-08-24T14:15:22Z",
                    "userIdCreated": "string",
                    "requestIdCreated": "string",
                    "reasonCreated": "string",
                    "asAtModified": "2019-08-24T14:15:22Z",
                    "userIdModified": "string",
                    "requestIdModified": "string",
                    "reasonModified": "string",
                    "asAtVersionNumber": -2147483648,
                    "entityUniqueId": "string",
                    "stagedModificationIdModified": "string"
                },
            }))

        sut = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        result = sut.create(self.client)

        assert result is not None

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope"

        body = json.loads(request.content)

        assert body == {
            "code": "testCode",
            "displayName": "example_display_name",
            "description": "example_description",
        }

        # To get the expected source version
        source_version = sut.__get_content_hash__()

        assert result == {
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_version,
            "remote_version": -2147483648
        }

    def test_create_with_properties(self, respx_mock, stock_chart_of_account_resource):
        respx_mock.post("/api/api/chartofaccounts/testScope").mock(
            return_value=httpx.Response(200, json={
                "version": {
                    "effectiveFrom": "2019-08-24T14:15:22Z",
                    "asAtDate": "2019-08-24T14:15:22Z",
                    "asAtCreated": "2019-08-24T14:15:22Z",
                    "userIdCreated": "string",
                    "requestIdCreated": "string",
                    "reasonCreated": "string",
                    "asAtModified": "2019-08-24T14:15:22Z",
                    "userIdModified": "string",
                    "requestIdModified": "string",
                    "reasonModified": "string",
                    "asAtVersionNumber": -2147483648,
                    "entityUniqueId": "string",
                    "stagedModificationIdModified": "string"
                },
            }))

        sut = stock_chart_of_account_resource
        result = sut.create(self.client)

        assert result is not None

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope"

        body = json.loads(request.content)

        assert body == {
            "code": "testCode",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "ChartOfAccounts/sc1/cd4": {
                    "key": "ChartOfAccounts/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            }
        }

        # To get the expected source version
        source_version = sut.__get_content_hash__()

        assert result == {
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_version,
            "remote_version": -2147483648
        }

    def test_create_with_prop_time_var(self, respx_mock, stock_chart_of_account_resource):
        respx_mock.post("/api/api/chartofaccounts/testScope").mock(
            return_value=httpx.Response(200, json={
                "version": {
                    "effectiveFrom": "2019-08-24T14:15:22Z",
                    "asAtDate": "2019-08-24T14:15:22Z",
                    "asAtCreated": "2019-08-24T14:15:22Z",
                    "userIdCreated": "string",
                    "requestIdCreated": "string",
                    "reasonCreated": "string",
                    "asAtModified": "2019-08-24T14:15:22Z",
                    "userIdModified": "string",
                    "requestIdModified": "string",
                    "reasonModified": "string",
                    "asAtVersionNumber": -2147483648,
                    "entityUniqueId": "string",
                    "stagedModificationIdModified": "string"
                },
            }))

        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.ChartOfAccounts, scope="sc1", code="cd4"
        )

        effective_from = dt.datetime(2000, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))
        effective_until = dt.datetime(2030, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))

        time_prop = fund_accounting.PropertyValue(
            property_key=property_example,
            label_value="Hello",
            effective_from=effective_from,
            effective_until=effective_until
        )

        sut = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
            properties=[time_prop]
        )

        result = sut.create(self.client)

        assert result is not None

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope"

        body = json.loads(request.content)

        assert body == {
            "code": "testCode",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "ChartOfAccounts/sc1/cd4": {
                    "key": "ChartOfAccounts/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                    "effectiveFrom": "2000-10-02T13:30:45Z",
                    "effectiveUntil": "2030-10-02T13:30:45Z"
                },
            }
        }

        # To get the expected source version
        source_version = sut.__get_content_hash__()

        assert result == {
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_version,
            "remote_version": -2147483648
        }

    def test_parse_api(self):
        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.ChartOfAccounts, scope="sc1", code="cd4"
        )
        data = {
            "scope": "fakeScope",  # note no actual scope in the body of the api response
            "code": "testCode",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "ChartOfAccounts/sc1/cd4": {
                    "key": {"$ref": "property_id"},
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            }
        }
        # when we parse it
        sut = fund_accounting.ChartOfAccountsResource.model_validate(data, context={
            "id": "something",
            "$refs": {
                "property_id": property_example
            }
        })
        # then properties is an array containing the property_example
        assert sut.properties
        assert len(sut.properties) == 1
        assert sut.properties[0].property_key == property_example
        assert sut.properties[0].label_value == "Hello"

    def test_update_no_change(self, respx_mock, stock_chart_of_account_resource):
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/properties").mock(
            return_value=httpx.Response(200, json={},))
        sut = stock_chart_of_account_resource

        remote_response = {
            "id": {
                "scope": "testScope",
                "code": "testCode"
            },
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "ChartOfAccounts/sc1/cd4": {
                    "key": "ChartOfAccounts/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            },
            "version": {
                "effectiveFrom": "2019-08-24T14:15:22Z",
                "asAtDate": "2019-08-24T14:15:22Z",
                "asAtCreated": "2019-08-24T14:15:22Z",
                "userIdCreated": "string",
                "requestIdCreated": "string",
                "reasonCreated": "string",
                "asAtModified": "2019-08-24T14:15:22Z",
                "userIdModified": "string",
                "requestIdModified": "string",
                "reasonModified": "string",
                "asAtVersionNumber": -2147483648,
                "entityUniqueId": "string",
                "stagedModificationIdModified": "string"
            },
        }

        respx_mock.get("/api/api/chartofaccounts/testScope/testCode").mock(
            return_value=httpx.Response(200, json=remote_response)
        )

        # Calculate hashes to simulate no change scenario
        source_hash = sut.__get_content_hash__()

        old_state = SimpleNamespace(
            scope="testScope",
            code="testCode",
            source_version=source_hash,
            remote_version=-2147483648
        )
        result = sut.update(self.client, old_state)
        assert result is None

    def test_update_with_change(self, respx_mock):
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/properties").mock(
            return_value=httpx.Response(200, json={},))
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": {
                        "scope": "testScope",
                        "code": "testCode"
                    },
                    "displayName": "example_display_name",
                    "description": "example_description",
                    "properties": {
                        "ChartOfAccounts/sc1/cd4": {
                            "key": "ChartOfAccounts/sc1/cd4",
                            "value": {
                                "labelValue": "Hello"
                            },
                        }
                    },
                    "version": {
                        "effectiveFrom": "2019-08-24T14:15:22Z",
                        "asAtDate": "2019-08-24T14:15:22Z",
                        "asAtCreated": "2019-08-24T14:15:22Z",
                        "userIdCreated": "string",
                        "requestIdCreated": "string",
                        "reasonCreated": "string",
                        "asAtModified": "2019-08-24T14:15:22Z",
                        "userIdModified": "string",
                        "requestIdModified": "string",
                        "reasonModified": "string",
                        "asAtVersionNumber": -2147483648,
                        "entityUniqueId": "string",
                        "stagedModificationIdModified": "string"
                    },
                },
            )
        )
        respx_mock.delete("/api/api/chartofaccounts/testScope/testCode").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/api/api/chartofaccounts/testScope").mock(
            return_value=httpx.Response(200, json={
                "version": {
                    "effectiveFrom": "2019-08-24T14:15:22Z",
                    "asAtDate": "2019-08-24T14:15:22Z",
                    "asAtCreated": "2019-08-24T14:15:22Z",
                    "userIdCreated": "string",
                    "requestIdCreated": "string",
                    "reasonCreated": "string",
                    "asAtModified": "2019-08-24T14:15:22Z",
                    "userIdModified": "string",
                    "requestIdModified": "string",
                    "reasonModified": "string",
                    "asAtVersionNumber": -123456789,
                    "entityUniqueId": "string",
                    "stagedModificationIdModified": "string"
                },
            }))

        old_state = SimpleNamespace(
            scope="testScope", code="testCode", remote_version="oldhash", source_version="different_hash"
        )

        updated_chart_of_account = fund_accounting.ChartOfAccountsResource(
            id="newId",
            scope="testScope",
            code="testCode",
            display_name="new_display_name",
            description="new_description",
        )

        result = updated_chart_of_account.update(self.client, old_state)
        assert result is not None

        # To get the expected source version
        source_version = updated_chart_of_account.__get_content_hash__()

        assert result == {
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_version,
            "remote_version": -123456789
        }

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope"

        # Body is now the updated version
        assert json.loads(request.content) == {
            "code": "testCode",
            "displayName": "new_display_name",
            "description": "new_description",
        }

        # Verify delete and create were called
        assert len(respx_mock.calls) == 4  # read (which also calls a get), delete, create
        assert respx_mock.calls[2].request.method == "DELETE"
        assert respx_mock.calls[3].request.method == "POST"

    def test_delete(self, respx_mock):
        respx_mock.delete(
            "api/api/chartofaccounts/testScope/testCode"
        ).mock(return_value=httpx.Response(200))
        client = self.client
        old_state = SimpleNamespace(scope="testScope", code="testCode")
        fund_accounting.ChartOfAccountsResource.delete(client, old_state)
        assert respx_mock.calls.last.request.method == "DELETE"

    def test_deps(self, stock_chart_of_account_resource):
        sut = stock_chart_of_account_resource
        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.ChartOfAccounts, scope="sc1", code="cd4"
        )
        assert sut.deps() == [property_example]

    def test_dump(self):
        property_example = property.DefinitionRef(
            id="property_id", domain=property.Domain.ChartOfAccounts, scope="sc1", code="cd4"
        )

        effective_from = dt.datetime(2000, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))
        effective_until = dt.datetime(2030, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))

        time_prop = fund_accounting.PropertyValue(
            property_key=property_example,
            label_value="Hello",
            effective_from=effective_from,
            effective_until=effective_until
        )

        sut = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
            properties=[time_prop]
        )

        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )

        assert result == {
            "scope": "testScope",
            "code": "testCode",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": [
                {
                    "propertyKey": {
                        "$ref": "property_id"
                    },
                    "labelValue": "Hello",
                    "effectiveFrom": "2000-10-02T13:30:45+00:00",
                    "effectiveUntil": "2030-10-02T13:30:45+00:00"
                }
            ]
        }

    def test_undump(self):
        # given dump data with $ref values
        prop1 = property.DefinitionRef(
            id="property_id", domain=property.Domain.Transaction, scope="sc1", code="TestProp"
        )

        effective_from = dt.datetime(2000, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))
        effective_until = dt.datetime(2030, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))

        data = {
            "scope": "testScope",
            "code": "testCode",
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": [
                {
                    "propertyKey": {
                        "$ref": "property_id"
                    },
                    "labelValue": "Test Label",
                    "effectiveFrom": "2000-10-02T13:30:45+00:00",
                    "effectiveUntil": "2030-10-02T13:30:45+00:00"
                }
            ]
        }

        result = fund_accounting.ChartOfAccountsResource.model_validate(
            data,
            context={
                "style": "undump",
                "$refs": {
                    "property_id": prop1
                },
                "id": "undump_chart",
            }
        )

        assert result.code == "testCode"
        assert result.display_name == "example_display_name"
        assert result.description == "example_description"
        assert result.properties
        assert len(result.properties) == 1
        assert result.properties[0].property_key == prop1
        assert result.properties[0].property_key.code == "TestProp"
        assert result.properties[0].label_value == "Test Label"
        assert result.properties[0].effective_from == effective_from
        assert result.properties[0].effective_until == effective_until

    def test_parse_api_format(self):
        # given dump data with $ref values
        prop1 = property.DefinitionRef(
            id="property_id", domain=property.Domain.Transaction, scope="sc1", code="TestProp"
        )

        effective_from = dt.datetime(2000, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))
        effective_until = dt.datetime(2030, 10, 2, 14, 30, 45, tzinfo=ZoneInfo("Europe/London"))

        prop2 = property.DefinitionRef(
            id="property_id_2", domain=property.Domain.Transaction, scope="sc2", code="TestProp2"
        )

        data = {
            "id": {
                "scope": "testScope",
                "code": "testCode"
            },
            "displayName": "example_display_name",
            "description": "example_description",
            "properties": {
                "ChartOfAccounts/sc1/cd4": {
                    "key": {
                        "$ref": "property_id"
                    },
                    "labelValue": "Test Label",
                    "effectiveFrom": "2000-10-02T13:30:45+00:00",
                    "effectiveUntil": "2030-10-02T13:30:45+00:00"

                },
                "ChartOfAccounts/sc2/cd2": {
                    "key": {
                        "$ref": "property_id_2"
                    },
                    "labelValue": "Test Label 2"
                }
            }
        }

        result = fund_accounting.ChartOfAccountsResource.model_validate(
            data,
            context={
                "style": "api",
                "$refs": {
                    "property_id": prop1,
                    "property_id_2": prop2
                },
                "id": "undump_chart",
            }
        )

        assert result.scope == "testScope"
        assert result.code == "testCode"
        assert result.display_name == "example_display_name"
        assert result.description == "example_description"
        assert result.properties
        assert len(result.properties) == 2
        assert result.properties[0].property_key == prop1
        assert result.properties[0].property_key.code == "TestProp"
        assert result.properties[0].label_value == "Test Label"
        assert result.properties[0].effective_from == effective_from
        assert result.properties[0].effective_until == effective_until
        assert result.properties[1].property_key == prop2
        assert result.properties[1].property_key.code == "TestProp2"
        assert result.properties[1].label_value == "Test Label 2"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeAccountsRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/accounts/accountCode").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        chart = fund_accounting.ChartOfAccountsRef(
            id="chart_example",
            code="testCode",
            scope="testScope"
        )
        sut = fund_accounting.AccountRef(
            id="account_example",
            account_code="accountCode",
            chart_of_accounts=chart,
        )

        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/accounts/accountCode").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        chart = fund_accounting.ChartOfAccountsRef(
            id="chart_example",
            code="testCode",
            scope="testScope"
        )
        sut = fund_accounting.AccountRef(
            id="account_example",
            account_code="accountCode",
            chart_of_accounts=chart,
        )
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Account accountCode not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/accounts/accountCode").mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        chart = fund_accounting.ChartOfAccountsRef(
            id="chart_example",
            code="testCode",
            scope="testScope"
        )
        sut = fund_accounting.AccountRef(
            id="account_example",
            account_code="accountCode",
            chart_of_accounts=chart,
        )
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeAccounts:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def stock_account_resource(self):
        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        perp_prop = fund_accounting.PropertyValue(
            property_key=property.DefinitionRef(
                id="one", domain=property.Domain.Account, scope="sc1", code="cd4"
            ),
            label_value="Hello"
        )

        return fund_accounting.AccountResource(
            id="example_id",
            chart_of_accounts=chart,
            code="account_code",
            description="example_desc",
            type=fund_accounting.AccountType.ASSET,
            status=fund_accounting.AccountStatus.ACTIVE,
            control="Manual",
            properties=[perp_prop]
        )

    def test_read(self, respx_mock, stock_account_resource):
        respx_mock.get("/api/api/chartofaccounts/oldScope/oldCode/accounts/different_account_code/properties").mock(
            return_value=httpx.Response(200, json={},))
        respx_mock.get("/api/api/chartofaccounts/oldScope/oldCode/accounts/different_account_code").mock(
            return_value=httpx.Response(
                200,
                json={
                    "code": "different_account_code",
                    "description": "different_example_desc",
                    "type": "Asset",
                    "status": "Active",
                    "control": "Manual",
                    "properties": {
                        "ChartOfAccounts/sc1/cd4": {
                            "key": "ChartOfAccounts/sc1/cd4",
                            "value": {
                                "labelValue": "Hello"
                            },
                        }
                    },
                }

            )
        )
        sut = stock_account_resource
        old_state = SimpleNamespace(
            scope="oldScope",
            code="oldCode",
            account_code="different_account_code"
        )
        result = sut.read(self.client, old_state)
        assert result is not None
        assert result["code"] == "different_account_code"

    def test_create_without_properties(self, respx_mock):
        response = {
            "accounts": [
                {
                    "code": "account_code",
                    "description": "example_desc",
                    "type": "Asset",
                    "status": "Active",
                    "control": "Manual",
                    "properties": {
                        "Account/sc1/cd1": {
                            "key": "Account/sc1/cd1",
                            "value": {
                                "labelValue": "Hello"
                            },
                        }
                    }
                }
            ]
        }

        respx_mock.post("/api/api/chartofaccounts/testScope/testCode/accounts").mock(
            return_value=httpx.Response(200, json=response))

        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        sut = fund_accounting.AccountResource(
            id="example_id",
            chart_of_accounts=chart,
            code="account_code",
            description="example_desc",
            type=fund_accounting.AccountType.ASSET,
            status=fund_accounting.AccountStatus.ACTIVE,
            control="Manual",
        )

        result = sut.create(self.client)

        assert result is not None

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope/testCode/accounts"

        body = json.loads(request.content)
        assert body == [
            {
                "code": "account_code",
                "description": "example_desc",
                "type": "Asset",
                "status": "Active",
                "control": "Manual"
            },
        ]

        dump = sut.model_dump(mode="json", exclude_none=True, by_alias=True)
        source_version = sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()
        account_to_dump = response["accounts"][0]

        remote_version = sha256(json.dumps(account_to_dump, sort_keys=True).encode()).hexdigest()

        assert result == {
            "account_code": "account_code",
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_version,
            "remote_version": remote_version,
        }

    def test_create_with_properties(self, respx_mock, stock_account_resource):
        response = {
            "accounts": [
                {
                    "code": "account_code",
                    "description": "example_desc",
                    "type": "Asset",
                    "status": "Active",
                    "control": "Manual",
                    "properties": {
                        "Account/sc1/cd1": {
                        "key": "Account/sc1/cd1",
                        "value": {
                            "labelValue": "Hello"
                        },
                        }
                    }
                }
            ]
        }
        respx_mock.post("/api/api/chartofaccounts/testScope/testCode/accounts").mock(
            return_value=httpx.Response(200, json=response))

        sut = stock_account_resource
        result = sut.create(self.client)

        assert result is not None

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope/testCode/accounts"

        body = json.loads(request.content)

        assert body == [
            {
                "code": "account_code",
                "description": "example_desc",
                "type": "Asset",
                "status": "Active",
                "control": "Manual",
                "properties": {
                    "Account/sc1/cd4": {
                        "key": "Account/sc1/cd4",
                        "value": {
                            "labelValue": "Hello"
                        },
                    }
                }
            }
        ]

        dump = sut.model_dump(mode="json", exclude_none=True, by_alias=True)
        source_version = sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()
        account_to_dump = response["accounts"][0]

        remote_version = sha256(json.dumps(account_to_dump, sort_keys=True).encode()).hexdigest()

        assert result == {
            "account_code": "account_code",
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_version,
            "remote_version": remote_version,
        }

    def test_update_no_change(self, respx_mock, stock_account_resource):
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/accounts/account_code/properties").mock(
            return_value=httpx.Response(200, json={},))
        sut = stock_account_resource

        remote_response = {
            "code": "account_code",
            "description": "example_desc",
            "type": "Asset",
            "status": "Active",
            "control": "Manual",
            "properties": {
                "ChartOfAccounts/sc1/cd4": {
                    "key": "ChartOfAccounts/sc1/cd4",
                    "value": {
                        "labelValue": "Hello"
                    },
                }
            },
        }

        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/accounts/account_code").mock(
            return_value=httpx.Response(200, json=remote_response)
        )

        # Calculate hashes to simulate no change scenario
        source_hash = sut.__get_content_hash__()

        # The remote hash should match what update() calculates from the read() response
        remote_hash = sha256(json.dumps(remote_response, sort_keys=True).encode()).hexdigest()

        old_state = SimpleNamespace(
            account_code="account_code",
            scope="testScope",
            code="testCode",
            source_version=source_hash,
            remote_version=remote_hash
        )
        result = sut.update(self.client, old_state)
        assert result is None

    def test_update_with_change(self, respx_mock):
        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/accounts/account_code/properties").mock(
            return_value=httpx.Response(200, json={},))
        remote_response = {
                "code": "account_code",
                "description": "example_desc",
                "type": "Asset",
                "status": "Active",
                "control": "Manual",
                "properties": {
                    "ChartOfAccounts/sc1/cd4": {
                        "key": "ChartOfAccounts/sc1/cd4",
                        "value": {
                            "labelValue": "Hello"
                        },
                    }
                },
            }

        respx_mock.get("/api/api/chartofaccounts/testScope/testCode/accounts/account_code").mock(
            return_value=httpx.Response(200, json=remote_response)
        )

        response = {
            "accounts": [
                {
                    "code": "account_code",
                    "description": "different_example_desc",
                    "type": "Asset",
                    "status": "Active",
                    "control": "Manual",
                    "properties": {
                        "Account/sc2/cd2": {
                            "key": "Account/sc2/cd2",
                            "value": {
                                "labelValue": "Goodbye"
                            },
                        }
                    }
                }
            ]
        }

        respx_mock.post("/api/api/chartofaccounts/testScope/testCode/accounts").mock(
            return_value=httpx.Response(200, json=response))

        old_state = SimpleNamespace(
            account_code="account_code",
            scope="testScope",
            code="testCode",
            remote_version="oldhash",
            source_version="different_hash"
        )

        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        different_perp_prop = fund_accounting.PropertyValue(
            property_key=property.DefinitionRef(
                id="one", domain=property.Domain.Account, scope="sc2", code="cd2"
            ),
            label_value="Goodbye"
        )

        updated_account = fund_accounting.AccountResource(
            id="different_example_id",
            chart_of_accounts=chart,
            code="account_code",
            description="different_example_desc",
            type=fund_accounting.AccountType.ASSET,
            status=fund_accounting.AccountStatus.ACTIVE,
            control="Manual",
            properties=[different_perp_prop]
        )

        result = updated_account.update(self.client, old_state)
        assert result is not None

        dump = updated_account.model_dump(mode="json", exclude_none=True, by_alias=True)
        source_version = sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()
        account_to_dump = response["accounts"][0]

        remote_version = sha256(json.dumps(account_to_dump, sort_keys=True).encode()).hexdigest()

        assert result == {
            "account_code": "account_code",
            "scope": "testScope",
            "code": "testCode",
            "source_version": source_version,
            "remote_version": remote_version,
        }

        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/chartofaccounts/testScope/testCode/accounts"

        body = json.loads(request.content)

        # Body is now the updated version
        assert body == [
            {
                "code": "account_code",
                "description": "different_example_desc",
                "type": "Asset",
                "status": "Active",
                "control": "Manual",
                "properties": {
                    "Account/sc2/cd2": {
                        "key": "Account/sc2/cd2",
                        "value": {
                            "labelValue": "Goodbye"
                        },
                    }
                }
            }
        ]

        # Verify upsert was called
        assert len(respx_mock.calls) == 3
        assert respx_mock.calls[2].request.method == "POST"

    def test_cannot_update_if_scope_changes(self, stock_account_resource):
        old_state = SimpleNamespace(
            account_code="account_code",
            scope="different_scope",
            code="testCode",
            remote_version="oldhash",
            source_version="different_hash"
        )

        sut = stock_account_resource
        error_message = "Cannot change the scope on an accounts"
        with pytest.raises(RuntimeError, match=error_message):
            sut.update(self.client, old_state)

    def test_cannot_update_if_code_changes(self, stock_account_resource):
        old_state = SimpleNamespace(
            account_code="account_code",
            scope="testScope",
            code="different_code",
            remote_version="oldhash",
            source_version="different_hash"
        )

        sut = stock_account_resource
        error_message = "Cannot change the code on an account"
        with pytest.raises(RuntimeError, match=error_message):
            sut.update(self.client, old_state)

    def test_delete(self, respx_mock):
        respx_mock.post(
            "/api/api/chartofaccounts/testScope/testCode/accounts/$delete"
        ).mock(return_value=httpx.Response(200))
        client = self.client
        old_state = SimpleNamespace(account_code="account_code", scope="testScope", code="testCode")
        fund_accounting.AccountResource.delete(client, old_state)
        assert respx_mock.calls.last.request.method == "POST"

    def test_deps_without_properties(self):
        chart = fund_accounting.ChartOfAccountsResource(
            id="chartDepend",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        account = fund_accounting.AccountResource(
            id="example_id",
            chart_of_accounts=chart,
            code="account_code",
            description="example_desc",
            type=fund_accounting.AccountType.ASSET,
            status=fund_accounting.AccountStatus.ACTIVE,
            control="Manual",
        )
        assert account.deps() == [chart]

    def test_deps_with_properties(self, stock_account_resource):
        chart_prop = property.DefinitionRef(
            id="property_id", domain=property.Domain.ChartOfAccounts, scope="sc1", code="cd4"
        )

        chart_perp_prop = fund_accounting.PropertyValue(
            property_key=chart_prop,
            label_value="Hello"
        )

        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
            properties=[chart_perp_prop]
        )

        account_prop = property.DefinitionRef(
            id="one", domain=property.Domain.Account, scope="sc1", code="cd4"
        )

        account_perp_prop = fund_accounting.PropertyValue(
            property_key=account_prop,
            label_value="Hello"
        )

        sut = fund_accounting.AccountResource(
            id="example_id",
            chart_of_accounts=chart,
            code="account_code",
            description="example_desc",
            type=fund_accounting.AccountType.ASSET,
            status=fund_accounting.AccountStatus.ACTIVE,
            control="Manual",
            properties=[account_perp_prop]
        )

        assert sut.deps() == [chart, chart_prop, account_prop]

    def test_dump(self, stock_account_resource):
        sut = stock_account_resource

        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )

        assert result == {
            "chartOfAccounts": {
                "$ref": "exampleId"
            },
            "code": "account_code",
            "description": "example_desc",
            "type": "Asset",
            "status": "Active",
            "control": "Manual",
            "properties": [
                {
                    "propertyKey": {
                        "$ref": "one"
                    },
                    "labelValue": "Hello"
                }
            ]
        }

    def test_undump(self):
        chart = fund_accounting.ChartOfAccountsResource(
            id="exampleId",
            scope="testScope",
            code="testCode",
            display_name="example_display_name",
            description="example_description",
        )

        # given dump data with $ref values
        prop1 = property.DefinitionRef(
            id="property_id", domain=property.Domain.Transaction, scope="sc1", code="TestProp"
        )

        data = {
            "chartOfAccounts": {
                "$ref": "exampleId"
            },
            "code": "account_code",
            "description": "example_desc",
            "type": "Asset",
            "status": "Active",
            "control": "Manual",
            "properties": [
                {
                    "propertyKey": {
                        "$ref": "property_id"
                    },
                    "labelValue": "Test Label"
                }
            ]
        }

        result = fund_accounting.AccountResource.model_validate(
            data,
            context={
                "style": "undump",
                "$refs": {
                    "exampleId": chart,
                    "property_id": prop1
                },
                "id": "undump_account",
            }
        )

        assert result.chart_of_accounts == chart
        assert result.code == "account_code"
        assert result.description == "example_desc"
        assert result.properties
        assert len(result.properties) == 1
        assert result.properties[0].property_key == prop1
        assert result.properties[0].property_key.code == "TestProp"
        assert result.properties[0].label_value == "Test Label"
