import json

import httpx
import pytest

from fbnconfig import datatype as dt
from fbnconfig import property as prop
from fbnconfig import reference_list as rl

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeReferenceListResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given a desired reference list with a string list
        sut = rl.ReferenceListResource(
            id="ref1",
            scope="scope-a",
            code="code-a",
            name="Test Reference List",
            description="A test reference list",
            tags=["test", "example"],
            reference_list=rl.StringList(values=["value1", "value2", "value3"])
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "scope-a"
        assert state["code"] == "code-a"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/referencelists"
        request_body = json.loads(request.content)
        assert request_body["id"] == {"scope": "scope-a", "code": "code-a"}
        assert request_body["name"] == "Test Reference List"
        assert request_body["description"] == "A test reference list"
        assert request_body["tags"] == ["test", "example"]
        assert request_body["referenceList"]["values"] == ["value1", "value2", "value3"]
        assert request_body["referenceList"]["referenceListType"] == "StringList"

    def test_create_with_portfolio_group_id_list(self, respx_mock):
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given a desired reference list with a portfolio group id list
        sut = rl.ReferenceListResource(
            id="ref2",
            scope="scope-b",
            code="code-b",
            name="Portfolio Group Reference List",
            reference_list=rl.PortfolioGroupIdList(values=[
                rl.ResourceId(scope="group-scope", code="group-1"),
                rl.ResourceId(scope="group-scope", code="group-2")
            ])
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "scope-b"
        assert state["code"] == "code-b"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/referencelists"
        request_body = json.loads(request.content)
        assert request_body["id"] == {"scope": "scope-b", "code": "code-b"}
        assert request_body["name"] == "Portfolio Group Reference List"
        assert request_body["referenceList"]["values"] == [
            {"scope": "group-scope", "code": "group-1"},
            {"scope": "group-scope", "code": "group-2"}
        ]
        assert request_body["referenceList"]["referenceListType"] == "PortfolioGroupIdList"

    def test_create_with_portfolio_id_list(self, respx_mock):
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given a desired reference list with a portfolio id list
        sut = rl.ReferenceListResource(
            id="ref3",
            scope="scope-c",
            code="code-c",
            name="Portfolio Reference List",
            reference_list=rl.PortfolioIdList(values=[
                rl.ResourceId(scope="portfolio-scope", code="portfolio-1"),
                rl.ResourceId(scope="portfolio-scope", code="portfolio-2")
            ])
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "scope-c"
        assert state["code"] == "code-c"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/referencelists"
        request_body = json.loads(request.content)
        assert request_body["id"] == {"scope": "scope-c", "code": "code-c"}
        assert request_body["name"] == "Portfolio Reference List"
        assert request_body["referenceList"]["values"] == [
            {"scope": "portfolio-scope", "code": "portfolio-1"},
            {"scope": "portfolio-scope", "code": "portfolio-2"}
        ]
        assert request_body["referenceList"]["referenceListType"] == "PortfolioIdList"

    def test_create_with_decimal_list(self, respx_mock):
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given a desired reference list with a decimal list
        sut = rl.ReferenceListResource(
            id="ref4",
            scope="scope-d",
            code="code-d",
            name="Decimal Reference List",
            reference_list=rl.DecimalList(values=[1.5, 2.75, 3.0, 4.25])
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "scope-d"
        assert state["code"] == "code-d"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/referencelists"
        request_body = json.loads(request.content)
        assert request_body["id"] == {"scope": "scope-d", "code": "code-d"}
        assert request_body["name"] == "Decimal Reference List"
        assert request_body["referenceList"]["values"] == [1.5, 2.75, 3.0, 4.25]
        assert request_body["referenceList"]["referenceListType"] == "DecimalList"

    def test_create_with_fund_id_list(self, respx_mock):
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given a desired reference list with a fund id list
        sut = rl.ReferenceListResource(
            id="ref5",
            scope="scope-e",
            code="code-e",
            name="Fund Reference List",
            reference_list=rl.FundIdList(values=[
                rl.ResourceId(scope="fund-scope", code="fund-1"),
                rl.ResourceId(scope="fund-scope", code="fund-2")
            ])
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "scope-e"
        assert state["code"] == "code-e"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/referencelists"
        request_body = json.loads(request.content)
        assert request_body["id"] == {"scope": "scope-e", "code": "code-e"}
        assert request_body["name"] == "Fund Reference List"
        assert request_body["referenceList"]["values"] == [
            {"scope": "fund-scope", "code": "fund-1"},
            {"scope": "fund-scope", "code": "fund-2"}
        ]
        assert request_body["referenceList"]["referenceListType"] == "FundIdList"

    def test_create_with_address_key_list(self, respx_mock):
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given a desired reference list with an address key list
        sut = rl.ReferenceListResource(
            id="ref6",
            scope="scope-f",
            code="code-f",
            name="Address Key Reference List",
            reference_list=rl.AddressKeyList(values=["address-key-1", "address-key-2", "address-key-3"])
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "scope-f"
        assert state["code"] == "code-f"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/referencelists"
        request_body = json.loads(request.content)
        assert request_body["id"] == {"scope": "scope-f", "code": "code-f"}
        assert request_body["name"] == "Address Key Reference List"
        assert request_body["referenceList"]["values"] == [
            "address-key-1", "address-key-2", "address-key-3"
        ]
        assert request_body["referenceList"]["referenceListType"] == "AddressKeyList"

    def test_create_with_instrument_list(self, respx_mock):
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given a desired reference list with an instrument list
        sut = rl.ReferenceListResource(
            id="ref7",
            scope="scope-g",
            code="code-g",
            name="Instrument Reference List",
            reference_list=rl.InstrumentList(values=["LUID_12345", "LUID_67890", "LUID_11111"])
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "scope-g"
        assert state["code"] == "code-g"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/referencelists"
        request_body = json.loads(request.content)
        assert request_body["id"] == {"scope": "scope-g", "code": "code-g"}
        assert request_body["name"] == "Instrument Reference List"
        assert request_body["referenceList"]["values"] == ["LUID_12345", "LUID_67890", "LUID_11111"]
        assert request_body["referenceList"]["referenceListType"] == "InstrumentList"

    def test_create_with_property_list(self, respx_mock):
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given property definitions for the property list
        prop_def = prop.DefinitionResource(
            id="test-prop",
            domain=prop.Domain.Portfolio,
            scope="test-scope",
            code="test-property",
            display_name="Test Property",
            data_type_id=dt.DataTypeRef(id="string-dt", scope="system", code="string"),
            property_description="A test property for reference lists"
        )
        # given a desired reference list with a property list
        sut = rl.ReferenceListResource(
            id="ref8",
            scope="scope-h",
            code="code-h",
            name="Property Reference List",
            reference_list=rl.PropertyList(values=[
                rl.PropertyListItem(
                    key=prop_def,
                    value=rl.PropertyValue(label_value="test-label-1")
                ),
                rl.PropertyListItem(
                    key=prop_def,
                    value=rl.PropertyValue(label_value="test-label-2")
                )
            ])
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "scope-h"
        assert state["code"] == "code-h"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/referencelists"
        request_body = json.loads(request.content)
        assert request_body["id"] == {"scope": "scope-h", "code": "code-h"}
        assert request_body["name"] == "Property Reference List"
        assert len(request_body["referenceList"]["values"]) == 2
        # Check the first property list item
        first_item = request_body["referenceList"]["values"][0]
        assert first_item["key"] == "Portfolio/test-scope/test-property"
        assert first_item["value"]["labelValue"] == "test-label-1"
        assert "metricValue" not in first_item["value"]
        assert "labelSetValue" not in first_item["value"]
        # Check the second property list item
        second_item = request_body["referenceList"]["values"][1]
        assert second_item["key"] == "Portfolio/test-scope/test-property"
        assert second_item["value"]["labelValue"] == "test-label-2"
        assert "metricValue" not in second_item["value"]
        assert "labelSetValue" not in second_item["value"]

    def test_deps_with_string_list(self):
        # given a reference list with a string list
        sut = rl.ReferenceListResource(
            id="ref1",
            scope="scope-a",
            code="code-a",
            name="Test Reference List",
            reference_list=rl.StringList(values=["value1", "value2", "value3"])
        )
        # when we get its dependencies
        deps = sut.deps()
        # then it has no dependencies
        assert deps == []

    def test_deps_with_property_list(self):
        # given property definitions for the property list
        prop_def1 = prop.DefinitionResource(
            id="test-prop1",
            domain=prop.Domain.Portfolio,
            scope="test-scope",
            code="test-property-1",
            display_name="Test Property 1",
            data_type_id=dt.DataTypeRef(id="string-dt", scope="system", code="string"),
            property_description="First test property"
        )
        prop_def2 = prop.DefinitionRef(
            id="test-prop2",
            domain=prop.Domain.Portfolio,
            scope="test-scope",
            code="test-property-2",
        )
        # given a reference list with a property list using multiple property definitions
        sut = rl.ReferenceListResource(
            id="ref8",
            scope="scope-h",
            code="code-h",
            name="Property Reference List",
            reference_list=rl.PropertyList(values=[
                rl.PropertyListItem(
                    key=prop_def1,
                    value=rl.PropertyValue(label_value="test-label-1")
                ),
                rl.PropertyListItem(
                    key=prop_def2,
                    value=rl.PropertyValue(label_value="test-label-2")
                )
            ])
        )
        # when we get its dependencies
        deps = sut.deps()
        # then it should return both property definitions
        assert len(deps) == 2
        assert prop_def1 in deps
        assert prop_def2 in deps

    def test_deps_with_property_list_duplicate_properties(self):
        # given a property definition that will be used multiple times
        prop_def = prop.DefinitionResource(
            id="test-prop",
            domain=prop.Domain.Portfolio,
            scope="test-scope",
            code="test-property",
            display_name="Test Property",
            data_type_id=dt.DataTypeRef(id="string-dt", scope="system", code="string"),
            property_description="A test property"
        )
        # given a reference list with a property list using the same property definition multiple times
        sut = rl.ReferenceListResource(
            id="ref8",
            scope="scope-h",
            code="code-h",
            name="Property Reference List",
            reference_list=rl.PropertyList(values=[
                rl.PropertyListItem(
                    key=prop_def,
                    value=rl.PropertyValue(label_value="test-label-1")
                ),
                rl.PropertyListItem(
                    key=prop_def,
                    value=rl.PropertyValue(label_value="test-label-2")
                ),
                rl.PropertyListItem(
                    key=prop_def,
                    value=rl.PropertyValue(label_value="test-label-3")
                )
            ])
        )
        # when we get its dependencies
        deps = sut.deps()
        # then it should return the property definition only once (deduplicated)
        assert len(deps) == 1
        assert deps[0] == prop_def

    def test_update_with_no_changes(self, respx_mock):
        from types import SimpleNamespace
        # given a reference list with a string list
        sut = rl.ReferenceListResource(
            id="ref1",
            scope="scope-a",
            code="code-a",
            name="Test Reference List",
            description="A test reference list",
            tags=["test", "example"],
            reference_list=rl.StringList(values=["value1", "value2", "value3"])
        )
        # and an old state with the same content hash
        desired = sut.model_dump(
            mode="json",
            exclude_none=True,
            by_alias=True,
            exclude={"id", "scope", "code"}
        )
        sorted_desired = json.dumps(desired, sort_keys=True)
        from hashlib import sha256
        content_hash = sha256(sorted_desired.encode()).hexdigest()
        old_state = SimpleNamespace(scope="scope-a", code="code-a", content_hash=content_hash)
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is None (no changes needed)
        assert state is None
        # and no HTTP requests were made
        assert len(respx_mock.calls) == 0

    def test_update_with_changes(self, respx_mock):
        from types import SimpleNamespace
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given a reference list with a string list
        sut = rl.ReferenceListResource(
            id="ref1",
            scope="scope-a",
            code="code-a",
            name="Test Reference List",
            description="A test reference list",
            tags=["test", "example"],
            reference_list=rl.StringList(values=["value1", "value2", "value3"])
        )
        # and an old state with a different content hash
        old_state = SimpleNamespace(scope="scope-a", code="code-a", content_hash="different_hash")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is returned with new content hash
        assert state is not None
        assert state["scope"] == "scope-a"
        assert state["code"] == "code-a"
        assert "content_hash" in state
        assert state["content_hash"] != "different_hash"
        # and a POST request was made to update the reference list
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/referencelists"
        request_body = json.loads(request.content)
        assert request_body["id"] == {"scope": "scope-a", "code": "code-a"}
        assert request_body["name"] == "Test Reference List"

    def test_update_with_scope_code_change(self, respx_mock):
        from types import SimpleNamespace
        respx_mock.delete("/api/api/referencelists/old-scope/old-code").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/api/api/referencelists").mock(return_value=httpx.Response(200, json={}))
        # given a reference list with new scope/code
        sut = rl.ReferenceListResource(
            id="ref1",
            scope="new-scope",
            code="new-code",
            name="Test Reference List",
            reference_list=rl.StringList(values=["value1", "value2", "value3"])
        )
        # and an old state with different scope/code
        old_state = SimpleNamespace(scope="old-scope", code="old-code", content_hash="old_hash")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the old one is deleted and a new one is created
        assert state is not None
        assert state["scope"] == "new-scope"
        assert state["code"] == "new-code"
        assert "content_hash" in state
        # and both DELETE and POST requests were made
        assert len(respx_mock.calls) == 2
        delete_request = respx_mock.calls[0].request
        assert delete_request.method == "DELETE"
        assert delete_request.url.path == "/api/api/referencelists/old-scope/old-code"
        create_request = respx_mock.calls[1].request
        assert create_request.method == "POST"
        assert create_request.url.path == "/api/api/referencelists"

    def test_delete(self, respx_mock):
        from types import SimpleNamespace
        respx_mock.delete("/api/api/referencelists/scope-a/code-a").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a resource that exists in the remote
        old_state = SimpleNamespace(scope="scope-a", code="code-a")
        # when we delete it
        rl.ReferenceListResource.delete(self.client, old_state)
        # then a DELETE request was made
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/api/api/referencelists/scope-a/code-a"

    def test_create_property_list_with_both_metric_and_label_values_throws(self):
        # when we try to create a PropertyValue with both metric_value and label_value set
        with pytest.raises(KeyError, match="Cannot set label_value and metric_value"):
            rl.PropertyValue(
                label_value="test-label",
                metric_value=rl.MetricValue(value=123.45, unit="USD")
            )

    def test_dump_property_list_with_ref_serialization(self):
        # given property definitions for the property list
        prop_def = prop.DefinitionResource(
            id="test-prop",
            domain=prop.Domain.Portfolio,
            scope="test-scope",
            code="test-property",
            display_name="Test Property",
            data_type_id=dt.DataTypeRef(id="string-dt", scope="system", code="string"),
            property_description="A test property for reference lists"
        )
        prop_ref = prop.DefinitionRef(
            id="test-prop-ref",
            domain=prop.Domain.Portfolio,
            scope="test-scope",
            code="test-property-ref"
        )
        # given a reference list with a property list
        sut = rl.ReferenceListResource(
            id="ref8",
            scope="scope-h",
            code="code-h",
            name="Property Reference List",
            reference_list=rl.PropertyList(values=[
                rl.PropertyListItem(
                    key=prop_def,
                    value=rl.PropertyValue(label_value="test-label-1")
                ),
                rl.PropertyListItem(
                    key=prop_ref,
                    value=rl.PropertyValue(label_value="test-label-2")
                )
            ])
        )
        # when we dump it
        dumped = sut.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            round_trip=True,
            context={"style": "dump"}
        )
        # then referenced objects should be serialized as $refs
        assert dumped["name"] == "Property Reference List"
        assert len(dumped["referenceList"]["values"]) == 2
        # Check the first property list item has $ref
        first_item = dumped["referenceList"]["values"][0]
        assert first_item["key"] == {"$ref": "test-prop"}
        assert first_item["value"]["labelValue"] == "test-label-1"
        # Check the second property list item has $ref
        second_item = dumped["referenceList"]["values"][1]
        assert second_item["key"] == {"$ref": "test-prop-ref"}
        assert second_item["value"]["labelValue"] == "test-label-2"

    def test_undump_simple_reference_list(self):
        # given dump data for a simple string list
        data = {
            "scope": "undump-scope",
            "code": "undump-string-list",
            "name": "Undump String List",
            "description": "String list for undump testing",
            "tags": ["undump", "test"],
            "referenceList": {
                "values": ["value1", "value2", "value3"],
                "referenceListType": "StringList"
            }
        }
        # when we undump it with id from context
        result = rl.ReferenceListResource.model_validate(
            data, context={"style": "dump", "id": "undump-string-list"}
        )
        # then it's correctly populated including id from context
        assert result.id == "undump-string-list"
        assert result.scope == "undump-scope"
        assert result.code == "undump-string-list"
        assert result.name == "Undump String List"
        assert result.description == "String list for undump testing"
        assert result.tags == ["undump", "test"]
        assert isinstance(result.reference_list, rl.StringList)
        assert result.reference_list.values == ["value1", "value2", "value3"]

    def test_undump_property_list_with_refs(self):
        # given dump data with property $refs
        data = {
            "scope": "undump-scope",
            "code": "undump-prop-list",
            "name": "Undump Property List",
            "description": "Property list for undump testing",
            "referenceList": {
                "values": [
                    {
                        "key": {"$ref": "prop-def-1"},
                        "value": {"labelValue": "undump-label-1"}
                    },
                    {
                        "key": {"$ref": "prop-ref-2"},
                        "value": {"labelValue": "undump-label-2"}
                    }
                ],
                "referenceListType": "PropertyList"
            }
        }
        # and refs in context
        prop_def = prop.DefinitionResource(
            id="prop-def-1",
            domain=prop.Domain.Portfolio,
            scope="undump-scope",
            code="undump-property-1",
            display_name="Undump Property 1",
            data_type_id=dt.DataTypeRef(id="string-dt", scope="system", code="string"),
            property_description="First undump property"
        )
        prop_ref = prop.DefinitionRef(
            id="prop-ref-2",
            domain=prop.Domain.Portfolio,
            scope="undump-scope",
            code="undump-property-2"
        )
        refs_dict = {
            "prop-def-1": prop_def,
            "prop-ref-2": prop_ref
        }
        # when we undump it
        result = rl.ReferenceListResource.model_validate(
            data, context={"style": "dump", "$refs": refs_dict, "id": "undump-prop-list"}
        )
        # then properties are correctly resolved
        assert result.id == "undump-prop-list"
        assert result.scope == "undump-scope"
        assert result.code == "undump-prop-list"
        assert result.name == "Undump Property List"
        assert result.description == "Property list for undump testing"
        assert isinstance(result.reference_list, rl.PropertyList)
        assert len(result.reference_list.values) == 2
        # Check first property list item
        first_item = result.reference_list.values[0]
        assert first_item.key == prop_def
        assert first_item.value.label_value == "undump-label-1"
        # Check second property list item
        second_item = result.reference_list.values[1]
        assert second_item.key == prop_ref
        assert second_item.value.label_value == "undump-label-2"

    def test_undump_decimal_list(self):
        # given dump data for a decimal list
        data = {
            "scope": "undump-scope",
            "code": "undump-decimal-list",
            "name": "Undump Decimal List",
            "referenceList": {
                "values": [1.5, 2.75, 3.0, 4.25],
                "referenceListType": "DecimalList"
            }
        }
        # when we undump it with id from context
        result = rl.ReferenceListResource.model_validate(
            data, context={"style": "dump", "id": "undump-decimal-list"}
        )
        # then it's correctly populated
        assert result.id == "undump-decimal-list"
        assert result.scope == "undump-scope"
        assert result.code == "undump-decimal-list"
        assert result.name == "Undump Decimal List"
        assert isinstance(result.reference_list, rl.DecimalList)
        assert result.reference_list.values == [1.5, 2.75, 3.0, 4.25]

    def test_undump_portfolio_id_list(self):
        # given dump data for a portfolio id list
        data = {
            "scope": "undump-scope",
            "code": "undump-portfolio-list",
            "name": "Undump Portfolio List",
            "referenceList": {
                "values": [
                    {"scope": "portfolio-scope", "code": "portfolio-1"},
                    {"scope": "portfolio-scope", "code": "portfolio-2"}
                ],
                "referenceListType": "PortfolioIdList"
            }
        }
        # when we undump it with id from context
        result = rl.ReferenceListResource.model_validate(
            data, context={"style": "dump", "id": "undump-portfolio-list"}
        )
        # then it's correctly populated
        assert result.id == "undump-portfolio-list"
        assert result.scope == "undump-scope"
        assert result.code == "undump-portfolio-list"
        assert result.name == "Undump Portfolio List"
        assert isinstance(result.reference_list, rl.PortfolioIdList)
        assert len(result.reference_list.values) == 2
        assert result.reference_list.values[0].scope == "portfolio-scope"
        assert result.reference_list.values[0].code == "portfolio-1"
        assert result.reference_list.values[1].scope == "portfolio-scope"
        assert result.reference_list.values[1].code == "portfolio-2"
