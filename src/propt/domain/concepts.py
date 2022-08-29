"""Game concept."""
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Iterator, NewType, TypeVar, Generic
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
    def list_all(self) -> Iterator[T]:
        """List the whole collection."""

    @abstractmethod
    def by_code(self, code: Code) -> T:
        """Get one Object by code"""


# @dataclass(frozen=True)
class Item(GameConcept):
    """An item in the game."""


# @dataclass(frozen=True)
class Building(GameConcept):
    """A building in the game."""

    speed_coef: float


class Quantity(pydantic.BaseModel):
    """A quantity of stuff."""

    item: Item
    qty: float

    class Config:
        frozen = True


class Recipe(GameConcept):
    """A recipe in the game."""

    base_time: float
    ingredients: tuple[Quantity, ...]
    products: tuple[Quantity, ...]
    buildings: tuple[Building, ...]

    def get_net_quantity_per_unit_of_time(self, item: Item):
        needed = sum(qty.qty for qty in self.ingredients if qty.item == item)
        produced = sum(qty.qty for qty in self.products if qty.item == item)
        if needed or produced:
            return (produced - needed) / self.base_time
        else:
            raise ObjectNotFound(item)


class ObjectNotFound(Exception):
    """The object is not found."""
