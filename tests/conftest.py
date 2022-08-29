"""General conftest."""
from typing import Type

import pytest
import propt.domain.concepts as concepts
import propt.adapters.yaml_repositories as yaml_repositories


@pytest.fixture
def resource_file() -> str:
    return "testdata.yaml"


@pytest.fixture
def repositories(
    resource_file,
) -> dict[Type[concepts.GameConcept], concepts.ConceptRepository]:
    item_repo = yaml_repositories.YAMLItemRepository(resource_file)
    building_repo = yaml_repositories.YAMLBuildingRepository(resource_file)
    recipe_repo = yaml_repositories.YAMLRecipeRepository(
        resource_file, building_repo, item_repo
    )
    return {
        concepts.Item: item_repo,
        concepts.Building: building_repo,
        concepts.Recipe: recipe_repo,
    }
