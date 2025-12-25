import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import datatype, property

TEST_BASE = "https://foo.lusid.com"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeDefinitionRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def test_attach_when_present(self, respx_mock):
        # given that the remote definition exists
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = property.DefinitionRef(id="one", domain=property.Domain.Holding, scope="sc1", code="cd1")
        # when we call attach
        sut.attach(client)
        # then a get request was made and no exception raised

    def test_attach_when_missing(self, respx_mock):
        # given the remote does not exist
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(404, json={})
        )
        client = self.client
        sut = property.DefinitionRef(id="one", domain=property.Domain.Holding, scope="sc1", code="cd1")
        # when we call attach an exception is raised
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Property definition Holding/sc1/cd" in str(ex.value)

    def test_attach_when_http_error(self, respx_mock):
        # given the server returns an error
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(400, json={})
        )
        client = self.client
        sut = property.DefinitionRef(id="one", domain=property.Domain.Holding, scope="sc1", code="cd1")
        # when we call attach an exception is raised
        with pytest.raises(httpx.HTTPError):
            sut.attach(client)


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeDefinitionResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def property_refs(self):
        names = ["x", "y"]
        domain = property.Domain.Instrument
        return [
            property.DefinitionRef(id=name, domain=domain, scope="refs", code=name) for name in names
        ]

    def test_create_value_prop(self, respx_mock):
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            life_time=property.LifeTime.Perpetual,
            constraint_style=property.ConstraintStyle.Property,
        )
        # when we call create
        state = sut.create(client)
        # then a post is made with the expected fields
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "ids", "code": "idc"},
            "propertyDescription": "description",
            "lifeTime": "Perpetual",
            "constraintStyle": "Property",
        }
        assert state == {"scope": "sc1", "code": "cd1", "domain": "Holding", "derived": False}

    def test_create_value_prop_optional_fields(self, respx_mock):
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
        )
        # when we call create
        sut.create(client)
        # then a post is made with the expected fields
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "ids", "code": "idc"},
        }

    def test_create_derived_prop(self, respx_mock, property_refs):
        respx_mock.post("/api/api/propertydefinitions/derived").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            derivation_formula=property.Formula("{a} + {b}", a=property_refs[0], b=property_refs[1]),
            is_filterable=False,
        )
        # when we call create
        state = sut.create(client)
        # then a post is made with the expected fields
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "ids", "code": "idc"},
            "propertyDescription": "description",
            "derivationFormula": "Properties[Instrument/refs/x] + Properties[Instrument/refs/y]",
            "isFilterable": False,
        }
        assert state == {"scope": "sc1", "code": "cd1", "domain": "Holding", "derived": True}

    def test_create_value_prop_datatype_ref(self, respx_mock):
        # create definition
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(200, json={}))
        # get datatype
        respx_mock.get("/api/api/datatypes/system/currency").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # given a references to a currency datatype that exists
        dt = datatype.DataTypeRef(id="dt", scope="system", code="currency")
        dt.attach(client)
        # when we use the datatype in the property definition
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=dt,
            property_description="description",
            life_time=property.LifeTime.Perpetual,
            constraint_style=property.ConstraintStyle.Property,
        )
        # when we call create
        state = sut.create(client)
        # then a post is made using the scope and code of the datatype
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "system", "code": "currency"},
            "propertyDescription": "description",
            "lifeTime": "Perpetual",
            "constraintStyle": "Property",
        }
        assert state == {"scope": "sc1", "code": "cd1", "domain": "Holding", "derived": False}

    def test_create_value_prop_datatype_resource(self, respx_mock):
        # create definition
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(200, json={}))
        # create datatype
        respx_mock.post("/api/api/datatypes").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # given a datatype resource that gets created during the deploy
        dt = datatype.DataTypeResource(
            id="dt",
            scope="dtscope",
            code="dtcode",
            type_value_range=datatype.TypeValueRange.CLOSED,
            display_name="Priority Test",
            description="A test datatype for Priority",
            value_type=datatype.ValueType.STRING,
            acceptable_values=["High", "Medium", "Low"],
        )
        dt.create(client)
        # when we use the datatype in the property definition
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=dt,
            property_description="description",
            life_time=property.LifeTime.Perpetual,
            constraint_style=property.ConstraintStyle.Property,
        )
        # when we call create
        state = sut.create(client)
        # then a post is made using the scope and code of the datatype
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "dtscope", "code": "dtcode"},
            "propertyDescription": "description",
            "lifeTime": "Perpetual",
            "constraintStyle": "Property",
        }
        assert state == {"scope": "sc1", "code": "cd1", "domain": "Holding", "derived": False}

    @staticmethod
    def test_validates_no_is_filterable_on_value_prop():
        with pytest.raises(RuntimeError) as err:
            property.DefinitionResource(
                id="one",
                domain=property.Domain.Holding,
                scope="sc1",
                code="cd1",
                display_name="name",
                data_type_id=property.ResourceId(scope="ids", code="idc"),
                property_description="description",
                life_time=property.LifeTime.Perpetual,
                is_filterable=False,
            )
        assert (
            str(err.value)
            == "Cannot set 'is_filterable' field, a property must be either derived or plain"
        )

    @staticmethod
    def test_validates_no_lifetime_on_derived():
        with pytest.raises(RuntimeError):
            property.DefinitionResource(
                id="one",
                domain=property.Domain.Holding,
                scope="sc1",
                code="cd1",
                display_name="name",
                data_type_id=property.ResourceId(scope="ids", code="idc"),
                property_description="description",
                life_time=property.LifeTime.Perpetual,
                derivation_formula=property.Formula("3 + 4"),
            )

    @staticmethod
    def test_validates_no_constraint_on_derived():
        with pytest.raises(RuntimeError):
            property.DefinitionResource(
                id="one",
                domain=property.Domain.Holding,
                scope="sc1",
                code="cd1",
                display_name="name",
                data_type_id=property.ResourceId(scope="ids", code="idc"),
                property_description="description",
                constraint_style=property.ConstraintStyle.Identifier,
                derivation_formula=property.Formula("3 + 4"),
            )

    @staticmethod
    def test_validates_no_collection_on_derived():
        with pytest.raises(RuntimeError):
            property.DefinitionResource(
                id="one",
                domain=property.Domain.Holding,
                scope="sc1",
                code="cd1",
                display_name="name",
                data_type_id=property.ResourceId(scope="ids", code="idc"),
                property_description="description",
                collection_type=property.CollectionType.Set,
                derivation_formula=property.Formula("3 + 4"),
            )

    @staticmethod
    def test_value_prop_deps():
        # give a value property
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
        )
        # it has no dependencies
        assert sut.deps() == []

    @staticmethod
    def test_valueprop_datatype_deps():
        # given a datatype resource that gets created during the deploy
        dt = datatype.DataTypeResource(
            id="dt",
            scope="dtscope",
            code="dtcode",
            type_value_range=datatype.TypeValueRange.CLOSED,
            display_name="Priority Test",
            description="A test datatype for Priority",
            value_type=datatype.ValueType.STRING,
            acceptable_values=["High", "Medium", "Low"],
        )
        # and the property refers to the datatype
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=dt,
        )
        # the datatype is included in the deps of the property
        assert sut.deps() == [dt]

    @staticmethod
    def test_derived_prop_deps(property_refs):
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            derivation_formula=property.Formula("{a} + {b}", a=property_refs[0], b=property_refs[1]),
        )
        assert sut.deps() == property_refs

    def test_formula_with_resource(self, respx_mock):
        respx_mock.post("/api/api/propertydefinitions/derived").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # given a value property
        used = property.DefinitionResource(
            id="two",
            domain=property.Domain.Instrument,
            scope="sc2",
            code="cd2",
            display_name="two",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
        )
        # and it is referenced in a formula on a derived prop
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            derivation_formula=property.Formula("2 * {a}", a=used),
            is_filterable=True,
        )
        # and we call create
        sut.create(client)
        # then a post is made with identifier of used
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "ids", "code": "idc"},
            "propertyDescription": "description",
            "derivationFormula": "2 * Properties[Instrument/sc2/cd2]",
            "isFilterable": True,
        }

    def test_parse_api_format_derived_prop(self):
        # given a datatype
        dt = datatype.DataTypeResource(
            id="dt",
            scope="ids",
            code="idc",
            type_value_range=datatype.TypeValueRange.CLOSED,
            display_name="Priority Test",
            description="A test datatype for Priority",
            value_type=datatype.ValueType.STRING,
        )
        # given a derived property in almost api format
        example = {
            "id": "one",
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"$ref": "dt_resource_id"},
            "propertyDescription": "description",
            "derivationFormula": {"formula": "{a} + {b}", "args": {"a": "x", "b": "y"}},
        }
        # when we parse it
        context = {"$refs": {"dt_resource_id": dt}}
        sut = property.DefinitionResource.model_validate(example, context=context)
        # the property fields are set
        assert sut.scope == "sc1"
        # and the datatype has been extracted from the context argsp
        assert sut.data_type_id.scope == "ids"
        assert sut.data_type_id.code == "idc"

    def test_formula_with_non_resource(self, respx_mock):
        respx_mock.post("/api/api/propertydefinitions/derived").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # given a derived formula with numbers passed in
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            derivation_formula=property.Formula("2 * {a}", a=17),
        )
        # and we call create
        sut.create(client)
        # then a post is made with identifier of used
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "ids", "code": "idc"},
            "propertyDescription": "description",
            "derivationFormula": "2 * 17",
        }
        # and the deps are empty
        assert sut.deps() == []

    def test_update_no_change(self, respx_mock):
        # given a derived property exists with y=2x17
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Holding",
                    "scope": "sc1",
                    "code": "cd1",
                    "displayName": "name",
                    "dataTypeId": {"scope": "ids", "code": "idc"},
                    "propertyDescription": "description",
                    "derivationFormula": "2 * 17",
                    "isFilterable": False,
                },
            )
        )
        client = self.client
        # when we update with the same properties
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            derivation_formula=property.Formula("2 * {a}", a=17),
            is_filterable=False,
        )
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=True)
        state = sut.update(client, old_state)
        # the new state is None and no put was made
        assert state is None

    def test_update_valueprop_name(self, respx_mock):
        # given a derived property exists with y=2x17
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Holding",
                    "scope": "sc1",
                    "code": "cd1",
                    "displayName": "name1",
                    "dataTypeId": {"scope": "ids", "code": "idc"},
                },
            )
        )
        # value url for the update
        respx_mock.put("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # when we update it with a new name
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name2",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
        )
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=False)
        state = sut.update(client, old_state)
        # then a put is made with the new formula
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name2",
            "dataTypeId": {"scope": "ids", "code": "idc"},
        }
        # and the state is returned
        assert state is not None

    def test_update_formula(self, respx_mock):
        # given a derived property exists with y=2x17
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Holding",
                    "scope": "sc1",
                    "code": "cd1",
                    "displayName": "name",
                    "dataTypeId": {"scope": "ids", "code": "idc"},
                    "propertyDescription": "description",
                    "derivationFormula": "2 * 17",
                },
            )
        )
        respx_mock.put("/api/api/propertydefinitions/derived/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # when we update it with a new formula
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            derivation_formula=property.Formula("3 * {a}", a=26),
        )
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=True)
        state = sut.update(client, old_state)
        # then a put is made with the new formula
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "ids", "code": "idc"},
            "propertyDescription": "description",
            "derivationFormula": "3 * 26",
        }
        # and the state is returned
        assert state is not None

    def test_update_is_filterable(self, respx_mock):
        # given a derived property exists with y=2x17
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Holding",
                    "scope": "sc1",
                    "code": "cd1",
                    "displayName": "name",
                    "dataTypeId": {"scope": "ids", "code": "idc"},
                    "propertyDescription": "description",
                    "derivationFormula": "2 * 17",
                    "isFilterable": True,
                },
            )
        )
        respx_mock.put("/api/api/propertydefinitions/derived/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # when we update it with a new formula
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            derivation_formula=property.Formula("2 * {a}", a=17),
            is_filterable=False,
        )
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=True)
        state = sut.update(client, old_state)
        # then a put is made with the new formula
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "ids", "code": "idc"},
            "propertyDescription": "description",
            "derivationFormula": "2 * 17",
            "isFilterable": False,
        }
        # and the state is returned
        assert state is not None

    def test_update_code(self, respx_mock):
        # delete using normal definition url
        respx_mock.delete("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        # create using derived url
        respx_mock.post("/api/api/propertydefinitions/derived").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # when we update it with a different code
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd2",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            derivation_formula=property.Formula("3 * {a}", a=26),
        )
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=True)
        state = sut.update(client, old_state)
        # then a post is made with the new formula
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd2",
            "displayName": "name",
            "dataTypeId": {"scope": "ids", "code": "idc"},
            "propertyDescription": "description",
            "derivationFormula": "3 * 26",
        }
        # and the state is returned
        assert state is not None
        # and the delete was called

    def test_update_derived_to_value(self, respx_mock):
        # delete using normal definition url
        respx_mock.delete("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        # create using value url
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # when we update it using the same scope/code but a value property
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
        )
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=True)
        state = sut.update(client, old_state)
        # then a post is made with the value property
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "ids", "code": "idc"},
        }
        # and the state is returned
        assert state == {"domain": "Holding", "scope": "sc1", "code": "cd1", "derived": False}
        # and the get and the delete are both called

    def test_update_data_type(self, respx_mock):
        # given a property exists with datatype=string
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Holding",
                    "scope": "sc1",
                    "code": "cd1",
                    "displayName": "name",
                    "dataTypeId": {"scope": "system", "code": "string"},
                },
            )
        )
        # delete using normal definition url
        respx_mock.delete("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        # create using value url
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # when we update it using the same scope/code but a number type
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="system", code="number"),
        )
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=False)
        state = sut.update(client, old_state)
        # then a post is made with the new datatype
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "system", "code": "number"},
        }
        # and the state is returned
        assert state == {"domain": "Holding", "scope": "sc1", "code": "cd1", "derived": False}
        # and the get and the delete are both called

    def test_update_constraint_style_recreates(self, respx_mock):
        # given a property exists with the default constraint style
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Holding",
                    "scope": "sc1",
                    "code": "cd1",
                    "displayName": "name",
                    "dataTypeId": {"scope": "system", "code": "string"},
                },
            )
        )
        # delete using normal definition url
        respx_mock.delete("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        # create using value url
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # when we update it using the same values but a modified constraint style
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            constraint_style=property.ConstraintStyle.Identifier,
            data_type_id=property.ResourceId(scope="system", code="string"),
        )
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=False)
        state = sut.update(client, old_state)
        # then the delete is triggered
        # and a post is made with the new constraint
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "constraintStyle": "Identifier",
            "dataTypeId": {"scope": "system", "code": "string"},
        }
        # and the state is returned
        assert state == {"domain": "Holding", "scope": "sc1", "code": "cd1", "derived": False}
        # and the get and the delete are both called

    def test_update_lifetime(self, respx_mock):
        # given a perpetual property
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Holding",
                    "scope": "sc1",
                    "code": "cd1",
                    "displayName": "name",
                    "dataTypeId": {"scope": "system", "code": "string"},
                    "lifeTime": "Perpetual",
                },
            )
        )
        # delete using normal definition url
        respx_mock.delete("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        # create using value url
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # when we update it using the same scope/code but a timevariant lifetime
        sut = property.DefinitionResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="system", code="string"),
            life_time=property.LifeTime.TimeVariant,
        )
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=False)
        state = sut.update(client, old_state)
        # then a post is made with the new lifetime

        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name",
            "dataTypeId": {"scope": "system", "code": "string"},
            "lifeTime": "TimeVariant",
        }
        # and the state is returned
        assert state == {"domain": "Holding", "scope": "sc1", "code": "cd1", "derived": False}
        # and the get and the delete are both called

    def test_delete(self, respx_mock):
        # delete using normal definition url
        respx_mock.delete("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # when we delete a property definition
        old_state = SimpleNamespace(domain="Holding", scope="sc1", code="cd1", derived=False)
        property.DefinitionResource.delete(client, old_state)
        # then the delete call is made

    def test_dump(self):
        # given a datatype resource
        dt = datatype.DataTypeResource(
            id="dt1",
            scope="dtscope",
            code="dtcode",
            type_value_range=datatype.TypeValueRange.CLOSED,
            display_name="Priority Test",
            description="A test datatype for Priority",
            value_type=datatype.ValueType.STRING,
            acceptable_values=["High", "Medium", "Low"],
        )
        # and a property definition with derivation formula
        prop_ref = property.DefinitionRef(
            id="prop1", domain=property.Domain.Instrument, scope="refs", code="x"
        )
        sut = property.DefinitionResource(
            id="def1",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="Test Property",
            data_type_id=dt,
            property_description="A test property description",
            derivation_formula=property.Formula("2 * {a}", a=prop_ref),
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )
        # then the datatype and the formula args have been ref'd
        assert dumped == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "Test Property",
            "dataTypeId": {"$ref": "dt1"},
            "propertyDescription": "A test property description",
            "derivationFormula": {"formula": "2 * {a}", "args": {"a": {"$ref": "prop1"}}},
        }

    def test_dump_value_property(self):
        # given a datatype reference
        dt_ref = property.ResourceId(scope="system", code="string")
        # and a value property definition (no derivation formula)
        sut = property.DefinitionResource(
            id="def2",
            domain=property.Domain.Holding,
            scope="sc2",
            code="cd2",
            display_name="Value Property",
            data_type_id=dt_ref,
            property_description="A test value property",
            life_time=property.LifeTime.Perpetual,
            constraint_style=property.ConstraintStyle.Property,
        )
        # when we dump it
        dumped = sut.model_dump(
            by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )
        # then the dumped state is correct and data_type_id is not converted to $ref for ResourceId
        assert dumped == {
            "domain": "Holding",
            "scope": "sc2",
            "code": "cd2",
            "displayName": "Value Property",
            "dataTypeId": {"scope": "system", "code": "string"},
            "propertyDescription": "A test value property",
            "lifeTime": "Perpetual",
            "constraintStyle": "Property",
        }

    def test_undump(self):
        # given a datatype resource and property ref for references
        dt = datatype.DataTypeResource(
            id="dt1",
            scope="dtscope",
            code="dtcode",
            type_value_range=datatype.TypeValueRange.CLOSED,
            display_name="Priority Test",
            description="A test datatype for Priority",
            value_type=datatype.ValueType.STRING,
            acceptable_values=["High", "Medium", "Low"],
        )
        prop_ref = property.DefinitionRef(
            id="prop1", domain=property.Domain.Instrument, scope="refs", code="x"
        )
        # and a dumped derived property state
        dumped = {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "Test Property",
            "dataTypeId": {"$ref": "dt1"},
            "propertyDescription": "A test property description",
            "derivationFormula": {"formula": "2 * {a}", "args": {"a": {"$ref": "prop1"}}},
        }
        # when we undump it
        sut = property.DefinitionResource.model_validate(
            dumped, context={"style": "undump", "$refs": {"dt1": dt, "prop1": prop_ref}, "id": "def1"}
        )
        # then the id has been extracted from the context
        assert sut.id == "def1"
        assert sut.domain == property.Domain.Holding
        assert sut.scope == "sc1"
        assert sut.code == "cd1"
        assert sut.display_name == "Test Property"
        assert sut.property_description == "A test property description"
        # and the datatype ref has been wired up
        assert sut.data_type_id == dt
        # and the derivation formula is correct with resolved references
        assert sut.derivation_formula
        assert sut.derivation_formula.formula == "2 * {a}"
        assert sut.derivation_formula.args == {"a": prop_ref}

    def test_undump_value_property(self):
        # given a dumped value property state
        dumped = {
            "domain": "Holding",
            "scope": "sc2",
            "code": "cd2",
            "displayName": "Value Property",
            "dataTypeId": {"scope": "system", "code": "string"},
            "propertyDescription": "A test value property",
            "lifeTime": "Perpetual",
            "constraintStyle": "Property",
        }
        # when we undump it
        sut = property.DefinitionResource.model_validate(
            dumped, context={"style": "undump", "$refs": {}, "id": "def2"}
        )
        # then the id has been extracted from the context
        assert sut.id == "def2"
        assert sut.domain == property.Domain.Holding
        assert sut.scope == "sc2"
        assert sut.code == "cd2"
        assert sut.display_name == "Value Property"
        assert sut.property_description == "A test value property"
        assert sut.life_time == property.LifeTime.Perpetual
        assert sut.constraint_style == property.ConstraintStyle.Property
        # and the datatype is a ResourceId object
        assert isinstance(sut.data_type_id, property.ResourceId)
        assert sut.data_type_id.scope == "system"
        assert sut.data_type_id.code == "string"
        # and no derivation formula
        assert sut.derivation_formula is None


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeDefinitionOverrideResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    def test_create_when_not_exists(self, respx_mock):
        # given no existing property
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                404,
                json={
                },
            )
        )
        # mock the create
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(200, json={}))
        client = self.client
        # when we create a desired override
        sut = property.DefinitionOverrideResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name2",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
        )
        state = sut.create(client)
        # then state is returned with pre-existing false because it didn't exist
        assert state is not None
        assert state == {
           "code": "cd1",
           "derived": False,
           "domain": "Holding",
           "preexisting": False,
           "scope": "sc1"
        }

    def test_create_when_already_exists(self, respx_mock):
        # given it already exists
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Holding",
                    "scope": "sc1",
                    "code": "cd1",
                    "displayName": "name",
                    "dataTypeId": {"scope": "ids", "code": "idc"},
                    "propertyDescription": "description",
                    "derivationFormula": "2 * 17",
                    "isFilterable": False,
                },
            )
        )
        # mock the update
        respx_mock.put("/api/api/propertydefinitions/derived/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # when we create it but with a new formula
        sut = property.DefinitionOverrideResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
            property_description="description",
            derivation_formula=property.Formula("100 * {a}", a=17),
            is_filterable=False,
        )
        state = sut.create(client)
        # then state is returned with pre-existing true
        assert state is not None
        assert state == {
           "code": "cd1",
           "derived": True,
           "domain": "Holding",
           "preexisting": True,
           "scope": "sc1",
        }
        # and update was called
        req = respx_mock.calls.last.request
        assert req.method == "PUT"

    def test_update_preserves_preexisting(self, respx_mock):
        # given a derived property exists with y=2x17
        respx_mock.get("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "domain": "Holding",
                    "scope": "sc1",
                    "code": "cd1",
                    "displayName": "name1",
                    "dataTypeId": {"scope": "ids", "code": "idc"},
                },
            )
        )
        # value url for the update
        respx_mock.put("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # when we update it with a new name
        sut = property.DefinitionOverrideResource(
            id="one",
            domain=property.Domain.Holding,
            scope="sc1",
            code="cd1",
            display_name="name2",
            data_type_id=property.ResourceId(scope="ids", code="idc"),
        )
        old_state = SimpleNamespace(
            domain="Holding", scope="sc1", code="cd1", derived=False, preexisting=True
        )
        state = sut.update(client, old_state)
        # then a put is made with the new formula
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "domain": "Holding",
            "scope": "sc1",
            "code": "cd1",
            "displayName": "name2",
            "dataTypeId": {"scope": "ids", "code": "idc"},
        }
        # and the state is returned preserving the preexisting state
        assert state is not None
        assert state["preexisting"]

    def test_deletes_if_created(self, respx_mock):
        # mock delete
        respx_mock.delete("/api/api/propertydefinitions/Holding/sc1/cd1").mock(
            return_value=httpx.Response(200, json={})
        )
        client = self.client
        # when we delete and it is we created it (not preexisting)
        old_state = SimpleNamespace(
            domain="Holding", scope="sc1", code="cd1", derived=False, preexisting=False
        )
        property.DefinitionOverrideResource.delete(client, old_state)
        # then the delete call is made
        req = respx_mock.calls.last.request
        assert req.method == "DELETE"

    def test_no_deletes_if_preexisting(self, respx_mock):
        client = self.client
        # when we delete and it is we created it (not preexisting)
        old_state = SimpleNamespace(
            domain="Holding", scope="sc1", code="cd1", derived=False, preexisting=True
        )
        property.DefinitionOverrideResource.delete(client, old_state)
