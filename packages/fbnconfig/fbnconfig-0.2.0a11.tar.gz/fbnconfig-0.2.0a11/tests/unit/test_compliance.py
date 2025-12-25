import copy
import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import compliance as cp
from fbnconfig import reference_list as rl

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeComplianceTemplateResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create_simple_template(self, respx_mock):
        respx_mock.post("/api/api/compliance/templates/test-scope").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a simple compliance template
        sut = cp.ComplianceTemplateResource(
            id="simple-template",
            scope="test-scope",
            code="simple-template",
            description="A simple compliance template for testing",
            tags=["test", "simple"],
            variations=[
                cp.ComplianceTemplateVariation(
                    label="Basic Variation",
                    description="Basic variation for testing",
                    outcome_description="This variation performs basic compliance checks",
                    steps=[
                        cp.FilterStep(
                            label="Filter-Step-1",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="filter_param",
                                    description="Parameter for filter step",
                                    type="string",
                                )
                            ]
                        )
                    ],
                    referenced_group_label=None
                )
            ]
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "test-scope"
        assert state["code"] == "simple-template"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/compliance/templates/test-scope"
        request_body = json.loads(request.content)
        expected_body = {
            "id": {"scope": "test-scope", "code": "simple-template"},
            "code": "simple-template",
            "description": "A simple compliance template for testing",
            "tags": ["test", "simple"],
            "variations": [{
                "label": "Basic Variation",
                "description": "Basic variation for testing",
                "outcomeDescription": "This variation performs basic compliance checks",
                "steps": [{
                    "label": "Filter-Step-1",
                    "complianceStepTypeRequest": "FilterStepRequest",
                    "parameters": [{
                        "name": "filter_param",
                        "description": "Parameter for filter step",
                        "type": "string"
                    }]
                }]
            }]
        }
        assert request_body == expected_body

    def test_create_complex_template_with_multiple_steps(self, respx_mock):
        respx_mock.post(
            "/api/api/compliance/templates/complex-scope"
        ).mock(return_value=httpx.Response(200, json={}))
        # given a complex compliance template with multiple step types
        sut = cp.ComplianceTemplateResource(
            id="complex-template",
            scope="complex-scope",
            code="complex-template",
            description="A complex compliance template with multiple step types",
            variations=[
                cp.ComplianceTemplateVariation(
                    label="Multi-Step Variation",
                    description="Variation with multiple step types",
                    outcome_description="This variation performs comprehensive compliance checks",
                    steps=[
                        cp.FilterStep(
                            label="Initial-Filter",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="asset_class",
                                    description="Asset class filter",
                                    type="string",
                                )
                            ]
                        ),
                        cp.BranchStep(
                            label="Branch-By-Category",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="category_field",
                                    description="Field to branch by",
                                    type="addressKey",
                                )
                            ]
                        ),
                        cp.PercentCheckStep(
                            label="Percentage-Check",
                            limit_check_parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="upper_limit",
                                    description="Upper percentage limit",
                                    type="decimal",
                                )
                            ],
                            warning_check_parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="warning_threshold",
                                    description="Warning threshold percentage",
                                    type="decimal",
                                )
                            ]
                        ),
                        cp.GroupFilterStep(
                            label="Group-Filter",
                            limit_check_parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="group_limit",
                                    description="Group-based limit",
                                    type="decimal",
                                )
                            ]
                        )
                    ],
                    referenced_group_label="test-group"
                )
            ]
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "complex-scope"
        assert state["code"] == "complex-template"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/compliance/templates/complex-scope"
        request_body = json.loads(request.content)
        expected_body = {
            "id": {"scope": "complex-scope", "code": "complex-template"},
            "code": "complex-template",
            "description": "A complex compliance template with multiple step types",
            "variations": [{
                "label": "Multi-Step Variation",
                "description": "Variation with multiple step types",
                "outcomeDescription": "This variation performs comprehensive compliance checks",
                "referencedGroupLabel": "test-group",
                "steps": [{
                    "label": "Initial-Filter",
                    "complianceStepTypeRequest": "FilterStepRequest",
                    "parameters": [{
                        "name": "asset_class",
                        "description": "Asset class filter",
                        "type": "string"
                    }]
                }, {
                    "label": "Branch-By-Category",
                    "complianceStepTypeRequest": "BranchStepRequest",
                    "parameters": [{
                        "name": "category_field",
                        "description": "Field to branch by",
                        "type": "addressKey"
                    }]
                }, {
                    "label": "Percentage-Check",
                    "complianceStepTypeRequest": "PercentCheckStepRequest",
                    "limitCheckParameters": [{
                        "name": "upper_limit",
                        "description": "Upper percentage limit",
                        "type": "decimal"
                    }],
                    "warningCheckParameters": [{
                        "name": "warning_threshold",
                        "description": "Warning threshold percentage",
                        "type": "decimal"
                    }]
                }, {
                    "label": "Group-Filter",
                    "complianceStepTypeRequest": "GroupFilterStepRequest",
                    "limitCheckParameters": [{
                        "name": "group_limit",
                        "description": "Group-based limit",
                        "type": "decimal"
                    }]
                }]
            }]
        }
        assert request_body == expected_body

    def test_create_template_with_all_step_types(self, respx_mock):
        respx_mock.post(
            "/api/api/compliance/templates/all-steps-scope"
        ).mock(return_value=httpx.Response(200, json={}))
        # given a template with all available step types
        sut = cp.ComplianceTemplateResource(
            id="all-steps-template",
            scope="all-steps-scope",
            code="all-steps-template",
            variations=[
                cp.ComplianceTemplateVariation(
                    label="All Steps Variation",
                    description="Variation showcasing all step types",
                    steps=[
                        cp.FilterStep(
                            label="Filter",
                            parameters=[cp.ComplianceTemplateParameter(
                                name="param1", description="desc1", type="string"
                            )]
                        ),
                        cp.BranchStep(
                            label="Branch",
                            parameters=[cp.ComplianceTemplateParameter(
                                name="param2", description="desc2", type="addressKey"
                            )]
                        ),
                        cp.CheckStep(
                            label="Check",
                            limit_check_parameters=[cp.ComplianceTemplateParameter(
                                name="limit", description="limit desc", type="decimal"
                            )],
                            warning_check_parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="warning", description="warning desc", type="decimal"
                                )
                            ]
                        ),
                        cp.GroupByStep(
                            values=["value1", "value2"],
                            parameters=[cp.ComplianceTemplateParameter(
                                name="group_param", description="group desc", type="string"
                            )]
                        ),
                        cp.GroupFilterStep(
                            label="GroupFilter",
                            limit_check_parameters=[cp.ComplianceTemplateParameter(
                                name="group_limit", description="group limit desc", type="decimal"
                            )]
                        ),
                        cp.PercentCheckStep(
                            label="PercentCheck",
                            limit_check_parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="percent_limit",
                                    description="percent limit desc",
                                    type="decimal",
                                )
                            ],
                            warning_check_parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="percent_warning",
                                    description="percent warning desc",
                                    type="decimal",
                                )]
                        ),
                        cp.RecombineStep(
                            values=["recombine1", "recombine2"],
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="recombine_param",
                                    description="recombine desc",
                                    type="string",
                                )
                            ]
                        )
                    ],
                    referenced_group_label=None
                )
            ]
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "all-steps-scope"
        assert state["code"] == "all-steps-template"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        request_body = json.loads(request.content)
        variation = request_body["variations"][0]
        assert len(variation["steps"]) == 7
        # Verify all step types are present with correct request types
        step_types = [step["complianceStepTypeRequest"] for step in variation["steps"]]
        expected_types = [
            "FilterStepRequest",
            "BranchStepRequest",
            "CheckStepRequest",
            "GroupByStepRequest",
            "GroupFilterStepRequest",
            "PercentCheckStepRequest",
            "RecombineStepRequest"
        ]
        assert step_types == expected_types

    def test_create_minimal_template(self, respx_mock):
        respx_mock.post(
            "/api/api/compliance/templates/minimal-scope"
        ).mock(return_value=httpx.Response(200, json={}))
        # given a minimal compliance template (no optional fields)
        sut = cp.ComplianceTemplateResource(
            id="minimal-template",
            scope="minimal-scope",
            code="minimal-template",
            variations=[
                cp.ComplianceTemplateVariation(
                    label="Minimal Variation",
                    description="Minimal variation",
                    steps=[
                        cp.FilterStep(
                            label="Single-Filter",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="single_param",
                                    description="Single parameter",
                                    type="string",
                                )
                            ]
                        )
                    ],
                    referenced_group_label=None
                )
            ]
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "minimal-scope"
        assert state["code"] == "minimal-template"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        request_body = json.loads(request.content)
        assert request_body["code"] == "minimal-template"
        # description and tags should not be present (None values excluded)
        assert "description" not in request_body
        assert "tags" not in request_body

    def test_update_template_same_scope_code(self, respx_mock):
        respx_mock.put(
            "/api/api/compliance/templates/update-scope/update-template"
        ).mock(return_value=httpx.Response(200, json={}))
        # given a compliance template that needs updating
        sut = cp.ComplianceTemplateResource(
            id="update-template",
            scope="update-scope",
            code="update-template",
            description="Updated description",
            variations=[
                cp.ComplianceTemplateVariation(
                    label="Updated Variation",
                    description="Updated variation description",
                    steps=[
                        cp.FilterStep(
                            label="Updated-Filter",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="updated_param",
                                    description="Updated parameter",
                                    type="string",
                                )
                            ]
                        )
                    ],
                    referenced_group_label=None
                )
            ]
        )
        # and an old state with different content hash
        old_state = type("MockState", (), {
            "scope": "update-scope",
            "code": "update-template",
            "content_hash": "old_hash_value"
        })()
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is returned with new content hash
        assert state is not None
        assert state["scope"] == "update-scope"
        assert state["code"] == "update-template"
        assert state["content_hash"] != "old_hash_value"
        # and an update request was sent
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/api/api/compliance/templates/update-scope/update-template"

    def test_can_roundtrip_own_output(self):
        # given a compliance template
        sut = cp.ComplianceTemplateResource(
            id="no-change-template",
            scope="no-change-scope",
            code="no-change-template",
            variations=[
                cp.ComplianceTemplateVariation(
                    label="No Change Variation",
                    description="No change variation",
                    steps=[
                        cp.FilterStep(
                            label="No-Change-Filter",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="no_change_param",
                                    description="No change parameter",
                                    type="string",
                                )
                            ]
                        )
                    ],
                    referenced_group_label="something"
                )
            ]
        )
        # when we serialize it
        serialized = sut.model_dump(mode="json", exclude_none=True, by_alias=True)
        # then we can parse it back
        parsed = cp.ComplianceTemplateResource.model_validate(
            serialized,
            context={"style": "api", "id": "no-change-template"},
        )
        redumped = parsed.model_dump(mode="json", exclude_none=True, by_alias=True)
        assert redumped == serialized

    def test_update_template_no_change(self, respx_mock):
        # given a compliance template
        sut = cp.ComplianceTemplateResource(
            id="no-change-template",
            scope="no-change-scope",
            code="no-change-template",
            variations=[
                cp.ComplianceTemplateVariation(
                    label="No Change Variation",
                    description="No change variation",
                    steps=[
                        cp.FilterStep(
                            label="No-Change-Filter",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="no_change_param",
                                    description="No change parameter",
                                    type="string",
                                )
                            ]
                        )
                    ],
                    referenced_group_label=None
                )
            ]
        )
        # and an old state with the same content
        desired = sut.model_dump(mode="json", exclude_none=True, by_alias=True,
                                 exclude={"id", "scope"})
        sorted_desired = json.dumps(desired, sort_keys=True)
        current_hash = cp.sha256(sorted_desired.encode()).hexdigest()
        old_state = type("MockState", (), {
            "scope": "no-change-scope",
            "code": "no-change-template",
            "content_hash": current_hash
        })()
        # when we update it
        state = sut.update(self.client, old_state)
        # then no update is performed
        assert state is None
        # and no requests were made
        assert len(respx_mock.calls) == 0

    def test_update_template_different_scope_code(self, respx_mock):
        respx_mock.delete(
            "/api/api/compliance/templates/old-scope/old-template"
        ).mock(return_value=httpx.Response(200, json={}))
        respx_mock.post(
            "/api/api/compliance/templates/new-scope"
        ).mock(return_value=httpx.Response(200, json={}))
        # given a compliance template with different scope/code
        sut = cp.ComplianceTemplateResource(
            id="new-template",
            scope="new-scope",
            code="new-template",
            variations=[
                cp.ComplianceTemplateVariation(
                    label="New Variation",
                    description="New variation",
                    steps=[
                        cp.FilterStep(
                            label="New-Filter",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="new_param",
                                    description="New parameter",
                                    type="string",
                                )
                            ]
                        )
                    ],
                    referenced_group_label=None
                )
            ]
        )
        # and an old state with different scope/code
        old_state = SimpleNamespace(scope="old-scope", code="old-template", content_hash="old_hash")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the old template is deleted and new one is created
        assert state is not None
        assert state["scope"] == "new-scope"
        assert state["code"] == "new-template"
        assert "content_hash" in state
        # and both delete and create requests were sent
        assert len(respx_mock.calls) == 2
        delete_request = respx_mock.calls[0].request
        create_request = respx_mock.calls[1].request
        assert delete_request.method == "DELETE"
        assert delete_request.url.path == "/api/api/compliance/templates/old-scope/old-template"
        assert create_request.method == "POST"
        assert create_request.url.path == "/api/api/compliance/templates/new-scope"

    def test_delete_template(self, respx_mock):
        respx_mock.delete(
            "/api/api/compliance/templates/delete-scope/delete-template"
        ).mock(return_value=httpx.Response(200, json={}))
        # given an old state to delete
        old_state = type("MockState", (), {
            "scope": "delete-scope",
            "code": "delete-template"
        })()
        # when we delete it
        cp.ComplianceTemplateResource.delete(self.client, old_state)
        # then a delete request was sent
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/api/api/compliance/templates/delete-scope/delete-template"

    def test_read_template(self, respx_mock):
        # Mock response data
        mock_response_data = {
            "id": {"scope": "read-scope", "code": "read-template"},
            "code": "read-template",
            "description": "Template for reading",
            "variations": [{
                "label": "Read Variation",
                "description": "Variation for reading",
                "steps": []
            }],
            "links": [{"rel": "self", "href": "some-link"}],
            "version": {"effectiveFrom": "2023-01-01T00:00:00Z"}
        }
        respx_mock.get("/api/api/compliance/templates/read-scope/read-template").mock(
            return_value=httpx.Response(200, json=mock_response_data)
        )
        # given a compliance template resource
        sut = cp.ComplianceTemplateResource(
            id="read-template",
            scope="read-scope",
            code="read-template",
            variations=[]
        )
        # and an old state
        old_state = SimpleNamespace(scope="read-scope", code="read-template")
        # when we read it
        result = sut.read(self.client, old_state)
        # then the response is returned without links and version
        assert result["id"] == {"scope": "read-scope", "code": "read-template"}
        assert result["code"] == "read-template"
        assert "links" not in result
        assert "version" not in result
        # and a get request was sent
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == "/api/api/compliance/templates/read-scope/read-template"

    def test_deps_returns_empty_list(self):
        # given a compliance template resource
        sut = cp.ComplianceTemplateResource(
            id="deps-template",
            scope="deps-scope",
            code="deps-template",
            variations=[]
        )
        # when we get dependencies
        deps = sut.deps()
        # then an empty list is returned
        assert deps == []


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeComplianceTemplateRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_existing_template(self, respx_mock):
        # Mock response data
        mock_response_data = {
            "id": {"scope": "ref-scope", "code": "ref-template"},
            "code": "ref-template",
            "name": "Referenced Template"
        }
        respx_mock.get("/api/api/compliance/templates/ref-scope/ref-template").mock(
            return_value=httpx.Response(200, json=mock_response_data)
        )
        # given a compliance template reference
        sut = cp.ComplianceTemplateRef(
            id="ref-template",
            scope="ref-scope",
            code="ref-template"
        )
        # when we attach it
        result = sut.attach(self.client)
        # then the template data is returned
        assert result is not None
        assert result["id"] == {"scope": "ref-scope", "code": "ref-template"}
        assert result["code"] == "ref-template"
        assert result["name"] == "Referenced Template"

    def test_attach_non_existing_template(self, respx_mock):
        respx_mock.get("/api/api/compliance/templates/missing-scope/missing-template").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )
        # given a compliance template reference to non-existing template
        sut = cp.ComplianceTemplateRef(
            id="missing-template",
            scope="missing-scope",
            code="missing-template"
        )
        # when we attach it
        result = sut.attach(self.client)
        # then None is returned
        assert result is None

    def test_attach_server_error(self, respx_mock):
        respx_mock.get("/api/api/compliance/templates/error-scope/error-template").mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )
        # given a compliance template reference
        sut = cp.ComplianceTemplateRef(
            id="error-template",
            scope="error-scope",
            code="error-template"
        )
        # when we attach it and server returns error
        # then the exception is re-raised
        with pytest.raises(httpx.HTTPStatusError):
            sut.attach(self.client)


class DescribeComplianceParameters():

    def test_serialize_propkey_param(self):
        # given a property
        prop = cp.property.DefinitionRef(
            id="test-property",
            domain=cp.property.Domain.Compliance,
            scope="prop-scope",
            code="prop-code"
        )
        # and a parameter that uses it
        sut = cp.PropertyKeyComplianceParameter(
            value=prop
        )
        # when we serialize it
        ser = sut.model_dump(mode="json", exclude_none=True, by_alias=True)
        # then we get the property key format that the api expects
        assert ser == {
            "value": "Compliance/prop-scope/prop-code",
            "complianceParameterType": "PropertyKeyComplianceParameter"
        }

    def test_deserialize_propkey_param(self):
        # given a serialiized compliance param
        # with an embedded property reference
        prop = cp.property.DefinitionRef(
            id="test-property",
            domain=cp.property.Domain.Compliance,
            scope="prop-scope",
            code="prop-code"
        )
        ser = {
            "value": {"$ref": prop.id},
            "complianceParameterType": "PropertyKeyComplianceParameter"
        }
        # when we deserialize it
        param = cp.PropertyKeyComplianceParameter.model_validate(
            ser, context={
                "style": "api",
                "$refs": {
                    prop.id: prop
                }
            }
        )
        # then we get the property reference
        assert param.value.id == "test-property"
        assert param.value.scope == "prop-scope"
        assert param.value.code == "prop-code"

    def test_serialize_reflist_param(self):
        # given a reference list
        reflist = rl.ReferenceListRef(
            id="test-reflist",
            scope="reflist-scope",
            code="reflist-code"
        )
        # and a parameter that uses it
        sut = cp.DecimalListComplianceParameter(
            value=reflist
        )
        # when we serialize it
        ser = sut.model_dump(mode="json", exclude_none=True, by_alias=True)
        # then we get a resourceId for the list
        assert ser == {
            "value": {"scope": "reflist-scope", "code": "reflist-code"},
            "complianceParameterType": "DecimalListComplianceParameter"
        }

    def test_deserialize_reflist_param(self):
        # given a serialized compliance parameter
        # with an embedded reference list
        reflist = rl.ReferenceListRef(
            id="test-reflist",
            scope="reflist-scope",
            code="reflist-code"
        )
        ser = {
            "value": {"$ref": reflist.id},
            "complianceParameterType": "DecimalListComplianceParameter"
        }
        # when we deserialize it
        param = cp.DecimalListComplianceParameter.model_validate(
            ser, context={
                "style": "api",
                "$refs": {
                    reflist.id: reflist
                }
            }
        )
        # then we get the reference list
        assert param.value.id == "test-reflist"
        assert param.value.scope == "reflist-scope"
        assert param.value.code == "reflist-code"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeComplianceRuleResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create_simple_rule(self, respx_mock):
        respx_mock.post("/api/api/compliance/rules").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a simple compliance rule
        template_ref = cp.ComplianceTemplateRef(
            id="test-template",
            scope="test-scope",
            code="test-template"
        )
        sut = cp.ComplianceRuleResource(
            id="simple-rule",
            scope="rule-scope",
            code="simple-rule",
            name="Simple Compliance Rule",
            description="A simple compliance rule for testing",
            active=True,
            template_id=template_ref,
            variation="standard",
            portfolio_group_id=cp.ResourceId(scope="portfolio-scope", code="test-group"),
            parameters={
                "DecimalParam": cp.DecimalComplianceParameter(value=75.5),
                "StringParam": cp.StringComplianceParameter(value="test-string"),
                "PortfolioGroupParam": cp.PortfolioGroupIdComplianceParameter(
                    value=cp.ResourceId(scope="group-scope", code="group-code")
                )
            },
            properties=[]
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "rule-scope"
        assert state["code"] == "simple-rule"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/compliance/rules"
        request_body = json.loads(request.content)
        # and the request is api format with id as an object
        # and templateId as a resourceId
        expected_body = {
            "id": {"scope": "rule-scope", "code": "simple-rule"},
            "name": "Simple Compliance Rule",
            "description": "A simple compliance rule for testing",
            "active": True,
            "templateId": {"scope": "test-scope", "code": "test-template"},
            "variation": "standard",
            "portfolioGroupId": {"scope": "portfolio-scope", "code": "test-group"},
            "parameters": {
                "DecimalParam": {
                    "value": 75.5,
                    "complianceParameterType": "DecimalComplianceParameter"
                },
                "StringParam": {
                    "value": "test-string",
                    "complianceParameterType": "StringComplianceParameter"
                },
                "PortfolioGroupParam": {
                    "value": {"scope": "group-scope", "code": "group-code"},
                    "complianceParameterType": "PortfolioGroupIdComplianceParameter"
                }
            },
            "properties": {}
        }
        assert request_body == expected_body

    def test_create_rule_with_template_resource(self, respx_mock):
        respx_mock.post("/api/api/compliance/rules").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a compliance rule with template resource dependency
        template = cp.ComplianceTemplateResource(
            id="template-resource",
            scope="template-scope",
            code="template-resource",
            variations=[
                cp.ComplianceTemplateVariation(
                    label="Test Variation",
                    description="Test variation",
                    steps=[
                        cp.FilterStep(
                            label="Test Filter",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="test_param",
                                    description="Test parameter",
                                    type="string"
                                )
                            ]
                        )
                    ],
                    referenced_group_label=None
                )
            ]
        )
        sut = cp.ComplianceRuleResource(
            id="rule-with-template",
            scope="rule-scope",
            code="rule-with-template",
            name="Rule with Template Resource",
            active=True,
            template_id=template,
            variation="Test Variation",
            portfolio_group_id=cp.ResourceId(scope="portfolio-scope", code="test-group"),
            parameters={
                "DecimalValue": cp.DecimalComplianceParameter(value=100.0)
            },
            properties=[]
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "rule-scope"
        assert state["code"] == "rule-with-template"
        assert "content_hash" in state
        # and the template is included in dependencies
        deps = sut.deps()
        assert len(deps) == 1
        assert deps[0] == template

    def test_create_rule_with_property(self, respx_mock):
        respx_mock.post("/api/api/compliance/rules").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a compliance rule with a property
        template_ref = cp.ComplianceTemplateRef(
            id="property-template",
            scope="property-scope",
            code="property-template"
        )
        # Create a simple property definition reference
        property_def_ref = cp.property.DefinitionRef(
            id="test-property",
            domain=cp.property.Domain.Compliance,
            scope="test-scope",
            code="test-property"
        )
        sut = cp.ComplianceRuleResource(
            id="rule-with-property",
            scope="rule-scope",
            code="rule-with-property",
            name="Rule with Property",
            description="A compliance rule with a property",
            active=True,
            template_id=template_ref,
            variation="standard",
            portfolio_group_id=cp.ResourceId(scope="portfolio-scope", code="test-group"),
            parameters={
                "StringParam": cp.StringComplianceParameter(value="property-test")
            },
            properties=[
                cp.PropertyListItem(
                    key=property_def_ref,
                    value=cp.PropertyValue(label_value="custom-value")
                )
            ]
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "rule-scope"
        assert state["code"] == "rule-with-property"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/compliance/rules"
        request_body = json.loads(request.content)
        expected_body = {
            "id": {"scope": "rule-scope", "code": "rule-with-property"},
            "name": "Rule with Property",
            "description": "A compliance rule with a property",
            "active": True,
            "templateId": {"scope": "property-scope", "code": "property-template"},
            "variation": "standard",
            "portfolioGroupId": {"scope": "portfolio-scope", "code": "test-group"},
            "parameters": {
                "StringParam": {
                    "value": "property-test",
                    "complianceParameterType": "StringComplianceParameter"
                }
            },
            "properties": {
                "Compliance/test-scope/test-property": {
                    "key": "Compliance/test-scope/test-property",
                    "value": {
                        "labelValue": "custom-value"
                    }
                }
            }
        }
        assert request_body == expected_body

    def test_create_rule_with_reflist(self, respx_mock):
        respx_mock.post("/api/api/compliance/rules").mock(
            return_value=httpx.Response(200, json={})
        )
        reflist_ref = rl.ReferenceListRef(
            id="test-reflist",
            scope="reflist-scope",
            code="reflist-code"
        )
        # given a simple compliance rule
        template_ref = cp.ComplianceTemplateRef(
            id="test-template",
            scope="test-scope",
            code="test-template"
        )
        sut = cp.ComplianceRuleResource(
            id="simple-rule",
            scope="rule-scope",
            code="simple-rule",
            name="Simple Compliance Rule",
            description="A simple compliance rule for testing",
            active=True,
            template_id=template_ref,
            variation="standard",
            portfolio_group_id=cp.ResourceId(scope="portfolio-scope", code="test-group"),
            parameters={
                "DecimalListParam": cp.DecimalListComplianceParameter(value=reflist_ref)
            },
            properties=[]
        )
        # when we create it
        state = sut.create(self.client)
        # then the state is returned with content hash
        assert state["scope"] == "rule-scope"
        assert state["code"] == "simple-rule"
        assert "content_hash" in state
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/compliance/rules"
        request_body = json.loads(request.content)
        # and the request is api format with id as an object
        # and templateId as a resourceId
        expected_body = {
            "id": {"scope": "rule-scope", "code": "simple-rule"},
            "name": "Simple Compliance Rule",
            "description": "A simple compliance rule for testing",
            "active": True,
            "templateId": {"scope": "test-scope", "code": "test-template"},
            "variation": "standard",
            "portfolioGroupId": {"scope": "portfolio-scope", "code": "test-group"},
            "parameters": {
                "DecimalListParam": {
                    "value": {"scope": "reflist-scope", "code": "reflist-code"},
                    "complianceParameterType": "DecimalListComplianceParameter"
                },
            },
            "properties": {}
        }
        assert request_body == expected_body

    def test_can_roundtrip(self):
        # given a compliance rule
        template_ref = cp.ComplianceTemplateRef(
            id="update-template",
            scope="template-scope",
            code="update-template"
        )
        sut = cp.ComplianceRuleResource(
            id="update-rule",
            scope="update-scope",
            code="update-rule",
            name="Updated Rule Name",
            description="Updated description",
            active=False,
            template_id=template_ref,
            variation="updated",
            portfolio_group_id=cp.ResourceId(scope="updated-scope", code="updated-group"),
            parameters={
                "UpdatedParam": cp.StringComplianceParameter(value="updated-value")
            },
            properties=[]
        )
        # when we serialise to api format
        serialized = sut.model_dump(mode="json", exclude_none=True, by_alias=True,
                                   exclude={"id", "scope", "code"})
        modified = serialized.copy()
        modified["templateId"] = {"$ref": "update-template"}
        deserialized = cp.ComplianceRuleResource.model_validate(
            modified,
            context={
                "style": "api",
                "id": "update-rule",
                "$refs": {"update-template": template_ref}
            }
        )
        reserialized = deserialized.model_dump(mode="json", exclude_none=True, by_alias=True,
            exclude={"id", "scope", "code"}
        )
        assert serialized == reserialized

    def test_roundtrip_with_property(self):
        # given a compliance rule with a property
        template_ref = cp.ComplianceTemplateRef(
            id="property-template",
            scope="property-scope",
            code="property-template"
        )
        # Create a simple property definition reference
        property_def_ref = cp.property.DefinitionRef(
            id="test-property",
            domain=cp.property.Domain.Compliance,
            scope="test-scope",
            code="test-property"
        )
        sut = cp.ComplianceRuleResource(
            id="rule-with-property",
            scope="rule-scope",
            code="rule-with-property",
            name="Rule with Property",
            description="A compliance rule with a property",
            active=True,
            template_id=template_ref,
            variation="standard",
            portfolio_group_id=cp.ResourceId(scope="portfolio-scope", code="test-group"),
            parameters={
                "StringParam": cp.StringComplianceParameter(value="property-test"),
                "PropParam": cp.PropertyKeyComplianceParameter(
                    value=property_def_ref
                )
            },
            properties=[
                cp.PropertyListItem(
                    key=property_def_ref,
                    value=cp.PropertyValue(label_value="custom-value")
                )
            ]
        )
        # when we serialise to api format
        serialized = sut.model_dump(mode="json", exclude_none=True, by_alias=True,
                                   exclude={"id", "scope", "code"})
        # the top level property is serialized
        assert serialized["properties"]["Compliance/test-scope/test-property"]["key"] == \
                "Compliance/test-scope/test-property"
        assert serialized["properties"]["Compliance/test-scope/test-property"].keys() == {"key", "value"}
        # and the property in a parameter is serialized
        assert serialized["parameters"]["PropParam"]["value"] == "Compliance/test-scope/test-property"
        # and replace the template with a ref
        modified = copy.deepcopy(serialized)
        modified["templateId"] = {"$ref": "update-template"}
        # and replace the property.key with a ref
        test_prop = serialized["properties"]["Compliance/test-scope/test-property"].copy()
        test_prop["key"] = {"$ref": "test-property"}
        modified["properties"] = {"Compliance/test-scope/test-property": test_prop}
        # and replace the parameter prop
        test_parm = serialized["parameters"]["PropParam"].copy()
        test_parm["value"] = {"$ref": "test-property"}
        modified["parameters"]["PropParam"] = test_parm
        # and reparse it
        deserialized = cp.ComplianceRuleResource.model_validate(
            modified,
            context={
                "style": "api",
                "id": "update-rule",
                "$refs": {
                    "update-template": template_ref,
                    "test-property": property_def_ref
                }
            }
        )
        assert deserialized.properties[0].key.id == \
                "test-property"
        assert deserialized.parameters
        assert isinstance(deserialized.parameters["PropParam"], cp.PropertyKeyComplianceParameter)
        assert deserialized.parameters["PropParam"].value.id == "test-property"
        # then the api format generated matches the  original
        reserialized = deserialized.model_dump(mode="json", exclude_none=True, by_alias=True,
            exclude={"id", "scope", "code"}
        )
        assert serialized["properties"]["Compliance/test-scope/test-property"]["key"] == \
                "Compliance/test-scope/test-property"
        assert reserialized["properties"]["Compliance/test-scope/test-property"]["key"] == \
                "Compliance/test-scope/test-property"
        assert reserialized["parameters"]["PropParam"]["value"] == "Compliance/test-scope/test-property"
        assert serialized["parameters"]["PropParam"]["value"] == "Compliance/test-scope/test-property"
        assert serialized == reserialized

    def test_update_rule_same_scope_code(self, respx_mock):
        respx_mock.post("/api/api/compliance/rules").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a compliance rule that needs updating
        template_ref = cp.ComplianceTemplateRef(
            id="update-template",
            scope="template-scope",
            code="update-template"
        )
        sut = cp.ComplianceRuleResource(
            id="update-rule",
            scope="update-scope",
            code="update-rule",
            name="Updated Rule Name",
            description="Updated description",
            active=False,
            template_id=template_ref,
            variation="updated",
            portfolio_group_id=cp.ResourceId(scope="updated-scope", code="updated-group"),
            parameters={
                "UpdatedParam": cp.StringComplianceParameter(value="updated-value")
            },
            properties=[]
        )
        # and an old state with different content hash
        old_state = SimpleNamespace(
            scope="update-scope",
            code="update-rule",
            content_hash="old_hash_value"
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is returned with new content hash
        assert state is not None
        assert state["scope"] == "update-scope"
        assert state["code"] == "update-rule"
        assert state["content_hash"] != "old_hash_value"
        # and an update request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/api/api/compliance/rules"

    def test_update_rule_no_change(self, respx_mock):
        # given a compliance rule
        template_ref = cp.ComplianceTemplateRef(
            id="no-change-template",
            scope="no-change-scope",
            code="no-change-template"
        )
        sut = cp.ComplianceRuleResource(
            id="no-change-rule",
            scope="no-change-scope",
            code="no-change-rule",
            name="No Change Rule",
            active=True,
            template_id=template_ref,
            variation="standard",
            portfolio_group_id=cp.ResourceId(scope="no-change-scope", code="no-change-group"),
            properties=[]
        )
        # and an old state with the same content
        desired = sut.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={
            "id", "scope", "code"}
        )
        sorted_desired = json.dumps(desired, sort_keys=True)
        current_hash = cp.sha256(sorted_desired.encode()).hexdigest()
        old_state = SimpleNamespace(
            scope="no-change-scope",
            code="no-change-rule",
            content_hash=current_hash
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then no update is performed
        assert state is None
        # and no requests were made
        assert len(respx_mock.calls) == 0

    def test_update_rule_different_scope_code(self, respx_mock):
        respx_mock.delete("/api/api/compliance/rules/old-scope/old-rule").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/api/api/compliance/rules").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a compliance rule with different scope/code
        template_ref = cp.ComplianceTemplateRef(
            id="new-template",
            scope="new-scope",
            code="new-template"
        )
        sut = cp.ComplianceRuleResource(
            id="new-rule",
            scope="new-scope",
            code="new-rule",
            name="New Rule",
            active=True,
            template_id=template_ref,
            variation="new",
            portfolio_group_id=cp.ResourceId(scope="new-scope", code="new-group"),
            properties=[]
        )
        # and an old state with different scope/code
        old_state = SimpleNamespace(
            scope="old-scope",
            code="old-rule",
            content_hash="old_hash"
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then the old rule is deleted and new one is created
        assert state is not None
        assert state["scope"] == "new-scope"
        assert state["code"] == "new-rule"
        assert "content_hash" in state
        # and both delete and create requests were sent
        assert len(respx_mock.calls) == 2
        delete_request = respx_mock.calls[0].request
        create_request = respx_mock.calls[1].request
        assert delete_request.method == "DELETE"
        assert delete_request.url.path == "/api/api/compliance/rules/old-scope/old-rule"
        assert create_request.method == "POST"
        assert create_request.url.path == "/api/api/compliance/rules"

    def test_delete_rule(self, respx_mock):
        respx_mock.delete("/api/api/compliance/rules/delete-scope/delete-rule").mock(
            return_value=httpx.Response(200, json={})
        )
        # given an old state to delete
        old_state = SimpleNamespace(
            scope="delete-scope",
            code="delete-rule"
        )
        # when we delete it
        cp.ComplianceRuleResource.delete(self.client, old_state)
        # then a delete request was sent
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/api/api/compliance/rules/delete-scope/delete-rule"

    def test_read_rule(self, respx_mock):
        # Mock response data
        mock_response_data = {
            "id": {"scope": "read-scope", "code": "read-rule"},
            "code": "read-rule",
            "name": "Read Rule",
            "description": "Rule for reading",
            "active": True,
            "templateId": {"scope": "template-scope", "code": "template-code"},
            "variation": "standard",
            "portfolio_group_id": {"scope": "group-scope", "code": "group-code"},
            "parameters": {
                "TestParam": {
                    "value": "test-value",
                    "complianceParameterType": "StringComplianceParameter"
                }
            },
            "links": [{"rel": "self", "href": "some-link"}],
            "version": {"effectiveFrom": "2023-01-01T00:00:00Z"}
        }
        respx_mock.get("/api/api/compliance/rules/read-scope/read-rule").mock(
            return_value=httpx.Response(200, json=mock_response_data)
        )
        # given a compliance rule resource
        template_ref = cp.ComplianceTemplateRef(
            id="template-code",
            scope="template-scope",
            code="template-code"
        )
        sut = cp.ComplianceRuleResource(
            id="read-rule",
            scope="read-scope",
            code="read-rule",
            name="Read Rule",
            active=True,
            template_id=template_ref,
            variation="standard",
            portfolio_group_id=cp.ResourceId(scope="group-scope", code="group-code"),
            properties=[]
        )
        # and an old state
        old_state = SimpleNamespace(scope="read-scope", code="read-rule")
        # when we read it
        result = sut.read(self.client, old_state)
        # then the response is returned without links and version
        assert result["id"] == {"scope": "read-scope", "code": "read-rule"}
        assert result["code"] == "read-rule"
        assert result["name"] == "Read Rule"
        assert "links" not in result
        assert "version" not in result
        # and a get request was sent
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == "/api/api/compliance/rules/read-scope/read-rule"

    def test_deps_compliance_rule(self):
        # given a compliance rule with property references
        template_ref = cp.ComplianceTemplateRef(
            id="template-ref-id",
            scope="template-scope",
            code="template-code"
        )
        property_ref = cp.property.DefinitionRef(
            id="property-ref-id",
            domain=cp.property.Domain.Compliance,
            scope="property-scope",
            code="property-code"
        )
        sut = cp.ComplianceRuleResource(
            id="dump-rule-with-props",
            scope="dump-scope",
            code="dump-rule-with-props",
            name="Dump Rule with Properties",
            active=True,
            template_id=template_ref,
            variation="dump-variation",
            portfolio_group_id=cp.ResourceId(scope="portfolio-scope", code="portfolio-code"),
            properties=[
                cp.PropertyListItem(
                    key=property_ref,
                    value=cp.PropertyValue(label_value="property-value")
                )
            ]
        )
        # when we get dependencies
        deps = sut.deps()
        # then the template and properties are returned
        assert deps == [template_ref, property_ref]


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeComplianceRuleRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_existing_rule(self, respx_mock):
        # Mock response data
        mock_response_data = {
            "id": {"scope": "ref-scope", "code": "ref-rule"},
            "code": "ref-rule",
            "name": "Referenced Rule",
            "active": True,
            "templateId": {"scope": "template-scope", "code": "template-code"}
        }
        respx_mock.get("/api/api/compliance/rules/ref-scope/ref-rule").mock(
            return_value=httpx.Response(200, json=mock_response_data)
        )
        # given a compliance rule reference
        sut = cp.ComplianceRuleRef(
            id="ref-rule",
            scope="ref-scope",
            code="ref-rule"
        )
        # when we attach it
        result = sut.attach(self.client)
        # then the rule data is returned
        assert result is not None
        assert result["id"] == {"scope": "ref-scope", "code": "ref-rule"}
        assert result["code"] == "ref-rule"
        assert result["name"] == "Referenced Rule"

    def test_attach_non_existing_rule(self, respx_mock):
        respx_mock.get("/api/api/compliance/rules/missing-scope/missing-rule").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )
        # given a compliance rule reference to non-existing rule
        sut = cp.ComplianceRuleRef(
            id="missing-rule",
            scope="missing-scope",
            code="missing-rule"
        )
        # when we attach it
        result = sut.attach(self.client)
        # then None is returned
        assert result is None

    def test_attach_server_error(self, respx_mock):
        respx_mock.get("/api/api/compliance/rules/error-scope/error-rule").mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )
        # given a compliance rule reference
        sut = cp.ComplianceRuleRef(
            id="error-rule",
            scope="error-scope",
            code="error-rule"
        )
        # when we attach it and server returns error
        # then the exception is re-raised
        with pytest.raises(httpx.HTTPStatusError):
            sut.attach(self.client)


class DescribeComplianceTemplateResourceDumpUndump:
    def test_dump_simple_template(self):
        # given a simple compliance template
        sut = cp.ComplianceTemplateResource(
            id="dump-template",
            scope="dump-scope",
            code="dump-template",
            description="Template for dump testing",
            tags=["dump", "test"],
            variations=[
                cp.ComplianceTemplateVariation(
                    label="Dump Variation",
                    description="Variation for dump testing",
                    steps=[
                        cp.FilterStep(
                            label="Dump-Filter",
                            parameters=[
                                cp.ComplianceTemplateParameter(
                                    name="dump_param",
                                    description="Dump parameter",
                                    type="string"
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then all fields are included (no excludes)
        expected = {
            "scope": "dump-scope",
            "code": "dump-template",
            "description": "Template for dump testing",
            "tags": ["dump", "test"],
            "variations": [
                {
                    "label": "Dump Variation",
                    "description": "Variation for dump testing",
                    "steps": [
                        {
                            "label": "Dump-Filter",
                            "parameters": [
                                {
                                    "name": "dump_param",
                                    "description": "Dump parameter",
                                    "type": "string"
                                }
                            ],
                            "complianceStepTypeRequest": "FilterStepRequest"
                        }
                    ]
                }
            ]
        }
        assert result == expected

    def test_undump_simple_template(self):
        # given dump data
        data = {
            "scope": "undump-scope",
            "code": "undump-template",
            "description": "Template for undump testing",
            "tags": ["undump", "test"],
            "variations": [
                {
                    "label": "Undump Variation",
                    "description": "Variation for undump testing",
                    "steps": [
                        {
                            "label": "Undump-Filter",
                            "parameters": [
                                {
                                    "name": "undump_param",
                                    "description": "Undump parameter",
                                    "type": "string"
                                }
                            ],
                            "complianceStepTypeRequest": "FilterStepRequest"
                        }
                    ]
                }
            ]
        }
        # when we undump it with id from context
        result = cp.ComplianceTemplateResource.model_validate(
            data, context={"style": "dump", "id": "template_id"}
        )
        # then it's correctly populated including id from context
        assert result.id == "template_id"
        assert result.scope == "undump-scope"
        assert result.code == "undump-template"
        assert result.description == "Template for undump testing"
        assert result.tags == ["undump", "test"]
        assert len(result.variations) == 1
        assert result.variations[0].label == "Undump Variation"


class DescribeComplianceRuleResourceDumpUndump:
    def test_dump_simple_rule(self):
        # given a simple compliance rule with template ref
        template_ref = cp.ComplianceTemplateRef(
            id="template-ref-id",
            scope="template-scope",
            code="template-code"
        )
        sut = cp.ComplianceRuleResource(
            id="dump-rule",
            scope="dump-scope",
            code="dump-rule",
            name="Dump Rule",
            description="Rule for dump testing",
            active=True,
            template_id=template_ref,
            variation="dump-variation",
            portfolio_group_id=cp.ResourceId(scope="portfolio-scope", code="portfolio-code"),
            parameters={
                "DumpParam": cp.StringComplianceParameter(value="dump-value")
            },
            properties=[]
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then all fields are included and template is $ref
        expected = {
            "id": "dump-rule",
            "scope": "dump-scope",
            "code": "dump-rule",
            "name": "Dump Rule",
            "description": "Rule for dump testing",
            "active": True,
            "templateId": {"$ref": "template-ref-id"},
            "variation": "dump-variation",
            "portfolioGroupId": {"scope": "portfolio-scope", "code": "portfolio-code"},
            "parameters": {
                "DumpParam": {
                    "value": "dump-value",
                    "complianceParameterType": "StringComplianceParameter"
                }
            },
            "properties": []
        }
        assert result == expected

    def test_dump_rule_with_property_refs(self):
        # given a compliance rule with property references
        template_ref = cp.ComplianceTemplateRef(
            id="template-ref-id",
            scope="template-scope",
            code="template-code"
        )
        property_ref = cp.property.DefinitionRef(
            id="property-ref-id",
            domain=cp.property.Domain.Compliance,
            scope="property-scope",
            code="property-code"
        )
        sut = cp.ComplianceRuleResource(
            id="dump-rule-with-props",
            scope="dump-scope",
            code="dump-rule-with-props",
            name="Dump Rule with Properties",
            active=True,
            template_id=template_ref,
            variation="dump-variation",
            portfolio_group_id=cp.ResourceId(scope="portfolio-scope", code="portfolio-code"),
            properties=[
                cp.PropertyListItem(
                    key=property_ref,
                    value=cp.PropertyValue(label_value="property-value")
                )
            ]
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then properties include property_definition as $ref
        assert result["templateId"] == {"$ref": "template-ref-id"}
        assert len(result["properties"]) == 1
        prop_item = result["properties"][0]
        assert prop_item["key"] == {"$ref": "property-ref-id"}
        assert prop_item["value"]["labelValue"] == "property-value"

    def test_undump_simple_rule(self):
        # given dump data with template $ref
        data = {
            "scope": "undump-scope",
            "code": "undump-rule",
            "name": "Undump Rule",
            "description": "Rule for undump testing",
            "active": False,
            "templateId": {"$ref": "template-ref-id"},
            "variation": "undump-variation",
            "portfolioGroupId": {"scope": "portfolio-scope", "code": "portfolio-code"},
            "parameters": {
                "UndumpParam": {
                    "value": "undump-value",
                    "complianceParameterType": "StringComplianceParameter"
                }
            },
            "properties": []
        }
        # and template ref in context
        template_ref = cp.ComplianceTemplateRef(
            id="template-ref-id",
            scope="template-scope",
            code="template-code"
        )
        refs_dict = {"template-ref-id": template_ref}
        # when we undump it
        result = cp.ComplianceRuleResource.model_validate(
            data, context={"style": "dump", "$refs": refs_dict, "id": "rule_id"}
        )
        # then it's correctly populated including resolved template ref
        assert result.id == "rule_id"
        assert result.scope == "undump-scope"
        assert result.code == "undump-rule"
        assert result.name == "Undump Rule"
        assert result.active is False
        assert result.template_id == template_ref
        assert result.variation == "undump-variation"

    def test_undump_rule_with_property_refs(self):
        # given dump data with property $refs
        data = {
            "scope": "undump-scope",
            "code": "undump-rule-with-props",
            "name": "Undump Rule with Properties",
            "active": True,
            "templateId": {"$ref": "template-ref-id"},
            "variation": "undump-variation",
            "portfolioGroupId": {"scope": "portfolio-scope", "code": "portfolio-code"},
            "properties": [
                {
                    "key": {"$ref": "property-ref-id"},
                    "value": {"labelValue": "undump-property-value"}
                }
            ]
        }
        # and refs in context
        template_ref = cp.ComplianceTemplateRef(
            id="template-ref-id",
            scope="template-scope",
            code="template-code"
        )
        property_ref = cp.property.DefinitionRef(
            id="property-ref-id",
            domain=cp.property.Domain.Compliance,
            scope="property-scope",
            code="property-code"
        )
        refs_dict = {
            "template-ref-id": template_ref,
            "property-ref-id": property_ref
        }
        # when we undump it
        result = cp.ComplianceRuleResource.model_validate(
            data, context={"style": "dump", "$refs": refs_dict, "id": "rule_id"}
        )
        # then properties are correctly resolved
        assert result.id == "rule_id"
        assert result.template_id == template_ref
        assert len(result.properties) == 1
        prop_item = result.properties[0]
        assert prop_item.key == property_ref
        assert prop_item.value.label_value == "undump-property-value"
