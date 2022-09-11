"""Test for JSON Factorio resource repository."""
import copy
import json
import pathlib
from typing import Any

import more_itertools

import propt.adapters.factorio_repositories.json as repos
import propt.domain.factorio as factorio_domain
import propt.data.pyanodons as factorio_data

import pytest


@pytest.fixture
def data() -> dict[str, Any]:
    return {
        "name": "uranium-ore",
        "localised_name": ["entity-name.uranium-ore"],
        "resource_category": "basic-solid",
        "mineable_properties": {
            "minable": True,
            "mining_time": 2,
            "mining_particle": "stone-particle",
            "products": [
                {"type": "item", "name": "uranium-ore", "probability": 1, "amount": 1}
            ],
            "fluid_amount": 10,
            "required_fluid": "sulfuric-acid",
        },
        "autoplace_specification": {
            "placement_density": 1,
            "control": "uranium-ore",
            "probability_expression": {"type": "literal-number", "literal_value": 0},
            "richness_expression": {"type": "literal-number", "literal_value": 0},
            "order": "c",
            "default_enabled": True,
            "force": "neutral",
        },
        "energy_source": {},
    }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "uranium-ore2"
    with open(tmp_path / "resource.json", "w") as f:
        json.dump({"uranium-ore": data1, "uranium-ore2": data2}, f)
    return tmp_path


def test_build_object(data_dir, data):
    path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    assmac_repo = repos.JSONFactorioAssemblingMachineRepository(path)
    furnace_repo = repos.JSONFactorioFurnaceRepository(path)
    rocket_silo_repo = repos.JSONFactorioRocketSiloRepository(path)
    mining_drill_repo = repos.JSONFactorioMiningDrillRepository(path)
    item_repo = repos.JSONFactorioItemRepository(
        path, assmac_repo, furnace_repo, rocket_silo_repo, mining_drill_repo
    )
    fluid_repo = repos.JSONFactorioFluidRepository(path)
    obj = repos.JSONFactorioResourceRepository(
        data_dir, item_repo, fluid_repo
    ).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioResource)
    assert obj.name == "uranium-ore"


def test_build_repository(data_dir, data):
    path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    assmac_repo = repos.JSONFactorioAssemblingMachineRepository(path)
    furnace_repo = repos.JSONFactorioFurnaceRepository(path)
    rocket_silo_repo = repos.JSONFactorioRocketSiloRepository(path)
    mining_drill_repo = repos.JSONFactorioMiningDrillRepository(path)

    item_repo = repos.JSONFactorioItemRepository(
        path, assmac_repo, furnace_repo, rocket_silo_repo, mining_drill_repo
    )
    fluid_repo = repos.JSONFactorioFluidRepository(path)
    repo = repos.JSONFactorioResourceRepository(data_dir, item_repo, fluid_repo)
    assert isinstance(repo, repos.JSONFactorioResourceRepository)
    assert repo
    assert "uranium-ore" in repo
    assert "uranium-ore2" in repo
    assert repo["uranium-ore"].name == data["name"]
