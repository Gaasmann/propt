"""Test for JSON Factorio boiler repository."""
import copy
import json
import pathlib
from typing import Any
import propt.adapters.new_factorio_repositories.json as repos
import propt.domain.factorio as factorio_domain

import pytest


@pytest.fixture
def data() -> dict[str, Any]:
    return {
        "name": "steel-furnace",
        "localised_name": ["entity-name.steel-furnace"],
        "type": "furnace",
        "energy_usage": 90000,
        "ingredient_count": 1,
        "crafting_speed": 2,
        "crafting_categories": {"smelting": True},
        "module_inventory_size": 0,
        "allowed_effects": {
            "consumption": False,
            "speed": False,
            "productivity": False,
            "pollution": False,
        },
        "friendly_map_color": {"r": 0, "g": 96, "b": 145, "a": 255},
        "enemy_map_color": {"r": 255, "g": 25, "b": 25, "a": 255},
        "energy_source": {
            "burner": {
                "effectivity": 1,
                "fuel_categories": {"chemical": True},
                "emissions": 7.4074074074074e-07,
            }
        },
        "pollution": 4,
    }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "steel-furnace2"
    with open(tmp_path / "furnace.json", "w") as f:
        json.dump({"steel-furnace": data1, "steel-furnace2": data2}, f)
    return tmp_path


def test_build_object(data_dir, data):
    obj = repos.JSONFactorioFurnaceRepository(data_dir).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioFurnace)
    assert obj.name == "steel-furnace"


def test_build_repository(data_dir, data):
    repo = repos.JSONFactorioFurnaceRepository(data_dir)
    assert isinstance(repo, repos.JSONFactorioFurnaceRepository)
    assert repo
    assert "steel-furnace" in repo
    assert "steel-furnace2" in repo
    assert repo["steel-furnace"].name == data["name"]
