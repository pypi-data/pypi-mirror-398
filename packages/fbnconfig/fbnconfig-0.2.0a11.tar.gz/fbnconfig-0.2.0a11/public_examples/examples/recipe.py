import pathlib

from fbnconfig import Deployment, recipe

"""
An example configuration for defining recipe entities.
The script configures the following entities:
- Configuration Recipe

This example will load recipes through two different
methods, via hardcoding or a JSON file.

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01855/
"""


def configure(env):
    configuration_recipe = recipe.RecipeResource(
        id="recipe1",
        scope="sc1",
        code="cd1",
        recipe={
            "market": {
                "marketRules": [
                    {
                        "key": "Fx.CurrencyPair.*",
                        "supplier": "DataScope",
                        "dataScope": "SomeScopeToLookAt",
                        "quoteType": "Rate",
                        "field": "Mid",
                        "priceSource": "",
                        "sourceSystem": "Lusid",
                    }
                ],
                "suppliers": {},
                "options": {
                    "defaultSupplier": "Lusid",
                    "defaultInstrumentCodeType": "LusidInstrumentId",
                    "defaultScope": "default",
                    "attemptToInferMissingFx": False,
                    "calendarScope": "CoppClarkHolidayCalendars",
                    "conventionScope": "Conventions",
                },
                "specificRules": [],
                "groupedMarketRules": [],
            },
            "pricing": {
                "modelRules": [],
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
            "description": "",
            "holding": {"taxLotLevelHoldings": True},
        },
    )
    configuration_recipe_from_drive = recipe.RecipeResource(
        id="recipe2",
        scope="sc1",
        code="cd2",
        recipe=pathlib.Path(__file__).parent.parent.resolve() / pathlib.Path("./data/recipe.json"),
    )
    return Deployment(
        "recipe_example",
        [configuration_recipe, configuration_recipe_from_drive],
    )
