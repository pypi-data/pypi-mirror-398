import os
from types import SimpleNamespace

import pytest
from httpx import HTTPStatusError
from pytest import fixture

import fbnconfig
from fbnconfig import datatype, property
from tests.integration.generate_test_name import gen


@fixture(scope="module")
def lusid_env():
    if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
        raise (
            RuntimeError("FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
        )

    env = os.environ["LUSID_ENV"]
    token = os.environ["FBN_ACCESS_TOKEN"]
    return SimpleNamespace(env=env, token=token)


@fixture(scope="module")
def client(lusid_env):
    return fbnconfig.create_client(lusid_env.env, lusid_env.token)


@fixture(scope="module")
def deployment_name():
    return gen("property")


def resources(deployment_name):
    df = property.DefinitionRef(
        id="property/dfdomccy", domain=property.Domain.Holding, scope="default", code="DfDomCcy"
    )
    nominal = property.DefinitionRef(
        id="property/nominal", domain=property.Domain.Holding, scope="default", code="Nominal"
    )
    rating = property.DefinitionResource(
        id="rating",
        domain=property.Domain.Instrument,
        scope=deployment_name,
        code="rating",
        display_name="robtest rating ",
        data_type_id=datatype.DataTypeRef(id="default_str", scope="system", code="string"),
        constraint_style=property.ConstraintStyle.Collection,
        property_description="robTest property",
        life_time=property.LifeTime.Perpetual,
        collection_type=property.CollectionType.Array,
    )
    pd = property.DefinitionResource(
        id="pd1",
        domain=property.Domain.Instrument,
        scope=deployment_name,
        code="pd1",
        display_name="robtest pd ",
        data_type_id=property.ResourceId(scope="system", code="number"),
        constraint_style=property.ConstraintStyle.Property,
        property_description="robTest property",
        life_time=property.LifeTime.Perpetual,
        collection_type=None,
    )
    pv_nominal = property.DefinitionResource(
        id="derived",
        domain=property.Domain.Holding,
        data_type_id=property.ResourceId(scope="system", code="number"),
        scope=deployment_name,
        code="PVNominal",
        property_description="nominal_x_df",
        display_name="DF Nominal",
        derivation_formula=property.Formula("{x} * {y}", x=df, y=nominal),
        is_filterable=False,
    )
    more_derived = property.DefinitionResource(
        id="derived_more",
        domain=property.Domain.Holding,
        data_type_id=property.ResourceId(scope="system", code="number"),
        scope=deployment_name,
        code="more_derived",
        property_description="pd1 x df x nominal",
        display_name="DF Nominal pd1",
        derivation_formula=property.Formula("{x} * {y}", x=pv_nominal, y=pd),
        is_filterable=True,
    )
    return {r.id: r for r in [df, nominal, rating, pd, pv_nominal, more_derived]}


@fixture()
def deployment(deployment_name, lusid_env):
    res = resources(deployment_name)
    print(f"\nRunning for deployment {deployment_name}...")
    yield fbnconfig.Deployment(deployment_name, list(res.values()))
    fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env.env, lusid_env.token)


def test_teardown(deployment, lusid_env, client):
    # create first
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    fbnconfig.deployex(fbnconfig.Deployment(deployment.id, []), lusid_env.env, lusid_env.token)
    with pytest.raises(HTTPStatusError) as error:
        client.get(f"/api/api/propertydefinitions/Holding/{deployment.id}/more_derived")
    assert error.value.response.status_code == 404


def test_create(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    search = client.get(f"/api/api/propertydefinitions/Holding/{deployment.id}/more_derived")
    assert search.status_code == 200


def test_update(deployment, lusid_env, client):
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    fbnconfig.deployex(deployment, lusid_env.env, lusid_env.token)
    search = client.get(f"/api/api/propertydefinitions/Holding/{deployment.id}/more_derived")
    assert search.status_code == 200
