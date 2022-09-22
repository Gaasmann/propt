"""Test for JSON Factorio boiler repository."""
import copy
import json
import pathlib
from typing import Any

import more_itertools

import propt.adapters.new_factorio_repositories.json as repos
import propt.domain.factorio as factorio_domain
import propt.data.pyanodons as factorio_data

import pytest


@pytest.fixture
def data() -> dict[str, Any]:
    return {
        "name": "raw-coal",
        "localised_name": ["item-name.raw-coal"],
        "type": "item",
        "order": "aaa",
        "fuel_value": 3000000,
        "stack_size": 500,
        "fuel_category": "chemical",
        "fuel_acceleration_multiplier": 1,
        "fuel_top_speed_multiplier": 1,
    }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "raw-coal2"
    with open(tmp_path / "item.json", "w") as f:
        json.dump({"raw-coal": data1, "raw-coal2": data2}, f)
    return tmp_path


def test_build_object(data_dir, data):
    path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    assmac_repo = repos.JSONFactorioAssemblingMachineRepository(path)
    furnace_repo = repos.JSONFactorioFurnaceRepository(path)
    rocket_silo_repo = repos.JSONFactorioRocketSiloRepository(path)
    mining_drill_repo = repos.JSONFactorioMiningDrillRepository(path)
    obj = repos.JSONFactorioItemRepository(
        data_dir, assmac_repo, furnace_repo, rocket_silo_repo, mining_drill_repo
    ).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioItem)
    assert obj.name == "raw-coal"


def test_build_repository(data_dir, data):
    path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    assmac_repo = repos.JSONFactorioAssemblingMachineRepository(path)
    furnace_repo = repos.JSONFactorioFurnaceRepository(path)
    rocket_silo_repo = repos.JSONFactorioRocketSiloRepository(path)
    mining_drill_repo = repos.JSONFactorioMiningDrillRepository(path)

    repo = repos.JSONFactorioItemRepository(
        data_dir, assmac_repo, furnace_repo, rocket_silo_repo, mining_drill_repo
    )
    assert isinstance(repo, repos.JSONFactorioItemRepository)
    assert repo
    assert "raw-coal" in repo
    assert "raw-coal2" in repo
    assert repo["raw-coal"].name == data["name"]
