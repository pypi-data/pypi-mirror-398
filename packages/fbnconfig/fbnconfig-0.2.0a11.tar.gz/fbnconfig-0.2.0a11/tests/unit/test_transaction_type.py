import json
from types import SimpleNamespace

import httpx
import pytest

from fbnconfig import property, side_definition, transaction_type

TEST_BASE = "https://foo.lusid.com"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeTransactionType:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [lambda x: x.raise_for_status()]})

    @pytest.fixture
    def simple_transaction_type(self):
        return transaction_type.TransactionTypeResource(
            id="txn1",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Something",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_definition.SideResource(
                        id="side1",
                        side="Side1",
                        scope="sc1",
                        security="Txn:LusidInstrumentId",
                        currency="Txn:SettlementCurrency",
                        rate="Txn:TradeToPortfolioRate",
                        units="Txn:Units",
                        amount="Txn:TotalConsideration",
                        notional_amount="0",
                    ),
                    direction=1,
                    name="Stock Movement",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    settlement_mode=transaction_type.SettlementMode.Internal,
                )
            ],
            calculations=[],
            properties=[],
        )

    @pytest.fixture
    def simple_transaction_type_no_movement_option(self):
        return transaction_type.TransactionTypeResource(
            id="txn1",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Something",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_definition.SideResource(
                        id="side1",
                        side="Side1",
                        scope="sc1",
                        security="Txn:LusidInstrumentId",
                        currency="Txn:SettlementCurrency",
                        rate="Txn:TradeToPortfolioRate",
                        units="Txn:Units",
                        amount="Txn:TotalConsideration",
                        notional_amount="0",
                    ),
                    direction=1,
                    name="Stock Movement",
                    settlement_mode=transaction_type.SettlementMode.Internal,
                )
            ],
            calculations=[],
            properties=[],
        )

    @pytest.fixture
    def complex_transaction_type(self):
        transaction_configuration_properties = [
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="one", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd4"
                ),
                label_value="Hello world",
            ),
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="one", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd5"
                ),
                metric_value=transaction_type.MetricValue(value=1.23456, unit="GBP"),
            ),
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="one", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd6"
                ),
                label_set_value=["one", "two", "three"],
            ),
        ]
        return transaction_type.TransactionTypeResource(
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Test buy 1",
                    transaction_class="ConfigurationTest",
                    transaction_roles="AllRoles",
                    is_default=False,
                ),
                transaction_type.TransactionTypeAlias(
                    type="BY",
                    description="Test buy 2",
                    transaction_class="ConfigurationTest",
                    transaction_roles="AllRoles",
                    is_default=False,
                ),
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_definition.SideRef(id="side1", side="Side1", scope="sc1"),
                    direction=1,
                    name="Stock Movement",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    mappings=[
                        transaction_type.TransactionTypePropertyMapping(
                            property_key=property.DefinitionRef(
                                id="one", domain=property.Domain.Transaction, scope="sc1", code="cd1"
                            ),
                            set_to="Hello world",
                        ),
                        transaction_type.TransactionTypePropertyMapping(
                            property_key=property.DefinitionRef(
                                id="two", domain=property.Domain.Transaction, scope="sc1", code="cd2"
                            ),
                            map_from=property.DefinitionRef(
                                id="three", domain=property.Domain.Transaction, scope="sc1", code="cd3"
                            ),
                        ),
                    ],
                    properties=transaction_configuration_properties,
                    settlement_mode=transaction_type.SettlementMode.Internal,
                )
            ],
            calculations=[
                transaction_type.TransactionTypeCalculation(
                    type=transaction_type.CalculationType.TaxAmounts,
                    side=side_definition.SideRef(id="side1", side="Side1", scope="sc1"),
                ),
                transaction_type.TransactionTypeCalculation(
                    type=transaction_type.CalculationType.NotionalAmount
                ),
            ],
            properties=transaction_configuration_properties,
            id="txn1",
            scope="sc1",
            source="default",
        )

    def test_read_transaction_type(self, respx_mock, simple_transaction_type):
        respx_mock.get(
            "/api/api/transactionconfiguration/types/default/Buy"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"aliases": [], "movements": [], "links": [{"x": "www.x.com"}]}
            )
        )
        # given an existing transaction type
        old_state = SimpleNamespace(transaction_type="Buy", source="default", scope="sc1")
        sut = simple_transaction_type
        # when it reads
        response = sut.read(self.client, old_state)
        # then it builds the correct url with the scope in params
        assert respx_mock.calls.last.request.url == "https://foo.lusid.com/api/api/transactionconfiguration/types/default/Buy?scope=sc1"
        # and it removes the links from the response
        assert response == {
            "aliases": [
            ],
            "movements": [
            ],
        }

    def test_read_transaction_type_missing(self, respx_mock, simple_transaction_type):
        # given a transaction type that does not exist at the server
        respx_mock.get(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type.source}/{simple_transaction_type._get_first_alias()}?scope={simple_transaction_type.scope}"
        ).mock(return_value=httpx.Response(404))
        # and we construct a desired state
        old_state = SimpleNamespace(transaction_type="Buy", source="default", scope="sc1")
        sut = simple_transaction_type
        # when we try to read it, it throws
        with pytest.raises(httpx.HTTPError):
            sut.read(self.client, old_state)

    def test_create_transaction_type(self, respx_mock, simple_transaction_type):
        respx_mock.put(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type.source}/{simple_transaction_type._get_first_alias()}?scope={simple_transaction_type.scope}"
        ).mock(
            return_value=httpx.Response(
                200, json={"source": "default", "scope": "sc1", "transaction_type": "Buy"}
            )
        )

        client = self.client
        sut = simple_transaction_type

        state = sut.create(client)
        req = respx_mock.calls.last.request

        assert json.loads(req.content) == {
            "aliases": [
                {
                    "type": "Buy",
                    "description": "Something",
                    "transactionClass": "default",
                    "transactionRoles": "LongLonger",
                    "isDefault": False,
                }
            ],
            "movements": [
                {
                    "movementTypes": "StockMovement",
                    "side": "Side1",
                    "direction": 1,
                    "properties": {},
                    "mappings": [],
                    "name": "Stock Movement",
                    "movementOptions": ["DirectAdjustment"],
                    "condition": "",
                    "settlementMode": "Internal",
                }
            ],
            "properties": {},
            "calculations": [],
        }
        assert state == {"source": "default", "scope": "sc1", "transaction_type": "Buy"}

    def test_complex_transaction_type_create(self, respx_mock, complex_transaction_type):
        respx_mock.put(
            "/api/api/transactionconfiguration/types/default/BY?scope=sc1"
        ).mock(
            return_value=httpx.Response(
                200, json={"source": "default", "scope": "sc1", "transaction_type": "Buy"}
            )
        )
        # given a complex transaction type
        sut = complex_transaction_type
        # when we create it
        state = sut.create(self.client)
        # then the state is unchanged
        assert state == {"source": "default", "scope": "sc1", "transaction_type": "BY"}
        # and the request body is correct
        req = respx_mock.calls.last.request
        assert json.loads(req.content) == {
            "aliases": [{
                "type": "Buy",
                "description": "Test buy 1",
                "transactionClass": "ConfigurationTest",
                "transactionRoles": "AllRoles",
                "isDefault": False,
            }, {
                "type": "BY",
                "description": "Test buy 2",
                "transactionClass": "ConfigurationTest",
                "transactionRoles": "AllRoles",
                "isDefault": False,
            }, ],
            "movements": [{
                "movementTypes": "StockMovement",
                "side": "Side1",
                "direction": 1,
                "settlementMode": "Internal",
                "properties": {
                    "TransactionConfiguration/sc1/cd4": {
                        "key": "TransactionConfiguration/sc1/cd4",
                        "value": {"labelValue": "Hello world"},
                    },
                    "TransactionConfiguration/sc1/cd5": {
                        "key": "TransactionConfiguration/sc1/cd5",
                        "value": {"metricValue": {"value": 1.23456, "unit": "GBP"}},
                    },
                    "TransactionConfiguration/sc1/cd6": {
                        "key": "TransactionConfiguration/sc1/cd6",
                        "value": {"labelSetValue": ["one", "two", "three"]},
                    },
                },
                "mappings": [
                    {"propertyKey": "Transaction/sc1/cd1", "setTo": "Hello world"},
                    {"propertyKey": "Transaction/sc1/cd2", "mapFrom": "Transaction/sc1/cd3"},
                ],
                "name": "Stock Movement",
                "movementOptions": ["DirectAdjustment"],
                "condition": "",
            }],
            "properties": {
                "TransactionConfiguration/sc1/cd4": {
                    "key": "TransactionConfiguration/sc1/cd4",
                    "value": {"labelValue": "Hello world"},
                },
                "TransactionConfiguration/sc1/cd5": {
                    "key": "TransactionConfiguration/sc1/cd5",
                    "value": {"metricValue": {"value": 1.23456, "unit": "GBP"}},
                },
                "TransactionConfiguration/sc1/cd6": {
                    "key": "TransactionConfiguration/sc1/cd6",
                    "value": {"labelSetValue": ["one", "two", "three"]},
                },
            },
            "calculations": [{"type": "TaxAmounts", "side": "Side1"}, {"type": "Txn:NotionalAmount"}],
        }

    def test_delete_transaction_type(self, respx_mock, simple_transaction_type):
        respx_mock.delete(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type.source}/{simple_transaction_type._get_first_alias()}?scope={simple_transaction_type.scope}"
        ).mock(return_value=httpx.Response(200))
        client = self.client
        old_state = SimpleNamespace(transaction_type="Buy", source="default", scope="sc1")
        sut = simple_transaction_type

        sut.delete(client, old_state)

    def test_delete_transaction_type_missing(self, respx_mock, simple_transaction_type):
        respx_mock.delete(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type.source}/{simple_transaction_type._get_first_alias()}?scope={simple_transaction_type.scope}"
        ).mock(return_value=httpx.Response(404))
        client = self.client
        with pytest.raises(httpx.HTTPError):
            old_state = SimpleNamespace(transaction_type="Buy", source="default", scope="sc1")
            sut = simple_transaction_type
            sut.delete(client, old_state)

    def test_update_transaction_type_no_change(self, respx_mock, simple_transaction_type):
        respx_mock.get(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type.source}/{simple_transaction_type._get_first_alias()}?scope={simple_transaction_type.scope}"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "aliases": [
                        {
                            "type": "Buy",
                            "description": "Something",
                            "transactionClass": "default",
                            "transactionRoles": "LongLonger",
                            "isDefault": False,
                        }
                    ],
                    "movements": [
                        {
                            "movementTypes": "StockMovement",
                            "side": "Side1",
                            "direction": 1,
                            "properties": {},
                            "mappings": [],
                            "name": "Stock Movement",
                            "movementOptions": ["DirectAdjustment"],
                            "condition": "",
                            "settlementMode": "Internal",
                        }
                    ],
                    "properties": {},
                    "calculations": [],
                },
            )
        )

        client = self.client
        old_state = SimpleNamespace(transaction_type="Buy", source="default", scope="sc1")
        sut = simple_transaction_type

        state = sut.update(client, old_state)

        assert state is None

    def test_update_transaction_type_no_change_no_movement_option(
        self, respx_mock, simple_transaction_type_no_movement_option
    ):
        respx_mock.get(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type_no_movement_option.source}/"
            f"{simple_transaction_type_no_movement_option._get_first_alias()}"
            f"?scope={simple_transaction_type_no_movement_option.scope}"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "aliases": [
                        {
                            "type": "Buy",
                            "description": "Something",
                            "transactionClass": "default",
                            "transactionRoles": "LongLonger",
                            "isDefault": False,
                        }
                    ],
                    "movements": [
                        {
                            "movementTypes": "StockMovement",
                            "side": "Side1",
                            "direction": 1,
                            "properties": {},
                            "mappings": [],
                            "name": "Stock Movement",
                            "movementOptions": [],
                            "condition": "",
                            "settlementMode": "Internal",
                        }
                    ],
                    "properties": {},
                    "calculations": [],
                },
            )
        )

        client = self.client
        old_state = SimpleNamespace(transaction_type="Buy", source="default", scope="sc1")
        sut = simple_transaction_type_no_movement_option

        state = sut.update(client, old_state)

        assert state is None

    def test_update_transaction_type_state_change(self, respx_mock, simple_transaction_type):
        respx_mock.delete(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type.source}/{simple_transaction_type._get_first_alias()}?scope=sc2"
        ).mock(return_value=httpx.Response(200))

        respx_mock.put(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type.source}/{simple_transaction_type._get_first_alias()}?scope={simple_transaction_type.scope}"
        ).mock(
            return_value=httpx.Response(
                200, json={"source": "default", "scope": "sc1", "transaction_type": "Buy"}
            )
        )

        client = self.client

        old_state = SimpleNamespace(transaction_type="Buy", source="default", scope="sc2")
        sut = simple_transaction_type
        state = sut.update(client, old_state)
        assert state == {"source": "default", "scope": "sc1", "transaction_type": "Buy"}

    def test_update_transaction_type_content_changed(self, respx_mock, simple_transaction_type):
        respx_mock.get(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type.source}/{simple_transaction_type._get_first_alias()}?scope={simple_transaction_type.scope}"
        ).mock(
            return_value=httpx.Response(
                200,
                json=simple_transaction_type.model_dump(mode="json", exclude_none=True, by_alias=True),
            )
        )

        respx_mock.put(
            f"/api/api/transactionconfiguration/types/{simple_transaction_type.source}/{simple_transaction_type._get_first_alias()}?scope={simple_transaction_type.scope}"
        ).mock(
            return_value=httpx.Response(
                200, json={"source": "default", "scope": "sc1", "transaction_type": "Buy"}
            )
        )

        client = self.client

        old_state = SimpleNamespace(transaction_type="Buy", source="default", scope="sc1")

        sut = simple_transaction_type

        sut.movements = []
        state = sut.update(client, old_state)
        assert state == {"source": "default", "scope": "sc1", "transaction_type": "Buy"}

    def test_deps_movements_unique(self):
        side_resource = side_definition.SideResource(
            id="side1",
            side="Side1",
            scope="sc1",
            security="Txn:LusidInstrumentId",
            currency="Txn:SettlementCurrency",
            rate="Txn:TradeToPortfolioRate",
            units="Txn:Units",
            amount="Txn:TotalConsideration",
            notional_amount="0",
        )

        side_ref = side_definition.SideRef(id="side1", side="Side1", scope="sc1")

        txn_type_no_movements = transaction_type.TransactionTypeResource(
            id="txn1",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Something",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[],
            calculations=[],
            properties=[],
        )

        txn_type_side_resource_movement = transaction_type.TransactionTypeResource(
            id="txn1",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Something",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_resource,
                    direction=1,
                    name="Stock Movement",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    settlement_mode=transaction_type.SettlementMode.Internal,
                ),
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_resource,
                    direction=1,
                    name="Stock Movement 2",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    settlement_mode=transaction_type.SettlementMode.Internal,
                ),
            ],
            calculations=[],
            properties=[],
        )

        txn_type_side_ref_movement = transaction_type.TransactionTypeResource(
            id="txn1",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Something",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_ref,
                    direction=1,
                    name="Stock Movement",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    settlement_mode=transaction_type.SettlementMode.Internal,
                ),
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_ref,
                    direction=1,
                    name="Stock Movement 2",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    settlement_mode=transaction_type.SettlementMode.Internal,
                ),
            ],
            calculations=[],
            properties=[],
        )

        deps_no_movements = txn_type_no_movements.deps()
        deps_side_resource_movement = txn_type_side_resource_movement.deps()
        deps_side_ref_movement = txn_type_side_ref_movement.deps()

        assert deps_no_movements == []
        assert deps_side_resource_movement == [side_resource]
        assert deps_side_ref_movement == [side_ref]

    def test_deps_movement_properties_unique(self):
        transaction_configuration_properties = [
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionResource(
                    id="pd1",
                    domain=property.Domain.TransactionConfiguration,
                    scope="sc1",
                    code="pd1",
                    display_name="property",
                    data_type_id=property.ResourceId(scope="system", code="number"),
                    constraint_style=property.ConstraintStyle.Property,
                    property_description="property",
                    life_time=property.LifeTime.Perpetual,
                    collection_type=None,
                ),
                label_value="Hello world",
            ),
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="one", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd5"
                ),
                metric_value=transaction_type.MetricValue(value=1.23456, unit="GBP"),
            ),
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="one", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd5"
                ),
                label_set_value=["one", "two", "three"],
            ),
        ]

        side_ref = side_definition.SideRef(id="side1", side="Side1", scope="sc1")

        txn_type = transaction_type.TransactionTypeResource(
            id="txn1",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Something",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_ref,
                    direction=1,
                    name="Stock Movement",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    properties=None,
                    settlement_mode=transaction_type.SettlementMode.Internal,
                )
            ],
            calculations=[],
            properties=[],
        )

        assert txn_type.deps() == [side_ref]

        txn_type.movements[0].properties = transaction_configuration_properties

        assert txn_type.deps() == [
            side_ref,
            property.DefinitionResource(
                id="pd1",
                domain=property.Domain.TransactionConfiguration,
                scope="sc1",
                code="pd1",
                display_name="property",
                data_type_id=property.ResourceId(scope="system", code="number"),
                constraint_style=property.ConstraintStyle.Property,
                property_description="property",
                life_time=property.LifeTime.Perpetual,
                collection_type=None,
            ),
            property.DefinitionRef(
                id="one", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd5"
            ),
        ]

    def test_deps_movements_mappings_unique(self):
        side_ref = side_definition.SideRef(id="side1", side="Side1", scope="sc1")

        mappings = [
            transaction_type.TransactionTypePropertyMapping(
                property_key=property.DefinitionRef(
                    id="one", domain=property.Domain.Transaction, scope="sc1", code="cd1"
                ),
                set_to="Hello world",
            ),
            transaction_type.TransactionTypePropertyMapping(
                property_key=property.DefinitionRef(
                    id="two", domain=property.Domain.Transaction, scope="sc1", code="cd2"
                ),
                map_from=property.DefinitionRef(
                    id="three", domain=property.Domain.Transaction, scope="sc1", code="cd3"
                ),
            ),
        ]

        txn_type = transaction_type.TransactionTypeResource(
            id="txn1",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Something",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_ref,
                    direction=1,
                    name="Stock Movement",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    settlement_mode=transaction_type.SettlementMode.Internal,
                )
            ],
            calculations=[],
            properties=[],
        )

        assert txn_type.deps() == [side_ref]

        txn_type.movements[0].mappings = mappings

        assert txn_type.deps() == [
            side_ref,
            property.DefinitionRef(
                id="one", domain=property.Domain.Transaction, scope="sc1", code="cd1"
            ),
            property.DefinitionRef(
                id="two", domain=property.Domain.Transaction, scope="sc1", code="cd2"
            ),
            property.DefinitionRef(
                id="three", domain=property.Domain.Transaction, scope="sc1", code="cd3"
            ),
        ]

    def test_deps_properties_unique(self):
        side_ref = side_definition.SideRef(id="side1", side="Side1", scope="sc1")

        properties = [
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="one", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd1"
                ),
                label_value="Hello world",
            ),
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="two", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd2"
                ),
                metric_value=transaction_type.MetricValue(value=1.23456, unit="GBP"),
            ),
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="two", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd2"
                ),
                label_set_value=["one", "two", "three"],
            ),
        ]

        txn_type = transaction_type.TransactionTypeResource(
            id="txn1",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Something",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_ref,
                    direction=1,
                    name="Stock Movement",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    settlement_mode=transaction_type.SettlementMode.Internal,
                )
            ],
            calculations=[],
            properties=[],
        )

        assert txn_type.deps() == [side_ref]

        txn_type.properties = properties

        assert txn_type.deps() == [
            side_ref,
            property.DefinitionRef(
                id="one", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd1"
            ),
            property.DefinitionRef(
                id="two", domain=property.Domain.TransactionConfiguration, scope="sc1", code="cd2"
            ),
        ]

    def test_deps_calculations_unique(self):
        side_ref = side_definition.SideRef(id="side1", side="Side1", scope="sc1")

        side_resource = side_definition.SideResource(
            id="side2",
            side="Side2",
            scope="sc2",
            security="Txn:LusidInstrumentId",
            currency="Txn:SettlementCurrency",
            rate="Txn:TradeToPortfolioRate",
            units="Txn:Units",
            amount="Txn:TotalConsideration",
            notional_amount="0",
        )

        calculations = [
            transaction_type.TransactionTypeCalculation(
                type=transaction_type.CalculationType.TaxAmounts, side=side_ref
            ),
            transaction_type.TransactionTypeCalculation(
                type=transaction_type.CalculationType.ExchangeRate, side=side_ref
            ),
            transaction_type.TransactionTypeCalculation(
                type=transaction_type.CalculationType.TaxAmounts, side=side_resource
            ),
            transaction_type.TransactionTypeCalculation(
                type=transaction_type.CalculationType.NotionalAmount
            ),
        ]

        txn_type = transaction_type.TransactionTypeResource(
            id="txn1",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Something",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side_ref,
                    direction=1,
                    name="Stock Movement",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                    settlement_mode=transaction_type.SettlementMode.Internal,
                )
            ],
            calculations=[],
            properties=[],
        )

        assert txn_type.deps() == [side_ref]

        txn_type.calculations = calculations

        assert txn_type.deps() == [side_ref, side_resource]

    def test_transaction_type_property_only_one_exists(self):
        # When we set more than one of label_value, label_set_value or metric_value
        # on a property, an error is thrown
        with pytest.raises(KeyError):
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="one", domain=property.Domain.Transaction, scope="sc1", code="cd1"
                ),
                label_value="Hello world",
                metric_value=transaction_type.MetricValue(value=1.23456, unit="GBP"),
            )

        # If three exist, throw error
        with pytest.raises(KeyError):
            transaction_type.PerpetualProperty(
                property_key=property.DefinitionRef(
                    id="one", domain=property.Domain.Transaction, scope="sc1", code="cd1"
                ),
                label_value="Hello world",
                label_set_value=["Hello", "World"],
                metric_value=transaction_type.MetricValue(value=1.23456, unit="GBP"),
            )

        # When one exists, it builds without error
        transaction_type.PerpetualProperty(
            property_key=property.DefinitionRef(
                id="one", domain=property.Domain.Transaction, scope="sc1", code="cd1"
            ),
            metric_value=transaction_type.MetricValue(value=1.23456, unit="GBP"),
        )

    def test_no_aliases_throws_value_error(self):
        with pytest.raises(ValueError):
            transaction_type.TransactionTypeResource(
                id="txn1", scope="sc1", source="default", aliases=[]
            )

    def test_equal_json_with_different_ordering(self):
        json1 = {
            "aliases": [
                {
                    "type": "ZZZZBuy",
                    "description": "Test buy 1",
                    "transactionClass": "ConfigurationTest",
                    "transactionRoles": "AllRoles",
                    "isDefault": False,
                },
                {
                    "type": "BY",
                    "description": "Test buy 2",
                    "transactionClass": "ConfigurationTest",
                    "transactionRoles": "AllRoles",
                    "isDefault": False,
                },
            ],
            "calculations": [
                {"type": "TaxAmounts", "side": "Side1"},
                {"type": "AAAAATaxAmounts", "side": "Side1"},
            ],
        }

        json2 = {
            "aliases": [
                {
                    "type": "BY",
                    "description": "Test buy 2",
                    "transactionClass": "ConfigurationTest",
                    "transactionRoles": "AllRoles",
                    "isDefault": False,
                },
                {
                    "type": "ZZZZBuy",
                    "description": "Test buy 1",
                    "transactionClass": "ConfigurationTest",
                    "transactionRoles": "AllRoles",
                    "isDefault": False,
                },
            ],
            "calculations": [
                {"type": "AAAAATaxAmounts", "side": "Side1"},
                {"type": "TaxAmounts", "side": "Side1"},
            ],
        }

        assert transaction_type._compare_json_structures(json1, json2)

    def test_not_equal_json(self):
        json1 = {
            "aliases": [
                {
                    "type": "ZZZZBuy",
                    "description": "Test buy 1",
                    "transactionClass": "ConfigurationTest",
                    "transactionRoles": "AllRoles",
                    "isDefault": False,
                },
                {
                    "type": "BY",
                    "description": "Test buy 2",
                    "transactionClass": "ConfigurationTest",
                    "transactionRoles": "AllRoles",
                    "isDefault": False,
                },
            ]
        }

        json2 = {
            "aliases": [
                {
                    "type": "BY",
                    "description": "Test buy 2",
                    "transactionClass": "ConfigurationTest",
                    "transactionRoles": "AllRoles",
                    "isDefault": False,
                },
                {
                    "type": "ZZZZBuy",
                    "description": "Test buy 1",
                    "transactionClass": "ConfigurationTest",
                    "transactionRoles": "AllRoles",
                    "isDefault": True,  # Difference here
                },
            ]
        }

        assert not transaction_type._compare_json_structures(json1, json2)

    def test_nested_json_with_different_ordering(self):
        json1 = {
            "movements": [
                {
                    "movementTypes": "StockMovement",
                    "side": "Side1",
                    "direction": 1,
                    "properties": {
                        "TransactionConfiguration/sc1/cd4": {
                            "key": "TransactionConfiguration/sc1/cd4",
                            "value": {"labelValue": "Hello world"},
                        },
                        "TransactionConfiguration/sc1/cd5": {
                            "key": "TransactionConfiguration/sc1/cd5",
                            "value": {"metricValue": {"value": 1.23456, "unit": "GBP"}},
                        },
                    },
                    "mappings": [
                        {"propertyKey": "Transaction/sc1/cd2", "mapFrom": "Transaction/sc1/cd3"},
                        {"propertyKey": "Transaction/sc1/cd1", "setTo": "Hello world"},
                    ],
                    "name": "Stock Movement",
                    "movementOptions": ["IncludeTaxLots", "DirectAdjustment"],
                    "condition": "",
                    "settlementMode": "Internal",
                }
            ]
        }

        json2 = {
            "movements": [
                {
                    "movementTypes": "StockMovement",
                    "side": "Side1",
                    "direction": 1,
                    "properties": {
                        "TransactionConfiguration/sc1/cd5": {
                            "key": "TransactionConfiguration/sc1/cd5",
                            "value": {"metricValue": {"value": 1.23456, "unit": "GBP"}},
                        },
                        "TransactionConfiguration/sc1/cd4": {
                            "key": "TransactionConfiguration/sc1/cd4",
                            "value": {"labelValue": "Hello world"},
                        },
                    },
                    "mappings": [
                        {"propertyKey": "Transaction/sc1/cd1", "setTo": "Hello world"},
                        {"propertyKey": "Transaction/sc1/cd2", "mapFrom": "Transaction/sc1/cd3"},
                    ],
                    "name": "Stock Movement",
                    "movementOptions": ["DirectAdjustment", "IncludeTaxLots"],
                    "condition": "",
                    "settlementMode": "Internal",
                }
            ]
        }

        assert transaction_type._compare_json_structures(json1, json2)

    def test_different_json_structure(self):
        json1 = {
            "movements": [
                {
                    "movementTypes": "StockMovement",
                    "side": "Side1",
                    "direction": 1,
                    "settlementMode": "Internal",
                }
            ]
        }
        json2 = {
            "movements": [
                {
                    "movementTypes": "StockMovement",
                    "side": "Side2",  # Different side
                    "direction": 1,
                    "settlementMode": "Internal",
                }
            ]
        }
        assert not transaction_type._compare_json_structures(json1, json2)

    def test_roundtrip_api_format(self):
        prop1 = property.DefinitionRef(
            id="prop1", domain=property.Domain.Transaction, scope="sc1", code="TestProp"
        )
        prop2 = property.DefinitionRef(
            id="prop2", domain=property.Domain.Transaction, scope="sc1", code="MapProp"
        )
        side1 = side_definition.SideRef(
            id="calc_side", side="CalcSide", scope="sc1"
        )
        # given API response format with scope and source included
        api_data = {
            "scope": "sc1",
            "source": "default",
            "aliases": [
                {
                    "type": "Buy",
                    "description": "Something",
                    "transaction_class": "default",
                    "transaction_roles": "LongLonger",
                    "is_default": False,
                }
            ],
            "movements": [
                {
                    "movement_types": "StockMovement",
                    "side": {"$ref": side1.id},
                    "direction": 1,
                    "properties": [
                        {
                            "property_key": {"$ref": "prop1"},
                            "label_value": "Test Label"
                        }
                    ],
                    "mappings": [
                        {
                            "property_key": {"$ref": "prop2"},
                            "set_to": "Test Value"
                        }
                    ],
                    "name": "Stock Movement",
                    "movement_options": ["DirectAdjustment"],
                    "condition": "",
                }
            ],
            "properties": [
                {
                    "property_key": {"$ref": "prop1"},
                    "metric_value": {"value": 123.45, "unit": "USD"}
                }
            ],
            "calculations": [
                {
                    "type": "TaxAmounts",
                    "side": {"$ref": side1.id},
                    "formula": "test_formula"
                }
            ],
        }
        # when we parse it back into a TransactionTypeResource with id in context
        result = transaction_type.TransactionTypeResource.model_validate(
            api_data, context={
                "id": "test-txn",
                "$refs": {
                    "prop1": prop1,
                    "prop2": prop2,
                    "calc_side": side1,
                }
            }
        )
        # then it's correctly populated
        assert result.id == "test-txn"
        assert result.scope == "sc1"
        assert result.source == "default"
        assert len(result.aliases) == 1
        assert result.aliases[0].type == "Buy"
        # verify movements with properties and mappings
        assert len(result.movements) == 1
        movement = result.movements[0]
        assert movement.side.side == "CalcSide"
        assert movement.properties
        assert len(movement.properties) == 1
        assert movement.properties[0].property_key.code == "TestProp"
        assert movement.properties[0].label_value == "Test Label"
        assert movement.mappings
        assert len(movement.mappings) == 1
        assert movement.mappings[0].property_key.code == "MapProp"
        assert movement.mappings[0].set_to == "Test Value"
        # verify global properties
        assert result.properties
        assert len(result.properties) == 1
        assert result.properties[0].property_key.code == "TestProp"
        assert result.properties[0].metric_value
        assert result.properties[0].metric_value.value == 123.45
        assert result.properties[0].metric_value.unit == "USD"
        assert result.calculations
        # verify calculations with side reference
        assert len(result.calculations) == 1
        assert result.calculations[0].type == "TaxAmounts"
        assert result.calculations[0].side
        assert result.calculations[0].side.side == "CalcSide"
        assert result.calculations[0].formula == "test_formula"

    def test_dump(self, simple_transaction_type):
        # given a transaction type resource
        sut = simple_transaction_type
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then it includes scope and source information
        expected_keys = {"scope", "source", "aliases", "movements", "properties", "calculations"}
        assert set(result.keys()) == expected_keys
        assert result["scope"] == "sc1"
        assert result["source"] == "default"
        assert len(result["aliases"]) == 1
        assert result["aliases"][0]["type"] == "Buy"

    def test_undump(self):
        # given dump data
        data = {
            "scope": "sc1",
            "source": "default",
            "aliases": [
                {
                    "type": "Buy",
                    "description": "Something",
                    "transaction_class": "default",
                    "transaction_roles": "LongLonger",
                    "is_default": False,
                }
            ],
            "movements": [],
            "properties": [],
            "calculations": [],
        }
        # when we undump it
        result = transaction_type.TransactionTypeResource.model_validate(
            data, context={"style": "undump", "id": "txn_id"}
        )
        # then it's correctly populated
        assert result.id == "txn_id"
        assert result.scope == "sc1"
        assert result.source == "default"
        assert len(result.aliases) == 1
        assert result.aliases[0].type == "Buy"

    def test_dump_with_refs(self):
        # given a transaction type resource with property and side references
        prop1 = property.DefinitionRef(
            id="prop1", domain=property.Domain.Transaction, scope="sc1", code="TestProp"
        )
        side1 = side_definition.SideRef(
            id="side1", side="TestSide", scope="sc1"
        )
        sut = transaction_type.TransactionTypeResource(
            id="txn_with_refs",
            scope="sc1",
            source="default",
            aliases=[
                transaction_type.TransactionTypeAlias(
                    type="Buy",
                    description="Test transaction",
                    transaction_class="default",
                    transaction_roles="LongLonger",
                    is_default=False,
                )
            ],
            movements=[
                transaction_type.TransactionTypeMovement(
                    movement_types=transaction_type.MovementType.StockMovement,
                    side=side1,
                    direction=1,
                    properties=[
                        transaction_type.PerpetualProperty(
                            property_key=prop1,
                            label_value="Test Label"
                        )
                    ],
                    mappings=[
                        transaction_type.TransactionTypePropertyMapping(
                            property_key=prop1,
                            set_to="Test Value"
                        )
                    ],
                    name="Stock Movement",
                    movement_options=[transaction_type.MovementOption.DirectAdjustment],
                )
            ],
            properties=[
                transaction_type.PerpetualProperty(
                    property_key=prop1,
                    metric_value=transaction_type.MetricValue(value=123.45, unit="USD")
                )
            ],
            calculations=[
                transaction_type.TransactionTypeCalculation(
                    type=transaction_type.CalculationType.TaxAmounts,
                    side=side1,
                    formula="test_formula"
                )
            ],
        )
        # when we dump it
        result = sut.model_dump(
            mode="json",
            by_alias=True,
            round_trip=True,
            exclude_none=True,
            context={"style": "dump"}
        )
        # then property and side references are serialized as $ref
        assert result["scope"] == "sc1"
        assert result["source"] == "default"
        # movement side uses $ref
        assert result["movements"][0]["side"] == {"$ref": "side1"}
        # movement properties use $ref
        assert result["movements"][0]["properties"][0]["propertyKey"] == {"$ref": "prop1"}
        # movement mappings use $ref
        assert result["movements"][0]["mappings"][0]["propertyKey"] == {"$ref": "prop1"}
        # global properties use $ref
        assert result["properties"][0]["propertyKey"] == {"$ref": "prop1"}
        # calculations side uses $ref
        assert result["calculations"][0]["side"] == {"$ref": "side1"}

    def test_undump_with_refs(self):
        # given dump data with $ref values
        prop1 = property.DefinitionRef(
            id="prop1", domain=property.Domain.Transaction, scope="sc1", code="TestProp"
        )
        side1 = side_definition.SideRef(
            id="side1", side="TestSide", scope="sc1"
        )
        data = {
            "scope": "sc1",
            "source": "default",
            "aliases": [
                {
                    "type": "Buy",
                    "description": "Test transaction",
                    "transaction_class": "default",
                    "transaction_roles": "LongLonger",
                    "is_default": False,
                }
            ],
            "movements": [
                {
                    "movement_types": "StockMovement",
                    "side": {"$ref": "side1"},
                    "direction": 1,
                    "properties": [
                        {
                            "property_key": {"$ref": "prop1"},
                            "label_value": "Test Label"
                        }
                    ],
                    "mappings": [
                        {
                            "property_key": {"$ref": "prop1"},
                            "set_to": "Test Value"
                        }
                    ],
                    "name": "Stock Movement",
                    "movement_options": ["DirectAdjustment"],
                    "condition": "",
                }
            ],
            "properties": [
                {
                    "property_key": {"$ref": "prop1"},
                    "metric_value": {"value": 123.45, "unit": "USD"}
                }
            ],
            "calculations": [
                {
                    "type": "TaxAmounts",
                    "side": {"$ref": "side1"},
                    "formula": "test_formula"
                }
            ],
        }
        # when we undump it with $refs context
        result = transaction_type.TransactionTypeResource.model_validate(
            data, context={
                "style": "undump",
                "id": "txn_with_refs",
                "$refs": {
                    "prop1": prop1,
                    "side1": side1,
                }
            }
        )
        # then references are resolved correctly
        assert result.id == "txn_with_refs"
        assert result.scope == "sc1"
        assert result.source == "default"
        # verify movement side is resolved
        movement = result.movements[0]
        assert movement.side == side1
        assert movement.side.side == "TestSide"
        # verify movement properties are resolved
        assert movement.properties
        assert len(movement.properties) == 1
        assert movement.properties[0].property_key == prop1
        assert movement.properties[0].property_key.code == "TestProp"
        assert movement.properties[0].label_value == "Test Label"
        # verify movement mappings are resolved
        assert movement.mappings
        assert len(movement.mappings) == 1
        assert movement.mappings[0].property_key == prop1
        assert movement.mappings[0].set_to == "Test Value"
        # verify global properties are resolved
        assert result.properties
        assert len(result.properties) == 1
        assert result.properties[0].property_key == prop1
        assert result.properties[0].metric_value
        assert result.properties[0].metric_value.value == 123.45
        # verify calculations side is resolved
        assert result.calculations
        assert len(result.calculations) == 1
        assert result.calculations[0].side == side1
        assert result.calculations[0].formula == "test_formula"
