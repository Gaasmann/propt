"""Tests for YAML repositories."""
from typing import Iterator

import propt.adapters.yaml_repositories as yaml_repositories
import propt.domain.concepts as concepts
import pytest


@pytest.fixture
def resource_file() -> str:
    """The resoource file used on those tests."""
    return "testdata.yaml"


@pytest.fixture(scope="function")
def repo(request, resource_file) -> yaml_repositories.YAMLItemRepository:
    """Return a ready to use repo."""
    item_repo = yaml_repositories.YAMLItemRepository(resource_file)
    building_repo = yaml_repositories.YAMLBuildingRepository(resource_file)
    recipe_repo = yaml_repositories.YAMLRecipeRepository(
        resource_file, building_repo, item_repo
    )
    rosetta_stone = {
        concepts.Item: item_repo,
        concepts.Building: building_repo,
        concepts.Recipe: recipe_repo,
    }
    return rosetta_stone[request.param]


def test_load_yaml_resource(resource_file):
    """Ensure we can access to data embedded in the package."""
    data = yaml_repositories.load_yaml_resource(resource_file)
    assert data
    assert isinstance(data, dict)


test_subjects = [
    (concepts.Item, concepts.Item, "coal", "Coal"),
    (concepts.Building, concepts.Building, "orecrusher", "Ore Crusher"),
    (concepts.Recipe, concepts.Recipe, "process-ore", "Process Ore"),
]


@pytest.mark.parametrize(
    ("repo", "concept", "osef", "osef2"), test_subjects, indirect=["repo"]
)
def test_list_all(repo, concept, osef, osef2):
    """Check list all for Item repo."""
    objects = repo.list_all()
    assert isinstance(objects, Iterator)
    assert all(isinstance(obj, concept) for obj in objects)


@pytest.mark.parametrize(
    ("repo", "concept", "code", "name"), test_subjects, indirect=["repo"]
)
def test_by_code(repo, concept, code, name):
    """Check by_code when everything's ok."""
    object = repo.by_code(concepts.Code(code))
    assert isinstance(object, concept)
    assert object.code == code
    assert object.name == name


@pytest.mark.parametrize(
    ("repo", "concept", "osef", "osef2"), test_subjects, indirect=["repo"]
)
def test_by_code_not_found(repo, concept, osef, osef2):
    """Check by_code when the item is not found."""
    with pytest.raises(concepts.ObjectNotFound):
        repo.by_code(concepts.Code("tututu"))
