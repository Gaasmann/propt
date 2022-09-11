"""Test for JSON Factorio technology repository."""
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
    "name" : "aluminium-mk04",
    "localised_name" : [
      "technology-name.aluminium-mk04"
    ],
    "effects" : [
      {
        "type" : "unlock-recipe",
        "recipe" : "sinter-aluminium-2"
      },
      {
        "type" : "unlock-recipe",
        "recipe" : "molten-aluminium-05"
      }
    ],
    "research_unit_ingredients" : [
      {
        "type" : "item",
        "name" : "py-science-pack",
        "amount" : 1
      },
      {
        "type" : "item",
        "name" : "automation-science-pack",
        "amount" : 1
      },
      {
        "type" : "item",
        "name" : "logistic-science-pack",
        "amount" : 1
      },
      {
        "type" : "item",
        "name" : "chemical-science-pack",
        "amount" : 1
      },
      {
        "type" : "item",
        "name" : "utility-science-pack",
        "amount" : 1
      }
    ],
    "research_unit_count" : 100,
    "research_unit_energy" : 3600,
    "max_level" : 1,
    "prerequisites" : [
      "machines-mk04",
      "aluminium-mk03"
    ]
  }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "aluminium-mk042"
    with open(tmp_path / "technology.json", "w") as f:
        json.dump(
            {"aluminium-mk04": data1, "aluminium-mk042": data2}, f
        )
    return tmp_path

def test_build_object(data_dir, data):
    path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    item_repo = repos.JSONFactorioItemRepository(path)
    fluid_repo = repos.JSONFactorioFluidRepository(path)
    recipe_repo = repos.JSONFactorioRecipeRepository(path, item_repo, fluid_repo)
    obj = repos.JSONFactorioTechnologyRepository(data_dir, recipe_repo).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioTechnology)
    assert obj.name == "aluminium-mk04"

def test_build_repository(data_dir, data):
    path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    item_repo = repos.JSONFactorioItemRepository(path)
    fluid_repo = repos.JSONFactorioFluidRepository(path)
    recipe_repo = repos.JSONFactorioRecipeRepository(path, item_repo, fluid_repo)
    repo = repos.JSONFactorioTechnologyRepository(data_dir, recipe_repo)
    assert isinstance(repo, repos.JSONFactorioTechnologyRepository)
    assert repo
    assert "aluminium-mk04" in repo
    assert "aluminium-mk042" in repo
    assert repo["aluminium-mk04"].name == data["name"]
