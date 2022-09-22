"""Factorio model.

This is a conformist layer that would be further converted to the simpler model.
"""
from __future__ import annotations

import abc
from typing import TypeVar, Optional, Union, Literal, Iterable, Any

import pydantic


class FactorioObject(pydantic.BaseModel):
    """A Factorio object."""

    name: str

    class Config:
        frozen = True


T = TypeVar("T", bound=FactorioObject)


class FactorioRepository(dict[str, T]):
    """An abstract Factorio repository."""


# Assembly machines
class FactorioAssemblingMachine(FactorioObject):
    """A factorio assembling machine."""

    energy_usage: int
    crafting_speed: float
    crafting_categories: tuple[str, ...]
    module_inventory_size: int
    allowed_effects: tuple[str, ...]
    energy_source: str
    energy_properties: tuple[tuple[str, Any], ...]


class FactorioAssemblingMachineRepository(
    FactorioRepository[FactorioAssemblingMachine]
):
    """A repository for factorio assembly machines."""


# RocketSilo
class FactorioRocketSilo(FactorioObject):
    """A factorio rocket silo."""

    energy_usage: int
    crafting_speed: float
    crafting_categories: tuple[str, ...]
    module_inventory_size: int
    allowed_effects: tuple[str, ...]
    energy_source: str
    energy_properties: tuple[tuple[str, Any], ...]


class FactorioRocketSiloRepository(FactorioRepository[FactorioRocketSilo]):
    """A repository for factorio rocket silo."""


# SolarPanel
class FactorioSolarPanel(FactorioObject):
    """A factorio solar panel."""

    max_energy_production: int


# Boilers
class FactorioBoiler(FactorioObject):
    """A factorio boiler."""

    max_energy_usage: int
    target_temperature: int
    energy_source: str
    energy_properties: tuple[tuple[str, Any], ...]


class FactorioBoilerRepository(FactorioRepository[FactorioBoiler]):
    """A repository for factorio boilers."""


# Fluids
class FactorioFluid(FactorioObject):
    """A factorio fluid."""

    default_temperature: int
    max_temperature: int
    fuel_value: int


class FactorioFluidRepository(FactorioRepository[FactorioFluid]):
    """A repository for factorio fluids."""


# Furnaces
class FactorioFurnace(FactorioObject):
    """A factorio furnace."""

    energy_usage: int
    crafting_speed: float
    crafting_categories: tuple[str, ...]
    module_inventory_size: int
    allowed_effects: tuple[str, ...]
    energy_source: str
    energy_properties: tuple[tuple[str, Any], ...]


class FactorioFurnaceRepository(FactorioRepository[FactorioFurnace]):
    """A repository for factorio furnaces."""


# Generator
class FactorioGenerator(FactorioObject):
    """A factorio generator."""

    max_temperature: int
    effectivity: float
    fluid_usage_per_tick: float
    max_energy_production: int
    energy_source: str
    energy_properties: tuple[tuple[str, Any], ...]


class FactorioGeneratorRepository(FactorioRepository[FactorioGenerator]):
    """A repository for factorio generators."""


# Mining drills
class FactorioMiningDrill(FactorioObject):
    """A factorio mining drill."""

    energy_usage: int
    mining_speed: float
    resource_categories: tuple[str, ...]
    allowed_effects: tuple[str, ...]
    energy_source: str
    energy_effectivity: float
    energy_properties: tuple[tuple[str, Any], ...]
    fuel_category: tuple[str, ...]


class FactorioMiningDrillRepository(FactorioRepository[FactorioMiningDrill]):
    """A repository for factorio mining drills."""


# Item
class FactorioItem(FactorioObject):
    """A factorio item."""

    fuel_value: int
    fuel_category: str
    place_result: Optional[
        FactorioAssemblingMachine
        | FactorioMiningDrill
        | FactorioRocketSilo
        | FactorioFurnace
    ]


class FactorioItemRepository(FactorioRepository[FactorioItem]):
    """A repository for factorio items."""


class Quantity(pydantic.BaseModel):
    """A quantity."""

    qty: float
    item: Union[FactorioItem, FactorioFluid]

    class Config:
        frozen = True


# Reactor
class FactorioReactor(FactorioObject):
    """A factorio reactor."""

    max_energy_usage: int
    neighbour_bonus: int
    energy_source: str
    energy_properties: tuple[tuple[str, Any], ...]
    energy_effectivity: float
    fuel_category: tuple[str, ...]


class FactorioReactorRepository(FactorioRepository[FactorioReactor]):
    """A repository for factorio reactors."""


# Recipe
class FactorioRecipe(FactorioObject):
    """A factorio recipe."""

    class Item(pydantic.BaseModel):
        item_type: Literal["item", "fluid"]
        stuff: Union[FactorioItem, FactorioFluid]
        amount: float = 0
        min_amount: float = 0
        max_amount: float = 0
        probability: float = 1
        temperature: Optional[int] = None

        @property
        def average_amount(self) -> float:
            try:
                return (
                    self.amount + self.max_amount - self.min_amount
                ) / self.probability
            except ZeroDivisionError:
                return 0.0

        class Config:
            frozen = True

    category: str
    enabled: bool
    hidden: bool
    hidden_from_player_crafting: bool
    energy: float
    ingredients: tuple[FactorioRecipe.Item, ...]
    products: tuple[FactorioRecipe.Item, ...]

    @property
    def available_from_start(self) -> bool:
        """True if the recipe is available without science."""
        return self.enabled


class FactorioRecipeRepository(
    FactorioRepository[FactorioRecipe], metaclass=abc.ABCMeta
):
    """A repository for factorio recipes."""

    @abc.abstractmethod
    def get_recipes_making_stuff(
        self, stuff: FactorioItem | FactorioFluid
    ) -> set[FactorioRecipe]:
        """Return the recipe that can make a given stuff."""


# Resource
class FactorioResource(FactorioObject):
    """A factorio resource."""

    resource_category: str
    mining_time: float
    products: tuple[Quantity, ...]
    required_fluid: Optional[FactorioFluid]
    fluid_amount: int


class FactorioResourceRepository(FactorioRepository[FactorioResource]):
    """A repository for factorio resources."""


class FactorioSolarPanelRepository(FactorioRepository[FactorioSolarPanel]):
    """A repository for factorio solar panel."""


# Technology
class FactorioTechnology(FactorioObject):
    """A factorio technology."""

    recipe_unlocked: tuple[FactorioRecipe, ...]


class FactorioTechnologyRepository(FactorioRepository[FactorioTechnology]):
    """A repository for factorio technologies."""


class TechnologySet(set[FactorioTechnology]):
    """A set storing technology and providing extra services."""

    def __init__(self, technologies: Iterable[FactorioTechnology]):
        super().__init__(technologies)
        self.unlocked_recipes: set[FactorioRecipe] = {
            recipe for technology in self for recipe in technology.recipe_unlocked
        }
