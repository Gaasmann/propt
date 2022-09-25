"""JSON repos for buildings."""
from __future__ import annotations

import itertools
import pathlib
from typing import Any, Iterable

import more_itertools

import propt.domain.factorio.energy
import propt.domain.factorio.prototypes
from propt.adapters.factorio_repositories.json.base import JSONFactorioRepository
from propt.domain.factorio import repositories as repo_model


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
    JSONFactorioRepository[propt.domain.factorio.prototypes.Building],
):
    override_speed = {"moss-farm-mk01": 1.075,
                      "ralesia-plantation-mk01": 1.3152,
                      "seaweed-crop-mk01": 1.1,
                      "auog-paddock-mk01": 2.0
                      }
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="assembling-machine.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> propt.domain.factorio.prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        key, energy_data = next(iter(data["energy_source"].items()))
        return propt.domain.factorio.prototypes.Building(
            name=data["name"],
            energy_usage=data["energy_usage"],
            speed_coefficient=self.override_speed.get(data["name"], data["crafting_speed"]),
            crafting_categories=tuple(
                key for key, value in data["crafting_categories"].items() if value
            ),
            energy_info=propt.domain.factorio.energy.Energy.create(key, energy_data)
        )


class JSONFactorioBoilerBuildingRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[propt.domain.factorio.prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__("boiler.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> propt.domain.factorio.prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        key, energy_data = next(iter(data["energy_source"].items()))
        return propt.domain.factorio.prototypes.Building(
            name=data["name"],
            energy_usage=data["max_energy_usage"],
            speed_coefficient=1.0,
            crafting_categories=(f"boiling-{data['name']}",),
            energy_info=propt.domain.factorio.energy.Energy.create(key, energy_data)
        )


class JSONFactorioFurnaceRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[propt.domain.factorio.prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="furnace.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> propt.domain.factorio.prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        key, energy_data = next(iter(data["energy_source"].items()))
        return propt.domain.factorio.prototypes.Building(
            name=data["name"],
            energy_usage=data["energy_usage"],
            speed_coefficient=data["crafting_speed"],
            crafting_categories=tuple(
                key for key, value in data["crafting_categories"].items() if value
            ),
            energy_info=propt.domain.factorio.energy.Energy.create(key, energy_data)
        )


class JSONFactorioGeneratorRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[propt.domain.factorio.prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="generator.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> propt.domain.factorio.prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        return propt.domain.factorio.prototypes.Building(
            name=data["name"],
            energy_usage=0,
            speed_coefficient=1.0,
            crafting_categories=(data["name"],),
            energy_info=propt.domain.factorio.energy.Void(),
        )


class JSONFactorioMiningDrillRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[propt.domain.factorio.prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="mining-drill.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> propt.domain.factorio.prototypes.Building:
        assert len(data["energy_source"]) < 2
        key, energy_data = next(iter(data["energy_source"].items()))
        try:
            return propt.domain.factorio.prototypes.Building(
                name=data["name"],
                energy_usage=data["energy_usage"],
                speed_coefficient=data["mining_speed"],
                crafting_categories=tuple(
                    key for key, value in data["resource_categories"].items() if value
                ),
                energy_info=propt.domain.factorio.energy.Energy.create(key, energy_data)
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

    def build_object(self, data: dict[str, Any]) -> propt.domain.factorio.prototypes.Building:
        assert len(data["energy_source"]) < 2
        print(data)
        return propt.domain.factorio.prototypes.Building(
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
    JSONFactorioRepository[propt.domain.factorio.prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="rocket-silo.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> propt.domain.factorio.prototypes.Building:
        assert len(data["energy_source"].keys()) < 2
        key, energy_data = next(iter(data["energy_source"].items()))
        return propt.domain.factorio.prototypes.Building(
            name=data["name"],
            energy_usage=data["energy_usage"],
            speed_coefficient=data["crafting_speed"],
            crafting_categories=tuple(
                key for key, value in data["crafting_categories"].items() if value
            ),
            energy_info=propt.domain.factorio.energy.Energy.create(key, energy_data)
        )


# TODO
class JSONFactorioSolarPanelRepository(
    repo_model.BuildingRepository,
    JSONFactorioRepository[propt.domain.factorio.prototypes.Building],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__(filename="solar-panel.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> propt.domain.factorio.prototypes.Building:
        return propt.domain.factorio.prototypes.Building(
            name=data["name"], max_energy_production=data["max_energy_production"]
        )
