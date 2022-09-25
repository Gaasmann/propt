"""YAML Repositories."""
import functools
import importlib.resources
from typing import Any, TypeVar, Type

import yaml

import propt.domain.concepts as concepts
from propt.domain.concepts import Code

import propt.domain.factorio.buildings
import propt.domain.factorio.prototypes


@functools.cache
def load_yaml_resource(resource_file: str) -> dict[str, Any]:
    """Open and load a YAML resource file."""
    with importlib.resources.open_text("propt.data", resource_file) as f:
        data = yaml.load(f, yaml.Loader)
    return data


T = TypeVar("T", bound=concepts.GameConcept)


class YAMLRepository(concepts.ConceptRepository[T]):
    """Generic YAML repository"""

    _CONCEPT: Type[concepts.GameConcept] = concepts.GameConcept
    _KEY: str = ""

    def __init__(self, resource_file: str):
        self.resource_file: str = resource_file

    def _data_dict(self) -> dict[concepts.Code, Any]:
        return load_yaml_resource(self.resource_file)[self._KEY]

    def list_all(self) -> list[T]:
        return [  # type: ignore
            self._CONCEPT(code=code, **data) for code, data in self._data_dict().items()  # type: ignore
        ]

    def by_code(self, code: Code) -> T:
        try:
            return self._CONCEPT(code=code, **self._data_dict()[code])  # type: ignore
        except KeyError as e:
            raise concepts.ObjectNotFound(code) from e


class YAMLItemRepository(YAMLRepository[concepts.Item]):
    """Repository for Items stored in a YAML file."""

    _CONCEPT = concepts.Item
    _KEY = "items"


class YAMLBuildingRepository(YAMLRepository[propt.domain.factorio.prototypes.Building]):
    """Repository for Buildings stored in a YAML file."""

    _CONCEPT = propt.domain.factorio.prototypes.Building
    _KEY = "buildings"


class YAMLRecipeRepository(YAMLRepository[concepts.Recipe]):
    """Repository for Recipes stored in a YAML file."""

    _CONCEPT = concepts.Recipe
    _KEY = "recipes"

    def __init__(
        self,
        resource_file: str,
        building_repository: concepts.ConceptRepository[propt.domain.factorio.prototypes.Building],
        item_repository: concepts.ConceptRepository[concepts.Item],
    ):
        super().__init__(resource_file)
        self._building_repository = building_repository
        self._item_repository = item_repository

    def _build_recipe_from_info(
        self, code: str, raw_file_info: dict[str, Any]
    ) -> concepts.Recipe:
        info = {
            "code": code,
            "name": raw_file_info["name"],
            "base_time": raw_file_info["base_time"],
            "ingredients": tuple(
                concepts.Quantity(
                    item=self._item_repository.by_code(raw["code"]), qty=raw["qty"]
                )
                for raw in raw_file_info["ingredients"]
            ),
            "products": tuple(
                concepts.Quantity(
                    item=self._item_repository.by_code(raw["code"]), qty=raw["qty"]
                )
                for raw in raw_file_info["products"]
            ),
            "buildings": tuple(
                self._building_repository.by_code(code)
                for code in raw_file_info["buildings"]
            ),
        }
        return concepts.Recipe(**info)

    def list_all(self) -> list[concepts.Recipe]:
        return [
            self._build_recipe_from_info(code, data)
            for code, data in self._data_dict().items()
        ]

    def by_code(self, code: Code) -> concepts.Recipe:
        try:
            return self._build_recipe_from_info(code, self._data_dict()[code])
        except KeyError as e:
            raise concepts.ObjectNotFound(code) from e
