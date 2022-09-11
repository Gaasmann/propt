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
    "name" : "steam-engine",
    "localised_name" : [
      "entity-name.steam-engine"
    ],
    "maximum_temperature" : 500,
    "effectivity" : 1,
    "fluid_usage_per_tick" : 0.5,
    "max_energy_production" : 2910000,
    "friendly_map_color" : {
      "r" : 0,
      "g" : 127,
      "b" : 160,
      "a" : 255
    },
    "enemy_map_color" : {
      "r" : 255,
      "g" : 25,
      "b" : 25,
      "a" : 255
    },
    "energy_source" : {
      "electric" : {
        "drain" : 0,
        "emissions" : 0
      }
    },
    "pollution" : 0
  }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "steam-engine2"
    with open(tmp_path / "generator.json", "w") as f:
        json.dump(
            {"steam-engine": data1, "steam-engine2": data2}, f
        )
    return tmp_path


def test_build_object(data_dir, data):
    obj = repos.JSONFactorioGeneratorRepository(data_dir).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioGenerator)
    assert obj.name == "steam-engine"


def test_build_repository(data_dir, data):
    repo = repos.JSONFactorioGeneratorRepository(data_dir)
    assert isinstance(repo, repos.JSONFactorioGeneratorRepository)
    assert repo
    assert "steam-engine" in repo
    assert "steam-engine2" in repo
    assert repo["steam-engine"].name == data["name"]
