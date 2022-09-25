"""Test about optimizer."""

import pytest
import propt.domain.factorio as factorio_model
import propt.domain.optimizer as optimizer


def test_prod_map_from_repo(repositories):
    """Test building a ProductionMap from repositories."""
    prod_map = optimizer.ProductionMap.from_repositories(
        recipe_repository=repositories[factorio_model.FactorioRecipe],
        item_repository=repositories[factorio_model.FactorioItem],
        resource_repository=repositories[factorio_model.FactorioResource],
        assembly_machine_repository=repositories[factorio_model.FactorioAssemblingMachine],
        furnace_repository=repositories[factorio_model.FactorioFurnace],
        rocket_silo_repository=repositories[factorio_model.FactorioRocketSilo],
        mining_drill_repository=repositories[factorio_model.FactorioMiningDrill],
        technology_set=factorio_model.TechnologySet([])
    )
    assert prod_map.production_units
    assert isinstance(prod_map.production_units[0], optimizer.ProductionUnit)


# @pytest.fixture
# def prod_unit(repositories) -> optimizer.ProductionUnit:
#     recipe = repositories[factorio_model.FactorioRecipe]["ore-to-plate"]
#     building = repositories[factorio_model.FactorioFurnace]["stone-furnace"]
#     return optimizer.ProductionUnit(recipe=recipe, building=building)


def test_pu_get_item_quantity_ingredients(prod_unit):
    """Test that we get a negative quantity on ingredients."""
    ingredient = prod_unit.recipe.ingredients[0].item
    assert prod_unit.get_item_net_quantity_by_unit_of_time(ingredient) < 0


# def test_production_unit_items(prod_unit):
#     res = prod_unit.items
#     assert res == {
#         concepts.Item(code=concepts.Code("plate"), name="Random Plate"),
#         concepts.Item(code=concepts.Code("ore"), name="Random Ore"),
#     }


def test_prod_unit_get_quantity(repositories):
    resource: factorio_model.FactorioResource = repositories[factorio_model.FactorioResource]["borax"]
    optimizer_recipe = optimizer.Recipe.from_factorio_resource(resource)
    print(optimizer_recipe)
    item = optimizer_recipe.products[0].item
    building: factorio_model.FactorioMiningDrill = repositories[factorio_model.FactorioMiningDrill]["borax-mine"]
    prod_unit = optimizer.ProductionUnit(
        recipe=optimizer_recipe,
        building=optimizer.Building.from_factorio_mining_drill(building)
    )
    assert prod_unit.get_item_net_quantity_by_unit_of_time(item) == pytest.approx(1.4)


def test_prod_unit_get_quantity(repositories):
    resource: factorio_model.FactorioResource = repositories[factorio_model.FactorioResource]["borax"]
    optimizer_recipe = optimizer.Recipe.from_factorio_resource(resource)
    item = optimizer_recipe.products[0].item
    building: factorio_model.FactorioMiningDrill = repositories[factorio_model.FactorioMiningDrill]["borax-mine"]
    prod_unit = optimizer.ProductionUnit(
        recipe=optimizer_recipe,
        building=optimizer.Building.from_factorio_mining_drill(building)
    )
    assert prod_unit.get_item_net_quantity_by_unit_of_time(item) == pytest.approx(1.4)



def test_item_equality():
    import propt.domain.optimizer.model as opt
    no_energy = opt.Item(name="dudul", temperature=None, energy_ingredient=False)
    energy = opt.Item(name="dudul", temperature=None, energy_ingredient=True)
    assert no_energy == energy
    assert hash(no_energy) == hash(energy)


def test_item_inequality():
    import propt.domain.optimizer.model as opt
    no_energy = opt.Item(name="dudul", temperature=None, energy_ingredient=False)
    energy = opt.Item(name="toto", temperature=None, energy_ingredient=True)
    assert no_energy != energy
    assert hash(no_energy) != hash(energy)

