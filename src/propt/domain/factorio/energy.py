from __future__ import annotations

import abc
from typing import Any, Type, TYPE_CHECKING

import pydantic

if TYPE_CHECKING:
    from propt.domain.factorio.prototypes import Ingredient, FluidIngredient, Building
    from propt.domain.factorio.object_set import RecipeSet
    from propt.domain.factorio import repositories as repos


class Energy(pydantic.BaseModel, metaclass=abc.ABCMeta):
    """Represent the energy source for something"""

    @classmethod
    def create(cls, energy_type: str, data: dict[str, Any]) -> Energy:
        children: dict[str, Type[Energy]] = {
            "void": Void,
            "electric": Electricity,
            "heat": Heat,
            "fluid": FluidEnergy,
            "burner": Burner,
        }
        return children[energy_type].from_data(data)

    @classmethod
    @abc.abstractmethod
    def from_data(cls, data: dict[str, Any]):
        """Create from data"""

    @abc.abstractmethod
    def return_sources(
        self,
        building: Building,
        available_recipes: RecipeSet,
        item_repo: repos.ItemRepository,
        fluid_repo: repos.FluidRepository,
    ) -> list[Ingredient]:
        """Return a list of possible ingredients."""

    class Config:
        frozen = True


class Electricity(Energy):
    """Electricity source"""

    @classmethod
    def from_data(cls, data: dict[str, Any]):
        """Create from data"""
        return Electricity()

    def return_sources(
        self,
        building: Building,
        available_recipes: RecipeSet,
        item_repo: repos.ItemRepository,
        fluid_repo: repos.FluidRepository,
    ) -> list[Ingredient]:
        import propt.domain.factorio.prototypes as prototypes
        electricity = prototypes.Item(name="Electricity")
        return [
            prototypes.ItemIngredient(obj=electricity, amount=building.energy_usage, energy_ingredient=True),
        ]


class Burner(Energy):
    """Burn solid stuff."""

    effectivity: float
    fuel_categories: frozenset[str]

    @classmethod
    def from_data(cls, data: dict[str, Any]):
        """Create from data"""
        return Burner(
            effectivity=data.get("effectivity", 1.0),
            fuel_categories=frozenset({
                cat for cat, active in data["fuel_categories"].items() if active
            }),
        )

    def return_sources(
        self,
        building: Building,
        available_recipes: RecipeSet,
        item_repo: repos.ItemRepository,
        fluid_repo: repos.FluidRepository,
    ) -> list[Ingredient]:
        ingredients: list[Ingredient] = []
        # return []
        import propt.domain.factorio.prototypes as prototypes
        for item in item_repo.values():
            if item.fuel_category in self.fuel_categories and item.fuel_value > 0:
                ingredients.append(
                    prototypes.ItemIngredient(
                        obj=item,
                        amount=building.energy_usage
                        / (item.fuel_value * self.effectivity),
                        energy_ingredient=True
                    )
                )
        return ingredients


class Heat(Energy):
    """Heat energy"""

    @classmethod
    def from_data(cls, data: dict[str, Any]):
        """Create from data"""
        return Heat()

    def return_sources(
        self,
        building: Building,
        available_recipes: RecipeSet,
        item_repo: repos.ItemRepository,
        fluid_repo: repos.FluidRepository,
    ) -> list[Ingredient]:
        """blah"""
        # TODO implement for heat
        return []


class Void(Energy):
    """No energy"""

    @classmethod
    def from_data(cls, data: dict[str, Any]):
        """Create from data"""
        return Void()

    def return_sources(
        self,
        building: Building,
        available_recipes: RecipeSet,
        item_repo: repos.ItemRepository,
        fluid_repo: repos.FluidRepository,
    ) -> list[Ingredient]:
        return []


class FluidEnergy(Energy):
    """Burn or consume fluid."""

    effectivity: float
    burns_fluid: bool
    """True, take fuel value, False, take temp"""
    max_temperature: int

    @classmethod
    def from_data(cls, data: dict[str, Any]):
        """Create from data"""
        return FluidEnergy(
            effectivity=data.get("effectivity", 1.0),
            burns_fluid=data.get("burns_fluid", False),
            max_temperature=data.get("maximum_temperature") or 999999999,
        )

    def return_sources(
        self,
        building: Building,
        available_recipes: RecipeSet,
        item_repo: repos.ItemRepository,
        fluid_repo: repos.FluidRepository,
    ) -> list[Ingredient]:
        ingredients: list[FluidIngredient] = []
        # return []
        import propt.domain.factorio.prototypes as prototypes
        for fluid in fluid_repo.values():
            if self.burns_fluid and fluid.fuel_value:
                print(f"AMOUNT {building}||{fluid}||{building.energy_usage/ (fluid.fuel_value * self.effectivity)}")
                ingredients.append(
                    prototypes.FluidIngredient(
                        obj=fluid,
                        amount=building.energy_usage
                        / (fluid.fuel_value * self.effectivity),
                        min_temperature=fluid.default_temperature,
                        max_temperature=fluid.default_temperature,
                        energy_ingredient=True
                    )
                )
            elif not self.burns_fluid:
                valid_temps = {
                    temp
                    for temp in available_recipes.product_temperatures[fluid]
                    if temp == fluid.default_temperature or temp > self.max_temperature
                }
                for temp in valid_temps:
                    print(f"AMOUNT {building.energy_usage / (temp * fluid.heat_capacity * self.effectivity)}")
                    ingredients.append(
                        prototypes.FluidIngredient(
                            obj=fluid,
                            min_temperature=temp,
                            max_temperature=temp,
                            amount=building.energy_usage
                            / (temp * fluid.heat_capacity * self.effectivity),
                            energy_ingredient=True
                        )
                    )
        return ingredients
