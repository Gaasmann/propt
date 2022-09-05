"""Game concept."""
from __future__ import annotations

import itertools
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Iterator, NewType, TypeVar, Generic, Iterable, Optional
import pydantic

Code = NewType("Code", str)
"""A code identifying a game object (recipe, building, ...)."""


# @dataclass(frozen=True)
class GameConcept(pydantic.BaseModel, metaclass=ABCMeta):
    """Game concept."""

    code: Code
    name: str

    class Config:
        frozen = True


T = TypeVar("T", bound=GameConcept)


class ConceptRepository(Generic[T], metaclass=ABCMeta):
    """A repository of Items."""

    @abstractmethod
    def list_all(self) -> list[T]:
        """List the whole collection."""

    @abstractmethod
    def by_code(self, code: Code) -> T:
        """Get one Object by code"""


# @dataclass(frozen=True)
class Building(GameConcept):
    """A building in the game."""

    crafting_categories: tuple[str, ...]
    speed_coef: float


class Item(GameConcept):
    """An item in the game."""
    place_result: Optional[Building]


# @dataclass(frozen=True)
class ItemRepository(ConceptRepository[Item], metaclass=ABCMeta):
    def by_building(self, building: Building) -> Item:
        """Return the item matching the given building."""
        try:
            return next(item for item in self.list_all() if building == item.place_result)
        except StopIteration as e:
            raise ObjectNotFound(building) from e


class BuildingRepository(ConceptRepository[Building], metaclass=ABCMeta):
    @abstractmethod
    def by_crafting_category(self, crafting_category: str) -> Iterator[Building]:
        """Return the building matching a crafting category."""


class Quantity(pydantic.BaseModel):
    """A quantity of stuff."""

    item: Item
    qty: float

    class Config:
        frozen = True


class Recipe(GameConcept):
    """A recipe in the game."""

    base_time: float
    available_from_start: bool
    ingredients: tuple[Quantity, ...]
    products: tuple[Quantity, ...]
    buildings: tuple[Building, ...]

    def get_net_quantity_per_unit_of_time(self, item: Item):
        needed = sum(qty.qty for qty in self.ingredients if qty.item == item)
        produced = sum(qty.qty for qty in self.products if qty.item == item)
        return (produced - needed) / self.base_time

    @property
    def ingredient_items(self) -> set[Item]:
        return {quantity.item for quantity in self.ingredients}

    @property
    def product_items(self) -> set[Item]:
        return {quantity.item for quantity in self.products}

    @property
    def items(self) -> set[Item]:
        return self.ingredient_items.union(self.product_items)

    def available(self, available_technologies: Iterable[Technology]) -> bool:
        """Return True if the recipe is available from the start or given the given tech set."""
        if self.available_from_start:
            return True
        return any(self in tech.recipes_unlocked for tech in available_technologies)


class RecipeRepository(ConceptRepository[Recipe], metaclass=ABCMeta):
    def by_product(self, item: Item) -> Iterator[Recipe]:
        """Return the building matching a crafting category."""
        yield from (
            recipe for recipe in self.list_all() if item in recipe.product_items
        )


class Technology(GameConcept):
    """A technology in the game."""

    recipes_unlocked: tuple[Recipe, ...]

    class Config:
        frozen = True


class ObjectNotFound(Exception):
    """The object is not found."""
