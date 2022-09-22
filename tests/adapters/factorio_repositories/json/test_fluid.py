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
        "name": "diesel",
        "localised_name": ["fluid-name.diesel"],
        "order": "z-[diesel]",
        "default_temperature": 10,
        "max_temperature": 100,
        "fuel_value": 1500000,
        "emissions_multiplier": 1,
    }


@pytest.fixture
def data_dir(data, tmp_path) -> pathlib.Path:
    data1 = data
    data2 = copy.deepcopy(data)
    data2["name"] = "diesel2"
    with open(tmp_path / "fluid.json", "w") as f:
        json.dump({"diesel": data1, "diesel2": data2}, f)
    return tmp_path


def test_build_object(data_dir, data):
    obj = repos.JSONFactorioFluidRepository(data_dir).build_object(data)
    assert isinstance(obj, factorio_domain.FactorioFluid)
    assert obj.name == "diesel"


def test_build_repository(data_dir, data):
    repo = repos.JSONFactorioFluidRepository(data_dir)
    assert isinstance(repo, repos.JSONFactorioFluidRepository)
    assert repo
    assert "diesel" in repo
    assert "diesel2" in repo
    assert repo["diesel"].name == data["name"]
