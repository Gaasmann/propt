"""JSON repositories."""
import importlib.resources
import json
import logging
import pathlib
import pprint
import traceback
from typing import Any, Iterator

import propt.domain.concepts as concepts
from propt.adapters.indexer import OneToOneIndexer, MultiToMultiIndexer
from propt.domain.concepts import Code, Building, Item

_LOGGER = logging.getLogger(__name__)


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
    BOILERS_FILENAMES = ("boiler.json",)

    def __init__(self, json_directory: pathlib.Path):
        self._buildings: list[concepts.Building] = self._build_collection(
            json_directory
        )

        self._code_idx: OneToOneIndexer[
            concepts.Code, concepts.Building
        ] = OneToOneIndexer(lambda x: x.code)
        self._code_idx.set_collection(self._buildings)

        self._crafting_cat_idx: MultiToMultiIndexer[
            str, concepts.Building
        ] = MultiToMultiIndexer(lambda x: x.crafting_categories)
        self._crafting_cat_idx.set_collection(self._buildings)

    def _build_collection(
        self, json_directory: pathlib.Path
    ) -> list[concepts.Building]:
        buildings: list[concepts.Building] = []
        for file in self.REGULAR_FILENAMES:
            data = load_json_file(json_directory / file)
            buildings.extend(
                concepts.Building(
                    code=concepts.Code(code),
                    name=building_data["name"],
                    speed_coef=building_data["crafting_speed"],
                    crafting_categories=tuple(
                        key
                        for key, active in building_data["crafting_categories"].items()
                        if active
                    ),
                )
                for code, building_data in data.items()
            )

        for file in self.MINING_FILENAMES:
            data = load_json_file(json_directory / file)
            buildings.extend(
                concepts.Building(
                    code=concepts.Code(code),
                    name=building_data["name"],
                    speed_coef=building_data["mining_speed"],
                    crafting_categories=tuple(
                        key
                        for key, active in building_data["resource_categories"].items()
                        if active
                    ),
                )
                for code, building_data in data.items()
            )
        for file in self.BOILERS_FILENAMES:
            data = load_json_file(json_directory / file)
            buildings.extend(
                concepts.Building(
                    code=concepts.Code(code),
                    name=building_data["name"],
                    speed_coef=1.0,
                    crafting_categories=(building_data["name"],),
                )
                for code, building_data in data.items()
            )
        return buildings

    def list_all(self) -> list[concepts.Building]:
        return self._buildings

    def by_code(self, code: Code) -> concepts.Building:
        try:
            return self._code_idx[code]
        except KeyError as e:
            raise concepts.ObjectNotFound(code) from e

    def by_crafting_category(
        self, crafting_category: str
    ) -> tuple[concepts.Building, ...]:
        return tuple(self._crafting_cat_idx[crafting_category])


class JSONItemRepository(concepts.ItemRepository):
    """Items from JSON files."""

    # REGULAR_FILENAMES = ("assembling-machine.json", "furnace.json", "rocket-silo.json")
    # # TODO boiler.json generator.json lab.json reactor.json solar panel are different
    # MINING_FILENAMES = ("mining-drill.json",)
    # # TODO How to deal with the boilers
    def __init__(
        self, json_directory: pathlib.Path, building_repo: concepts.BuildingRepository
    ):
        self._items = self._build_collection(json_directory, building_repo)

        self._code_idx: OneToOneIndexer[concepts.Code, concepts.Item] = OneToOneIndexer(
            lambda x: x.code
        )
        self._code_idx.set_collection(self._items)

        self._buildings_idx: OneToOneIndexer[concepts.Building, concepts.Item] = OneToOneIndexer(
            lambda x: x.place_result
        )
        self._buildings_idx.set_collection(self._items)


    @staticmethod
    def _build_collection(
        json_directory: pathlib.Path, building_repo: concepts.BuildingRepository
    ) -> list[concepts.Item]:
        items: list[concepts.Item] = []
        for filename in ("item.json", "fluid.json"):
            data = load_json_file(json_directory / filename)
            for code, data in data.items():
                try:
                    place_result = (
                        building_repo.by_code(concepts.Code(data["place_result"]))
                        if data.get("place_result")
                        else None
                    )
                except concepts.ObjectNotFound:
                    place_result = None
                items.append(
                    concepts.Item(
                        code=concepts.Code(code),
                        name=data["name"],
                        item_type=data.get("type", "fluid"),
                        place_result=place_result,
                    )
                )
        return items

    def list_all(self) -> list[concepts.Item]:
        return self._items

    def by_code(self, code: Code) -> concepts.Item:
        try:
            return self._code_idx[code]
        except KeyError as e:
            raise concepts.ObjectNotFound(code) from e

    def by_building(self, building: Building) -> Item:
        try:
            return self._buildings_idx[building]
        except KeyError as e:
            raise concepts.ObjectNotFound(building) from e


class JSONRecipeRepository(concepts.RecipeRepository):
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
        self._recipes = self._build_collection(json_directory, item_repo, building_repo)
        self._code_idx: OneToOneIndexer[
            concepts.Code, concepts.Recipe
        ] = OneToOneIndexer(lambda x: x.code)
        self._code_idx.set_collection(self._recipes)

    @staticmethod
    def _get_items(
        item_list: list[dict[str, Any]],
        item_repo: concepts.ConceptRepository[concepts.Item],
    ) -> Iterator[concepts.Quantity]:
        for item in item_list:
            try:
                concept_item = item_repo.by_code(item["name"])
                if (amount := item.get("amount")) is None:
                    amount = (item["amount_min"] + item["amount_max"]) / 2
                try:
                    amount /= item.get("probability", 1.0)
                except ZeroDivisionError:
                    amount = 0
                yield concepts.Quantity(item=concept_item, qty=amount)
            except concepts.ObjectNotFound as e:
                _LOGGER.warning(f"Can't find item {e.args}")

    @staticmethod
    def _get_buildings(
        data: dict[str, Any], building_repo: concepts.BuildingRepository
    ) -> tuple[concepts.Building, ...]:
        category = data.get("category") or data.get("resource_category") or ""
        buildings = list(building_repo.by_crafting_category(category))
        if not buildings:
            _LOGGER.warning(
                f"No building found for recipe '{data['name']}' category: '{category}' {buildings}."
            )
            buildings = [building_repo.list_all()[0]]
        return tuple(buildings)

    def _build_collection(
        self,
        json_directory: pathlib.Path,
        item_repo: concepts.ConceptRepository[concepts.Item],
        building_repo: concepts.BuildingRepository,
    ) -> list[concepts.Recipe]:
        # TODO add energy
        recipes: list[concepts.Recipe] = []
        for filename in ("recipe.json",):
            data = load_json_file(json_directory / filename)
            for code, data in data.items():
                try:
                    if data["group"]["name"] == "recycling":
                        continue
                    if data.get("subgroup", {}).get("name", "").startswith("py-void"):
                        continue
                    if data["name"].startswith("blackhole-"):
                        continue
                    buildings = self._get_buildings(data, building_repo)
                    recipes.append(
                        concepts.Recipe(
                            code=concepts.Code(code),
                            name=data["name"],
                            available_from_start=data["enabled"],
                            hidden_from_player_crafting=data["hidden_from_player_crafting"],
                            base_time=data["energy"],
                            ingredients=tuple(
                                self._get_items(data["ingredients"], item_repo)
                            ),
                            products=tuple(
                                self._get_items(data["products"], item_repo)
                            ),
                            buildings=buildings,
                        )
                    )

                except Exception as e:
                    traceback.print_exc()
                    _LOGGER.warning(
                        f"can't load the recipe:{pprint.pformat(data)}\n{e}"
                    )
        for filename in ("resource.json",):
            data = load_json_file(json_directory / filename)
            for code, data in data.items():
                try:
                    buildings = self._get_buildings(data, building_repo)
                    mineprop = data["mineable_properties"]
                    recipes.append(
                        concepts.Recipe(
                            code=concepts.Code(f"res-{code}"),
                            name="res-" + data["name"],
                            available_from_start=True,
                            hidden_from_player_crafting=True,
                            base_time=mineprop["mining_time"],
                            ingredients=(
                                concepts.Quantity(
                                    item=item_repo.by_code(mineprop["required_fluid"]),
                                    qty=mineprop["fluid_amount"],
                                ),
                            )
                            if "required_fluid" in mineprop
                            else tuple(),
                            products=tuple(
                                self._get_items(mineprop["products"], item_repo)
                            ),
                            buildings=buildings,
                        )
                    )

                except Exception as e:
                    _LOGGER.warning(
                        f"can't load the recipe:{pprint.pformat(data)}\n{e}"
                    )
        for filename in ("boiler.json",):
            data = load_json_file(json_directory / filename)
            for boiler_code, boiler_data in data.items():
                steam_throughput = (
                    boiler_data["max_energy_usage"]
                    / (boiler_data["target_temperature"] - 15)
                    * 200
                )
                recipes.append(
                    concepts.Recipe(
                        code=concepts.Code(f"water-boiling-{boiler_code}"),
                        name=f"water-boiling-{boiler_code}",
                        available_from_start=True,  # TODO think about avail_from_start for boiler
                        hidden_from_player_crafting=True,
                        base_time=1.0,
                        ingredients=(
                            concepts.Quantity(
                                item=item_repo.by_code(concepts.Code("water")),
                                qty=steam_throughput,
                            ),
                        ),
                        products=(
                            concepts.Quantity(
                                item=item_repo.by_code(concepts.Code("steam")),
                                qty=steam_throughput,
                            ),
                        ),
                        buildings=(building_repo.by_code(concepts.Code(boiler_code)),),
                    )
                )

        return recipes

    def list_all(self) -> list[concepts.Recipe]:
        return self._recipes

    def by_code(self, code: Code) -> concepts.Recipe:
        try:
            return self._code_idx[code]
        except KeyError as e:
            raise concepts.ObjectNotFound(code) from e


class JSONTechnologyRepository(concepts.ConceptRepository[concepts.Technology]):
    def __init__(
        self, recipe_repo: concepts.RecipeRepository, json_directory: pathlib.Path
    ):
        self._technologies = self._build_collection(json_directory, recipe_repo)

        self._code_idx: OneToOneIndexer[
            concepts.Code, concepts.Technology
        ] = OneToOneIndexer(lambda x: x.code)
        self._code_idx.set_collection(self._technologies)

    @staticmethod
    def _build_collection(
        json_directory: pathlib.Path, recipe_repo: concepts.RecipeRepository
    ) -> list[concepts.Technology]:
        data = load_json_file(json_directory / "technology.json")
        techs: list[concepts.Technology] = []
        for code, tech in data.items():
            recipe_to_unlock = tuple(
                recipe_repo.by_code(effect["recipe"])
                for effect in tech["effects"]
                if effect["type"] == "unlock-recipe"
            )
            techs.append(
                concepts.Technology(
                    code=concepts.Code(code),
                    name=tech["name"],
                    recipes_unlocked=recipe_to_unlock,
                )
            )
        return techs

    def list_all(self) -> list[concepts.Technology]:
        return self._technologies

    def by_code(self, code: Code) -> concepts.Technology:
        try:
            return self._code_idx[code]
        except KeyError as e:
            raise concepts.ObjectNotFound(code) from e
