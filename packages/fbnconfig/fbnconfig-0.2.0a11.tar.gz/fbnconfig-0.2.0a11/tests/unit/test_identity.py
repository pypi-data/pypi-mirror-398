import json
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import identity

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.raise_for_status()


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeIdentityRoleRef:
    # This should use the same method of creating a client as the host
    # To be refactored
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_when_exists(self, respx_mock):
        # given 2 roles in the system where role2 matches the sut
        respx_mock.get("/identity/api/roles").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "11111111",
                        "roleId": {"scope": "default", "code": "role1"},
                        "name": "role1",
                        "description": "role one",
                    },
                    {
                        "id": "22222222",
                        "roleId": {"scope": "default", "code": "role2"},
                        "name": "role2",
                        "description": "role two",
                    },
                ],
            )
        )
        client = self.client
        # when we attach
        sut = identity.IdentityRoleRef(id="xyz", name="role2")
        sut.attach(client)
        # then the roleId property is populated from the response
        assert sut.role_id == "22222222"

    def test_attach_when_not_exists(self, respx_mock):
        # given 2 roles in the system where neither matches the sut
        respx_mock.get("/identity/api/roles").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "11111111",
                        "roleId": {"scope": "default", "code": "role1"},
                        "name": "role1",
                        "description": "role one",
                    },
                    {
                        "id": "22222222",
                        "roleId": {"scope": "default", "code": "role2"},
                        "name": "role2",
                        "description": "role two",
                    },
                ],
            )
        )
        client = self.client
        # when we attach an exception is thrown
        sut = identity.IdentityRoleRef(id="xyz", name="none_of_those")
        with pytest.raises(RuntimeError):
            sut.attach(client)

    def test_attach_when_http_error(self, respx_mock):
        # given a server which returns a 500
        respx_mock.get("/identity/api/roles").mock(return_value=httpx.Response(500, json={}))
        client = self.client
        # when we attach a http exception is thrown
        sut = identity.IdentityRoleRef(id="xyz", name="none_of_those")
        with pytest.raises(httpx.HTTPStatusError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeIdentityRoleResource:
    client = httpx.Client(base_url=TEST_BASE)

    def test_create(self, respx_mock):
        respx_mock.post("/identity/api/roles").mock(
            return_value=httpx.Response(
                200, json={"id": "aaaaaa", "roleId": {"scope": "default", "code": "role1"}}
            )
        )
        # given a desired role
        sut = identity.IdentityRoleResource(id="role_id", name="role1", description="role one")
        # when we create it
        state = sut.create(self.client)
        # then the state is returned
        assert state == {
            "id": "role_id",
            "scope": "default",
            "name": "role1",
            "code": "role1",
            "roleId": "aaaaaa",
        }
        # and a create request was sent
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/identity/api/roles"
        assert json.loads(request.content) == {"name": "role1", "description": "role one"}

    def test_update_with_no_changes(self, respx_mock):
        respx_mock.get("/identity/api/roles/bxbxbx").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "bxbxbx",
                    "roleId": {"scope": "default", "code": "role_b"},
                    "source": "source1",
                    "samlName": "abcxxxx",
                    "name": "role_b",
                    "description": "role bee",
                },
            )
        )
        # given a desired role
        sut = identity.IdentityRoleResource(id="res_id", name="role_b", description="role bee")
        old_state = SimpleNamespace(
            roleId="bxbxbx", id="res_id", scope="default", code="role_b", name="role_b"
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is None
        assert state is None
        # and a read was made
        request = respx_mock.calls.last.request
        assert request.method == "GET"
        assert request.url.path == "/identity/api/roles/bxbxbx"
        # but no PUT

    def test_update_with_change_description(self, respx_mock):
        respx_mock.get("/identity/api/roles/bxbxbx").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "bxbxbx",
                    "roleId": {"scope": "default", "code": "role_b"},
                    "source": "source1",
                    "samlName": "abcxxxx",
                    "name": "role_b",
                    "description": "role bee",
                },
            )
        )
        respx_mock.put("/identity/api/roles/bxbxbx").mock(return_value=httpx.Response(200, json={}))
        # given a desired role
        sut = identity.IdentityRoleResource(
            id="res_id", name="role_b", description="modified description"
        )
        old_state = SimpleNamespace(
            roleId="bxbxbx", id="res_id", scope="default", code="role_b", name="role_b"
        )
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state returned because we made a modification
        assert state is not None
        # and the put is sent
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/identity/api/roles/bxbxbx"
        assert json.loads(request.content) == {"description": "modified description"}

    def test_update_with_change_name_should_throw(self):
        # given a desired role
        sut = identity.IdentityRoleResource(id="res_id", name="modified_name", description="role bee")
        old_state = SimpleNamespace(
            roleId="bxbxbx", id="res_id", scope="default", code="role_b", name="role_b"
        )
        # when we update it throws
        with pytest.raises(RuntimeError):
            sut.update(self.client, old_state)

    def test_delete(self, respx_mock):
        respx_mock.delete("/identity/api/roles/bxbxbx").mock(return_value=httpx.Response(200, json={}))
        # given a role that exists
        old_state = SimpleNamespace(
            roleId="bxbxbx", id="res_id", scope="default", code="role_b", name="role_b"
        )
        # when we delete it
        identity.IdentityRoleResource.delete(self.client, old_state)
        # then a delete request is sent with the roleId
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/identity/api/roles/bxbxbx"

    def test_deps(self):
        # given a desired role
        sut = identity.IdentityRoleResource(id="res_id", name="modified_name", description="role bee")
        # it's deps are empty
        assert sut.deps() == []

    def test_dump(self):
        # given an identity role resource
        sut = identity.IdentityRoleResource(id="role_id", name="role1", description="role one")
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then it's correctly serialized
        assert result == {
            "name": "role1",
            "description": "role one"
        }

    def test_undump(self):
        # given dump data
        data = {
            "name": "role1",
            "description": "role one"
        }
        # when we undump it
        result = identity.IdentityRoleResource.model_validate(
            data, context={"style": "undump", "id": "role_id"}
        )
        # then it's correctly populated
        assert result.id == "role_id"
        assert result.name == "role1"
        assert result.description == "role one"

    def test_model_validate_with_role_id(self):
        # given JSON data with nested roleId
        data = {
            "description": "LUSID Administrators. ...",
            "id": "00grojv3wxWdHXgtV2p7",
            "name": "lusid-administrator",
            "roleId": {
                "code": "lusid-administrator",
                "scope": "LUSID_SYSTEM"
            },
            "samlName": "lusid:LUSID_SYSTEM:lusid-administrator",
            "source": "LusidUser"
        }
        # when we validate it
        result = identity.IdentityRoleResource.model_validate(data)
        # then it correctly extracts scope and code from roleId
        assert result.name == "lusid-administrator"
        assert result.description == "LUSID Administrators. ..."
        assert result.scope == "LUSID_SYSTEM"
        assert result.code == "lusid-administrator"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeUserRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_exists(self, respx_mock):
        # given the user "match" exists in the remote
        respx_mock.get("/identity/api/users").mock(
            return_value=httpx.Response(
                200, json=[{"id": "cvex", "login": "no_match"}, {"id": "bdxe", "login": "match"}]
            )
        )
        # when we attach a UserRef
        sut = identity.UserRef(id="user", login="match")
        sut.attach(self.client)
        # then it's userId will be from the matching entry
        assert sut.user_id == "bdxe"

    def test_attach_when_not_exists(self, respx_mock):
        # given the user "match" does not exist
        respx_mock.get("/identity/api/users").mock(
            return_value=httpx.Response(
                200,
                json=[{"id": "cvex", "login": "no_match"}, {"id": "bdxe", "login": "other_no_match"}],
            )
        )
        # when we attach a UserRef
        sut = identity.UserRef(id="user", login="match")
        # an exception is thrown
        with pytest.raises(RuntimeError):
            sut.attach(self.client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeUserResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_create(self, respx_mock):
        respx_mock.post("/identity/api/users").mock(
            return_value=httpx.Response(200, json={"id": "bcdef"})
        )
        # given a desired user
        sut = identity.UserResource(
            id="user",
            login="match",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        # when we create
        sut.create(self.client)
        # then the request is made
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url.path == "/identity/api/users"
        assert json.loads(request.content) == {
            "login": "match",
            "firstName": "Jess",
            "lastName": "Blofeldt",
            "emailAddress": "jess@blo.com",
            "type": "Service",
        }
        # and the user gets an id
        assert sut.user_id == "bcdef"

    def test_deps(self):
        # given a desired user
        sut = identity.UserResource(
            id="user",
            login="match",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        # it has no dependencies
        assert sut.deps() == []

    def test_update_with_change(self, respx_mock):
        # given a user in the remote
        respx_mock.get("/identity/api/users/xxyyzz").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "xxyyzz",
                    "login": "login@login.com",
                    "firstName": "Jess",
                    "lastName": "Blofeldt",
                    "emailAddress": "jess@blo.com",
                    "type": "Service",
                    "status": "active",
                },
            )
        )
        respx_mock.put("/identity/api/users/xxyyzz").mock(return_value=httpx.Response(200, json={}))
        # and existing state
        old_state = SimpleNamespace(id="22", userId="xxyyzz")
        # and desired state with a different firstname
        sut = identity.UserResource(
            id="22",
            login="login@login.com",
            first_name="New Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        # when we update
        new_state = sut.update(self.client, old_state)
        # then the request is made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/identity/api/users/xxyyzz"
        assert json.loads(request.content) == {
            "login": "login@login.com",
            "firstName": "New Jess",
            "lastName": "Blofeldt",
            "emailAddress": "jess@blo.com",
            "type": "Service",
        }
        # and the new state is returned (the same as before)
        assert new_state is not None
        assert new_state["userId"] == "xxyyzz"

    def test_update_with_no_change(self, respx_mock):
        # given a user in the remote
        respx_mock.get("/identity/api/users/xxyyzz").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "xxyyzz",
                    "login": "login@login.com",
                    "firstName": "Jess",
                    "lastName": "Blofeldt",
                    "emailAddress": "jess@blo.com",
                    "type": "Service",
                    "status": "active",
                    "external": False,
                },
            )
        )
        # and existing state
        old_state = SimpleNamespace(id="22", userId="xxyyzz")
        # and desired state which is the same as the remote
        sut = identity.UserResource(
            id="22",
            login="login@login.com",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        # when we update
        new_state = sut.update(self.client, old_state)
        # the new state is None
        assert new_state is None
        # and no put request is made

    def test_update_cannot_change_login(self, respx_mock):
        # given a user in the remote
        respx_mock.get("/identity/api/users/xxyyzz").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "xxyyzz",
                    "login": "login@login.com",
                    "firstName": "Jess",
                    "lastName": "Blofeldt",
                    "emailAddress": "jess@blo.com",
                    "type": "Service",
                    "status": "active",
                    "external": False,
                },
            )
        )
        # and existing state
        old_state = SimpleNamespace(id="22", userId="xxyyzz")
        # and desired state with a different login
        sut = identity.UserResource(
            id="22",
            login="different_login@login.com",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        with pytest.raises(RuntimeError):
            sut.update(self.client, old_state)

    def test_delete(self, respx_mock):
        respx_mock.delete("/identity/api/users/xxyyzz").mock(return_value=httpx.Response(200, json={}))
        # given a role that exists
        old_state = SimpleNamespace(userId="xxyyzz", id="res_id")
        # when we delete it
        identity.UserResource.delete(self.client, old_state)
        # then a delete request is sent with the userId
        request = respx_mock.calls.last.request
        assert request.method == "DELETE"
        assert request.url.path == "/identity/api/users/xxyyzz"

    def test_dump(self):
        # given a user resource
        sut = identity.UserResource(
            id="user_id",
            login="match",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then it's correctly serialized
        assert result == {
            "firstName": "Jess",
            "lastName": "Blofeldt",
            "emailAddress": "jess@blo.com",
            "login": "match",
            "type": "Service"
        }

    def test_undump(self):
        # given dump data
        data = {
            "firstName": "Jess",
            "lastName": "Blofeldt",
            "emailAddress": "jess@blo.com",
            "login": "match",
            "type": "Service"
        }
        # when we undump it
        result = identity.UserResource.model_validate(
            data, context={"style": "undump", "id": "user_id"}
        )
        # then it's correctly populated
        assert result.id == "user_id"
        assert result.login == "match"
        assert result.first_name == "Jess"
        assert result.last_name == "Blofeldt"
        assert result.email_address == "jess@blo.com"
        assert result.type == identity.UserType.SERVICE


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeRoleAssignment:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture
    def created_role(self, respx_mock):
        respx_mock.post("/identity/api/roles").mock(
            return_value=httpx.Response(
                200, json={"id": "role01", "roleId": {"scope": "default", "code": "role1"}}
            )
        )
        # given a desired role
        role = identity.IdentityRoleResource(id="role_id", name="role1", description="role one")
        role.create(self.client)
        return role

    @pytest.fixture
    def created_user(self, respx_mock):
        respx_mock.post("/identity/api/users").mock(
            return_value=httpx.Response(200, json={"id": "user02"})
        )
        user = identity.UserResource(
            id="user",
            login="match",
            first_name="Jess",
            last_name="Blofeldt",
            email_address="jess@blo.com",
            type=identity.UserType.SERVICE,
        )
        user.create(self.client)
        return user

    def test_create(self, respx_mock, created_user, created_role):
        respx_mock.put("/identity/api/roles/role01/users/user02").mock(
            return_value=httpx.Response(200, json={})
        )
        # given a user and a role
        # and the desired assignment
        sut = identity.RoleAssignment(id="ass1", user=created_user, role=created_role)
        # when we create
        sut.create(self.client)
        # then the request is made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/identity/api/roles/role01/users/user02"

    def test_create_with_user_ref(self, respx_mock, created_role):
        respx_mock.get("/identity/api/users").mock(
            return_value=httpx.Response(200, json=[{"id": "user02", "login": "match"}])
        )
        user_ref = identity.UserRef(id="user", login="match")
        user_ref.attach(self.client)

        respx_mock.put("/identity/api/roles/role01/users/user02").mock(
            return_value=httpx.Response(200, json={})
        )

        # given a user ref and a role
        # and the desired assignment
        sut = identity.RoleAssignment(id="ass1", user=user_ref, role=created_role)
        # when we create
        sut.create(self.client)
        # then the request is made
        request = respx_mock.calls.last.request
        assert request.method == "PUT"
        assert request.url.path == "/identity/api/roles/role01/users/user02"

    def test_update_no_change(self, created_user, created_role):
        # gvien an assignment which matches the remote
        sut = identity.RoleAssignment(id="ass1", user=created_user, role=created_role)
        # when we update
        old_state = SimpleNamespace(id="ass1", roleId="role01", userId="user02")
        new_state = sut.update(self.client, old_state)
        # the new state is none
        assert new_state is None
        # and no put request is made

    def test_update_change_user_when_remote_exists(self, respx_mock, created_user, created_role):
        respx_mock.put("/identity/api/roles/role01/users/user02").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.delete("/identity/api/roles/role01/users/user01").mock(
            return_value=httpx.Response(200, json={})
        )
        # given the existing remote is for user01
        old_state = SimpleNamespace(id="ass1", roleId="role01", userId="user01")
        # and a desired state of user02
        sut = identity.RoleAssignment(id="ass1", user=created_user, role=created_role)
        # when we update
        new_state = sut.update(self.client, old_state)
        # then the new state is user02
        assert new_state == {"id": "ass1", "roleId": "role01", "userId": "user02"}
        # and the existing assignment is deleted
        request = respx_mock.calls[-2].request
        assert request.method == "DELETE"
        assert request.url.path == "/identity/api/roles/role01/users/user01"
        # and a new one is created
        request = respx_mock.calls[-1].request
        assert request.method == "PUT"
        assert request.url.path == "/identity/api/roles/role01/users/user02"

    def test_deps(self, created_user, created_role):
        # given a desired assignment
        sut = identity.RoleAssignment(id="ass1", user=created_user, role=created_role)
        # it depends on the user and the role
        assert sut.deps() == [created_user, created_role]
        ref = identity.UserRef(id="user", login="match")
        sut = identity.RoleAssignment(id="ass1", user=ref, role=created_role)
        assert sut.deps() == [ref, created_role]

    def test_delete(self, respx_mock):
        respx_mock.delete("/identity/api/roles/role01/users/user02").mock(
            return_value=httpx.Response(200, json={})
        )
        # given an existing remote
        old_state = SimpleNamespace(id="ass1", roleId="role01", userId="user02")
        # when we delete it
        identity.RoleAssignment.delete(self.client, old_state)
        # the existing assignment is deleted
        request = respx_mock.calls[-1].request
        assert request.method == "DELETE"
        assert request.url.path == "/identity/api/roles/role01/users/user02"

    def test_dump(self, created_user, created_role):
        # given a role assignment
        sut = identity.RoleAssignment(id="ass1", user=created_user, role=created_role)
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then references are serialized as $ref
        assert result == {
            "user": {"$ref": "user"},
            "role": {"$ref": "role_id"}
        }

    def test_undump(self, created_user, created_role):
        # given dump data
        data = {
            "user": {"$ref": "user"},
            "role": {"$ref": "role_id"}
        }
        # when we undump it
        result = identity.RoleAssignment.model_validate(
            data,
            context={
                "style": "undump",
                "$refs": {
                    "user": created_user,
                    "role_id": created_role
                },
                "id": "ass1"
            }
        )
        # then it's correctly populated
        assert result.id == "ass1"
        assert result.user == created_user
        assert result.role == created_role


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeApplicationResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_read(self, respx_mock):
        respx_mock.get("/identity/api/applications/app123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "app123",
                    "clientId": "cid",
                    "displayName": "App",
                    "type": "Service",
                    "secret": "sec",
                    "issuer": "iss",
                },
            )
        )
        old_state = SimpleNamespace(application_id="app123")
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        result = sut.read(self.client, old_state)
        assert result is not None
        assert result["id"] == "app123"
        assert result["clientId"] == "cid"
        assert result["secret"] == "sec"
        assert result["issuer"] == "iss"

    def test_create(self, respx_mock):
        respx_mock.post("/identity/api/applications").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "app123",
                    "clientId": "cid",
                    "displayName": "App",
                    "type": "Native",
                    "secret": "sec",
                    "issuer": "iss",
                },
            )
        )
        # given a new desired application resource
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
            redirect_uris=["http://foo.bar"],
            post_logout_redirect_uris=["http://post-foo.bar"]
        )
        # when we call create
        new_state = sut.create(self.client)
        # then the new state is returned
        assert new_state == {
            "application_id": "app123",
            "client_id": "cid",
            "remote_version": "19ddb7925c142f10e3e4fc92c4929b9a48148725a94d967cbbe6349dfd2a0f6c",
            "source_version": "5f3a6c69866404a80d51260f15d8bb48f8dae1d8d22b1bc33965f40effe4a5f2"
        }
        # and the local object state captures the useful fields
        assert sut.secret == "sec"
        assert sut.issuer == "iss"
        assert sut.application_id == "app123"
        # and a post was made to the api
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "clientId": "cid",
            "displayName": "App",
            "postLogoutRedirectUris": [
                "http://post-foo.bar",
            ],
            "redirectUris": [
                "http://foo.bar",
            ],
            "type": "Native",
        }

    def test_update_no_change(self, respx_mock):
        # Simulate no change: desired hash matches old_state hashes
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )

        # Mock the read call that update() makes - this is what the remote data looks like
        remote_response = {
            "id": "app123",
            "clientId": "cid",
            "displayName": "App",
            "type": "Native",
            "secret": "sec",
            "issuer": "iss",
        }

        respx_mock.get("/identity/api/applications/app123").mock(
            return_value=httpx.Response(200, json=remote_response)
        )

        # Calculate hashes to simulate no change scenario
        source_hash = sut.__get_content_hash__()

        # The remote hash should match what update() calculates from the read() response
        remote_hash = sha256(json.dumps(remote_response, sort_keys=True).encode()).hexdigest()

        old_state = SimpleNamespace(
            application_id="app123", source_version=source_hash, remote_version=remote_hash
        )
        result = sut.update(self.client, old_state)
        assert result is None

    def test_update_with_change(self, respx_mock):
        # Given a remote resource which does not have the same hash as the desired
        respx_mock.get("/identity/api/applications/app123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "app123",
                    "clientId": "cid",
                    "displayName": "App",
                    "type": "Native",
                    "secret": "sec",
                    "issuer": "iss",
                },
            )
        )
        respx_mock.delete("/identity/api/applications/app123").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/identity/api/applications").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "app456",
                    "clientId": "cid",
                    "displayName": "App",
                    "type": "Native",
                    "secret": "sec2",
                    "issuer": "iss2",
                },
            )
        )
        # when we update
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        old_state = SimpleNamespace(
            application_id="app123", remote_version="oldhash", source_version="different_hash"
        )
        new_state = sut.update(self.client, old_state)
        # then the new state is returned with the new hashes
        assert new_state == {
            "application_id": "app456",
            "client_id": "cid",
            "remote_version": "3eff8886f75d274a4df926261c4a14f0338a982447881980924b5625ab1ff850",
            "source_version": "1c7e575d201e03054c0ab81638f45f15b65a618036be5763d67a26ef25fccfc7"
        }
        # and the object has populated key variables
        assert sut.secret == "sec2"
        assert sut.issuer == "iss2"
        assert sut.application_id == "app456"
        # and a delete plus a create call were made
        delete_request = respx_mock.calls[1].request
        assert delete_request.method == "DELETE"
        assert delete_request.url.path == "/identity/api/applications/app123"
        create_request = respx_mock.calls[2].request
        assert create_request.method == "POST"
        assert create_request.url.path == "/identity/api/applications"

    def test_delete(self, respx_mock):
        respx_mock.delete("/identity/api/applications/app123").mock(
            return_value=httpx.Response(200, json={})
        )
        old_state = SimpleNamespace(application_id="app123")
        identity.ApplicationResource.delete(self.client, old_state)
        request = respx_mock.calls[-1].request
        assert request.method == "DELETE"
        assert request.url.path == "/identity/api/applications/app123"

    def test_deps(self):
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        assert sut.deps() == []

    def test_read_missing_application_id(self, respx_mock):
        # Should handle missing application_id gracefully (simulate 404)
        respx_mock.get("/identity/api/applications/").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )
        old_state = SimpleNamespace(application_id="")
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        with pytest.raises(httpx.HTTPStatusError):
            sut.read(self.client, old_state)

    def test_create_missing_required_fields(self, respx_mock):
        # Should fail if required fields are missing (simulate 400)
        respx_mock.post("/identity/api/applications").mock(
            return_value=httpx.Response(400, json={"detail": "Missing required fields"})
        )
        sut = identity.ApplicationResource(
            id="app1",
            client_id="test_client",
            display_name="Test App",
            type=identity.ApplicationType.NATIVE,
        )
        with pytest.raises(httpx.HTTPStatusError):
            sut.create(self.client)

    def test_create_duplicate_application(self, respx_mock):
        # Simulate duplicate application (409 conflict)
        respx_mock.post("/identity/api/applications").mock(
            return_value=httpx.Response(409, json={"detail": "Duplicate application"})
        )
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        with pytest.raises(httpx.HTTPStatusError):
            sut.create(self.client)

    def test_delete_nonexistent_application(self, respx_mock):
        # Simulate deleting a non-existent application (404)
        respx_mock.delete("/identity/api/applications/app404").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )
        old_state = SimpleNamespace(application_id="app404")
        with pytest.raises(httpx.HTTPStatusError):
            identity.ApplicationResource.delete(self.client, old_state)

    def test_read_server_error(self, respx_mock):
        # Simulate server error on read (500)
        respx_mock.get("/identity/api/applications/app123").mock(
            return_value=httpx.Response(500, json={"detail": "Server error"})
        )
        old_state = SimpleNamespace(application_id="app123")
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        with pytest.raises(httpx.HTTPStatusError):
            sut.read(self.client, old_state)

    def test_create_server_error(self, respx_mock):
        # Simulate server error on create (500)
        respx_mock.post("/identity/api/applications").mock(
            return_value=httpx.Response(500, json={"detail": "Server error"})
        )
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        with pytest.raises(httpx.HTTPStatusError):
            sut.create(self.client)

    def test_update_with_server_error_on_delete(self, respx_mock):
        # Simulate server error on delete
        respx_mock.get("/identity/api/applications/app123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "app123",
                    "clientId": "cid",
                    "displayName": "App",
                    "type": "Native",
                    "secret": "sec",
                    "issuer": "iss",
                },
            )
        )
        respx_mock.delete("/identity/api/applications/app123").mock(
            return_value=httpx.Response(500, json={"detail": "Server error"})
        )
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        old_state = SimpleNamespace(
            application_id="app123", remote_version="oldhash", source_version="different_hash"
        )
        with pytest.raises(httpx.HTTPStatusError):
            sut.update(self.client, old_state)

    def test_update_with_server_error_on_create(self, respx_mock):
        # Simulate server error on create
        respx_mock.get("/identity/api/applications/app123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "app123",
                    "clientId": "cid",
                    "displayName": "App",
                    "type": "Native",
                    "secret": "sec",
                    "issuer": "iss",
                },
            )
        )
        respx_mock.delete("/identity/api/applications/app123").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/identity/api/applications").mock(
            return_value=httpx.Response(500, json={"detail": "Server error"})
        )
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        old_state = SimpleNamespace(
            application_id="app123", remote_version="oldhash", source_version="different_hash"
        )
        with pytest.raises(httpx.HTTPStatusError):
            sut.update(self.client, old_state)

    def test_update_remote_changed_source_unchanged(self, respx_mock):
        """Test update when remote has changed but source code hasn't changed"""
        # Setup: Create an ApplicationResource with specific content
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App",
            type=identity.ApplicationType.NATIVE,
        )
        # Calculate the source hash (this won't change)
        source_hash = sut.__get_content_hash__()
        # Mock the remote read to return different content than what was originally stored
        respx_mock.get("/identity/api/applications/app123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "app123",
                    "clientId": "cid",
                    "displayName": "App - Modified Remotely",  # Remote was changed
                    "type": "Native",
                    "secret": "sec",
                    "issuer": "iss",
                },
            )
        )
        # Mock delete and recreate operations
        respx_mock.delete("/identity/api/applications/app123").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/identity/api/applications").mock(
            return_value=httpx.Response(
                200, json={
                    "id": "app456",
                    "clientId": "cid",
                    "displayName": "App",  # Source content restored
                    "type": "Native",
                    "secret": "sec2",
                    "issuer": "iss2",
                }
            )
        )
        # Create old_state where source_version matches current source but remote_version is different
        old_remote_data = {
            "id": "app123",
            "clientId": "cid",
            "displayName": "App",  # Original remote content
            "type": "Native",
        }
        old_remote_hash = sha256(json.dumps(old_remote_data, sort_keys=True).encode()).hexdigest()
        old_state = SimpleNamespace(
            application_id="app123",
            source_version=source_hash,  # Source hasn't changed
            remote_version=old_remote_hash,  # But remote has changed - different from what read() return
        )
        # When update is called
        result = sut.update(self.client, old_state)
        # Then update should be performed (delete + create)
        assert result is not None
        assert result["application_id"] == "app456"
        assert sut.application_id == "app456"
        # Verify delete and create were called
        assert len(respx_mock.calls) == 3  # read, delete, create
        delete = respx_mock.calls[1]
        assert delete.request.method == "DELETE"
        post = respx_mock.calls[2]
        assert post.request.method == "POST"
        assert json.loads(post.request.content) == {
            "clientId": "cid",
            "type": "Native",
            "displayName": "App"
        }

    def test_update_source_changed_remote_unchanged(self, respx_mock):
        """Test update when source code has changed but remote hasn't changed"""
        # Setup: Create an ApplicationResource with modified content
        sut = identity.ApplicationResource(
            id="app1",
            client_id="cid",
            display_name="App - Modified Locally",  # Source was changed
            type=identity.ApplicationType.NATIVE,
        )
        # Mock the remote read to return the same content as stored in old_state
        original_remote_data = {
            "id": "app123",
            "clientId": "cid",
            "displayName": "App",  # Original content
            "type": "Native",
        }
        respx_mock.get("/identity/api/applications/app123").mock(
            return_value=httpx.Response(200, json=original_remote_data)
        )
        # Mock delete and recreate operations
        respx_mock.delete("/identity/api/applications/app123").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.post("/identity/api/applications").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "app456",
                    "clientId": "cid",
                    "displayName": "App - Modified Locally",  # New source content
                    "type": "Native",
                    "secret": "sec2",
                    "issuer": "iss2",
                },
            )
        )
        # Create old_state where remote_version matches what read returns but source_version is different
        old_remote_hash = sha256(json.dumps(original_remote_data, sort_keys=True).encode()).hexdigest()
        old_source_hash = sha256(
            json.dumps(
                {
                    "clientId": "cid",
                    "displayName": "App",  # Original source content
                    "type": "Native",
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        old_state = SimpleNamespace(
            application_id="app123",
            source_version=old_source_hash,  # Source has changed
            remote_version=old_remote_hash,  # Remote hasn't changed
        )
        # When update is called
        result = sut.update(self.client, old_state)
        # Then update should be performed (delete + create)
        assert result is not None
        assert result["application_id"] == "app456"
        assert sut.application_id == "app456"
        # Verify delete and create were called
        assert len(respx_mock.calls) == 3  # read, delete, create
        assert respx_mock.calls[1].request.method == "DELETE"
        assert respx_mock.calls[2].request.method == "POST"

    def test_dump(self):
        sut = identity.ApplicationResource(
            id="seven",
            client_id="cid",
            display_name="a great one",
            type=identity.ApplicationType.NATIVE,
            redirect_uris=["http://foo.example.com"],
            post_logout_redirect_uris=["http://boo.example.com"]
        )
        # when we dump it
        dump = sut.model_dump(by_alias=True, round_trip=True, exclude_none=True)
        # then we get all the input fields
        assert dump == {
            "clientId": "cid",
            "displayName": "a great one",
            "postLogoutRedirectUris": [
                "http://boo.example.com",
            ],
            "redirectUris": [
                "http://foo.example.com",
            ],
            "type": "Native"
        }

    def test_undump(self):
        # given dump data
        data = {
            "clientId": "cid",
            "displayName": "a great one",
            "postLogoutRedirectUris": [
                "http://boo.example.com",
            ],
            "redirectUris": [
                "http://foo.example.com",
            ],
            "type": "Native"
        }
        # when we undump it
        result = identity.ApplicationResource.model_validate(
            data, context={"style": "undump", "id": "app3"}
        )
        # then the id is extracted from the context
        assert result.id == "app3"

    def test_parse_api_format(self):
        # give a response from the get endpoint
        data = {
           "id": "UniqueApplicationId",
           "type": "Native",
           "displayName": "Example Native Application",
           "secret": "123456789",
           "clientId": "my-example-native-app",
           "issuer": "https://exampleiusser.lusid.com"
        }
        # when we read it
        sut = identity.ApplicationResource.model_validate(data, context={"id": "res-id"})
        # the resource id is from the context (not the body)
        assert sut.id == "res-id"
        # the application_id  is from the id
        assert sut.application_id == "UniqueApplicationId"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeApplicationRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_attach_when_exists(self, respx_mock):
        # given 2 applications in the system where app2 matches the sut
        respx_mock.get("/identity/api/applications").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "app11111111",
                        "clientId": "client1",
                        "displayName": "Application One",
                        "type": "Web",
                    },
                    {
                        "id": "app22222222",
                        "clientId": "client2",
                        "displayName": "Application Two",
                        "type": "Service",
                    },
                ],
            )
        )
        client = self.client
        # when we attach
        sut = identity.ApplicationRef(id="xyz", client_id="client2")
        sut.attach(client)
        # then the application_id property is populated from the response
        assert sut.application_id == "app22222222"

    def test_attach_when_not_exists(self, respx_mock):
        # given 2 applications in the system where neither matches the sut
        respx_mock.get("/identity/api/applications").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "app11111111",
                        "clientId": "client1",
                        "displayName": "Application One",
                        "type": "Web",
                    },
                    {
                        "id": "app22222222",
                        "clientId": "client2",
                        "displayName": "Application Two",
                        "type": "Service",
                    },
                ],
            )
        )
        client = self.client
        # when we attach, an exception is thrown
        sut = identity.ApplicationRef(id="xyz", client_id="none_of_those")
        with pytest.raises(RuntimeError, match="No matching application with client ID none_of_those"):
            sut.attach(client)

    def test_attach_when_http_error(self, respx_mock):
        # given a server which returns a 500
        respx_mock.get("/identity/api/applications").mock(return_value=httpx.Response(500, json={}))
        client = self.client
        # when we attach, an http exception is thrown
        sut = identity.ApplicationRef(id="xyz", client_id="client1")
        with pytest.raises(httpx.HTTPStatusError):
            sut.attach(client)
