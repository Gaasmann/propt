"""JSON repos for buildings."""
from __future__ import annotations

import itertools
import pathlib
from typing import Any, Iterable

import more_itertools

from propt.adapters.factorio_repositories.json.base import JSONFactorioRepository
from propt.domain.factorio import repositories as repo_model, prototypes as prototypes


class JSONFactorioAggregateBuildingRepository(repo_model.BuildingRepository):
    """Aggregate Building repository into one."""
    def __init__(self, building_repos: Iterable[repo_model.BuildingRepository]):
        super().__init__(
            itertools.chain.from_iterable(
                tuple(repo.items()) for repo in building_repos
            )
        )


class JSONFactorioAssemblingMachineRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="assembling-machine.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        return prototypes.Building(
            name=data["name"],
            energy_usage=data["energy_usage"],
            speed_coefficient=data["crafting_speed"],
            crafting_categories=tuple(
                key for key, value in data["crafting_categories"].items() if value
            ),
        )


class JSONFactorioBoilerBuildingRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__("boiler.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        return prototypes.Building(
            name=data["name"],
            energy_usage=data["max_energy_usage"],
            speed_coefficient=1.0,
            crafting_categories=("boiling",),
        )


class JSONFactorioFurnaceRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="furnace.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        return prototypes.Building(
            name=data["name"],
            energy_usage=data["energy_usage"],
            speed_coefficient=data["crafting_speed"],
            crafting_categories=tuple(
                key for key, value in data["crafting_categories"].items() if value
            ),
        )


# TODO
class JSONFactorioGeneratorRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="generator.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        return prototypes.Building(
            name=data["name"],
            max_temperature=data["maximum_temperature"],
            effectivity=data["effectivity"],
            fluid_usage_per_tick=data["fluid_usage_per_tick"],
            max_energy_production=data["max_energy_production"],
            energy_source=more_itertools.first(data["energy_source"].keys()),
            energy_properties=tuple(
                more_itertools.first(data["energy_source"].values()).items()
            ),
        )


class JSONFactorioMiningDrillRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="mining-drill.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Building:
        assert len(data["energy_source"]) < 2
        try:
            return prototypes.Building(
                name=data["name"],
                energy_usage=data["energy_usage"],
                speed_coefficient=data["mining_speed"],
                crafting_categories=tuple(
                    key for key, value in data["resource_categories"].items() if value
                ),
            )
        except KeyError:
            print(data)
            raise


# TODO
class JSONFactorioReactorRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[repo_model.BuildingRepository],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="reactor.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Building:
        assert len(data["energy_source"]) < 2
        print(data)
        return prototypes.Building(
            name=data["name"],
            max_energy_usage=data["max_energy_usage"],
            neighbour_bonus=data["neighbour_bonus"],
            energy_source=more_itertools.first(data["energy_source"].keys()),
            energy_effectivity=tuple(
                more_itertools.first(data["energy_source"].values()).items()
            )["effectivity"],
            fuel_category=tuple(
                key
                for key, value in tuple(
                    more_itertools.first(data["energy_source"].values()).items()
                )["fuel_categories"].items()
                if value
            ),
            energy_properties=tuple(
                more_itertools.first(data["energy_source"].values()).items()
            ),
        )


class JSONFactorioRocketSiloRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="rocket-silo.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        return prototypes.Building(
            name=data["name"],
            energy_usage=data["energy_usage"],
            speed_coefficient=data["crafting_speed"],
            crafting_categories=tuple(
                key for key, value in data["crafting_categories"].items() if value
            ),
        )


# TODO
class JSONFactorioSolarPanelRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="solar-panel.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Building:
        return prototypes.Building(
            name=data["name"], max_energy_production=data["max_energy_production"]
        )
