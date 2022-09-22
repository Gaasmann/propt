"""JSON repos for objects (item and fluids)."""
from __future__ import annotations

import pathlib
from typing import Any

import propt.domain.factorio.prototypes as prototypes
import propt.domain.factorio.repositories as repo_models
import propt.adapters.factorio_repositories.json.base as json_base


class JSONFactorioFluidRepository(
    repo_models.FluidRepository,
    json_base.JSONFactorioRepository[prototypes.Fluid],
):
    def __init__(self, json_directory: pathlib.Path):
        super().__init__("fluid.json")
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Fluid:
        return prototypes.Fluid(
            name=data["name"],
            default_temperature=data["default_temperature"],
            max_temperature=data["max_temperature"],
        )


class JSONFactorioItemRepository(
    repo_models.ItemRepository,
    json_base.JSONFactorioRepository[prototypes.Item],
):
    def __init__(
        self,
        json_directory: pathlib.Path,
        building_repo: repo_models.BuildingRepository,
    ):
        super().__init__(filename="item.json")
        self._building_repo = building_repo
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Item:
        pl = data.get("place_result")
        place_result = self._building_repo.get(pl) if pl else None
        return prototypes.Item(
            name=data["name"],
            place_result=place_result,
        )
