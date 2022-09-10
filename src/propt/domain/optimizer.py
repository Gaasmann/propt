"""Things related to optimization."""
from __future__ import annotations

import abc
import traceback
from typing import Iterable

import pydantic
import propt.domain.concepts as concepts


class ProductionUnit(pydantic.BaseModel):
    """Represent a unit of production (recipe+building)."""

    recipe: concepts.Recipe
    building: concepts.Building
    quantity: float = 0

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
        cls,
        recipe_repository: concepts.RecipeRepository,
        item_repository: concepts.ItemRepository,
        technology_set: concepts.TechnologySet,
    ) -> ProductionMap:
        production_units: list[ProductionUnit] = []
        for recipe in recipe_repository.list_all():
            building_added = False
            if recipe.code == "logistic-science-pack":
                print("wait for it")
                print(technology_set)
            if not recipe.available(technology_set):
                if recipe.code == "logistic-science-pack":
                    print("NEIN")
                continue
            for building in recipe.buildings:
                try:
                    if any(
                        building_recipe.available(technology_set)
                        for building_recipe in recipe_repository.by_product(
                            item_repository.by_building(building)
                        )
                    ):
                        production_units.append(
                            ProductionUnit(recipe=recipe, building=building)
                        )
                        building_added = True
                except concepts.ObjectNotFound:
                    traceback.print_exc()
            if not building_added and recipe.handcraftable:
                production_units.append(
                    ProductionUnit(
                        recipe=recipe,
                        building=concepts.Building(
                            code=concepts.Code("character"),
                            name="character",
                            speed_coef=0.001,
                            crafting_categories=tuple(),
                        ),
                    )
                )

        return cls(production_units)

    def __init__(self, production_units: list[ProductionUnit]):
        self.production_units = production_units

    def add_magic_unit(self) -> None:
        """Add some magic prod units for items on the map that has no way of being produced.

        This is mainly to debug situation when the solver can't find a solution.
        """
        produced_items = {
            quantity.item
            for prod_unit in self.production_units
            for quantity in prod_unit.recipe.products
        }
        missing_items = self.items.difference(produced_items)
        for item in missing_items:
            print(f"MISSING ITEM: {item}")
            building = concepts.Building(
                code=concepts.Code("magic-building"),
                name="magic-building",
                speed_coef=1.0,
                crafting_categories=tuple(),
            )
            self.production_units.append(
                ProductionUnit(
                    recipe=concepts.Recipe(
                        code=concepts.Code(f"magic-{item.name}"),
                        name=f"magic-{item.name}",
                        hidden_from_player_crafting=True,
                        ingredients=tuple(),
                        base_time=1.0,
                        available_from_start=True,
                        products=(concepts.Quantity(item=item, qty=1),),
                        buildings=(building,),
                    ),
                    building=building,
                )
            )

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
