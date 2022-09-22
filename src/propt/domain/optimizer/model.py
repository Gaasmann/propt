"""Things related to optimization."""
from __future__ import annotations

import abc
import functools
import itertools
from collections import defaultdict
from typing import Iterable, Optional, Iterator

import immutables
import pydantic


class Item(pydantic.BaseModel):
    """An item."""

    name: str
    temperature: Optional[int] = None

    class Config:
        frozen = True


# class Amount(pydantic.BaseModel):
#     item: Item
#     qty: float
#
#     class Config:
#         frozen = True


# class Recipe(pydantic.BaseModel):
#     """A recipe in the eye of the optimizer."""
#
#     name: str
#     base_time: float
#     ingredients: tuple[Amount, ...]
#     products: tuple[Amount, ...]
#     hidden_from_player: bool
#     category: str
#
#     @classmethod
#     def from_factorio_recipe(cls, recipe: factorio.FactorioRecipe) -> Recipe:
#         ingredients = tuple(
#             Amount(
#                 item=Item.from_factorio_item_or_fluid(
#                     famount.stuff, famount.temperature
#                 ),
#                 qty=famount.average_amount,
#             )
#             for famount in recipe.ingredients
#         )
#         products = tuple(
#             Amount(
#                 item=Item.from_factorio_item_or_fluid(
#                     famount.stuff, famount.temperature
#                 ),
#                 qty=famount.average_amount,
#             )
#             for famount in recipe.products
#         )
#         return Recipe(
#             name=recipe.name,
#             base_time=recipe.energy,
#             ingredients=ingredients,
#             products=products,
#             hidden_from_player=recipe.hidden_from_player_crafting,
#             category=recipe.category,
#         )
#
#     @classmethod
#     def from_factorio_resource(cls, resource: factorio.FactorioResource) -> Recipe:
#         return Recipe(
#             name=resource.name,
#             base_time=resource.mining_time,
#             ingredients=(
#                 Amount(
#                     item=Item.from_factorio_item_or_fluid(
#                         resource.required_fluid,
#                         resource.required_fluid.default_temperature,
#                     ),
#                     qty=resource.fluid_amount,
#                 ),
#             )
#             if resource.fluid_amount
#             else tuple(),
#             products=tuple(
#                 Amount(
#                     item=Item.from_factorio_item_or_fluid(
#                         product.item,
#                         product.item.default_temperature
#                         if isinstance(product.item, factorio.FactorioFluid)
#                         else None,
#                     ),
#                     qty=product.qty,
#                 )
#                 for product in resource.products
#             ),
#             hidden_from_player=True,
#             category=resource.resource_category,
#         )
#
#     @classmethod
#     def from_factorio_boiler(cls, boiler: factorio.FactorioBoiler) -> Recipe:
#         qty_water = boiler.max_energy_usage / ((boiler.target_temperature - 15) * 200)
#         amount_water = Amount(item=Item(name="water", type="fluid", temperature=15), qty=qty_water)
#         amount_steam = Amount(item=Item(name="steam", type="fluid", temperature=boiler.target_temperature), qty=qty_water)
#         return Recipe(
#             name=f"{boiler.name}-recipe",
#             hidden_from_player=True,
#             category="boiling",
#             base_time=1.0,
#             ingredients=(amount_water,),
#             products=(amount_steam,),
#         )
#
#     @property
#     def items(self) -> set[Item]:
#         ingredients = {amount.item for amount in self.ingredients}
#         products = {amount.item for amount in self.products}
#         return ingredients.union(products)
#
#     @property
#     def handcraftable(self) -> bool:
#         """True is the user can craft it."""
#         if self.hidden_from_player:
#             return False
#         return all(item.type == "item" for item in self.items)
#
#     def get_consumed_quantity_per_unit_of_time(self, item: Item) -> float:
#         consumption = sum(
#             amount.qty for amount in self.ingredients if amount.item == item
#         )
#         return consumption / self.base_time
#
#     def get_produced_quantity_per_unit_of_time(self, item: Item) -> float:
#         production = sum(
#             amount.qty for amount in self.products if amount.item == item
#         )  # TODO check recipe producing an amount + a proba
#         return production / self.base_time
#
#     def get_net_quantity_per_unit_of_time(self, item: Item) -> float:
#         try:
#             return self.get_produced_quantity_per_unit_of_time(
#                 item
#             ) - self.get_consumed_quantity_per_unit_of_time(item)
#         except ZeroDivisionError:
#             print(self)
#             print(item)
#             raise
#
#     class Config:
#         frozen = True

import propt.domain.factorio.prototypes as prototypes
import propt.domain.factorio.repositories as repo_models


class RecipeSet(set[prototypes.Recipe]):
    @classmethod
    def from_factorio_repositories(
        cls,
        recipe_repo: repo_models.RecipeRepository,
        available_tech: prototypes.TechnologySet,
    ):
        def recipe_to_include(recipe: prototypes.Recipe) -> bool:
            return not recipe.category.startswith("recycle-")

        available_factorio_recipes: set[prototypes.Recipe] = {
            recipe for recipe in recipe_repo.values() if recipe.available_from_start
        }.union(available_tech.unlocked_recipes)
        available_recipes = set(filter(recipe_to_include, available_factorio_recipes))
        return cls(available_recipes)

    @functools.cached_property
    def product_temperatures(self) -> dict[prototypes.Fluid, set[int]]:
        temperatures: dict[prototypes.Fluid, set[int]] = defaultdict(set)
        for recipe in self:
            for product in recipe.products:
                if isinstance(product, prototypes.ProductFluid):
                    temperatures[product.obj].add(product.temperature)
        return temperatures


class BuildingSet(set[prototypes.Building]):
    """Set of available buildings."""

    @classmethod
    def from_factorio_repositories(
        cls,
        building_repository: repo_models.BuildingRepository,
        item_repository: repo_models.ItemRepository,
        recipe_repository: repo_models.RecipeRepository,
        available_recipes: RecipeSet,
    ) -> BuildingSet:
        available_buildings: set[prototypes.Building] = set()
        for building in building_repository.values():
            for item in item_repository.values():
                if item.place_result and item.place_result == building:
                    for recipe in recipe_repository.get_recipes_making_stuff(item):
                        if recipe.name in (rec.name for rec in available_recipes):
                            available_buildings.add(building)
        return cls(available_buildings)


# class Building(pydantic.BaseModel):
#     """A production building in the eye of the optimizer."""
#
#     name: str
#     speed_coefficient: float
#     crafting_categories: tuple[str, ...]
#
#     class Config:
#         frozen = True
#
#     @classmethod
#     def from_factorio_building(
#         cls,
#         building: factorio.FactorioAssemblingMachine
#         | factorio.FactorioFurnace
#         | factorio.FactorioRocketSilo,
#     ) -> Building:
#         return Building(
#             name=building.name,
#             speed_coefficient=building.crafting_speed,
#             crafting_categories=building.crafting_categories,
#         )
#
#     @classmethod
#     def from_factorio_mining_drill(
#         cls, mining_drill: factorio.FactorioMiningDrill
#     ) -> Building:
#         return Building(
#             name=mining_drill.name,
#             speed_coefficient=mining_drill.mining_speed,
#             crafting_categories=mining_drill.resource_categories,
#         )
#
#     @classmethod
#     def from_factorio_boiler(cls, boiler: factorio.FactorioBoiler) -> Building:
#         return Building(
#             name=boiler.name, speed_coefficient=1.0, crafting_categories=("boiling",)
#         )


class ProductionUnit(pydantic.BaseModel):
    """Represent a unit of production (recipe+building)."""

    recipe_name: str
    building_name: str
    ingredients: immutables.Map[Item, float]
    products: immutables.Map[Item, float]
    quantity: float = 0

    @classmethod
    def from_recipe_and_building(
        cls,
        *,
        recipe: prototypes.Recipe,
        building: prototypes.Building,
        available_recipes: RecipeSet,
    ) -> Iterator[ProductionUnit]:
        """Create zero, one or several production unit from a recipe/building/"""
        expended_ingredients = cls._expend_ingredients_on_temperature(
            recipe, available_recipes
        )
        for nb, ingredient_set in enumerate(itertools.product(*expended_ingredients)):
            yield ProductionUnit(
                recipe_name=f"{recipe.name}-{nb}",
                building_name=building.name,
                ingredients=immutables.Map({
                    ingredient[0]: ingredient[1] / recipe.base_time * building.speed_coefficient for ingredient in ingredient_set
                }),
                products=immutables.Map({
                    Item(
                        name=product.obj.name,
                        temperature=product.temperature
                        if isinstance(product, prototypes.ProductFluid)
                        else None,
                    ): product.avg_amount / recipe.base_time
                    * building.speed_coefficient
                    for product in recipe.products
                    if product.avg_amount
                    * building.speed_coefficient != 0.0
                }),
            )

    @classmethod
    def from_recipe_and_character(cls, recipe: prototypes.Recipe) -> ProductionUnit:
        """Create a Production unit, using the character."""
        if not recipe.handcraftable:
            raise RuntimeError(f"Character can't make {recipe}")
        return ProductionUnit(
            recipe_name=recipe.name,
            building_name="character",
            ingredients=immutables.Map({
                Item(name=ingredient.obj.name, temperature=None): ingredient.amount
                * 0.001
                for ingredient in recipe.ingredients
            }),
            products=immutables.Map({
                Item(name=product.obj.name, temperature=None): product.avg_amount * 0.001
                for product in recipe.products
            }),
        )

    @classmethod
    def from_recipe_and_magic_building(
        cls, recipe: prototypes.Recipe, available_recipes: RecipeSet
    ) -> Iterator[ProductionUnit]:
        """Create one or several production unit with a magic building."""
        magic_building = prototypes.Building(
            name="magic_building",
            energy_usage=0,
            crafting_categories=("magic",),
            speed_coefficient=1.0,
        )
        yield from cls.from_recipe_and_building(
            recipe=recipe, building=magic_building, available_recipes=available_recipes
        )

    @classmethod
    def _expend_ingredients_on_temperature(
        cls, recipe: prototypes.Recipe, available_recipes: RecipeSet
    ) -> tuple[tuple[tuple[Item, float], ...]]:
        """Return a tuple of tuple containing each possible fluid temperature."""
        result: list[tuple[tuple[Item, float]]] = []
        if not recipe.ingredients:
            return ()
        for ingredient in recipe.ingredients:
            if isinstance(ingredient, prototypes.FluidIngredient):
                possible_temperatures = filter(
                    lambda x: (ingredient.min_temperature or 0)
                    <= x
                    <= (ingredient.max_temperature or 99999999),
                    available_recipes.product_temperatures[ingredient.obj],
                )
                result.append(
                    tuple(
                        (
                            Item(name=ingredient.obj.name, temperature=temp),
                            ingredient.amount,
                        )
                        for temp in possible_temperatures
                    )
                )
            else:  # solid, no temperature
                result.append(
                    (
                        (
                            Item(name=ingredient.obj.name, temperature=None),
                            ingredient.amount,
                        ),
                    ),
                )
        return tuple(result)

    @property
    def name(self) -> str:
        return f"{self.recipe_name}\n{self.building_name}"

    @property
    def items(self) -> set[Item]:
        return set(itertools.chain(self.ingredients.keys(), self.products.keys()))

    def get_item_consumed_quantity_by_unit_of_time(self, item: Item) -> float:
        """Return the amount of item required/produced by unit of time."""
        return self.ingredients.get(item, 0.0)

    def get_item_produced_quantity_by_unit_of_time(self, item: Item) -> float:
        """Return the amount of item required/produced by unit of time."""

        return self.products.get(item, 0.0)

    def get_item_net_quantity_by_unit_of_time(self, item: Item) -> float:
        """Return the amount of item required/produced by unit of time."""
        return self.get_item_produced_quantity_by_unit_of_time(
            item
        ) - self.get_item_consumed_quantity_by_unit_of_time(item)

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class ProductionMap:
    """Represent all the possible ways of doing stuff."""

    @classmethod
    def from_repositories(
        cls,
        available_recipes: RecipeSet,
        available_buildings: BuildingSet,
    ) -> ProductionMap:
        temp_map: dict[prototypes.Fluid, set[int]] = defaultdict(set)
        for recipe in available_recipes:
            for product in recipe.products:
                if isinstance(product, prototypes.ProductFluid):
                    temp_map[product.obj].add(product.temperature)

        production_units: list[ProductionUnit] = []
        for recipe in available_recipes:
            prod_unit_size = len(production_units)
            for building in (
                building
                for building in available_buildings
                if recipe.category in building.crafting_categories
            ):
                production_units.extend(
                    ProductionUnit.from_recipe_and_building(
                        recipe=recipe, building=building, available_recipes=available_recipes
                    )
                )
            if prod_unit_size == len(production_units) and recipe.handcraftable:
                production_units.append(
                    ProductionUnit.from_recipe_and_character(recipe)
                )

        return cls(production_units)

    def __init__(self, production_units: list[ProductionUnit]):
        self.production_units = production_units

    def add_magic_unit(self) -> None:
        """Add some magic prod units for items on the map that has no way of being produced.

        This is mainly to debug situation when the solver can't find a solution.
        """
        produced_items = {
            item
            for prod_unit in self.production_units
            for item in prod_unit.products.keys()
        }
        missing_items = self.items.difference(produced_items)
        for item in missing_items:
            print(f"MISSING ITEM: {item}")
            self.production_units.append(
                ProductionUnit(
                    recipe_name=f"magic-{item}",
                    ingredients=immutables.Map({}),
                    products=immutables.Map({item: 1}),
                    building_name="magic-building",
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
        item_constraints: Iterable[tuple[Item, float]],
        prod_unit_constraints: Iterable[tuple[ProductionUnit, float]],
    ):
        self._production_map = production_map
        self._item_constraints = list(item_constraints)
        self._prod_unit_constraints = prod_unit_constraints

    @abc.abstractmethod
    def optimize(self) -> ProductionMap:
        """Do the optimization and return a new ProductionMap."""
