"""JSON implementation of Factorio repositories."""
from __future__ import annotations

import abc
import json
import pathlib
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, TypeVar

import more_itertools

import propt.domain.factorio as factorio_model
from propt.domain.factorio import FactorioItem, FactorioFluid, FactorioRecipe

T = TypeVar("T", bound=factorio_model.FactorioObject)


class JSONFactorioRepository(
    factorio_model.FactorioRepository[str, T], metaclass=abc.ABCMeta
):
    def __init__(self, filename: str):
        super().__init__()
        self.__filename = filename

    @abc.abstractmethod
    def build_object(self, data: Mapping[str, any]) -> T:
        """Build a Factorio object from its JSON dict representation."""

    def _load_file(self, json_directory: pathlib.Path) -> None:
        with open(json_directory / self.__filename) as f:
            data = json.load(f)
        for data_item in data.values():
            obj = self.build_object(data_item)
            self[obj.name] = obj


class JSONFactorioAssemblingMachineRepository(
    factorio_model.FactorioAssemblingMachineRepository,
    JSONFactorioRepository[factorio_model.FactorioAssemblingMachine],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="assembling-machine.json")
        self._load_file(json_directory)

    def build_object(
        self, data: dict[str, Any]
    ) -> factorio_model.FactorioAssemblingMachine:
        assert len(data["energy_source"].keys()) < 2
        return factorio_model.FactorioAssemblingMachine(
            name=data["name"],
            energy_usage=data["energy_usage"],
            crafting_speed=data["crafting_speed"],
            crafting_categories=tuple(
                key for key, value in data["crafting_categories"].items() if value
            ),
            module_inventory_size=data["module_inventory_size"],
            allowed_effects=tuple(
                key for key, value in data["allowed_effects"].items() if value
            ),
            energy_source=more_itertools.first(data["energy_source"].keys()),
        )


class JSONFactorioBoilerRepository(
    factorio_model.FactorioBoilerRepository,
    JSONFactorioRepository[factorio_model.FactorioAssemblingMachine],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__("boiler.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> factorio_model.FactorioBoiler:
        assert len(data["energy_source"].keys()) < 2
        return factorio_model.FactorioBoiler(
            name=data["name"],
            max_energy_usage=data["max_energy_usage"],
            target_temperature=data["target_temperature"],
            energy_source=more_itertools.first(data["energy_source"].keys()),
        )


class JSONFactorioFluidRepository(
    factorio_model.FactorioFluidRepository,
    JSONFactorioRepository[factorio_model.FactorioAssemblingMachine],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__("fluid.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> factorio_model.FactorioFluid:
        return factorio_model.FactorioFluid(
            name=data["name"],
            default_temperature=data["default_temperature"],
            max_temperature=data["max_temperature"],
            fuel_value=data["fuel_value"],
        )


class JSONFactorioFurnaceRepository(
    factorio_model.FactorioFurnaceRepository,
    JSONFactorioRepository[factorio_model.FactorioFurnace],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="furnace.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> factorio_model.FactorioFurnace:
        assert len(data["energy_source"].keys()) < 2
        return factorio_model.FactorioFurnace(
            name=data["name"],
            energy_usage=data["energy_usage"],
            crafting_speed=data["crafting_speed"],
            crafting_categories=tuple(
                key for key, value in data["crafting_categories"].items() if value
            ),
            module_inventory_size=data["module_inventory_size"],
            allowed_effects=tuple(
                key for key, value in data["allowed_effects"].items() if value
            ),
            energy_source=more_itertools.first(data["energy_source"].keys()),
        )


class JSONFactorioGeneratorRepository(
    factorio_model.FactorioGeneratorRepository,
    JSONFactorioRepository[factorio_model.FactorioGenerator],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="generator.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> factorio_model.FactorioGenerator:
        assert len(data["energy_source"].keys()) < 2
        return factorio_model.FactorioGenerator(
            name=data["name"],
            max_temperature=data["maximum_temperature"],
            effectivity=data["effectivity"],
            fluid_usage_per_tick=data["fluid_usage_per_tick"],
            max_energy_production=data["max_energy_production"],
            energy_source=more_itertools.first(data["energy_source"].keys()),
        )


class JSONFactorioItemRepository(
    factorio_model.FactorioItemRepository,
    JSONFactorioRepository[factorio_model.FactorioItem],
):
    def __init__(
        self,
        json_directory: pathlib.Path,
        assembly_machine_repo: factorio_model.FactorioAssemblingMachineRepository,
        furnace_repo: factorio_model.FactorioFurnaceRepository,
        rocket_silo_repo: factorio_model.FactorioRocketSiloRepository,
        mining_drill_repo: factorio_model.FactorioMiningDrillRepository,
    ):  # TODO add all type of buildings
        super().__init__(filename="item.json")
        self._assembly_machine_repo = assembly_machine_repo
        self._furnace_repo = furnace_repo
        self._rocket_silo_repo = rocket_silo_repo
        self._mining_drill_repo = mining_drill_repo
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> factorio_model.FactorioItem:
        pl = data.get("place_result")
        place_result = (
            (
                self._assembly_machine_repo.get(pl)
                or self._rocket_silo_repo.get(pl)
                or self._furnace_repo.get(pl)
                or self._mining_drill_repo.get(pl)
            )
            if pl
            else None
        )
        return factorio_model.FactorioItem(
            name=data["name"],
            fuel_value=data.get("fuel_value", 0),
            fuel_category=data.get("fuel_category", "no_category"),
            place_result=place_result,
        )


class JSONFactorioMiningDrillRepository(
    factorio_model.FactorioMiningDrillRepository,
    JSONFactorioRepository[factorio_model.FactorioMiningDrill],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="mining-drill.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> factorio_model.FactorioMiningDrill:
        assert len(data["energy_source"]) < 2
        try:
            return factorio_model.FactorioMiningDrill(
                name=data["name"],
                energy_usage=data["energy_usage"],
                mining_speed=data["mining_speed"],
                resource_categories=tuple(
                    key for key, value in data["resource_categories"].items() if value
                ),
                allowed_effects=tuple(
                    key for key, value in data["allowed_effects"].items() if value
                ),
                energy_source=more_itertools.first(data["energy_source"].keys()),
                energy_effectivity=more_itertools.first(
                    data["energy_source"].values()
                ).get("effectivity", 1.0),
                fuel_category=tuple(
                    key
                    for key, value in more_itertools.first(
                        data["energy_source"].values()
                    )
                    .get("fuel_categories", {})
                    .items()
                    if value
                ),
            )
        except KeyError:
            print(data)
            raise


class JSONFactorioReactorRepository(
    factorio_model.FactorioReactorRepository,
    JSONFactorioRepository[factorio_model.FactorioReactor],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="reactor.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> factorio_model.FactorioReactor:
        assert len(data["energy_source"]) < 2
        return factorio_model.FactorioReactor(
            name=data["name"],
            max_energy_usage=data["max_energy_usage"],
            neighbour_bonus=data["neighbour_bonus"],
            energy_source=more_itertools.first(data["energy_source"].keys()),
            energy_effectivity=more_itertools.first(data["energy_source"].values())[
                "effectivity"
            ],
            fuel_category=tuple(
                key
                for key, value in more_itertools.first(data["energy_source"].values())[
                    "fuel_categories"
                ].items()
                if value
            ),
        )


class JSONFactorioRocketSiloRepository(
    factorio_model.FactorioRocketSiloRepository,
    JSONFactorioRepository[factorio_model.FactorioRocketSilo],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="rocket-silo.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> factorio_model.FactorioRocketSilo:
        assert len(data["energy_source"].keys()) < 2
        return factorio_model.FactorioRocketSilo(
            name=data["name"],
            energy_usage=data["energy_usage"],
            crafting_speed=data["crafting_speed"],
            crafting_categories=tuple(
                key for key, value in data["crafting_categories"].items() if value
            ),
            module_inventory_size=data["module_inventory_size"],
            allowed_effects=tuple(
                key for key, value in data["allowed_effects"].items() if value
            ),
            energy_source=more_itertools.first(data["energy_source"].keys()),
        )


class JSONFactorioSolarPanelRepository(
    factorio_model.FactorioSolarPanelRepository,
    JSONFactorioRepository[factorio_model.FactorioSolarPanel],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="solar-panel.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> factorio_model.FactorioSolarPanel:
        return factorio_model.FactorioSolarPanel(
            name=data["name"], max_energy_production=data["max_energy_production"]
        )


class JSONFactorioResourceRepository(
    factorio_model.FactorioResourceRepository,
    JSONFactorioRepository[factorio_model.FactorioResource],
):
    def __init__(
        self,
        json_directory: pathlib.Path,
        item_repo: factorio_model.FactorioItemRepository,
        fluid_repo: factorio_model.FactorioFluidRepository,
    ):
        super().__init__(filename="resource.json")
        self._item_repo = item_repo
        self._fluid_repo = fluid_repo
        self._load_file(json_directory)

    def build_object(self, data) -> factorio_model.FactorioResource:
        try:
            return factorio_model.FactorioResource(
                name=data["name"],
                resource_category=data["resource_category"],
                mining_time=data["mineable_properties"]["mining_time"],
                required_fluid=self._fluid_repo[data["required_fluid"]]
                if "required_fluid" in data
                else None,
                fluid_amount=data.get("fluid_amount", 0),
                products=tuple(
                    factorio_model.Quantity(
                        item=self._item_repo[product["name"]]
                        if product["type"] == "item"
                        else self._fluid_repo[product["name"]],
                        qty=(
                            product.get("amount")
                            or (product.get("max_amount") - product.get("min_amount"))
                        )
                        / product.get("probability", 1)
                        if product.get("probability") != 0
                        else 0,
                    )
                    for product in data["mineable_properties"]["products"]
                ),
            )
        except KeyError:
            print(data)
            raise


class JSONFactorioRecipeRepository(
    factorio_model.FactorioRecipeRepository,
    JSONFactorioRepository[factorio_model.FactorioRecipe],
):
    def __init__(
        self,
        json_directory: pathlib.Path,
        item_repo: factorio_model.FactorioItemRepository,
        fluid_repo: factorio_model.FactorioFluidRepository,
    ):
        super().__init__(filename="recipe.json")
        self._item_repo = item_repo
        self._fluid_repo = fluid_repo
        self._recipe_per_product: dict[
            str, set[factorio_model.FactorioRecipe]
        ] = defaultdict(set)
        self._load_file(json_directory)

    def build_object(self, data) -> factorio_model.FactorioRecipe:
        try:
            ingredients = tuple(
                factorio_model.FactorioRecipe.Item(
                    item_type=item["type"],
                    stuff=self._item_repo[item["name"]]
                    if item["type"] == "item"
                    else self._fluid_repo[item["name"]],
                    amount=item.get("amount", 0),
                    min_amount=item.get("min_amount", 0),
                    max_amount=item.get("max_amount", 0),
                    probability=item.get("probability", 1),
                    temperature=item.get("temperature"),
                )
                for item in data["ingredients"]
            )
            products = tuple(
                factorio_model.FactorioRecipe.Item(
                    item_type=item["type"],
                    stuff=self._item_repo[item["name"]]
                    if item["type"] == "item"
                    else self._fluid_repo[item["name"]],
                    amount=item.get("amount", 0),
                    min_amount=item.get("min_amount", 0),
                    max_amount=item.get("max_amount", 0),
                    probability=item.get("probability", 1),
                    temperature=item.get("temperature"),
                )
                for item in data["products"]
            )
            recipe = factorio_model.FactorioRecipe(
                name=data["name"],
                category=data["category"],
                enabled=data["enabled"],
                hidden=data["hidden"],
                hidden_from_player_crafting=data["hidden_from_player_crafting"],
                energy=data["energy"],
                ingredients=ingredients,
                products=products,
            )
            for product in products:
                self._recipe_per_product[product.stuff.name].add(recipe)
            return recipe
        except KeyError:
            print(data)
            raise

    def get_recipes_making_stuff(
        self, stuff: FactorioItem | FactorioFluid
    ) -> set[FactorioRecipe]:
        return self._recipe_per_product[stuff.name]


class JSONFactorioTechnologyRepository(
    factorio_model.FactorioTechnologyRepository,
    JSONFactorioRepository[factorio_model.FactorioTechnology],
):
    def __init__(
        self,
        json_directory: pathlib.Path,
        recipe_repo: factorio_model.FactorioRecipeRepository,
    ):
        super().__init__(filename="technology.json")
        self._recipe_repo = recipe_repo
        self._load_file(json_directory)

    def build_object(self, data) -> factorio_model.FactorioTechnology:
        try:
            recipe_unlocked = tuple(
                self._recipe_repo[effect["recipe"]]
                for effect in data["effects"]
                if effect["type"] == "unlock-recipe"
            )
            return factorio_model.FactorioTechnology(
                name=data["name"], recipe_unlocked=recipe_unlocked
            )
        except KeyError:
            print(data)
            raise
