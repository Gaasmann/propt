"""Test for JSON Factorio rocket silo repository."""
import copy
import json
import pathlib
from typing import Any
import propt.adapters.factorio_repositories.json as repos
import propt.domain.factorio as factorio_domain

import pytest


@pytest.fixture
def data() -> dict[str, Any]:
    return {
        "name": "mega-farm",
        "localised_name": ["entity-name.mega-farm"],
        "type": "rocket-silo",
        "energy_usage": 650000,
        "ingredient_count": 255,
        "crafting_speed": 1,
        "crafting_categories": {
            "ralesia-farm": True,
            "rennea-farm": True,
            "tuuphra-farm": True,
            "grod-farm": True,
            "yotoi-farm": True,
            "kicalk-farm": True,
            "arum-farm": True,
            "bioreserve-farm": True,
        },
        "module_inventory_size": 4,
        "allowed_effects": {
            "consumption": True,
            "speed": True,
            "productivity": False,
            "pollution": False,
        },
        "friendly_map_color": {"r": 0, "g": 96, "b": 145, "a": 255},
        "enemy_map_color": {"r": 255, "g": 25, "b": 25, "a": 255},
        "energy_source": {"electric": {"drain": 21666.666666667, "emissions": 0}},
        "pollution": 0,
        "rocket_parts_required": 1,
    }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "mega-farm2"
    with open(tmp_path / "rocket-silo.json", "w") as f:
        json.dump({"mega-farm": data1, "mega-farm2": data2}, f)
    return tmp_path


def test_build_object(data, data_dir):
    obj = repos.JSONFactorioRocketSiloRepository(data_dir).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioRocketSilo)
    assert obj.name == "mega-farm"


def test_build_repository(data_dir, data):
    repo = repos.JSONFactorioRocketSiloRepository(data_dir)
    assert isinstance(repo, repos.JSONFactorioRocketSiloRepository)
    assert repo
    assert "mega-farm" in repo
    assert "mega-farm2" in repo
    assert repo["mega-farm"].name == data["name"]
