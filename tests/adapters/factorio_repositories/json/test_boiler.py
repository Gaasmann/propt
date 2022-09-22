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
        "name": "boiler",
        "localised_name": ["entity-name.boiler"],
        "max_energy_usage": 1800000,
        "target_temperature": 165,
        "friendly_map_color": {"r": 0, "g": 96, "b": 145, "a": 255},
        "enemy_map_color": {"r": 255, "g": 25, "b": 25, "a": 255},
        "energy_source": {
            "burner": {
                "effectivity": 1,
                "fuel_categories": {"chemical": True},
                "emissions": 2.7777777777778e-07,
            }
        },
        "pollution": 30,
    }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "boiler2"
    with open(tmp_path / "boiler.json", "w") as f:
        json.dump({"boiler": data1, "boiler2": data2}, f)
    return tmp_path


def test_build_object(data_dir, data):
    obj = repos.JSONFactorioBoilerRepository(data_dir).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioBoiler)
    assert obj.name == "boiler"


def test_build_repository(data_dir, data):
    repo = repos.JSONFactorioBoilerRepository(data_dir)
    assert isinstance(repo, repos.JSONFactorioBoilerRepository)
    assert repo
    assert "boiler" in repo
    assert "boiler2" in repo
    assert repo["boiler"].name == data["name"]
