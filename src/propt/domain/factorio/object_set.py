from __future__ import annotations

import functools
from collections import defaultdict

from typing import Iterable, TYPE_CHECKING

from propt.domain.factorio.prototypes import Technology, Recipe, Fluid, ProductFluid
if TYPE_CHECKING:
    from propt.domain.factorio import repositories as repo_models


class TechnologySet(set[Technology]):
    """A set storing technology and providing extra services."""

    def __init__(self, technologies: Iterable[Technology]):
        super().__init__(technologies)
        self.unlocked_recipes: set[Recipe] = {
            recipe for technology in self for recipe in technology.recipe_unlocked
        }


class RecipeSet(set[Recipe]):
    @classmethod
    def from_factorio_repositories(
        cls,
        recipe_repo: repo_models.RecipeRepository,
        available_tech: TechnologySet,
    ):
        def recipe_to_include(recipe: Recipe) -> bool:
            return not recipe.category.startswith("recycle-")

        available_factorio_recipes: set[Recipe] = {
            recipe for recipe in recipe_repo.values() if recipe.available_from_start
        }.union(available_tech.unlocked_recipes)
        available_recipes = set(filter(recipe_to_include, available_factorio_recipes))
        return cls(available_recipes)

    @functools.cached_property
    def product_temperatures(self) -> dict[Fluid, set[int]]:
        temperatures: dict[Fluid, set[int]] = defaultdict(set)
        for recipe in self:
            for product in recipe.products:
                if isinstance(product, ProductFluid):
                    temperatures[product.obj].add(product.temperature)
        return temperatures
