"""Test for JSON Factorio recipe repository."""
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
    "name" : "refsyngas-combustion",
    "localised_name" : [
      "recipe-name.refsyngas-combustion"
    ],
    "category" : "combustion",
    "order" : "f",
    "group" : {
      "name" : "coal-processing",
      "type" : "item-group"
    },
    "subgroup" : {
      "name" : "py-combustion",
      "type" : "item-subgroup"
    },
    "enabled" : False,
    "hidden" : False,
    "hidden_from_player_crafting" : False,
    "emissions_multiplier" : 1,
    "energy" : 3,
    "ingredients" : [
      {
        "type" : "item",
        "name" : "coke",
        "amount" : 3
      },
      {
        "type" : "fluid",
        "name" : "refsyngas",
        "amount" : 100
      },
      {
        "type" : "fluid",
        "name" : "water",
        "amount" : 500
      }
    ],
    "products" : [
      {
        "type" : "fluid",
        "name" : "combustion-mixture1",
        "probability" : 1,
        "amount" : 150,
        "temperature" : 700
      },
      {
        "type" : "fluid",
        "name" : "steam",
        "probability" : 1,
        "amount" : 500,
        "temperature" : 60
      }
    ]
  }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "refsyngas-combustion2"
    with open(tmp_path / "recipe.json", "w") as f:
        json.dump(
            {"refsyngas-combustion": data1, "refsyngas-combustion2": data2}, f
        )
    return tmp_path


def test_build_object(data_dir, data):
    path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    item_repo = repos.JSONFactorioItemRepository(path)
    fluid_repo = repos.JSONFactorioFluidRepository(path)
    obj = repos.JSONFactorioRecipeRepository(data_dir, item_repo, fluid_repo).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioRecipe)
    assert obj.name == "refsyngas-combustion"


def test_build_repository(data_dir, data):
    path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    item_repo = repos.JSONFactorioItemRepository(path)
    fluid_repo = repos.JSONFactorioFluidRepository(path)
    repo = repos.JSONFactorioRecipeRepository(data_dir, item_repo, fluid_repo)
    assert isinstance(repo, repos.JSONFactorioRecipeRepository)
    assert repo
    assert "refsyngas-combustion" in repo
    assert "refsyngas-combustion2" in repo
    assert repo["refsyngas-combustion"].name == data["name"]
