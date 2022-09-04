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


class JSONBuildingRepository(concepts.BuildingRepository):
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
                    crafting_categories=tuple(
                        key
                        for key, active in building_data["crafting_categories"].items()
                        if active
                    ),
                )
        for file in self.MINING_FILENAMES:
            data = load_json_file(self._json_directory / file)
            for code, building_data in data.items():
                yield concepts.Building(
                    code=concepts.Code(code),
                    name=building_data["name"],
                    speed_coef=building_data["mining_speed"],
                    crafting_categories=tuple(
                        key
                        for key, active in building_data["resource_categories"].items()
                        if active
                    ),
                )

    def by_code(self, code: Code) -> concepts.Building:
        return next(building for building in self.list_all() if building.code == code)

    @functools.cache
    def by_crafting_category(self, crafting_category: str) -> tuple[concepts.Building]:
        return tuple(
            building
            for building in self.list_all()
            if crafting_category in building.crafting_categories
        )


class JSONItemRepository(concepts.ConceptRepository[concepts.Item]):
    """Items from JSON files."""

    # REGULAR_FILENAMES = ("assembling-machine.json", "furnace.json", "rocket-silo.json")
    # # TODO boiler.json generator.json lab.json reactor.json solar panel are different
    # MINING_FILENAMES = ("mining-drill.json",)
    # # TODO How to deal with the boilers
    def __init__(self, json_directory: pathlib.Path):
        self._json_directory = json_directory

    def list_all(self) -> Iterator[concepts.Item]:
        for filename in ("item.json", "fluid.json"):
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
        building_repo: concepts.BuildingRepository,
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
                if (amount := item.get("amount")) is None:
                    amount = (item["amount_min"] + item["amount_max"]) / 2
                try:
                    amount /= item.get("probability", 1.0)
                except ZeroDivisionError:
                    amount = 0
                yield concepts.Quantity(item=concept_item, qty=amount)
            except concepts.ObjectNotFound as e:
                _LOGGER.warning(f"Can't find item {e.args}")

    @functools.cache
    def _get_buildings(
        self, receipe_code: str, category: str
    ) -> tuple[concepts.Building]:
        buildings = tuple(self._building_repo.by_crafting_category(category))
        if not buildings:
            _LOGGER.warning(
                f"No building found for receipe '{receipe_code}' category: '{category}' {buildings}."
            )
            buildings = (next(self._building_repo.list_all()),)
        return buildings

    def list_all(self) -> Iterator[concepts.Recipe]:
        # TODO add energy
        for filename in ("recipe.json",):
            data = load_json_file(self._json_directory / filename)
            for code, data in data.items():
                try:
                    if data["group"]["name"] == "recycling":
                        continue
                    buildings = self._get_buildings(code, data["category"])
                    yield concepts.Recipe(
                        code=concepts.Code(code),
                        name=data["name"],
                        base_time=data["energy"],
                        ingredients=tuple(self._get_items(data["ingredients"])),
                        products=tuple(self._get_items(data["products"])),
                        buildings=buildings,
                    )

                except Exception as e:
                    _LOGGER.warning(
                        f"can't load the recipe:{pprint.pformat(data)}\n{e}"
                    )
        for filename in ("resource.json",):
            data = load_json_file(self._json_directory / filename)
            for code, data in data.items():
                try:
                    buildings = self._get_buildings(code, data["resource_category"])
                    mineprop = data["mineable_properties"]
                    yield concepts.Recipe(
                        code=concepts.Code(f"res-{code}"),
                        name="res-" + data["name"],
                        base_time=mineprop["mining_time"],
                        ingredients=(
                            concepts.Quantity(
                                item=self._item_repo.by_code(
                                    mineprop["required_fluid"]
                                ),
                                qty=mineprop["fluid_amount"],
                            ),
                        )
                        if "required_fluid" in mineprop
                        else tuple(),
                        products=tuple(self._get_items(mineprop["products"])),
                        buildings=buildings,
                    )

                except Exception as e:
                    _LOGGER.warning(
                        f"can't load the recipe:{pprint.pformat(data)}\n{e}"
                    )

    def by_code(self, code: Code) -> concepts.Recipe:
        return next(item for item in self.list_all() if item.code == code)
