import pathlib
from types import SimpleNamespace
from unittest import mock

import httpx
import pytest
from httpx import HTTPStatusError
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import ValidationError

from fbnconfig import recipe

TEST_BASE = "https://foo.lusid.com"


class RecipeFactory(ModelFactory[recipe.RecipeResource]): ...


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeRecipeResource:
    base_url = TEST_BASE
    recipe_url = "/api/api/recipes"
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def configuration_recipe(self):
        return {
            "scope": "sasd",
            "code": "Abcd",
            "market": {
                "marketRules": [
                    {
                        "key": "Quote.ClientInternal.*",
                        "supplier": "Lusid",
                        "dataScope": "luminesce-examples",
                        "quoteType": "Price",
                        "field": "mid",
                        "quoteInterval": "100D.0D",
                        "priceSource": "",
                        "sourceSystem": "Lusid",
                    },
                    {
                        "key": "FX.*.*",
                        "supplier": "Lusid",
                        "dataScope": "luminesce-examples",
                        "quoteType": "Rate",
                        "field": "mid",
                        "quoteInterval": "100D.0D",
                        "priceSource": "",
                        "sourceSystem": "Lusid",
                    },
                ],
                "suppliers": {
                    "Commodity": "Client",
                    "Credit": "Client",
                    "Equity": "Client",
                    "Fx": "Client",
                    "Rates": "Client",
                },
                "options": {
                    "defaultSupplier": "Lusid",
                    "defaultInstrumentCodeType": "ClientInternal",
                    "defaultScope": "luminesce-examples",
                    "attemptToInferMissingFx": True,
                    "calendarScope": "CoppClarkHolidayCalendars",
                    "conventionScope": "Conventions",
                },
                "specificRules": [],
                "groupedMarketRules": [],
            },
            "pricing": {
                "modelRules": [
                    {
                        "supplier": "Lusid",
                        "modelName": "SimpleStatic",
                        "instrumentType": "Bond",
                        "parameters": "",
                        "modelOptions": {"modelOptionsType": "EmptyModelOptions"},
                        "instrumentId": "",
                        "addressKeyFilters": [],
                    }
                ],
                "modelChoice": {},
                "options": {
                    "modelSelection": {"library": "Lusid", "model": "SimpleStatic"},
                    "useInstrumentTypeToDeterminePricer": False,
                    "allowAnyInstrumentsWithSecUidToPriceOffLookup": False,
                    "allowPartiallySuccessfulEvaluation": False,
                    "produceSeparateResultForLinearOtcLegs": False,
                    "enableUseOfCachedUnitResults": False,
                    "windowValuationOnInstrumentStartEnd": False,
                    "removeContingentCashflowsInPaymentDiary": False,
                    "useChildSubHoldingKeysForPortfolioExpansion": False,
                    "validateDomesticAndQuoteCurrenciesAreConsistent": False,
                    "conservedQuantityForLookthroughExpansion": "PV",
                },
                "resultDataRules": [],
            },
            "aggregation": {
                "options": {
                    "useAnsiLikeSyntax": False,
                    "allowPartialEntitlementSuccess": False,
                    "applyIso4217Rounding": False,
                }
            },
            "holding": {"taxLotLevelHoldings": True},
        }

    @pytest.fixture
    def content_hash(self):
        return "bd3c111146dce83acf358b05351ce1965cc43e87fa88bc0f9634690c372cbc20"

    def test_read_recipe(self, respx_mock):
        recipe_model = {"scope": "a", "code": "b", "market": "something"}
        source_recipe = RecipeFactory.build(recipe=recipe_model)
        remote_recipe = recipe_model | {"somedefaultvalue": "abcs"}
        respx_mock.get(f"{self.recipe_url}/{source_recipe.scope}/{source_recipe.code}").mock(
            return_value=httpx.Response(200, json={"value": remote_recipe})
        )

        old_state = SimpleNamespace(
            id="abc",
            scope=source_recipe.scope,
            code=source_recipe.code,
            local_version="somehash",
            remote_version="someotherHash")

        response = source_recipe.read(self.client, old_state=old_state)
        remote_recipe.pop("scope")
        remote_recipe.pop("code")
        assert response == remote_recipe

    def test_read_recipe_not_found(self, respx_mock, configuration_recipe):
        sut = RecipeFactory.build(recipe=configuration_recipe)
        respx_mock.get(f"{self.recipe_url}/{sut.scope}/{sut.code}").mock(return_value=httpx.Response(404))

        with pytest.raises(HTTPStatusError):
            sut.read(
                self.client,
                old_state=SimpleNamespace(
                    id="abc",
                    scope=sut.scope,
                    code=sut.code,
                    local_version="somehash",
                    remote_version="someotherHash",
                ),
            )

    def test_create_recipe(self, respx_mock, configuration_recipe, content_hash):
        remote_recipe = configuration_recipe | {"somedefault": "something"}
        respx_mock.post(self.recipe_url).mock(
            return_value=httpx.Response(200, json={"value": "2000-01-01T00:00:00+00:00"})
        )
        respx_mock.get(f"{self.recipe_url}/sc1/cd1", params={"asAt": "2000-01-01T00:00:00+00:00"}).mock(
            return_value=httpx.Response(200, json={"value": remote_recipe})
        )

        sut = recipe.RecipeResource(
            id="recipe1", scope="sc1", code="cd1", recipe=configuration_recipe
        )
        state = sut.create(client=self.client)

        assert state == {
            "scope": "sc1",
            "code": "cd1",
            "source_version": content_hash,
            "remote_version": "edd788fdb0a3f48ad5d90becd031f2e216d4763f9624c91632b568c3d0b7ffdb"
        }

    def test_delete_recipe(self, respx_mock, configuration_recipe, content_hash):
        respx_mock.delete("/api/api/recipes/sc1/cd1").mock(return_value=httpx.Response(200))

        sut = recipe.RecipeResource(
            id="recipe1", scope="sc1", code="cd1", recipe=configuration_recipe
        )
        old_state = SimpleNamespace(scope="sc1", code="cd1")
        sut.delete(client=self.client, old_state=old_state)

    def test_delete_recipe_not_found(self, respx_mock, configuration_recipe, content_hash):
        respx_mock.delete("/api/api/recipes/sc1/cd1").mock(return_value=httpx.Response(404))

        sut = recipe.RecipeResource(
            id="recipe1", scope="sc1", code="cd1", recipe=configuration_recipe
        )
        old_state = SimpleNamespace(scope="sc1", code="cd1")
        with pytest.raises(HTTPStatusError):
            sut.delete(client=self.client, old_state=old_state)

    def test_recipe_source_content_changes(self, respx_mock, configuration_recipe, content_hash):
        remote_recipe = {"scope": "a", "code": "b", "somedefault": "value"}
        as_at = "2025-02-19T00:00:00+00:00"

        # GIVEN A recipe already exists
        sut = recipe.RecipeResource(id="recipe1", scope="sc1", code="cd1", recipe=configuration_recipe)
        respx_mock.get("/api/api/recipes/sc1/cd1").mock(side_effect=[
            httpx.Response(200, json={"value": remote_recipe}),
            httpx.Response(200, json={"value": remote_recipe} | {"somekey": "Values"})])

        # AND Update is called
        respx_mock.post("/api/api/recipes").mock(
            return_value=httpx.Response(200, json={"value": as_at})
        )
        old_state = SimpleNamespace(
            scope="sc1",
            code="cd1",
            source_version=content_hash,
            remote_version="94bcd66609372eb7974f310e906aff33e97d3ff71afa9b375de47a2fc96a7ee6"
        )

        # WHEN The source recipe changes
        if isinstance(sut.recipe, dict):
            sut.recipe.update({"heres": "somethingnew"})

        state = sut.update(client=self.client, old_state=old_state)
        assert state is not None
        assert state["source_version"] != content_hash
        assert state == {
            "scope": "sc1",
            "code": "cd1",
            "source_version": "a63bc7db459fc9ef80753fd25042bed84e213a4ffbb7792cb86ba3e08911c52b",
            "remote_version": "71cdcf3e703becaae96946eba8984aed745431f39a88605d5931f3217598ead7",
        }

        assert respx_mock.calls.last.request.url.params.get("asAt") == as_at

    def test_recipe_remote_content_changes(self, respx_mock, configuration_recipe):
        remote_recipe = {"scope": "a", "code": "b", "something new": "value"}
        as_at = "2025-02-19T00:00:00+00:00"

        # GIVEN A recipe already exists
        sut = recipe.RecipeResource(id="recipe1", scope="sc1", code="cd1", recipe=configuration_recipe)
        respx_mock.get("/api/api/recipes/sc1/cd1").mock(
            side_effect=[
                httpx.Response(200, json={"value": remote_recipe}),
                httpx.Response(200, json={"value": configuration_recipe} | {"somedefault": "Values"}),
            ]
        )
        content_hash = "a63bc7db459fc9ef80753fd25042bed84e213a4ffbb7792cb86ba3e08911c52b"
        # AND Update is called
        respx_mock.post("/api/api/recipes").mock(return_value=httpx.Response(200, json={"value": as_at}))
        old_state = SimpleNamespace(
            scope="sc1",
            code="cd1",
            source_version=content_hash,
            remote_version="94bcd66609372eb7974f310e906aff33e97d3ff71afa9b375de47a2fc96a7ee6",
        )

        # WHEN The source recipe changes
        if isinstance(sut.recipe, dict):
            sut.recipe.update({"heres": "somethingnew"})

        state = sut.update(client=self.client, old_state=old_state)
        assert state == {
            "scope": "sc1",
            "code": "cd1",
            "source_version": content_hash,
            "remote_version": "c3c325b634053f0bc4e0b0ef3b914f514c8c03dff0bd3e792a0fab21c7079053",
        }

        assert respx_mock.calls.last.request.url.params.get("asAt") == as_at

    @pytest.mark.parametrize("scope_and_code", [("sc2", "cd2"), ("sc1", "cd2"), ("sc2", "cd1")])
    def test_recipe_identifier_change(self, respx_mock, configuration_recipe, scope_and_code):
        scope, code = scope_and_code

        respx_mock.delete(f"/api/api/recipes/{scope}/{code}").mock(
            return_value=httpx.Response(200)
        )
        respx_mock.post("/api/api/recipes").mock(
            return_value=httpx.Response(200, json={"value": "2000-01-01T00:00:00+00:00"})
        )
        respx_mock.get("/api/api/recipes/sc1/cd1", params={"asAt": "2000-01-01T00:00:00+00:00"}).mock(
            return_value=httpx.Response(200, json={"value": {"scope": "a", "code": "b",
                                                             "original": "same object"}})
        )

        sut = recipe.RecipeResource(
            id="recipe1", scope="sc1", code="cd1", recipe=configuration_recipe
        )
        old_state = SimpleNamespace(
            scope=scope, code=code, source_version="something", remote_verson="somethingelse"
        )
        state = sut.update(client=self.client, old_state=old_state)
        assert state == {
            "scope": "sc1",
            "code": "cd1",
            "source_version": "bd3c111146dce83acf358b05351ce1965cc43e87fa88bc0f9634690c372cbc20",
            "remote_version": "2ae263bc3b030b776c16a689bc0d39edcb68ec6a3b1488b4c1759b5a75205333",
        }
        assert state != old_state

    def test_update_recipe_no_change(self, respx_mock, configuration_recipe, content_hash):
        remote_recipe = {"value": configuration_recipe | {"somedefault": "val"}}

        respx_mock.get("/api/api/recipes/sc1/cd1").mock(
            return_value=httpx.Response(200, json=remote_recipe)
        )

        sut = recipe.RecipeResource(
            id="recipe1", scope="sc1", code="cd1", recipe=configuration_recipe
        )
        old_state = SimpleNamespace(scope="sc1", code="cd1",
                                    source_version=content_hash,
                                    remote_version="def1eab0f0d8b5e90bedfa32b076efaeb379873e4bb0c79cf4f5f9c439eb7a5e")
        state = sut.update(client=self.client, old_state=old_state)
        assert state is None

    @staticmethod
    def test_read_file(configuration_recipe, content_hash):
        mock_open = mock.mock_open(read_data=b'{"test": "12"}')
        with mock.patch("builtins.open", mock_open) as m:
            sut = recipe.RecipeResource(
                id="from-file", recipe=pathlib.PurePath("/foo.txt"), scope="sc1", code="cd1"
            )
            assert sut.recipe == pathlib.PurePath("/foo.txt")
            assert sut._recipe_model_ == {"test": "12"}
            # not asserting content hash as we haven't ran a read yet
            m.assert_called_once_with(pathlib.PurePosixPath("/foo.txt"), "rb")

        mock_open_file_update = mock.mock_open(read_data=b'{"test": "34"}')
        with mock.patch("builtins.open", mock_open_file_update) as m:
            sut = recipe.RecipeResource(
                id="from-file", recipe=pathlib.PurePath("/foo.txt"), scope="sc1", code="cd1"
            )
            # not asserting content hash as we haven't ran a read yet
            assert sut.recipe == pathlib.PurePath("/foo.txt")
            assert sut._recipe_model_ == {"test": "34"}
            m.assert_called_once_with(pathlib.PurePosixPath("/foo.txt"), "rb")

    @staticmethod
    def test_ctor_throws_runtime_error_when_path_and_str_not_exists():
        with pytest.raises(ValidationError):
            # noinspection PyArgumentList
            recipe.RecipeResource(id="recipe1", scope="sc1", code="cd1")  # type:ignore

    @staticmethod
    def test_ctor_throws_value_error_when_path_not_absolute():
        with pytest.raises(ValueError):
            recipe.RecipeResource(
                id="recipe1", scope="sc1", code="cd1", recipe=pathlib.Path("./foo.txt")
            )

    @staticmethod
    def test_deps():
        sut = recipe.RecipeResource(id="recipe1", scope="sc1", code="cd1", recipe={})
        assert sut.deps() == []

    def test_dump(self):
        # given a recipe resource
        recipe_data = {
            "market": {
                "marketRules": [
                    {
                        "key": "Quote.ClientInternal.*",
                        "supplier": "Lusid",
                        "dataScope": "test-scope",
                        "quoteType": "Price",
                        "field": "mid",
                        "quoteInterval": "100D.0D",
                        "priceSource": "",
                        "sourceSystem": "Lusid",
                    }
                ]
            }
        }
        sut = recipe.RecipeResource(
            id="test-recipe",
            scope="test-scope",
            code="test-code",
            recipe=recipe_data
        )
        # when we dump it
        result = sut.model_dump(
            mode="json", by_alias=True, round_trip=True, exclude_none=True, context={"style": "dump"}
        )
        # then it's correctly serialized
        assert result == {
            "scope": "test-scope",
            "code": "test-code",
            "recipe": recipe_data
        }

    def test_undump(self):
        # given dump data
        recipe_data = {
            "market": {
                "marketRules": [
                    {
                        "key": "FX.*.*",
                        "supplier": "Lusid",
                        "dataScope": "test-scope",
                        "quoteType": "Rate",
                        "field": "mid",
                        "quoteInterval": "100D.0D",
                        "priceSource": "",
                        "sourceSystem": "Lusid",
                    }
                ]
            }
        }
        data = {
            "scope": "test-scope",
            "code": "test-code",
            "recipe": recipe_data
        }
        # when we undump it
        result = recipe.RecipeResource.model_validate(
            data, context={"style": "undump", "id": "test-recipe"}
        )
        # then it's correctly populated
        assert result.id == "test-recipe"
        assert result.scope == "test-scope"
        assert result.code == "test-code"
        assert result.recipe == recipe_data
        assert result._recipe_model_ == recipe_data
