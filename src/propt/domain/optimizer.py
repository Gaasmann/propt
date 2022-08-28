"""Things related to optimization."""
from __future__ import annotations

import abc
from typing import Iterable

import pydantic
import propt.domain.concepts as concepts


class ProductionUnit(pydantic.BaseModel):
    """Represent a unit of production (recipe+building)."""

    recipe: concepts.Recipe
    building: concepts.Building
    quantity: int = 0


class ProductionMap:
    """Represent all the possible ways of doing stuff."""

    @classmethod
    def from_repositories(
        cls, recipe_repository: concepts.ConceptRepository[concepts.Recipe]
    ) -> ProductionMap:
        production_units: list[ProductionUnit] = [
            ProductionUnit(recipe=recipe, building=building)
            for recipe in recipe_repository.list_all()
            for building in recipe.buildings
        ]
        return cls(production_units)

    def __init__(self, production_units: list[ProductionUnit]):
        self.production_units = production_units


class Optimizer(metaclass=abc.ABCMeta):
    """Optimize a Production map."""
    def __init__(self, production_map: ProductionMap, constraints: Iterable[concepts.Quantity]):
        self._production_map = production_map
        self._constraints = list(constraints)

    @abc.abstractmethod
    def optimize(self) -> ProductionMap:
        """Do the optimization and return a new ProductionMap."""