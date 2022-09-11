"""Test for JSON Factorio boiler repository."""
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
        "name": "nuclear-reactor",
        "localised_name": ["entity-name.nuclear-reactor"],
        "max_energy_usage": 40000000,
        "neighbour_bonus": 1,
        "friendly_map_color": {"r": 0, "g": 96, "b": 145, "a": 255},
        "enemy_map_color": {"r": 255, "g": 25, "b": 25, "a": 255},
        "energy_source": {
            "burner": {
                "effectivity": 1,
                "fuel_categories": {"nuclear": True},
                "emissions": 0,
            }
        },
        "pollution": 0,
    }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "nuclear-reactor2"
    with open(tmp_path / "reactor.json", "w") as f:
        json.dump({"nuclear-reactor": data1, "nuclear-reactor2": data2}, f)
    return tmp_path


def test_build_object(data_dir, data):
    obj = repos.JSONFactorioReactorRepository(data_dir).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioReactor)
    assert obj.name == "nuclear-reactor"


def test_build_repository(data_dir, data):
    repo = repos.JSONFactorioReactorRepository(data_dir)
    assert isinstance(repo, repos.JSONFactorioReactorRepository)
    assert repo
    assert "nuclear-reactor" in repo
    assert "nuclear-reactor2" in repo
    assert repo["nuclear-reactor"].name == data["name"]
