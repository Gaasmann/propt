"""JSON repos for technologies."""
from __future__ import annotations

import pathlib

import propt.domain.new_factorio.repositories as repo_models
import propt.domain.new_factorio.prototypes as prototypes
import propt.adapters.new_factorio_repositories.json.base as json_base


class JSONFactorioTechnologyRepository(
    repo_models.TechnologyRepository,
    json_base.JSONFactorioRepository[prototypes.Technology],
):
    def __init__(
        self,
        json_directory: pathlib.Path,
        recipe_repo: repo_models.RecipeRepository,
    ):
        super().__init__(filename="technology.json")
        self._recipe_repo = recipe_repo
        self._load_file(json_directory)

    def build_object(self, data) -> prototypes.Technology:
        try:
            recipe_unlocked = tuple(
                self._recipe_repo[effect["recipe"]]
                for effect in data["effects"]
                if effect["type"] == "unlock-recipe"
            )
            return prototypes.Technology(
                name=data["name"], recipe_unlocked=recipe_unlocked
            )
        except KeyError:
            print(data)
            raise
