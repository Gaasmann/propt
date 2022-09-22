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
        "name": "salt-mine",
        "localised_name": ["entity-name.salt-mine"],
        "energy_usage": 800000,
        "mining_speed": 10,
        "resource_categories": {"salt-rock": True},
        "allowed_effects": {
            "consumption": True,
            "speed": True,
            "productivity": False,
            "pollution": True,
        },
        "friendly_map_color": {"r": 0, "g": 96, "b": 145, "a": 255},
        "enemy_map_color": {"r": 255, "g": 25, "b": 25, "a": 255},
        "energy_source": {
            "burner": {
                "effectivity": 0.4,
                "fuel_categories": {"chemical": True},
                "emissions": 1.25e-09,
            }
        },
        "pollution": 0.06,
    }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "salt-mine2"
    with open(tmp_path / "mining-drill.json", "w") as f:
        json.dump({"salt-mine": data1, "salt-mine2": data2}, f)
    return tmp_path


def test_build_object(data_dir, data):
    obj = repos.JSONFactorioMiningDrillRepository(data_dir).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioMiningDrill)
    assert obj.name == "salt-mine"


def test_build_repository(data_dir, data):
    repo = repos.JSONFactorioMiningDrillRepository(data_dir)
    assert isinstance(repo, repos.JSONFactorioMiningDrillRepository)
    assert repo
    assert "salt-mine" in repo
    assert "salt-mine2" in repo
    assert repo["salt-mine"].name == data["name"]
