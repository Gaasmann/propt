"""Test for JSON Factorio solar panel repository."""
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
    "name" : "solar-panel",
    "localised_name" : [
      "entity-name.solar-panel"
    ],
    "max_energy_production" : 60000,
    "friendly_map_color" : {
      "r" : 30,
      "g" : 33,
      "b" : 35,
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
    data2["name"] = "solar-panel2"
    with open(tmp_path / "solar-panel.json", "w") as f:
        json.dump(
            {"solar-panel": data1, "solar-panel2": data2}, f
        )
    return tmp_path


def test_build_object(data_dir, data):
    obj = repos.JSONFactorioSolarPanelRepository(data_dir).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioSolarPanel)
    assert obj.name == "solar-panel"


def test_build_repository(data_dir, data):
    repo = repos.JSONFactorioSolarPanelRepository(data_dir)
    assert isinstance(repo, repos.JSONFactorioSolarPanelRepository)
    assert repo
    assert "solar-panel" in repo
    assert "solar-panel2" in repo
    assert repo["solar-panel"].name == data["name"]
