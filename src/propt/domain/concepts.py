"""Game concept."""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Iterator, NewType, TypeVar, Generic, Iterable, Optional, Literal

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

    item_type: Literal[
        "item", "fluid", "rail-planner", "item-with-entity-data", "spidertron-remote", "capsule",
        "selection-tool", "mining-tool", "repair-tool", "blueprint", "deconstruction-item", "upgrade-item",
        "blueprint-book", "gun", "ammo", "copy-paste-tool", "module", "tool", "armor", "item-with-inventory",
        "item-with-label", "item-with-tags"
    ]
    place_result: Optional[Building]


# @dataclass(frozen=True)
class ItemRepository(ConceptRepository[Item], metaclass=ABCMeta):
    @abstractmethod
    def by_building(self, building: Building) -> Item:
        """Return the item matching the given building."""


class BuildingRepository(ConceptRepository[Building], metaclass=ABCMeta):
    @abstractmethod
    def by_crafting_category(self, crafting_category: str) -> tuple[Building, ...]:
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
    hidden_from_player_crafting: bool
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

    def available(self, available_technologies: TechnologySet) -> bool:
        """Return True if the recipe is available from the start or given the given tech set."""
        if self.available_from_start:
            return True
        return self in available_technologies.unlocked_recipes

    @property
    def handcraftable(self) -> bool:
        return not self.hidden_from_player_crafting and not any(
            item.item_type == "fluid" for item in self.items
        )


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


class TechnologySet(set[Technology]):
    """A set storing technology and providing extra services."""

    def __init__(self, technologies: Iterable[Technology]):
        super().__init__(technologies)
        self.unlocked_recipes: set[Recipe] = {
            recipe for technology in self for recipe in technology.recipes_unlocked
        }


class ObjectNotFound(Exception):
    """The object is not found."""
