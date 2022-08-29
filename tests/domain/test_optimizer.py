"""Test about optimizer."""

import pytest
import propt.domain.concepts as concepts
import propt.adapters.yaml_repositories as yaml_repo
import propt.domain.optimizer as optimizer


@pytest.fixture
def recipe_repo() -> concepts.ConceptRepository[concepts.Recipe]:
    return yaml_repo.YAMLRecipeRepository(
        "testdata.yaml",
        yaml_repo.YAMLBuildingRepository("testdata.yaml"),
        yaml_repo.YAMLItemRepository("testdata.yaml"),
    )


def test_prod_map_from_repo(recipe_repo):
    """Test building a ProductionMap from repositories."""
    prod_map = optimizer.ProductionMap.from_repositories(recipe_repo)
    assert prod_map.production_units
    assert isinstance(prod_map.production_units[0], optimizer.ProductionUnit)


@pytest.fixture
def prod_unit(recipe_repo) -> optimizer.ProductionUnit:
    recipe = recipe_repo.by_code(concepts.Code("ore-to-plate"))
    return optimizer.ProductionUnit(recipe=recipe, building=recipe.buildings[0])


def test_pu_get_item_quantity_ingredients(prod_unit):
    """Test that we get a negative quantity on ingredients."""
    ingredient = prod_unit.recipe.ingredients[0].item
    assert prod_unit.get_item_net_quantity_by_unit_of_time(ingredient) < 0
