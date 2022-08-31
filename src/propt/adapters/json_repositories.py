"""JSON repositories."""
import functools
import importlib.resources
import json
import logging
import pathlib
import pprint
from contextlib import suppress
from typing import Any, Iterator
import propt.domain.concepts as concepts
from propt.domain.concepts import Code, T


_LOGGER = logging.getLogger(__name__)


@functools.cache
def load_json_file(resource_file: pathlib.Path) -> dict[str, Any]:
    """Open and load a JSON file."""
    path = ".".join(resource_file.parts[:-1])
    filename = resource_file.parts[-1]
    with importlib.resources.open_text(
        f"propt.data{f'.{path}' if path else ''}", filename
    ) as f:
        data = json.load(f)
    return data


class JSONBuildingRepository(concepts.ConceptRepository[concepts.Building]):
    """Buildings from JSON files."""

    REGULAR_FILENAMES = ("assembling-machine.json", "furnace.json", "rocket-silo.json")
    # TODO boiler.json generator.json lab.json reactor.json solar panel are different
    MINING_FILENAMES = ("mining-drill.json",)
    # TODO How to deal with the boilers
    def __init__(self, json_directory: pathlib.Path):
        self._json_directory = json_directory

    def list_all(self) -> Iterator[concepts.Building]:
        for file in self.REGULAR_FILENAMES:
            data = load_json_file(self._json_directory / file)
            for code, building_data in data.items():
                yield concepts.Building(
                    code=concepts.Code(code),
                    name=building_data["name"],
                    speed_coef=building_data["crafting_speed"],
                )
        for file in self.MINING_FILENAMES:
            data = load_json_file(self._json_directory / file)
            for code, building_data in data.items():
                yield concepts.Building(
                    code=concepts.Code(code),
                    name=building_data["name"],
                    speed_coef=building_data["mining_speed"],
                )

    def by_code(self, code: Code) -> concepts.Building:
        return next(building for building in self.list_all() if building.code == code)


class JSONItemRepository(concepts.ConceptRepository[concepts.Item]):
    """Items from JSON files."""

    # REGULAR_FILENAMES = ("assembling-machine.json", "furnace.json", "rocket-silo.json")
    # # TODO boiler.json generator.json lab.json reactor.json solar panel are different
    # MINING_FILENAMES = ("mining-drill.json",)
    # # TODO How to deal with the boilers
    def __init__(self, json_directory: pathlib.Path):
        self._json_directory = json_directory

    def list_all(self) -> Iterator[concepts.Item]:
        # TODO need to add fluids
        for filename in ("item.json",):
            data = load_json_file(self._json_directory / filename)
            for code, data in data.items():
                yield concepts.Item(code=concepts.Code(code), name=data["name"])

    @functools.cache
    def by_code(self, code: Code) -> concepts.Item:
        try:
            return next(item for item in self.list_all() if item.code == code)
        except StopIteration:
            raise concepts.ObjectNotFound(code)


class JSONRecipeRepository(concepts.ConceptRepository[concepts.Recipe]):
    """Recipe from JSON files."""

    # REGULAR_FILENAMES = ("assembling-machine.json", "furnace.json", "rocket-silo.json")
    # # TODO boiler.json generator.json lab.json reactor.json solar panel are different
    # MINING_FILENAMES = ("mining-drill.json",)
    # # TODO How to deal with the boilers
    def __init__(
        self,
        item_repo: concepts.ConceptRepository[concepts.Item],
        building_repo: concepts.ConceptRepository[concepts.Building],
        json_directory: pathlib.Path,
    ):
        self._item_repo = item_repo
        self._building_repo = building_repo
        self._json_directory = json_directory

    def _get_items(
        self, item_list: list[dict[str, Any]]
    ) -> Iterator[concepts.Quantity]:
        for item in item_list:
            try:
                concept_item = self._item_repo.by_code(item["name"])
                yield concepts.Quantity(item=concept_item, qty=item["amount"])
            except concepts.ObjectNotFound as e:
                _LOGGER.warning(f"Can't find item {e.args}")

    def list_all(self) -> Iterator[concepts.Recipe]:
        # TODO need to add fluids
        for filename in ("recipe.json",):
            data = load_json_file(self._json_directory / filename)
            for code, data in data.items():
                # TODO Where to find the machines
                try:
                    if data["group"]["name"] == "recycling":
                        continue
                    yield concepts.Recipe(
                        code=concepts.Code(code),
                        name=data["name"],
                        base_time=data["energy"],
                        ingredients=tuple(
                            ingredient
                            for ingredient in self._get_items(data["ingredients"])
                        ),
                        products=tuple(
                            product for product in self._get_items(data["products"])
                        ),
                        buildings=(next(self._building_repo.list_all()),),
                    )
                except Exception as e:
                    _LOGGER.warning(f"can't load the recipe:{pprint.pformat(data)}")

    def by_code(self, code: Code) -> concepts.Recipe:
        return next(item for item in self.list_all() if item.code == code)
