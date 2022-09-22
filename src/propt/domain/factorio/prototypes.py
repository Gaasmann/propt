"""The prototypes (Item, Fluid, Buildings, ...)."""
from __future__ import annotations

import itertools
from typing import Iterable

import pydantic


class Prototype(pydantic.BaseModel):
    """A something in factorio."""

    name: str

    class Config:
        frozen = True


class Object(Prototype):
    """An object, item or fluid."""

    name: str



class Building(Prototype):
    """A building."""

    energy_usage: int
    speed_coefficient: float
    crafting_categories: tuple[str, ...]


class Item(Object):
    """A solid object."""

    place_result: Building | None = None


ELECTRICITY = Item(name="Electricity")


class Fluid(Object):
    """A fluid."""

    default_temperature: int = 15
    max_temperature: int = 15


# TODO check max_temperature for heat
HEAT = Fluid(name="Heat", max_temperature=900000)


class Ingredient(pydantic.BaseModel):
    """An ingredient in a recipe."""

    obj: Object
    amount: float

    class Config:
        frozen = True


class ItemIngredient(Ingredient):
    """A solid ingredient in a recipe."""

    obj: Item


class FluidIngredient(Ingredient):
    """A fluid ingredient in a recipe."""

    obj: Fluid
    min_temperature: int | None
    max_temperature: int | None


class Product(pydantic.BaseModel):
    """A product in a recipe."""

    obj: Object
    amount: float = 0.0
    """A fixed amount."""
    min_amount: float = 0.0
    """The minimum amount the recipe can produce."""
    max_amount: float = 0.0
    """The maximum amount the recipe can produce."""
    probability: float = 1.0
    """The probability to get that item when the recipe completes."""

    @property
    def avg_amount(self) -> float:
        """Return the avg amount produced."""
        return (self.amount + self.max_amount - self.min_amount) * self.probability

    class Config:
        frozen = True


class ProductItem(Product):
    """A solid product in a recipe."""

    obj: Item


class ProductFluid(Product):
    """A fluid product."""

    obj: Fluid
    temperature: int


class Recipe(Prototype):
    """A recipe."""

    category: str
    available_from_start: bool
    hidden_from_player_crafting: bool
    base_time: float
    """The base time to execute the recipe."""
    ingredients: tuple[Ingredient, ...]
    products: tuple[Product, ...]

    @property
    def handcraftable(self) -> bool:
        """True if the character can make this recipe."""
        return not self.hidden_from_player_crafting and all(
            isinstance(obj.obj, Item)
            for obj in itertools.chain(self.ingredients, self.products)
        )



class Technology(Prototype):
    """A factorio technology."""

    recipe_unlocked: tuple[Recipe, ...]


class TechnologySet(set[Technology]):
    """A set storing technology and providing extra services."""

    def __init__(self, technologies: Iterable[Technology]):
        super().__init__(technologies)
        self.unlocked_recipes: set[Recipe] = {
            recipe for technology in self for recipe in technology.recipe_unlocked
        }
