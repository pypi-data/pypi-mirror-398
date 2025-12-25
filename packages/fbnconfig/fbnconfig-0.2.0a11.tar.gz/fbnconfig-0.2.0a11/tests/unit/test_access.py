import json
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import access

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.read()
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribePolicyRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @staticmethod
    def test_scope_default():
        # when scope is omitted
        sut = access.PolicyRef(id="one", code="cd")
        # then it uses "default"
        assert sut.scope == "default"

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/access/api/policies/pol1?scope=sc1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = access.PolicyRef(id="one", scope="sc1", code="pol1")
        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/access/api/policies/pol1?scope=sc1").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        sut = access.PolicyRef(id="one", scope="sc1", code="pol1")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Policy sc1/pol1 not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/access/api/policies/pol1?scope=sc1").mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        sut = access.PolicyRef(id="one", scope="sc1", code="pol1")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribePolicy:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def stock_policy_resource(self):
        # uses new style selector definition: List[Selector]
        return access.PolicyResource(
            id="policy1",
            code="a_policy",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.IdSelector(
                    name="banjo",
                    description="whatever",
                    identifier={"scope": "w", "code": "y"},
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )

    def test_create(self, respx_mock):
        respx_mock.post("/access/api/policies").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # given no policies exist yet
        # when we create one
        sut = access.PolicyResource(
            id="policy1",
            code="a_policy",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.IdSelector(
                    name="banjo",
                    description="whatever",
                    identifier={"scope": "w", "code": "y"},
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )
        state = sut.create(client)
        # then the state is returned
        assert state["id"] == "policy1"
        assert state["code"] == "a_policy"
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/policies"
        assert json.loads(request.content) == {
            "applications": ["lusid"],
            "code": "a_policy",
            "description": "policy description",
            "grant": "Allow",
            "selectors": [
                {
                    "idSelectorDefinition": {
                        "actions": [{"activity": "execute", "entity": "Feature", "scope": "actscope"}],
                        "description": "whatever",
                        "identifier": {"code": "y", "scope": "w"},
                        "name": "banjo",
                    }
                }
            ],
            "when": {"activate": "2024-08-31T18:00:00.0000000+00:00"},
        }

    def test_parse_api_format(self):
        # given an api format as returned by /access/api/policy
        remote = {
            "applications": ["lusid"],
            "id": {
                "code": "a_policy",
                "scope": "a_scope",
            },
            "description": "policy description",
            "grant": "Allow",
            "selectors": [
                {
                    "idSelectorDefinition": {
                        "actions": [{"activity": "execute", "entity": "Feature", "scope": "actscope"}],
                        "description": "whatever",
                        "identifier": {"code": "y", "scope": "w"},
                        "name": "banjo",
                    }
                }
            ],
            "when": {"activate": "2024-08-31T18:00:00.0000000+00:00"},
        }
        # when we push it through the deserialization
        converted = access.PolicyResource.model_validate(remote, context={"id": "res123"})
        # then
        assert converted.id == "res123"  # the resource id is from the context
        assert converted.applications == ["lusid"]
        assert converted.scope == "a_scope"  # scope and code get lifted to the top level
        assert converted.code == "a_policy"
        assert type(converted.selectors[0]).__name__ == "IdSelector"  # selector type inferred
        assert converted.selectors[0].type_name == "idSelectorDefinition"
        assert converted.when.activate == "2024-08-31T18:00:00.0000000+00:00"

    def test_dump_policy_resource(self):
        # given a policy resource
        sut = access.PolicyResource(
            id="dump-policy",
            code="DumpPolicy",
            description="A test policy for dumping",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.IdSelector(
                    name="test-selector",
                    description="Test ID selector",
                    identifier={"scope": "test-scope", "code": "test-code"},
                    actions=[access.ActionId(scope="test", activity="execute", entity="Feature")],
                )
            ],
        )
        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )
        # then all fields are included with proper aliases
        expected = {
            "code": "DumpPolicy",
            "description": "A test policy for dumping",
            "applications": ["lusid"],
            "grant": "Allow",
            "selectors": [
                {
                    "typeName": "idSelectorDefinition",
                    "identifier": {"scope": "test-scope", "code": "test-code"},
                    "actions": [{"scope": "test", "activity": "execute", "entity": "Feature"}],
                    "name": "test-selector",
                    "description": "Test ID selector",
                }
            ],
            "when": {"activate": "2024-08-31T18:00:00.0000000+00:00"},
        }
        assert result == expected

    def test_undump_policy_resource(self):
        # given dumped policy data
        data = {
            "code": "UndumpPolicy",
            "description": "A test policy for undumping",
            "applications": ["lusid"],
            "grant": "Allow",
            "selectors": [
                {
                    "typeName": "idSelectorDefinition",
                    "identifier": {"scope": "undump-scope", "code": "undump-code"},
                    "actions": [{"scope": "undump", "activity": "read", "entity": "Portfolio"}],
                    "name": "undump-selector",
                    "description": "Undump ID selector",
                }
            ],
            "when": {"activate": "2024-12-01T00:00:00.0000000+00:00"},
        }
        # when we undump it
        result = access.PolicyResource.model_validate(data, context={
            "style": "dump", "id": "undump-policy"
        })
        # then the resource Id is extracted from the context
        assert result.id == "undump-policy"
        assert result.code == "UndumpPolicy"
        # and the selector has the right type
        assert len(result.selectors) == 1
        assert isinstance(result.selectors[0], access.IdSelector)
        assert result.selectors[0].type_name == "idSelectorDefinition"
        assert result.when.activate == "2024-12-01T00:00:00.0000000+00:00"

    def test_create_matchall_selector(self, respx_mock):
        respx_mock.post("/access/api/policies").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # given no policies exist yet
        # when we create one with a matchall selector
        sut = access.PolicyResource(
            id="policy1",
            code="a_policy",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.MatchAllSelector(
                    name="banjo",
                    description="whatever",
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )
        state = sut.create(client)
        # then the state is returned
        assert state["id"] == "policy1"
        assert state["code"] == "a_policy"
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/policies"
        assert json.loads(request.content) == {
            "applications": ["lusid"],
            "code": "a_policy",
            "description": "policy description",
            "grant": "Allow",
            "selectors": [
                {
                    "matchAllSelectorDefinition": {
                        "actions": [{"activity": "execute", "entity": "Feature", "scope": "actscope"}],
                        "description": "whatever",
                        "name": "banjo",
                    }
                }
            ],
            "when": {"activate": "2024-08-31T18:00:00.0000000+00:00"},
        }

    def test_create_metadata_selector(self, respx_mock):
        respx_mock.post("/access/api/policies").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # given no policies exist yet
        # when we create one with a metadata selector
        sut = access.PolicyResource(
            id="policy1",
            code="a_policy",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.MetadataSelector(
                    name="banjo",
                    description="whatever",
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                    expressions=[
                        access.MetadataExpression(
                            metadata_key="foo", operator="Equals", text_value="bingo"
                        )
                    ],
                )
            ],
        )
        state = sut.create(client)
        # then the state is returned
        assert state["id"] == "policy1"
        assert state["code"] == "a_policy"
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/policies"
        assert json.loads(request.content) == {
            "applications": ["lusid"],
            "code": "a_policy",
            "description": "policy description",
            "grant": "Allow",
            "selectors": [
                {
                    "metadataSelectorDefinition": {
                        "actions": [{"activity": "execute", "entity": "Feature", "scope": "actscope"}],
                        "description": "whatever",
                        "name": "banjo",
                        "expressions": [
                            {"metadataKey": "foo", "operator": "Equals", "textValue": "bingo"}
                        ],
                    }
                }
            ],
            "when": {"activate": "2024-08-31T18:00:00.0000000+00:00"},
        }

    def test_create_policy_selector(self, respx_mock):
        respx_mock.post("/access/api/policies").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # given no policies exist yet
        # when we create one with a policy selector and a nested matchall
        inner_selector = access.MatchAllSelector(
            name="banjo",
            description="whatever",
            actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
        )
        sut = access.PolicyResource(
            id="policy1",
            code="a_policy",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.PolicySelector(
                    name="banjo",
                    description="whatever",
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                    identity_restriction={"id": "value"},
                    restriction_selectors=[inner_selector],
                )
            ],
        )
        state = sut.create(client)
        # then the state is returned
        assert state["id"] == "policy1"
        assert state["code"] == "a_policy"
        # and a create request was sent including the inner selector
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/policies"
        assert json.loads(request.content) == {
            "applications": ["lusid"],
            "code": "a_policy",
            "description": "policy description",
            "grant": "Allow",
            "selectors": [
                {
                    "policySelectorDefinition": {
                        "actions": [{"activity": "execute", "entity": "Feature", "scope": "actscope"}],
                        "description": "whatever",
                        "name": "banjo",
                        "identityRestriction": {"id": "value"},
                        "restrictionSelectors": [
                            {
                                "matchAllSelectorDefinition": {
                                    "actions": [
                                        {"activity": "execute", "entity": "Feature", "scope": "actscope"}
                                    ],
                                    "description": "whatever",
                                    "name": "banjo",
                                }
                            }
                        ],
                    }
                }
            ],
            "when": {"activate": "2024-08-31T18:00:00.0000000+00:00"},
        }

    @pytest.fixture
    def read_policy_response(self):
        return {
            "applications": ["lusid"],
            "id": {
                "code": "a_policy_code",
                "scope": "default",
            },  # get returns an ID where post takes a code only
            "description": "policy description",
            "grant": "Allow",
            "selectors": [
                {
                    "idSelectorDefinition": {
                        "actions": [{"activity": "execute", "entity": "Feature", "scope": "actscope"}],
                        "description": "whatever",
                        "identifier": {"code": "y", "scope": "w"},
                        "name": "banjo",
                    }
                }
            ],
            "when": {
                "activate": "2024-08-31T18:00:00.0000000+00:00",
                "deactivate": "99999-12-31T18:00:00.0000000+00:00",
            },
            "links": {},
        }

    def test_update_no_changes(self, respx_mock, read_policy_response):
        # given the policy exists
        respx_mock.get("/access/api/policies/a_policy_code").mock(
            side_effect=[httpx.Response(200, json=read_policy_response)]
        )
        # and the desired is the same as the existing
        sut = access.PolicyResource(
            id="policy1",
            code="a_policy_code",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.IdSelector(
                    name="banjo",
                    description="whatever",
                    identifier={"scope": "w", "code": "y"},
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )
        # when we update
        log = sut.update(self.client, SimpleNamespace(code="a_policy_code", id="x"))
        # then there is no change and the log remains as is
        assert log is None
        # and no put request was made

    def test_update_modify_description(self, respx_mock, read_policy_response):
        # given the policy exists with a description = "policy description"
        respx_mock.get("/access/api/policies/a_policy_code").mock(
            side_effect=[httpx.Response(200, json=read_policy_response)]
        )
        respx_mock.put("/access/api/policies/a_policy_code").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        # and the desired has a different description
        sut = access.PolicyResource(
            id="policy1",
            code="a_policy_code",
            description="a different policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.IdSelector(
                    name="banjo",
                    description="whatever",
                    identifier={"scope": "w", "code": "y"},
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )
        # when we update
        log = sut.update(self.client, SimpleNamespace(code="a_policy_code", id="x"))
        # the log is returned (but unchanged)
        assert log == {"code": "a_policy_code", "id": "policy1"}
        # and a put request was made to update the policy
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/access/api/policies/a_policy_code"
        assert json.loads(request.content) == {
            "applications": ["lusid"],
            "description": "a different policy description",
            "grant": "Allow",
            "selectors": [
                {
                    "idSelectorDefinition": {
                        "actions": [{"activity": "execute", "entity": "Feature", "scope": "actscope"}],
                        "description": "whatever",
                        "identifier": {"code": "y", "scope": "w"},
                        "name": "banjo",
                    }
                }
            ],
            "when": {"activate": "2024-08-31T18:00:00.0000000+00:00"},
        }

    def test_deps(self, stock_policy_resource):
        # policy doesn't have any deps
        sut = stock_policy_resource
        assert sut.deps() == []

    def test_delete(self, respx_mock):
        respx_mock.delete("/access/api/policies/a_policy_code").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        # given an existing policy
        # when we delete it
        old_state = SimpleNamespace(id="policy1", code="a_policy_code")
        access.PolicyResource.delete(self.client, old_state)
        # then a delete request is made
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/access/api/policies/a_policy_code"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeRoleRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/access/api/roles/cd1?scope=sc1").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        sut = access.RoleRef(id="one", scope="sc1", code="cd1")
        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/access/api/roles/cd1?scope=default").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        sut = access.RoleRef(id="one", code="cd1")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Role default/cd1 not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/access/api/roles/cd1?scope=sc1").mock(return_value=httpx.Response(500, json={}))
        client = self.client
        sut = access.RoleRef(id="one", scope="sc1", code="cd1")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeRole:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def stock_policy_resource(self):
        return access.PolicyResource(
            id="policy1",
            code="a_policy",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.IdSelector(
                    name="banjo",
                    description="whatever",
                    identifier={"scope": "w", "code": "y"},
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )

    def test_create_with_new_resource_request(self, respx_mock, stock_policy_resource):
        respx_mock.post("/access/api/roles").mock(return_value=httpx.Response(200, json={}))
        # given no role exists yet and we create one using the updadted RoleResourceRequest
        sut = access.RoleResource(
            id="role1",
            code="a_role_code",
            resource=access.RoleResourceRequest(
                policy_id_role_resource=access.PolicyIdRoleResource(policies=[stock_policy_resource])
            ),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        sut.create(self.client)
        # then a post request is made
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/roles"
        assert json.loads(request.content) == {
            "code": "a_role_code",
            "permission": "Read",
            "resource": {
                "policyIdRoleResource": {
                    "policies": [{"code": "a_policy", "scope": "default"}],
                    "policyCollections": [],
                }
            },
            "when": {"activate": "2024-03-01:00:00.0000000+00:00"},
        }

    def test_can_parse_role_with_policy_id(self):
        serialized = {
            "id": "whatever",
            "code": "a_role_code",
            "permission": "Read",
            "resource": {
                "policyIdRoleResource": {
                    "policies": [],
                    "policyCollections": [],
                }
            },
            "when": {"activate": "2024-03-01:00:00.0000000+00:00"},
        }
        sut = access.RoleResource.model_validate(serialized, context={"$refs": {}})
        assert sut.resource
        assert sut.resource.policy_id_role_resource is not None

    def test_can_parse_role_with_non_transitive(self):
        serialized = {
            "id": "whatever",
            "code": "a_role_code",
            "permission": "Read",
            "resource": {
                "nonTransitiveSupervisorRoleResource": {
                    "roles": [],
                }
            },
            "when": {"activate": "2024-03-01:00:00.0000000+00:00"},
        }
        sut = access.RoleResource.model_validate(serialized, context={"$refs": {}})
        assert sut.resource
        assert sut.resource.non_transitive_supervisor_role_resource is not None

    def test_create_with_nontransitive(self, respx_mock, stock_policy_resource):
        respx_mock.post("/access/api/roles").mock(return_value=httpx.Response(200, json={}))
        # given a pre-existing supervisor role
        sup = access.RoleResource(
            id="sup",
            code="supervisor",
            resource=access.RoleResourceRequest(
                policy_id_role_resource=access.PolicyIdRoleResource(policies=[])
            ),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        # when we create a new role which references the supervisor
        sut = access.RoleResource(
            id="role1",
            code="a_role_code",
            resource=access.RoleResourceRequest(
                non_transitive_supervisor_role_resource=access.NonTransitiveSupervisorRoleResource(
                    roles=[sup]
                )
            ),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        sut.create(self.client)
        # then a post request is made
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/roles"
        assert json.loads(request.content) == {
            "code": "a_role_code",
            "permission": "Read",
            "resource": {
                "nonTransitiveSupervisorRoleResource": {
                    "roles": [{"scope": "default", "code": "supervisor"}]
                }
            },
            "when": {"activate": "2024-03-01:00:00.0000000+00:00"},
        }

    def test_create_with_policy_collection(self, respx_mock, stock_policy_resource):
        respx_mock.post("/access/api/roles").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/access/api/policycollections").mock(
            return_value=httpx.Response(200, json={"id": {"scope": "default", "code": "col-inner"}})
        )
        respx_mock.post("/access/api/policycollections").mock(
            return_value=httpx.Response(200, json={"id": {"scope": "default", "code": "col-code"}})
        )
        # given an inner collection which has already been created
        inner = access.PolicyCollectionResource(id="polly-collection", code="col-code", policies=[])
        inner.create(self.client)
        # when we create a role referenccing the collection
        sut = access.RoleResource(
            id="role1",
            code="a_role_code",
            resource=access.RoleResourceRequest(
                policy_id_role_resource=access.PolicyIdRoleResource(policy_collections=[inner])
            ),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        sut.create(self.client)
        # then a post request is made
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/roles"
        assert json.loads(request.content) == {
            "code": "a_role_code",
            "permission": "Read",
            "resource": {
                "policyIdRoleResource": {
                    "policies": [],
                    "policyCollections": [{"scope": "default", "code": "col-code"}],
                }
            },
            "when": {"activate": "2024-03-01:00:00.0000000+00:00"},
        }

    def test_delete(self, respx_mock, stock_policy_resource):
        respx_mock.delete("/access/api/roles/a_role").mock(side_effect=[httpx.Response(200, json={})])
        # given an existing policy
        # when we delete it
        old_state = SimpleNamespace(id="role1", code="a_role")
        access.RoleResource.delete(self.client, old_state)
        # then a delete request is made
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/access/api/roles/a_role"

    @staticmethod
    def test_deps(stock_policy_resource):
        # given a role with two policy resources
        sut = access.RoleResource(
            id="role1",
            code="a_role_code",
            resource=access.RoleResourceRequest(
                policy_id_role_resource=access.PolicyIdRoleResource(policies=[stock_policy_resource])
            ),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        # when we ask for the deps we get two back
        assert sut.deps() == [stock_policy_resource]

    def test_deps_policy_collection(self, stock_policy_resource):
        # given a role with a policy collection
        inner = access.PolicyCollectionResource(
            id="polly-collection", code="col-inner", policies=[stock_policy_resource]
        )
        sut = access.RoleResource(
            id="role1",
            code="a_role_code",
            resource=access.RoleResourceRequest(
                policy_id_role_resource=access.PolicyIdRoleResource(policy_collections=[inner])
            ),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        # when we ask for the deps
        assert sut.deps() == [inner]

    @pytest.fixture
    def read_role_response(self):
        return {
            "id": {"scope": "default", "code": "a_role_code"},
            "when": {
                "activate": "2024-03-01:00:00.0000000+00:00",
                "deactivate": "2024-03-01:00:00.0000000+00:00",
            },
            "roleHierarchyIndex": 20,
            "permission": "Read",
            "resource": {
                "policyIdRoleResource": {"policies": [{"code": "a_policy", "scope": "default"}]}
            },
            "links": [],
        }

    def test_update_remove_policies(self, respx_mock, read_role_response):
        # given the role exists and has a policy
        respx_mock.get("/access/api/roles/a_role_code").mock(
            side_effect=[httpx.Response(200, json=read_role_response)]
        )
        respx_mock.put("/access/api/roles/a_role_code").mock(side_effect=[httpx.Response(200, json={})])
        # and the desired state is no policies
        sut = access.RoleResource(
            id="role1",
            code="a_role_code",
            resource=access.RoleResourceRequest(
                policy_id_role_resource=access.PolicyIdRoleResource(policies=[])
            ),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        # when we update
        log = sut.update(self.client, SimpleNamespace(id="role1", code="a_role_code"))
        # then the log returned is the same
        assert log == {"code": "a_role_code", "id": "role1"}
        # and a put request to modify the role was made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/access/api/roles/a_role_code"
        assert json.loads(request.content) == {
            "permission": "Read",  # nb no code set when its a PUT
            "resource": {"policyIdRoleResource": {"policies": [], "policyCollections": []}},
            "when": {"activate": "2024-03-01:00:00.0000000+00:00"},
        }

    def test_update_non_transitive(self, respx_mock, read_role_response):
        # given the role exists and has a policy
        respx_mock.get("/access/api/roles/a_role_code").mock(
            side_effect=[httpx.Response(200, json=read_role_response)]
        )
        respx_mock.put("/access/api/roles/a_role_code").mock(side_effect=[httpx.Response(200, json={})])
        # and there is an existing supervisor role
        sup = access.RoleResource(
            id="sup",
            code="supervisor",
            resource=access.RoleResourceRequest(
                policy_id_role_resource=access.PolicyIdRoleResource(policies=[])
            ),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        # and the desired state only a nonTransitiveSupervisor....
        sut = access.RoleResource(
            id="role1",
            code="a_role_code",
            resource=access.RoleResourceRequest(
                non_transitive_supervisor_role_resource=access.NonTransitiveSupervisorRoleResource(
                    roles=[sup]
                )
            ),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        # when we update
        log = sut.update(self.client, SimpleNamespace(id="role1", code="a_role_code"))
        # then the log returned is the same
        assert log == {"code": "a_role_code", "id": "role1"}
        # and a put request to modify the role was made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/access/api/roles/a_role_code"
        assert json.loads(request.content) == {
            "permission": "Read",  # nb no code set when its a PUT
            "resource": {
                "nonTransitiveSupervisorRoleResource": {
                    "roles": [{"scope": "default", "code": "supervisor"}]
                }
            },
            "when": {"activate": "2024-03-01:00:00.0000000+00:00"},
        }

    def test_update_non_transitive_ref(self, respx_mock, read_role_response):
        # given the role exists and has a policy
        respx_mock.get("/access/api/roles/a_role_code").mock(
            side_effect=[httpx.Response(200, json=read_role_response)]
        )
        respx_mock.put("/access/api/roles/a_role_code").mock(side_effect=[httpx.Response(200, json={})])
        # and we reference a system role
        ref = access.RoleRef(id="supervisor", scope="support", code="support-iam-readonly")
        # and the desired state only a nonTransitiveSupervisor....
        ntsrs = access.NonTransitiveSupervisorRoleResource(roles=[ref])
        sut = access.RoleResource(
            id="role1",
            code="a_role_code",
            resource=access.RoleResourceRequest(non_transitive_supervisor_role_resource=ntsrs),
            when=access.WhenSpec(activate="2024-03-01:00:00.0000000+00:00"),
            permission=access.Permission.READ,
        )
        # when we update
        log = sut.update(self.client, SimpleNamespace(id="role1", code="a_role_code"))
        # then the log returned is the same
        assert log == {"code": "a_role_code", "id": "role1"}
        # and a put request to modify the role was made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/access/api/roles/a_role_code"
        assert json.loads(request.content) == {
            "permission": "Read",  # nb no code set when its a PUT
            "resource": {
                "nonTransitiveSupervisorRoleResource": {
                    "roles": [{"scope": "support", "code": "support-iam-readonly"}]
                }
            },
            "when": {"activate": "2024-03-01:00:00.0000000+00:00"},
        }

    def test_dump(self, stock_policy_resource):
        # given a role resource with policies
        sut = access.RoleResource(
            id="role1",
            code="test-role",
            description="A test role with policies",
            resource=access.RoleResourceRequest(
                policy_id_role_resource=access.PolicyIdRoleResource(
                    policies=[stock_policy_resource]
                )
            ),
            when=access.WhenSpec(activate="2024-01-01T00:00:00.0000000+00:00"),
            permission=access.Permission.READ
        )
        # when we dump it
        dumped = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then the dumped state is correct
        assert dumped == {
            "code": "test-role",
            "description": "A test role with policies",
            "resource": {
                "policyIdRoleResource": {
                    "policies": [
                        {"$ref": "policy1"}
                    ],
                    "policyCollections": []
                }
            },
            "when": {
                "activate": "2024-01-01T00:00:00.0000000+00:00"
            },
            "permission": "Read"
        }

    def test_undump(self, stock_policy_resource):
        # given a dumped role state
        dumped = {
            "code": "test-role",
            "description": "A test role with policies",
            "resource": {
                "policyIdRoleResource": {
                    "policies": [
                        {"$ref": "policy1"}
                    ],
                    "policyCollections": []
                }
            },
            "when": {
                "activate": "2024-01-01T00:00:00.0000000+00:00"
            },
            "permission": "Read"
        }
        # when we undump it
        sut = access.RoleResource.model_validate(
            dumped,
            context={
                "style": "undump",
                "$refs": {
                    "policy1": stock_policy_resource,
                },
                "id": "role1",
            }
        )
        # then the id has been extracted from the context
        assert sut.id == "role1"
        assert sut.code == "test-role"
        assert sut.description == "A test role with policies"
        assert sut.permission == access.Permission.READ
        assert sut.when.activate == "2024-01-01T00:00:00.0000000+00:00"
        # and the policy references have been wired up
        assert sut.resource
        assert sut.resource.policy_id_role_resource is not None
        assert sut.resource.policy_id_role_resource.policies is not None
        assert len(sut.resource.policy_id_role_resource.policies) == 1
        assert sut.resource.policy_id_role_resource.policies[0] == stock_policy_resource
        assert sut.resource.policy_id_role_resource.policy_collections is not None
        assert len(sut.resource.policy_id_role_resource.policy_collections) == 0


@pytest.mark.respx(base_url=TEST_BASE)
class DescribePolicyCollectionRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/access/api/policycollections/cd1?scope=sc1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = access.PolicyCollectionRef(id="one", scope="sc1", code="cd1")
        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/access/api/policycollections/cd1?scope=sc1").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        sut = access.PolicyCollectionRef(id="one", scope="sc1", code="cd1")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "PolicyCollection sc1/cd1 not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/access/api/policycollections/cd1?scope=sc1").mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        sut = access.PolicyCollectionRef(id="one", scope="sc1", code="cd1")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribePolicyCollectionResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def policy1(self):
        return access.PolicyResource(
            id="policy1",
            code="a_policy1",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.IdSelector(
                    name="banjo",
                    description="whatever",
                    identifier={"scope": "w", "code": "y"},
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )

    @pytest.fixture
    def policy2(self):
        return access.PolicyResource(
            id="policy2",
            code="a_policy2",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.MatchAllSelector(
                    name="banjo",
                    description="whatever",
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )

    def test_create_with_policies(self, respx_mock, policy1, policy2):
        respx_mock.post("/access/api/policycollections").mock(
            return_value=httpx.Response(200, json={"id": {"scope": "default", "code": "col-code"}})
        )
        client = self.client
        # given a desired collection
        sut = access.PolicyCollectionResource(
            id="polly-collection", code="col-code", policies=[policy1, policy2]
        )
        # when we create it
        state = sut.create(client)
        # then the state is returned
        assert state == {"scope": "default", "code": "col-code"}
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/policycollections"
        assert json.loads(request.content) == {
            "code": "col-code",
            "policies": [
                {"scope": "default", "code": "a_policy1"},
                {"scope": "default", "code": "a_policy2"},
            ],
            "policyCollections": [],
        }

    def test_create_with_policy_ref(self, respx_mock, policy1, policy2):
        respx_mock.post("/access/api/policycollections").mock(
            return_value=httpx.Response(200, json={"id": {"scope": "default", "code": "col-code"}})
        )
        client = self.client
        # given a policy ref to a non-default scope (eg a ref to a builtin
        # policy like an admin one
        ref = access.PolicyRef(id="ref", scope="sc1", code="cd1")
        # given a desired collection
        sut = access.PolicyCollectionResource(id="polly-collection", code="col-code", policies=[ref])
        # when we create it
        state = sut.create(client)
        # then the state is returned
        assert state == {"scope": "default", "code": "col-code"}
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/policycollections"
        assert json.loads(request.content) == {
            "code": "col-code",
            "policies": [{"scope": "sc1", "code": "cd1"}],
            "policyCollections": [],
        }

    def test_create_with_nested_collection(self, respx_mock, policy1, policy2):
        respx_mock.post("/access/api/policycollections").mock(
            return_value=httpx.Response(200, json={"id": {"scope": "default", "code": "col-inner"}})
        )
        respx_mock.post("/access/api/policycollections").mock(
            return_value=httpx.Response(200, json={"id": {"scope": "default", "code": "col-code"}})
        )
        client = self.client
        # given an inner collection which has already been created
        inner = access.PolicyCollectionResource(
            id="polly-collection", code="col-inner", policies=[policy1, policy2]
        )
        inner.create(self.client)
        # and a desired collection which references it
        sut = access.PolicyCollectionResource(
            id="polly-collection", code="col-code", policy_collections=[inner]
        )
        # when we create it
        state = sut.create(client)
        # then the state is returned
        assert state == {"scope": "default", "code": "col-code"}
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/policycollections"
        assert json.loads(request.content) == {
            "code": "col-code",
            "policyCollections": [{"scope": "default", "code": "col-inner"}],
            "policies": [],
        }

    def test_update_no_change(self, respx_mock, policy1, policy2):
        # given an existing collection
        respx_mock.get("/access/api/policycollections/col-code").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": {"code": "col-code", "scope": "default"},
                    "policies": [
                        {"scope": "default", "code": "a_policy1"},
                        {"scope": "default", "code": "a_policy2"},
                    ],
                    "policyCollections": [],
                    "links": [],
                },
            )
        )
        old_state = SimpleNamespace(scope="default", code="col-code")
        # given a desired collection
        sut = access.PolicyCollectionResource(
            id="polly-collection", code="col-code", policies=[policy1, policy2]
        )
        # when we update
        state = sut.update(self.client, old_state)
        # then state is None and no further requests are made
        assert state is None

    def test_update_rename(self, respx_mock, policy1, policy2):
        respx_mock.delete("/access/api/policycollections/col-code").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        respx_mock.post("/access/api/policycollections").mock(
            return_value=httpx.Response(200, json={"id": {"scope": "default", "code": "col-code2"}})
        )
        # given an existing collection at col-code
        old_state = SimpleNamespace(scope="default", code="col-code")
        # and a desired collection with code col-code2
        sut = access.PolicyCollectionResource(
            id="polly-collection", code="col-code2", policies=[policy1, policy2]
        )
        # when we update
        state = sut.update(self.client, old_state)
        # the new state is returned
        assert state == {"scope": "default", "code": "col-code2"}
        # and a delete and a create call were made

    def test_update_remove_policy(self, respx_mock, policy1, policy2):
        # given an existing collection
        respx_mock.get("/access/api/policycollections/col-code").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": {"code": "col-code", "scope": "default"},
                    "policies": [
                        {"scope": "default", "code": "a_policy1"},
                        {"scope": "default", "code": "a_policy2"},
                    ],
                    "policyCollections": [],
                    "links": [],
                },
            )
        )
        respx_mock.put("/access/api/policycollections/col-code").mock(
            return_value=httpx.Response(200, json={"id": {"scope": "default", "code": "col-code"}})
        )
        old_state = SimpleNamespace(scope="default", code="col-code")
        # given a desired collection
        sut = access.PolicyCollectionResource(id="polly-collection", code="col-code", policies=[policy1])
        # when we update
        state = sut.update(self.client, old_state)
        # then state returned
        assert state == {"scope": "default", "code": "col-code"}
        # and a put request was sent
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/access/api/policycollections/col-code"
        assert json.loads(request.content) == {
            "policies": [{"scope": "default", "code": "a_policy1"}],
            "policyCollections": [],
        }

    def test_delete(self, respx_mock):
        respx_mock.delete("/access/api/policycollections/col-code").mock(
            side_effect=[httpx.Response(200, json={})]
        )
        # given an existing collection
        # when we delete it
        old_state = SimpleNamespace(scope="default", code="col-code")
        access.PolicyCollectionResource.delete(self.client, old_state)
        # then a delete request is made
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/access/api/policycollections/col-code"

    def test_deps_policy_ref(self, respx_mock, policy1, policy2):
        ref = access.PolicyRef(id="ref", scope="sc1", code="cd1")
        # given a desired collection with two policies
        sut = access.PolicyCollectionResource(id="polly-collection", code="col-code", policies=[ref])
        # when we get the deps
        deps = sut.deps()
        assert deps == [ref]

    def test_deps_policies_only(self, respx_mock, policy1, policy2):
        # given a desired collection with two policies
        sut = access.PolicyCollectionResource(
            id="polly-collection", code="col-code", policies=[policy1, policy2]
        )
        # when we get the deps
        deps = sut.deps()
        assert deps == [policy1, policy2]

    def test_deps_collections_only(self, respx_mock, policy1, policy2):
        # given an inner collection which has already been created
        inner = access.PolicyCollectionResource(
            id="polly-collection", code="col-inner", policies=[policy1, policy2]
        )
        # and a desired collection which references it
        sut = access.PolicyCollectionResource(
            id="polly-collection", code="col-code", policy_collections=[inner]
        )
        # when we get the deps
        deps = sut.deps()
        assert deps == [inner]

    def test_dump(self, policy1, policy2):
        # given an existing policy collection
        sut = access.PolicyCollectionResource(
            id="collection1",
            code="test-collection",
            description="A test collection",
            policies=[policy1, policy2],
            metadata={"key1": ["value1", "value2"], "key2": ["value3"]}
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True,
            round_trip=True,   # excludes computeds
            exclude_none=True,
            context={"style": "dump"}
        )
        # then the dumped state is correct
        assert dumped == {
            "code": "test-collection",
            "description": "A test collection",
            "policies": [
                {"$ref": policy1.id},
                {"$ref": policy2.id}
            ],
            "policyCollections": [],
            "metadata": {
                "key1": ["value1", "value2"],
                "key2": ["value3"]
            }
        }

    def test_undump(self, policy1, policy2):
        # given a dumped policy collection state
        dumped = {
            "code": "test-collection",
            "description": "A test collection",
            "policies": [
                {"$ref": policy1.id},
                {"$ref": policy2.id}
            ],
            "policyCollections": [],
            "metadata": {
                "key1": ["value1", "value2"],
                "key2": ["value3"]
            }
        }
        # when we undump it
        sut = access.PolicyCollectionResource.model_validate(
            dumped,
            context={
                "style": "undump",
                "$refs": {
                    policy1.id: policy1,
                    policy2.id: policy2,
                },
                "id": "collection1",
            }
        )
        # then the id has been extracted from the context
        assert sut.id == "collection1"
        assert sut.code == "test-collection"
        assert sut.description == "A test collection"
        # and the policy refs have been wired up
        assert sut.policies == [policy1, policy2]
        assert sut.policy_collections == []
        assert sut.metadata == {
            "key1": ["value1", "value2"],
            "key2": ["value3"]
        }

    def test_parse_api_format(self):
        policy1 = access.PolicyRef(
            id="p1",
            scope="sc1",
            code="cd1",
        )
        coll1 = access.PolicyCollectionRef(
            id="c1",
            scope="sc1",
            code="cd1"
        )
        api_format = {
          "id": {
            "scope": "default",
            "code": "organisation-wide-policies"
          },
          "policies": [
              {"$ref": "p1"}
          ],
          "policyCollections": [
              {"$ref": "c1"}
          ],
          "description": "Collection of organisation wide policies"
        }
        parsed = access.PolicyCollectionResource.model_validate(
            api_format,
            context={"id": "someid", "$refs": {
                "p1": policy1,
                "c1": coll1
            }}
        )
        assert parsed.id == "someid"
        assert parsed.policies == [policy1]
        assert parsed.policy_collections == [coll1]


@pytest.mark.respx(base_url=TEST_BASE)
class DescribePolicyTemplateRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @staticmethod
    def test_scope_default():
        # when scope is omitted
        sut = access.PolicyTemplateRef(id="one", code="cd")
        # then it uses "default"
        assert sut.scope == "default"

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/access/api/policytemplates/pol1?scope=sc1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = access.PolicyTemplateRef(id="one", scope="sc1", code="pol1")

        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/access/api/policytemplates/pol1?scope=sc1").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        sut = access.PolicyTemplateRef(id="one", scope="sc1", code="pol1")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Policy Template sc1/pol1 not found" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/access/api/policytemplates/pol1?scope=sc1").mock(
            return_value=httpx.Response(500, json={})
        )
        client = self.client
        sut = access.PolicyTemplateRef(id="one", scope="sc1", code="pol1")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribePolicyTemplate:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def policy1(self):
        return access.PolicyResource(
            id="policy1",
            code="a_policy1",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.IdSelector(
                    name="banjo",
                    description="whatever",
                    identifier={"scope": "w", "code": "y"},
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )

    @pytest.fixture
    def policy2(self):
        return access.PolicyResource(
            id="policy2",
            code="a_policy2",
            description="policy description",
            applications=["lusid"],
            grant=access.Grant.ALLOW,
            when=access.WhenSpec(activate="2024-08-31T18:00:00.0000000+00:00"),
            selectors=[
                access.MatchAllSelector(
                    name="banjo",
                    description="whatever",
                    actions=[access.ActionId(scope="actscope", activity="execute", entity="Feature")],
                )
            ],
        )

    @pytest.fixture
    def stock_policy_template_resource(self):
        selector = access.IdSelector(
            name="example_id_selector",
            description="test_description",
            identifier={"scope": "w"},
            actions=[access.ActionId(scope="default", activity="Read", entity="Portfolio")],
        )
        return access.PolicyTemplateResource(
            id="policy_template1",
            display_name="display_name",
            code="code1",
            description="some_description",
            templated_selectors=[access.TemplatedSelector(
                application="LUSID",
                tag="Data",
                selector=selector
            )]
        )

    def test_read(self, respx_mock, stock_policy_template_resource):
        respx_mock.get("/access/api/policytemplates/code1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "displayName": "display_name",
                    "scope": "scope1",
                    "code": "code1",
                    "description": "some_description",
                    "applications": [
                        "LUSID"
                    ],
                    "tags": [
                        "example_tag"
                    ],
                    "templatedSelectors": [
                        {
                        "application": "LUSID",
                        "tag": "example_tag",
                        "selector": {
                            "idSelectorDefinition": {
                            "identifier": {
                                "scope": "w"
                            },
                            "actions": [
                                {
                                "scope": "default",
                                "activity": "Read",
                                "entity": "Portfolio"
                                },
                            ],
                            "name": "example_id_selector",
                            "description": "test_description"
                            }
                        }
                        }
                    ]
                }
            )
        )
        sut = stock_policy_template_resource
        old_state = SimpleNamespace(code=stock_policy_template_resource.code)
        result = sut.read(self.client, old_state)
        assert result is not None
        assert result["code"] == "code1"
        assert result["scope"] == "scope1"
        assert result["displayName"] == "display_name"

    def test_create(self, respx_mock, stock_policy_template_resource):
        respx_mock.post("/access/api/policytemplates").mock(return_value=httpx.Response(200, json={}))
        sut = stock_policy_template_resource
        result = sut.create(self.client)
        assert result is not None
        assert result["id"] == "policy_template1"
        assert result["code"] == "code1"
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/access/api/policytemplates"
        assert json.loads(request.content) == {
            "code": "code1",
            "displayName": "display_name",
            "description": "some_description",
            "templatedSelectors": [
                {
                "application": "LUSID",
                "tag": "Data",
                "selector": {
                    "idSelectorDefinition": {
                    "identifier": {
                        "scope": "w"
                    },
                    "actions": [
                        {
                        "scope": "default",
                        "activity": "Read",
                        "entity": "Portfolio"
                        },
                    ],
                    "name": "example_id_selector",
                    "description": "test_description"
                    }
                }
                }
            ]
        }
        assert "source_version" in result
        assert "remote_version" in result

    def test_update_no_change(self, respx_mock, stock_policy_template_resource):
        sut = stock_policy_template_resource
        remote_response = {
            "displayName": "display_name",
            "scope": "scope1",
            "code": "code1",
            "description": "some_description",
            "applications": [
                "LUSID"
            ],
            "tags": [
                "example_tag"
            ],
            "templatedSelectors": [
                {
                "application": "LUSID",
                "tag": "example_tag",
                "selector": {
                    "idSelectorDefinition": {
                        "identifier": {
                            "scope": "w"
                        },
                        "actions": [
                            {
                            "scope": "default",
                            "activity": "Read",
                            "entity": "Portfolio"
                            },
                        ],
                        "name": "example_id_selector",
                        "description": "test_description"
                        }
                    }
                }
            ]
        }
        respx_mock.get("/access/api/policytemplates/code1").mock(
            return_value=httpx.Response(200, json=remote_response)
        )
        # Calculate hashes to simulate no change scenario
        source_hash = sut.__get_content_hash__()
        # The remote hash should match what update() calculates from the read() response
        remote_hash = sha256(json.dumps(remote_response, sort_keys=True).encode()).hexdigest()
        old_state = SimpleNamespace(
            code="code1", source_version=source_hash, remote_version=remote_hash
        )
        result = sut.update(self.client, old_state)
        assert result is None

    def test_update_with_change(self, respx_mock):
        respx_mock.get("/access/api/policytemplates/code1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "displayName": "display_name",
                    "scope": "scope1",
                    "code": "code1",
                    "description": "some_description",
                    "applications": [
                        "LUSID"
                    ],
                    "tags": [
                        "example_tag"
                    ],
                    "templatedSelectors": [
                        {
                        "application": "LUSID",
                        "tag": "example_tag",
                        "selector": {
                            "idSelectorDefinition": {
                                "identifier": {
                                    "scope": "w"
                                },
                                "actions": [
                                    {
                                    "scope": "default",
                                    "activity": "Read",
                                    "entity": "Portfolio"
                                    },
                                ],
                                "name": "example_id_selector",
                                "description": "test_description"
                                }
                            }
                        }
                    ]
                }
            )
        )
        respx_mock.put("/access/api/policytemplates/code1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "displayName": "display_name_another",
                    "scope": "scope2",
                    "code": "code1",
                    "description": "some_description_another",
                    "applications": [
                        "LUSID"
                    ],
                    "tags": [
                        "example_tag"
                    ],
                    "templatedSelectors": [
                        {
                        "application": "LUSID",
                        "tag": "example_tag",
                        "selector": {
                            "idSelectorDefinition": {
                            "identifier": {
                                "scope": "w"
                            },
                            "actions": [
                                {
                                "scope": "default",
                                "activity": "Read",
                                "entity": "Portfolio"
                                },
                            ],
                            "name": "example_id_selector",
                            "description": "test_description"
                            }
                        }
                        }
                    ]
                }
            )
        )
        id_selector = access.IdSelector(
            name="example_id_selector",
            description="test_description",
            identifier={"scope": "w"},
            actions=[access.ActionId(scope="default", activity="Read", entity="Portfolio")],
        )
        templated_selector = access.TemplatedSelector(
                application="LUSID",
                tag="example_tag",
                selector=id_selector
            )
        sut = access.PolicyTemplateResource(
            id="policy_template1",
            display_name="display_name_another",
            code="code1",
            description="some_description_another",
            templated_selectors=[templated_selector]
        )
        old_state = SimpleNamespace(
            code="code1", remote_version="oldhash", source_version="different_hash"
        )
        result = sut.update(self.client, old_state)
        assert result is not None
        assert result["id"] == "policy_template1"
        assert result["code"] == "code1"
        assert "source_version" in result
        assert "remote_version" in result
        # Check for put request is called
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/access/api/policytemplates/code1"
        assert json.loads(request.content) == {
            "displayName": "display_name_another",
            "description": "some_description_another",
            "templatedSelectors": [
                {
                "application": "LUSID",
                "tag": "example_tag",
                "selector": {
                    "idSelectorDefinition": {
                    "identifier": {
                        "scope": "w"
                    },
                    "actions": [
                        {
                        "scope": "default",
                        "activity": "Read",
                        "entity": "Portfolio"
                        },
                    ],
                    "name": "example_id_selector",
                    "description": "test_description"
                    }
                }
                }
            ]
            }

    def test_delete(self, respx_mock):
        respx_mock.delete("/access/api/policytemplates/code1").mock(
            return_value=httpx.Response(200, json={})
        )
        old_state = SimpleNamespace(code="code1")
        access.PolicyTemplateResource.delete(self.client, old_state)
        request = respx_mock.calls[-1].request
        assert request.method == "DELETE"
        assert request.url.path == "/access/api/policytemplates/code1"

    def test_deps(self, stock_policy_template_resource):
        sut = stock_policy_template_resource
        assert sut.deps() == []

    def test_dump(self, stock_policy_template_resource):
        sut = stock_policy_template_resource
        dumped = sut.model_dump(
            by_alias=True,
            round_trip=True,   # excludes computeds
            exclude_none=True,
            context={"style": "dump"}
        )
        # then the dumped state is correct
        assert dumped == {
           "code": "code1",
           "description": "some_description",
           "displayName": "display_name",
           "templatedSelectors": [{
               "application": "LUSID",
               "selector": {
                   "actions": [{
                       "activity": "Read",
                       "entity": "Portfolio",
                       "scope": "default",
                   }],
                   "description": "test_description",
                   "identifier": {
                       "scope": "w",
                   },
                   "name": "example_id_selector",
                   "typeName": "idSelectorDefinition",
               },
               "tag": "Data",
           }],
         }

    def test_undump(self):
        # given a dump
        data = {
           "code": "code1",
           "description": "some_description",
           "displayName": "display_name",
           "templatedSelectors": [{
               "application": "LUSID",
               "selector": {
                   "actions": [{
                       "activity": "Read",
                       "entity": "Portfolio",
                       "scope": "default",
                   }],
                   "description": "test_description",
                   "identifier": {
                       "scope": "w",
                   },
                   "name": "example_id_selector",
                   "typeName": "idSelectorDefinition",
               },
               "tag": "Data",
           }],
        }
        # when undumped
        des = access.PolicyTemplateResource.model_validate(data,
            context={"style": "dump", "id": "some-id-thing"}
        )
        # the id is extracted from the context
        assert des.id == "some-id-thing"
        # the selector has discriminated to get the correct type
        assert len(des.templated_selectors) == 1
        assert des.templated_selectors[0].selector.type_name == "idSelectorDefinition"

    def test_parse_api_format(self):
        # given a response from the get api
        api = {
            "displayName": "display_name",
            "scope": "scope1",
            "code": "code1",
            "description": "some_description",
            "applications": [
                "LUSID"
            ],
            "tags": [
                "example_tag"
            ],
            "templatedSelectors": [
                {
                "application": "LUSID",
                "tag": "example_tag",
                "selector": {
                    "idSelectorDefinition": {
                        "identifier": {
                            "scope": "w"
                        },
                        "actions": [
                            {
                            "scope": "default",
                            "activity": "Read",
                            "entity": "Portfolio"
                            },
                        ],
                        "name": "example_id_selector",
                        "description": "test_description"
                        }
                    }
                }
            ]
        }
        # when parsed
        sut = access.PolicyTemplateResource.model_validate(
            api,
            context={"id": "someid"}
        )
        # then the id from the context is used for the resource id
        assert sut.id == "someid"
        # and the  selector dictionary has turned into an array
        # of selectors with a type_name on each
        assert sut.templated_selectors[0].tag == "example_tag"
        assert sut.templated_selectors[0].selector.type_name == "idSelectorDefinition"
