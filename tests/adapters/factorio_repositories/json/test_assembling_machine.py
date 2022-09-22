"""Test for JSON Factorio assembling machine repository."""
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
        "name": "kicalk-plantation-mk01",
        "localised_name": ["entity-name.kicalk-plantation-mk01"],
        "type": "assembling-machine",
        "energy_usage": 900000,
        "ingredient_count": 255,
        "crafting_speed": 0.08,
        "crafting_categories": {"kicalk": True},
        "module_inventory_size": 25,
        "allowed_effects": {
            "consumption": True,
            "speed": True,
            "productivity": True,
            "pollution": True,
        },
        "friendly_map_color": {"r": 0, "g": 96, "b": 145, "a": 255},
        "enemy_map_color": {"r": 255, "g": 25, "b": 25, "a": 255},
        "energy_source": {
            "electric": {"drain": 30000, "emissions": -6.4814814814815e-07}
        },
        "pollution": -35,
    }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "kicalk-plantation-mk01copy"
    with open(tmp_path / "assembling-machine.json", "w") as f:
        json.dump(
            {"kicalk-plantation-mk01": data1, "kicalk-plantation-mk01copy": data2}, f
        )
    return tmp_path


def test_build_object(data_dir, data):
    obj = repos.JSONFactorioAssemblingMachineRepository(data_dir).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioAssemblingMachine)
    assert obj.name == "kicalk-plantation-mk01"


def test_build_repository(data_dir, data):
    repo = repos.JSONFactorioAssemblingMachineRepository(data_dir)
    assert isinstance(repo, repos.JSONFactorioAssemblingMachineRepository)
    assert repo
    assert "kicalk-plantation-mk01" in repo
    assert "kicalk-plantation-mk01copy" in repo
    assert repo["kicalk-plantation-mk01"].name == data["name"]
