"""Things related to optimization."""
from __future__ import annotations

import abc
import itertools
from collections import defaultdict
from typing import Iterable, Optional, Iterator

import immutables
import pydantic

import propt.domain.factorio.prototypes
import propt.domain.factorio.prototypes as prototypes
import propt.domain.factorio.repositories as repo_models
from propt.domain.factorio.object_set import RecipeSet


class Item(pydantic.BaseModel):
    """An item."""

    name: str
    temperature: Optional[int] = None
    energy_ingredient: bool = False  # TODO lot of trouble for this parameter. Shouldn't be there

    def __eq__(self, other):
        return self.name == other.name and self.temperature == other.temperature if isinstance(other, self.__class__) else False

    def __hash__(self):
        return hash(tuple(self.dict(exclude={"energy_ingredient"}).items()))
    class Config:
        frozen = True


class BuildingSet(set[propt.domain.factorio.prototypes.Building]):
    """Set of available buildings."""

    @classmethod
    def from_factorio_repositories(
        cls,
        building_repository: repo_models.BuildingRepository,
        item_repository: repo_models.ItemRepository,
        recipe_repository: repo_models.RecipeRepository,
        available_recipes: RecipeSet,
    ) -> BuildingSet:
        available_buildings: set[propt.domain.factorio.prototypes.Building] = set()
        for building in building_repository.values():
            for item in item_repository.values():
                if item.place_result and item.place_result == building:
                    for recipe in recipe_repository.get_recipes_making_stuff(item):
                        if recipe.name in (rec.name for rec in available_recipes):
                            available_buildings.add(building)
        return cls(available_buildings)


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
        building: propt.domain.factorio.prototypes.Building,
        item_repo: repo_models.ItemRepository,
        fluid_repo: repo_models.FluidRepository,
        available_recipes: RecipeSet,
    ) -> Iterator[ProductionUnit]:
        """Create zero, one or several production unit from a recipe/building/"""
        expended_ingredients = cls._expend_ingredients_on_temperature(
            recipe, available_recipes
        )
        # add energy
        energy_ingredients = tuple(
            (
                Item(
                    name=ingredient.obj.name,
                    temperature=ingredient.min_temperature
                    if isinstance(ingredient, prototypes.FluidIngredient)
                    else None,
                    energy_ingredient=True
                ),
                ingredient.amount,
            )
            for ingredient in building.energy_info.return_sources(
                building, available_recipes, item_repo, fluid_repo
            )
        )
        ingredients = tuple(
            filter(lambda x: x, (*expended_ingredients, energy_ingredients))
        )
        for nb, ingredient_set in enumerate(itertools.product(*ingredients)):
            yield ProductionUnit(
                recipe_name=f"{recipe.name}-{nb}",
                building_name=building.name,
                ingredients=immutables.Map(
                    {
                        ingredient[0]: ingredient[1]
                        / recipe.base_time
                        * building.speed_coefficient
                        if not ingredient[0].energy_ingredient
                        else ingredient[1]
                        for ingredient in ingredient_set
                    }
                ),
                products=immutables.Map(
                    {
                        Item(
                            name=product.obj.name,
                            temperature=product.temperature
                            if isinstance(product, prototypes.ProductFluid)
                            else None,
                        ): product.avg_amount
                        / recipe.base_time
                        * building.speed_coefficient
                        for product in recipe.products
                        if product.avg_amount * building.speed_coefficient != 0.0
                    }
                ),
            )

    @classmethod
    def from_recipe_and_character(cls, recipe: prototypes.Recipe) -> ProductionUnit:
        """Create a Production unit, using the character."""
        if not recipe.handcraftable:
            raise RuntimeError(f"Character can't make {recipe}")
        return ProductionUnit(
            recipe_name=recipe.name,
            building_name="character",
            ingredients=immutables.Map(
                {
                    Item(name=ingredient.obj.name, temperature=None): ingredient.amount
                    * 0.001
                    for ingredient in recipe.ingredients
                }
            ),
            products=immutables.Map(
                {
                    Item(name=product.obj.name, temperature=None): product.avg_amount
                    * 0.001
                    for product in recipe.products
                }
            ),
        )

    @classmethod
    def from_recipe_and_magic_building(
        cls, recipe: prototypes.Recipe, available_recipes: RecipeSet
    ) -> Iterator[ProductionUnit]:
        """Create one or several production unit with a magic building."""
        magic_building = propt.domain.factorio.prototypes.Building(
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
        item_repo: repo_models.ItemRepository,
        fluid_repo: repo_models.FluidRepository,
    ) -> ProductionMap:
        temp_map: dict[prototypes.Fluid, set[int]] = defaultdict(set)
        for recipe in available_recipes:
            for product in recipe.products:
                if isinstance(product, prototypes.ProductFluid):
                    temp_map[product.obj].add(product.temperature)

        production_units: list[ProductionUnit] = []
        for recipe in available_recipes:
            if recipe.name == "elec-from-steam-engine-165":
                print("blah")
            prod_unit_size = len(production_units)
            matching_buildings = {
                building
                for building in available_buildings
                if recipe.category in building.crafting_categories
            }
            for building in (
                building
                for building in available_buildings
                if recipe.category in building.crafting_categories
            ):
                production_units.extend(
                    ProductionUnit.from_recipe_and_building(
                        recipe=recipe,
                        building=building,
                        available_recipes=available_recipes,
                        fluid_repo=fluid_repo,
                        item_repo=item_repo,
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
