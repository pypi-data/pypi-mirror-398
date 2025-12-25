import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import property, side_definition

TEST_BASE = "https://foo.lusid.com"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeSideRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/api/api/transactionconfiguration/sides/sd1?scope=sc1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = side_definition.SideRef(id="one", scope="sc1", side="sd1")
        # when we call attach
        sut.attach(client)
        # then a get request was made with the scope passed as a parameter
        req = respx_mock.calls.last.request
        assert dict(req.url.params) == {"scope": "sc1"}

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/api/api/transactionconfiguration/sides/sd2?scope=sc1").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        sut = side_definition.SideRef(id="two", scope="sc1", side="sd2")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Side sd2 does not exist in scope sc1" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/api/api/transactionconfiguration/sides/sd3?scope=sc1").mock(
            return_value=httpx.Response(400, json={})
        )
        client = self.client
        sut = side_definition.SideRef(id="three", scope="sc1", side="sd3")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeSideResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def property_definition_refs(self):
        names = ["a", "b", "c", "d", "e", "f"]
        return [
            property.DefinitionRef(id=name, domain=property.Domain.Transaction, scope="sc1", code=name)
            for name in names
        ]

    @pytest.fixture
    def side_resource_side_1(self):
        return side_definition.SideResource(
            id="one",
            side="sd1",
            scope="sc1",
            security="Txn:LusidInstrumentId",
            currency="Txn:TradeCurrency",
            rate="Txn:TradeToPortfolioRate",
            units="Txn:Units",
            amount="Txn:TradeAmount",
            notional_amount="0",
        )

    @pytest.fixture
    def property_definition_resources(self):
        names = ["a", "b", "c", "d", "e", "f"]
        return [
            property.DefinitionResource(
                id=name,
                domain=property.Domain.Transaction,
                scope="sc1",
                code=name,
                display_name="Example Display Name",
                data_type_id=property.ResourceId(scope="system", code="number"),
                property_description="Example property description",
                life_time=property.LifeTime.Perpetual,
                constraint_style=property.ConstraintStyle.Property,
            )
            for name in names
        ]

    @pytest.fixture
    def definition_fixtures(self, request):
        return request.getfixturevalue(request.param)

    def test_create_side(self, respx_mock, side_resource_side_1):
        respx_mock.put("/api/api/transactionconfiguration/sides/sd1?scope=sc1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = side_resource_side_1
        state = sut.create(client)

        req = respx_mock.calls.last.request

        assert json.loads(req.content) == {
            "side": "sd1",
            "security": "Txn:LusidInstrumentId",
            "currency": "Txn:TradeCurrency",
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": "Txn:TradeAmount",
            "notionalAmount": "0"
        }
        assert state == {"side": "sd1", "scope": "sc1"}

    def test_create_side_with_current_face(self, respx_mock):
        respx_mock.put("/api/api/transactionconfiguration/sides/sd1?scope=sc1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = side_definition.SideResource(
            id="one",
            side="sd1",
            scope="sc1",
            security="Txn:LusidInstrumentId",
            currency="Txn:TradeCurrency",
            rate="Txn:TradeToPortfolioRate",
            units="Txn:Units",
            amount="Txn:TradeAmount",
            notional_amount="0",
            current_face="Txn:CurrentFace",
        )
        state = sut.create(client)

        req = respx_mock.calls.last.request

        assert json.loads(req.content) == {
            "side": "sd1",
            "security": "Txn:LusidInstrumentId",
            "currency": "Txn:TradeCurrency",
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": "Txn:TradeAmount",
            "notionalAmount": "0",
            "currentFace": "Txn:CurrentFace"
        }
        assert state == {"side": "sd1", "scope": "sc1"}

    def test_create_side_with_current_face_property_ref(self, respx_mock, property_definition_refs):
        respx_mock.put("/api/api/transactionconfiguration/sides/sd1?scope=sc1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = side_definition.SideResource(
            id="one",
            side="sd1",
            scope="sc1",
            security="Txn:LusidInstrumentId",
            currency="Txn:TradeCurrency",
            rate="Txn:TradeToPortfolioRate",
            units="Txn:Units",
            amount="Txn:TradeAmount",
            notional_amount="0",
            current_face=property_definition_refs[0],
        )
        state = sut.create(client)

        req = respx_mock.calls.last.request

        assert json.loads(req.content) == {
            "side": "sd1",
            "security": "Txn:LusidInstrumentId",
            "currency": "Txn:TradeCurrency",
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": "Txn:TradeAmount",
            "notionalAmount": "0",
            "currentFace": "Transaction/sc1/a"
        }
        assert state == {"side": "sd1", "scope": "sc1"}

    @pytest.mark.parametrize(
        "definition_fixtures",
        ["property_definition_refs", "property_definition_resources"],
        indirect=True,
    )
    def test_create_side_with_property_definitions(self, respx_mock, definition_fixtures):
        prop_resources = definition_fixtures

        respx_mock.put("/api/api/transactionconfiguration/sides/sd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = side_definition.SideResource(
            id="one",
            side="sd1",
            scope="sc1",
            security=prop_resources[0],
            currency=prop_resources[1],
            rate=prop_resources[2],
            units=prop_resources[3],
            amount=prop_resources[4],
            notional_amount=prop_resources[5],
        )

        state = sut.create(client)

        req = respx_mock.calls.last.request
        assert sut.deps() == [
            prop_resources[0],
            prop_resources[1],
            prop_resources[4],
            prop_resources[2],
            prop_resources[3],
            prop_resources[5],
        ]

        assert json.loads(req.content) == {
            "side": "sd1",
            "security": "Transaction/sc1/a",
            "currency": "Transaction/sc1/b",
            "rate": "Transaction/sc1/c",
            "units": "Transaction/sc1/d",
            "amount": "Transaction/sc1/e",
            "notionalAmount": "Transaction/sc1/f",
        }
        assert state == {"side": "sd1", "scope": "sc1"}

    def test_create_side_with_mixed_definitions(
        self, respx_mock, property_definition_refs, property_definition_resources
    ):
        respx_mock.put("/api/api/transactionconfiguration/sides/sd1?scope=sc1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = side_definition.SideResource(
            id="one",
            side="sd1",
            scope="sc1",
            security=property_definition_refs.pop(0),
            currency=property_definition_refs.pop(0),
            rate=property_definition_resources.pop(0),
            units=property_definition_resources.pop(0),
            amount="Txn:TradeAmount",
            notional_amount="0",
        )

        state = sut.create(client)

        req = respx_mock.calls.last.request

        assert sut.deps() == [
            property.DefinitionRef(id="a", domain=property.Domain.Transaction, scope="sc1", code="a"),
            property.DefinitionRef(id="b", domain=property.Domain.Transaction, scope="sc1", code="b"),
            property.DefinitionResource(
                id="a",
                domain=property.Domain.Transaction,
                scope="sc1",
                code="a",
                display_name="Example Display Name",
                data_type_id=property.ResourceId(scope="system", code="number"),
                property_description="Example property description",
                life_time=property.LifeTime.Perpetual,
                constraint_style=property.ConstraintStyle.Property,
            ),
            property.DefinitionResource(
                id="b",
                domain=property.Domain.Transaction,
                scope="sc1",
                code="b",
                display_name="Example Display Name",
                data_type_id=property.ResourceId(scope="system", code="number"),
                property_description="Example property description",
                life_time=property.LifeTime.Perpetual,
                constraint_style=property.ConstraintStyle.Property,
            ),
        ]

        assert json.loads(req.content) == {
            "side": "sd1",
            "security": "Transaction/sc1/a",
            "currency": "Transaction/sc1/b",
            "rate": "Transaction/sc1/a",
            "units": "Transaction/sc1/b",
            "amount": "Txn:TradeAmount",
            "notionalAmount": "0",
        }
        assert state == {"side": "sd1", "scope": "sc1"}

    def test_read_side(self, respx_mock, side_resource_side_1):
        respx_mock.get("/api/api/transactionconfiguration/sides/sd1?scope=sc1").mock(
            return_value=httpx.Response(200, json=side_resource_side_1.model_dump(by_alias=True))
        )

        client = self.client
        old_state = SimpleNamespace(scope="sc1", side="sd1")

        sut = side_resource_side_1

        remote = sut.read(client, old_state)
        assert remote == side_resource_side_1.model_dump(by_alias=True)
        assert {"scope": old_state.scope, "side": old_state.side} == {
            "scope": sut.scope,
            "side": sut.side,
        }

    def test_read_side_failure_not_found(self, respx_mock, side_resource_side_1):
        respx_mock.get("/api/api/transactionconfiguration/sides/sd1?scope=sc1").mock(
            return_value=httpx.Response(404)
        )
        old_state = SimpleNamespace(scope="sc1", side="sd1")
        client = self.client
        sut = side_resource_side_1

        with pytest.raises(httpx.HTTPStatusError):
            remote = sut.read(client, old_state)
            assert remote is None

    def test_delete_side(self, respx_mock, side_resource_side_1):
        respx_mock.delete("/api/api/transactionconfiguration/sides/sd1/$delete?scope=sc1").mock(
            return_value=httpx.Response(200)
        )
        client = self.client
        old_state = SimpleNamespace(scope="sc1", side="sd1")
        sut = side_resource_side_1

        sut.delete(client, old_state)

    def test_delete_side_missing(self, respx_mock, side_resource_side_1):
        respx_mock.delete("/api/api/transactionconfiguration/sides/sd1/$delete?scope=sc1").mock(
            return_value=httpx.Response(404)
        )
        client = self.client
        old_state = SimpleNamespace(scope="sc1", side="sd1")
        sut = side_resource_side_1

        with pytest.raises(httpx.HTTPStatusError):
            sut.delete(client, old_state)

    def test_update_side_no_change(self, respx_mock, side_resource_side_1):
        respx_mock.get("/api/api/transactionconfiguration/sides/sd1?scope=sc1").mock(
            return_value=httpx.Response(200, json=side_resource_side_1.model_dump(by_alias=True))
        )

        client = self.client

        sut = side_resource_side_1
        old_state = SimpleNamespace(scope="sc1", side="sd1")
        state = sut.update(client, old_state)
        assert state is None

    @pytest.mark.parametrize(
        "update_changes",
        [
            {
                "does_require_get": False,
                "put_side": "sd1",
                "put_scope": "sc2",
                "put_response": {
                    "side": "sd1",
                    "security": "Txn:LusidInstrumentId",
                    "currency": "Txn:TradeCurrency",
                    "rate": "Txn:TradeToPortfolioRate",
                    "units": "Txn:Units",
                    "amount": "Txn:TradeAmount",
                    "notionalAmount": "0",
                },
                "resource": side_definition.SideResource(
                    id="two",
                    side="sd1",
                    scope="sc2",
                    security="Txn:LusidInstrumentId",
                    currency="Txn:TradeCurrency",
                    rate="Txn:TradeToPortfolioRate",
                    units="Txn:Units",
                    amount="Txn:TradeAmount",
                    notional_amount="0",
                ),
            },
        ],
    )
    def test_update_side_change_scope(self, respx_mock, update_changes):
        respx_mock.put(
            "/api/api/transactionconfiguration/sides/sd1?scope=sc2"
        ).mock(return_value=httpx.Response(200, json=update_changes["put_response"]))
        respx_mock.delete("/api/api/transactionconfiguration/sides/sd1/$delete?scope=sc1").mock(
            return_value=httpx.Response(200)
        )
        # given the remote has scope sc1
        old_state = SimpleNamespace(scope="sc1", side="sd1")
        sut = update_changes["resource"]
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is changed
        assert state != old_state
        # and the old one got deleted
        assert respx_mock.calls[0].request.method == "DELETE"

    @pytest.mark.parametrize(
        "update_changes",
        [
            {
                "put_response": {
                    "side": "sd2",
                    "security": "Txn:LusidInstrumentId",
                    "currency": "Txn:TradeCurrency",
                    "rate": "Txn:TradeToPortfolioRate",
                    "units": "Txn:Units",
                    "amount": "Txn:TradeAmount",
                    "notionalAmount": "0",
                },
                "resource": side_definition.SideResource(
                    id="two",
                    side="sd2",
                    scope="sc1",
                    security="Txn:LusidInstrumentId",
                    currency="Txn:TradeCurrency",
                    rate="Txn:TradeToPortfolioRate",
                    units="Txn:Units",
                    amount="Txn:TradeAmount",
                    notional_amount="0",
                ),
            },
        ],
    )
    def test_update_side_changed_sidename(self, respx_mock, update_changes):
        respx_mock.put(
            "/api/api/transactionconfiguration/sides/sd2?scope=sc1"
        ).mock(return_value=httpx.Response(200, json=update_changes["put_response"]))
        respx_mock.delete("/api/api/transactionconfiguration/sides/sd1/$delete?scope=sc1").mock(
            return_value=httpx.Response(200)
        )
        # given a side with sc1/sd1
        old_state = SimpleNamespace(scope="sc1", side="sd1")
        # when we update it it to sc1/sd2
        sut = update_changes["resource"]
        state = sut.update(self.client, old_state)
        assert state != old_state
        # and the old one got deleted
        assert respx_mock.calls[0].request.method == "DELETE"

    @pytest.mark.parametrize(
        "update_changes",
        [
            {
                "does_require_get": True,
                "put_side": "sd1",
                "put_scope": "sc1",
                "put_response": {
                    "side": "sd1",
                    "security": "Txn:TradeCurrency",
                    "currency": "Txn:TradeCurrency",
                    "rate": "Txn:TradeToPortfolioRate",
                    "units": "Txn:Units",
                    "amount": "Txn:TradeAmount",
                    "notionalAmount": "0",
                },
                "resource": side_definition.SideResource(
                    id="one",
                    side="sd1",
                    scope="sc1",
                    security="Txn:TradeCurrency",
                    currency="Txn:TradeCurrency",
                    rate="Txn:TradeToPortfolioRate",
                    units="Txn:Units",
                    amount="Txn:TradeAmount",
                    notional_amount="0",
                ),
                "get_side": "sd1",
                "get_scope": "sc1",
                "get_response": {
                    "side": "sd1",
                    "security": "Txn:LusidInstrumentId",
                    "currency": "Txn:TradeCurrency",
                    "rate": "Txn:TradeToPortfolioRate",
                    "units": "Txn:Units",
                    "amount": "Txn:TradeAmount",
                    "notionalAmount": "0",
                },
            },
        ],
    )
    def test_update_side_change_security(self, respx_mock, update_changes):
        respx_mock.put(
            "/api/api/transactionconfiguration/sides/sd1?scope=sc1"
        ).mock(return_value=httpx.Response(200, json=update_changes["put_response"]))
        respx_mock.get(
            "/api/api/transactionconfiguration/sides/sd1?scope=sc1"
        ).mock(return_value=httpx.Response(200, json=update_changes["get_response"]))
        # given the side exists with Luid for seccurity
        old_state = SimpleNamespace(scope="sc1", side="sd1")
        # when we update to use trade currency
        sut = update_changes["resource"]
        state = sut.update(self.client, old_state)
        # then the state is returned
        assert state == {"scope": old_state.scope, "side": old_state.side}
        # and the put request is made to modify the side
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == update_changes["put_response"]

    def test_deps(self, property_definition_refs):
        sut = side_definition.SideResource(
            id="one",
            side="sd1",
            scope="sc1",
            security=property_definition_refs[0],
            currency=property_definition_refs[1],
            rate=property_definition_refs[2],
            units=property_definition_refs[2],
            amount="Txn:TradeAmount",
            notional_amount="0",
        )
        deps = sut.deps()
        assert deps == [
            property.DefinitionRef(id="a", domain=property.Domain.Transaction, scope="sc1", code="a"),
            property.DefinitionRef(id="b", domain=property.Domain.Transaction, scope="sc1", code="b"),
            property.DefinitionRef(id="c", domain=property.Domain.Transaction, scope="sc1", code="c"),
            property.DefinitionRef(id="c", domain=property.Domain.Transaction, scope="sc1", code="c"),
        ]

    def test_deps_with_current_face(self, property_definition_refs):
        sut = side_definition.SideResource(
            id="one",
            side="sd1",
            scope="sc1",
            security=property_definition_refs[0],
            currency=property_definition_refs[1],
            rate=property_definition_refs[2],
            units=property_definition_refs[2],
            amount="Txn:TradeAmount",
            notional_amount="0",
            current_face=property_definition_refs[3],
        )
        deps = sut.deps()
        assert deps == [
            property.DefinitionRef(id="a", domain=property.Domain.Transaction, scope="sc1", code="a"),
            property.DefinitionRef(id="b", domain=property.Domain.Transaction, scope="sc1", code="b"),
            property.DefinitionRef(id="c", domain=property.Domain.Transaction, scope="sc1", code="c"),
            property.DefinitionRef(id="c", domain=property.Domain.Transaction, scope="sc1", code="c"),
            property.DefinitionRef(id="d", domain=property.Domain.Transaction, scope="sc1", code="d"),
        ]

    def test_deps_with_current_face_string(self, property_definition_refs):
        # current_face as string should not be in deps
        sut = side_definition.SideResource(
            id="one",
            side="sd1",
            scope="sc1",
            security=property_definition_refs[0],
            currency=property_definition_refs[1],
            rate=property_definition_refs[2],
            units=property_definition_refs[2],
            amount="Txn:TradeAmount",
            notional_amount="0",
            current_face="Txn:CurrentFace",
        )
        deps = sut.deps()
        # Should not include current_face since it's a string
        assert deps == [
            property.DefinitionRef(id="a", domain=property.Domain.Transaction, scope="sc1", code="a"),
            property.DefinitionRef(id="b", domain=property.Domain.Transaction, scope="sc1", code="b"),
            property.DefinitionRef(id="c", domain=property.Domain.Transaction, scope="sc1", code="c"),
            property.DefinitionRef(id="c", domain=property.Domain.Transaction, scope="sc1", code="c"),
        ]

    def test_dump(self, side_resource_side_1):
        # given a side resource with string values (no property refs)
        sut = side_resource_side_1
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then it includes scope and side information with string values
        expected = {
            "side": "sd1",
            "scope": "sc1",
            "security": "Txn:LusidInstrumentId",
            "currency": "Txn:TradeCurrency",
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": "Txn:TradeAmount",
            "notionalAmount": "0"
        }
        assert result == expected

    def test_dump_with_current_face(self):
        # given a side resource with current_face
        sut = side_definition.SideResource(
            id="one",
            side="sd1",
            scope="sc1",
            security="Txn:LusidInstrumentId",
            currency="Txn:TradeCurrency",
            rate="Txn:TradeToPortfolioRate",
            units="Txn:Units",
            amount="Txn:TradeAmount",
            notional_amount="0",
            current_face="Txn:CurrentFace",
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then current_face is included
        expected = {
            "side": "sd1",
            "scope": "sc1",
            "security": "Txn:LusidInstrumentId",
            "currency": "Txn:TradeCurrency",
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": "Txn:TradeAmount",
            "notionalAmount": "0",
            "currentFace": "Txn:CurrentFace"
        }
        assert result == expected

    def test_dump_with_property_refs(self, property_definition_refs):
        # given a side resource with property definition references
        sut = side_definition.SideResource(
            id="side_with_refs",
            side="sd1",
            scope="sc1",
            security=property_definition_refs[0],  # DefinitionRef
            currency=property_definition_refs[1],  # DefinitionRef
            rate="Txn:TradeToPortfolioRate",       # string
            units="Txn:Units",                     # string
            amount=property_definition_refs[2],    # DefinitionRef
            notional_amount="0"                    # string
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then property refs are serialized as $ref and strings remain as strings
        expected = {
            "side": "sd1",
            "scope": "sc1",
            "security": {"$ref": "a"},
            "currency": {"$ref": "b"},
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": {"$ref": "c"},
            "notionalAmount": "0"
        }
        assert result == expected

    def test_dump_with_property_refs_and_current_face(self, property_definition_refs):
        # given a side resource with property definition references including current_face
        sut = side_definition.SideResource(
            id="side_with_refs",
            side="sd1",
            scope="sc1",
            security=property_definition_refs[0],  # DefinitionRef
            currency=property_definition_refs[1],  # DefinitionRef
            rate="Txn:TradeToPortfolioRate",       # string
            units="Txn:Units",                     # string
            amount=property_definition_refs[2],    # DefinitionRef
            notional_amount="0",                   # string
            current_face=property_definition_refs[3]  # DefinitionRef
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then property refs including current_face are serialized as $ref
        expected = {
            "side": "sd1",
            "scope": "sc1",
            "security": {"$ref": "a"},
            "currency": {"$ref": "b"},
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": {"$ref": "c"},
            "notionalAmount": "0",
            "currentFace": {"$ref": "d"}
        }
        assert result == expected

    def test_undump(self):
        # given dump data with string values
        data = {
            "side": "sd1",
            "scope": "sc1",
            "security": "Txn:LusidInstrumentId",
            "currency": "Txn:TradeCurrency",
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": "Txn:TradeAmount",
            "notionalAmount": "0"
        }
        # when we undump it
        result = side_definition.SideResource.model_validate(
            data, context={"style": "undump", "id": "side_id"}
        )
        # then it's correctly populated
        assert result.id == "side_id"
        assert result.side == "sd1"
        assert result.scope == "sc1"
        assert result.security == "Txn:LusidInstrumentId"
        assert result.currency == "Txn:TradeCurrency"
        assert result.rate == "Txn:TradeToPortfolioRate"
        assert result.units == "Txn:Units"
        assert result.amount == "Txn:TradeAmount"
        assert result.notional_amount == "0"
        assert result.current_face is None

    def test_undump_with_current_face(self):
        # given dump data with current_face
        data = {
            "side": "sd1",
            "scope": "sc1",
            "security": "Txn:LusidInstrumentId",
            "currency": "Txn:TradeCurrency",
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": "Txn:TradeAmount",
            "notionalAmount": "0",
            "currentFace": "Txn:CurrentFace"
        }
        # when we undump it
        result = side_definition.SideResource.model_validate(
            data, context={"style": "undump", "id": "side_id"}
        )
        # then it's correctly populated including current_face
        assert result.id == "side_id"
        assert result.side == "sd1"
        assert result.scope == "sc1"
        assert result.security == "Txn:LusidInstrumentId"
        assert result.currency == "Txn:TradeCurrency"
        assert result.rate == "Txn:TradeToPortfolioRate"
        assert result.units == "Txn:Units"
        assert result.amount == "Txn:TradeAmount"
        assert result.notional_amount == "0"
        assert result.current_face == "Txn:CurrentFace"

    def test_undump_with_property_refs(self, property_definition_refs):
        # given dump data with $ref values
        data = {
            "side": "sd1",
            "scope": "sc1",
            "security": {"$ref": "a"},
            "currency": {"$ref": "b"},
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": {"$ref": "c"},
            "notionalAmount": "0"
        }
        # when we undump it with $refs context
        refs_dict = {ref.id: ref for ref in property_definition_refs}
        result = side_definition.SideResource.model_validate(
            data, context={"style": "undump", "$refs": refs_dict, "id": "side_id"}
        )
        # then property refs are resolved and strings remain as strings
        assert result.id == "side_id"
        assert result.side == "sd1"
        assert result.scope == "sc1"
        assert result.security == property_definition_refs[0]  # resolved DefinitionRef
        assert result.currency == property_definition_refs[1]  # resolved DefinitionRef
        assert result.rate == "Txn:TradeToPortfolioRate"       # string
        assert result.units == "Txn:Units"                     # string
        assert result.amount == property_definition_refs[2]    # resolved DefinitionRef
        assert result.notional_amount == "0"                   # string
        assert result.current_face is None                     # not in data

    def test_undump_with_property_refs_and_current_face(self, property_definition_refs):
        # given dump data with $ref values including current_face
        data = {
            "side": "sd1",
            "scope": "sc1",
            "security": {"$ref": "a"},
            "currency": {"$ref": "b"},
            "rate": "Txn:TradeToPortfolioRate",
            "units": "Txn:Units",
            "amount": {"$ref": "c"},
            "notionalAmount": "0",
            "currentFace": {"$ref": "d"}
        }
        # when we undump it with $refs context
        refs_dict = {ref.id: ref for ref in property_definition_refs}
        result = side_definition.SideResource.model_validate(
            data, context={"style": "undump", "$refs": refs_dict, "id": "side_id"}
        )
        # then property refs including current_face are resolved
        assert result.id == "side_id"
        assert result.side == "sd1"
        assert result.scope == "sc1"
        assert result.security == property_definition_refs[0]  # resolved DefinitionRef
        assert result.currency == property_definition_refs[1]  # resolved DefinitionRef
        assert result.rate == "Txn:TradeToPortfolioRate"       # string
        assert result.units == "Txn:Units"                     # string
        assert result.amount == property_definition_refs[2]    # resolved DefinitionRef
        assert result.notional_amount == "0"                   # string
        assert result.current_face == property_definition_refs[3]  # resolved DefinitionRef
