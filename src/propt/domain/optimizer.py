"""Things related to optimization."""
from __future__ import annotations

import abc
import itertools
from typing import Iterable, Literal

import pydantic

import propt.domain.factorio as factorio


class Item(pydantic.BaseModel):
    """An item that can be an ingredient or a product."""

    name: str
    type: Literal["item", "fluid"]

    @classmethod
    def from_factorio_item_or_fluid(
        cls, item: factorio.FactorioItem | factorio.FactorioFluid
    ) -> Item:
        return cls(
            name=item.name,
            type="fluid" if isinstance(item, factorio.FactorioFluid) else "item",
        )

    class Config:
        frozen = True


class Amount(pydantic.BaseModel):
    item: Item
    qty: float

    class Config:
        frozen = True


class Recipe(pydantic.BaseModel):
    """A recipe in the eye of the optimizer."""

    name: str
    base_time: float
    ingredients: tuple[Amount, ...]
    products: tuple[Amount, ...]
    hidden_from_player: bool
    category: str

    @classmethod
    def from_factorio_recipe(cls, recipe: factorio.FactorioRecipe) -> Recipe:
        ingredients = tuple(
            Amount(
                item=Item.from_factorio_item_or_fluid(famount.stuff),
                qty=famount.average_amount,
            )
            for famount in recipe.ingredients
        )
        products = tuple(
            Amount(
                item=Item.from_factorio_item_or_fluid(famount.stuff),
                qty=famount.average_amount,
            )
            for famount in recipe.products
        )
        return Recipe(
            name=recipe.name,
            base_time=recipe.energy,
            ingredients=ingredients,
            products=products,
            hidden_from_player=recipe.hidden_from_player_crafting,
            category=recipe.category,
        )

    @classmethod
    def from_factorio_resource(cls, resource: factorio.FactorioResource) -> Recipe:
        return Recipe(
            name=resource.name,
            base_time=resource.mining_time,
            ingredients=(
                Amount(
                    item=Item.from_factorio_item_or_fluid(resource.required_fluid),
                    qty=resource.fluid_amount,
                ),
            )
            if resource.fluid_amount
            else tuple(),
            products=tuple(
                Amount(
                    item=Item.from_factorio_item_or_fluid(product.item), qty=product.qty
                )
                for product in resource.products
            ),
            hidden_from_player=True,
            category=resource.resource_category,
        )

    @classmethod
    def from_factorio_boiler(cls, boiler: factorio.FactorioBoiler) -> Recipe:
        qty_water = boiler.max_energy_usage / ((boiler.target_temperature - 15) * 200)
        amount_water = Amount(item=Item(name="water", type="fluid"), qty=qty_water)
        amount_steam = Amount(item=Item(name="steam", type="fluid"), qty=qty_water)
        return Recipe(
            name=f"{boiler.name}-recipe",
            hidden_from_player=True,
            category="boiling",
            base_time=1.0,
            ingredients=(amount_water,),
            products=(amount_steam,)
        )

    @property
    def items(self) -> set[Item]:
        ingredients = {amount.item for amount in self.ingredients}
        products = {amount.item for amount in self.products}
        return ingredients.union(products)

    @property
    def handcraftable(self) -> bool:
        """True is the user can craft it."""
        if self.hidden_from_player:
            return False
        return all(item.type == "item" for item in self.items)

    def get_consumed_quantity_per_unit_of_time(self, item: Item) -> float:
        consumption = sum(
            amount.qty for amount in self.ingredients if amount.item == item
        )
        return consumption / self.base_time

    def get_produced_quantity_per_unit_of_time(self, item: Item) -> float:
        production = sum(
            amount.qty for amount in self.products if amount.item == item
        )  # TODO check recipe producing an amount + a proba
        return production / self.base_time

    def get_net_quantity_per_unit_of_time(self, item: Item) -> float:
        try:
            return (
                self.get_produced_quantity_per_unit_of_time(item)
                - self.get_consumed_quantity_per_unit_of_time(item)
            )
        except ZeroDivisionError:
            print(self)
            print(item)
            raise

    class Config:
        frozen = True


class Building(pydantic.BaseModel):
    """A production building in the eye of the optimizer."""

    name: str
    speed_coefficient: float
    crafting_categories: tuple[str, ...]

    class Config:
        frozen = True

    @classmethod
    def from_factorio_building(
        cls,
        building: factorio.FactorioAssemblingMachine
        | factorio.FactorioFurnace
        | factorio.FactorioRocketSilo,
    ) -> Building:
        return Building(
            name=building.name,
            speed_coefficient=building.crafting_speed,
            crafting_categories=building.crafting_categories,
        )

    @classmethod
    def from_factorio_mining_drill(
        cls, mining_drill: factorio.FactorioMiningDrill
    ) -> Building:
        return Building(
            name=mining_drill.name,
            speed_coefficient=mining_drill.mining_speed,
            crafting_categories=mining_drill.resource_categories,
        )

    @classmethod
    def from_factorio_boiler(
            cls,
            boiler: factorio.FactorioBoiler
                             ) -> Building:
        return Building(
            name=boiler.name,
            speed_coefficient=1.0,
            crafting_categories=("boiling",)
        )


class ProductionUnit(pydantic.BaseModel):
    """Represent a unit of production (recipe+building)."""

    recipe: Recipe
    building: Building
    quantity: float = 0

    @property
    def name(self) -> str:
        return f"{self.recipe.name}\n{self.building.name}"

    @property
    def items(self) -> set[Item]:
        return self.recipe.items

    def get_item_consumed_quantity_by_unit_of_time(self, item: Item) -> float:
        """Return the amount of item required/produced by unit of time."""
        return (
            self.recipe.get_consumed_quantity_per_unit_of_time(item)
            * self.building.speed_coefficient
        )

    def get_item_produced_quantity_by_unit_of_time(self, item: Item) -> float:
        """Return the amount of item required/produced by unit of time."""
        return (
            self.recipe.get_produced_quantity_per_unit_of_time(item)
            * self.building.speed_coefficient
        )

    def get_item_net_quantity_by_unit_of_time(self, item: Item) -> float:
        """Return the amount of item required/produced by unit of time."""
        return (
            self.recipe.get_net_quantity_per_unit_of_time(item)
            * self.building.speed_coefficient
        )

    class Config:
        frozen = True


class ProductionMap:
    """Represent all the possible ways of doing stuff."""

    @classmethod
    def from_repositories(
        cls,
        recipe_repository: factorio.FactorioRecipeRepository,
        item_repository: factorio.FactorioItemRepository,
        resource_repository: factorio.FactorioResourceRepository,
        assembly_machine_repository: factorio.FactorioAssemblingMachineRepository,
        furnace_repository: factorio.FactorioFurnaceRepository,
        rocket_silo_repository: factorio.FactorioRocketSiloRepository,
        mining_drill_repository: factorio.FactorioMiningDrillRepository,
        boiler_repository: factorio.FactorioBoilerRepository,
        technology_set: factorio.TechnologySet,
    ) -> ProductionMap:
        # define what is available
        # available factorio recipes
        def recipe_to_include(recipe: factorio.FactorioRecipe) -> bool:
            return not recipe.category.startswith("recycle-")

        available_recipes: set[factorio.FactorioRecipe] = {
            recipe
            for recipe in recipe_repository.values()
            if recipe.available_from_start
        }.union(technology_set.unlocked_recipes)
        available_recipes = set(filter(recipe_to_include, available_recipes))
        # Available factorio buildings
        available_buildings: set[factorio.FactorioAssemblingMachine] = set()
        for building in itertools.chain(
            assembly_machine_repository.values(),
            furnace_repository.values(),
            rocket_silo_repository.values(),
            mining_drill_repository.values(),
        ):
            for item in item_repository.values():
                if item.place_result and item.place_result == building:
                    for recipe in recipe_repository.get_recipes_making_stuff(item):
                        if recipe in available_recipes:
                            available_buildings.add(building)

        recipes: set[Recipe] = {
            Recipe.from_factorio_recipe(recipe) for recipe in available_recipes
        }
        # Add resource recipe
        for resource in resource_repository.values():
            recipes.add(Recipe.from_factorio_resource(resource))
        # Add boiler recipe
        recipes.update(Recipe.from_factorio_boiler(boiler) for boiler in boiler_repository.values())
        buildings: set[Building] = {
            Building.from_factorio_mining_drill(building)
            if isinstance(building, factorio.FactorioMiningDrill)
            else Building.from_factorio_building(building)
            for building in available_buildings
        }
        buildings.update(Building.from_factorio_boiler(boiler) for boiler in boiler_repository.values())
        # TODO place assert or something to catch when an item is unmakable
        #
        production_units: list[ProductionUnit] = []
        for recipe in recipes:
            building_added = False
            for building in (
                building
                for building in buildings
                if recipe.category in building.crafting_categories
            ):
                production_units.append(
                    ProductionUnit(recipe=recipe, building=building)
                )
                building_added = True
            if not building_added and recipe.handcraftable:
                production_units.append(
                    ProductionUnit(
                        recipe=recipe,
                        building=Building(
                            name="character",
                            speed_coefficient=0.001,
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
            building = Building(
                name="magic-building",
                speed_coefficient=1.0,
                crafting_categories=tuple(),
            )
            self.production_units.append(
                ProductionUnit(
                    recipe=Recipe(
                        name=f"magic-{item.name}",
                        hidden_from_player=True,
                        ingredients=tuple(),
                        base_time=1.0,
                        category="magic",
                        products=(Amount(item=item, qty=1),),
                    ),
                    building=building,
                )
            )

    @property
    def items(self) -> set[Item]:
        return {item for prod_unit in self.production_units for item in prod_unit.items}


class SolutionNotFound(Exception):
    """Raised when the optimizer can't find a solution."""


class Optimizer(metaclass=abc.ABCMeta):
    """Optimize a Production map."""

    def __init__(
        self,
        production_map: ProductionMap,
        item_constraints: Iterable[Amount],
        prod_unit_constraints: Iterable[tuple[ProductionUnit, float]],
    ):
        self._production_map = production_map
        self._item_constraints = list(item_constraints)
        self._prod_unit_constraints = prod_unit_constraints

    @abc.abstractmethod
    def optimize(self) -> ProductionMap:
        """Do the optimization and return a new ProductionMap."""
