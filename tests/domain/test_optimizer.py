"""Test about optimizer."""

import pytest
import propt.domain.concepts as concepts
import propt.adapters.yaml_repositories as yaml_repo
import propt.domain.optimizer as optimizer


@pytest.fixture
def recipe_repo() -> concepts.ConceptRepository[concepts.Recipe]:
    return yaml_repo.YAMLRecipeRepository(
        "pyanodons.yaml",
        yaml_repo.YAMLBuildingRepository("pyanodons.yaml"),
        yaml_repo.YAMLItemRepository("pyanodons.yaml"),
    )


def test_prod_map_from_repo(recipe_repo):
    """Test building a ProductionMap from repositories."""
    prod_map = optimizer.ProductionMap.from_repositories(recipe_repo)
    assert prod_map.production_units
    assert isinstance(prod_map.production_units[0], optimizer.ProductionUnit)
