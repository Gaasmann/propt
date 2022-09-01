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

    @property
    def name(self) -> str:
        return f"{self.recipe.name}\n{self.building.name}"

    @property
    def items(self) -> set[concepts.Item]:
        return self.recipe.items

    def get_item_net_quantity_by_unit_of_time(self, item: concepts.Item) -> float:
        """Return the amount of item required/produced by unit of time."""
        return (
            self.recipe.get_net_quantity_per_unit_of_time(item)
            * self.building.speed_coef
        )

    class Config:
        frozen = True


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

    @property
    def items(self) -> set[concepts.Item]:
        return {item for prod_unit in self.production_units for item in prod_unit.items}


class SolutionNotFound(Exception):
    """Raised when the optimizer can't find a solution."""


class Optimizer(metaclass=abc.ABCMeta):
    """Optimize a Production map."""

    def __init__(
        self, production_map: ProductionMap, constraints: Iterable[concepts.Quantity]
    ):
        self._production_map = production_map
        self._constraints = list(constraints)

    @abc.abstractmethod
    def optimize(self) -> ProductionMap:
        """Do the optimization and return a new ProductionMap."""
