"""JSON repos for recipes."""
from __future__ import annotations

import itertools
import pathlib
from collections import defaultdict
from typing import Any, Iterable

import propt.domain.new_factorio.prototypes as prototypes
import propt.domain.new_factorio.repositories as repo_models
import propt.adapters.new_factorio_repositories.json.base as json_base


class JSONFactorioAggregateRecipeRepository(repo_models.RecipeRepository):
    """Aggregate Building repository into one."""
    def __init__(self, recipe_repos: Iterable[repo_models.RecipeRepository]):
        super().__init__(
            itertools.chain.from_iterable(
                tuple(repo.items()) for repo in recipe_repos
            )
        )
        self._recipe_per_product: dict[str, set[prototypes.Recipe]] = defaultdict(set)
        for recipe in self.values():
            for product in recipe.products:
                self._recipe_per_product[product.obj.name].add(recipe)

    def get_recipes_making_stuff(
        self, stuff: prototypes.Object
    ) -> set[prototypes.Recipe]:
        return self._recipe_per_product[stuff.name]


class JSONFactorioRecipeRepository(
    repo_models.RecipeRepository,
    json_base.JSONFactorioRepository[prototypes.Recipe],
):
    def __init__(
        self,
        json_directory: pathlib.Path,
        item_repo: repo_models.ItemRepository,
        fluid_repo: repo_models.FluidRepository,
    ):
        super().__init__(filename="recipe.json")
        self._item_repo = item_repo
        self._fluid_repo = fluid_repo
        self._recipe_per_product: dict[str, set[prototypes.Recipe]] = defaultdict(set)
        self._load_file(json_directory)

    def _build_ingredient(self, item: dict[str, Any]) -> prototypes.Ingredient:
        print(item)
        common = {
            "obj": self._item_repo[item["name"]]
            if item["type"] == "item"
            else self._fluid_repo[item["name"]],
            "amount": item.get("amount", 0),
        }
        return (
            prototypes.ItemIngredient(**common)
            if item["type"] == "item"
            else prototypes.FluidIngredient(
                **{
                    **common,
                    "min_temperature": item.get("temperature")
                    or item.get("minimum_temperature")
                    or self._fluid_repo[item["name"]].default_temperature,
                    "max_temperature": item.get("temperature")
                    or item.get("maximum_temperature")
                    or self._fluid_repo[item["name"]].default_temperature,
                }
            )
        )

    def _build_product(self, item: dict[str, Any]) -> prototypes.Product:
        common = {
            "obj": self._item_repo[item["name"]]
            if item["type"] == "item"
            else self._fluid_repo[item["name"]],
            "amount": item.get("amount", 0),
            "min_amount": item.get("min_amount", 0),
            "max_amount": item.get("max_amount", 0),
            "probability": item.get("probability", 1),
        }
        return (
            prototypes.ProductItem(**common)
            if item["type"] == "item"
            else prototypes.ProductFluid(**common, temperature=item.get("temperature", self._fluid_repo[item["name"]].default_temperature))
        )

    def build_object(self, data) -> prototypes.Recipe:
        try:
            ingredients = tuple(
                self._build_ingredient(item) for item in data["ingredients"]
            )
            products = tuple(self._build_product(item) for item in data["products"])
            recipe = prototypes.Recipe(
                name=data["name"],
                category=data["category"],
                available_from_start=data["enabled"],
                hidden_from_player_crafting=data["hidden_from_player_crafting"],
                base_time=data["energy"],
                ingredients=ingredients,
                products=products,
            )
            for product in products:
                self._recipe_per_product[product.obj.name].add(recipe)
            return recipe
        except (KeyError, TypeError):
            print(data)
            raise

    def get_recipes_making_stuff(
        self, stuff: prototypes.Object
    ) -> set[prototypes.Recipe]:
        return self._recipe_per_product[stuff.name]


class JSONFactorioResourceRepository(
    repo_models.RecipeRepository,
    json_base.JSONFactorioRepository[prototypes.Recipe],
):
    def __init__(
        self,
        json_directory: pathlib.Path,
        item_repo: repo_models.ItemRepository,
        fluid_repo: repo_models.FluidRepository,
    ):
        super().__init__(filename="resource.json")
        self._item_repo = item_repo
        self._fluid_repo = fluid_repo
        self._recipe_per_product: dict[str, set[prototypes.Recipe]] = defaultdict(set)
        self._load_file(json_directory)

    def build_object(self, data) -> prototypes.Recipe:
        try:
            mine_prop = data["mineable_properties"]
            ingredients = (prototypes.FluidIngredient(
                obj=self._fluid_repo[mine_prop["required_fluid"]],
                amount=mine_prop.get("fluid_amount", 0) / 10,
                min_temperature=None,
                max_temperature=None
            ),) if mine_prop.get("fluid_amount") else tuple()
            products = tuple(
                prototypes.ProductItem(
                    obj=self._item_repo[product["name"]],
                    amount=product.get("amount", 0.0),
                    min_amount=product.get("min_amount", 0.0),
                    max_amount=product.get("max_amount", 0.0),
                    probability=product.get("probability", 1),
                                       ) if product["type"] == "item"
                else prototypes.ProductFluid(
                    obj=self._fluid_repo[product["name"]],
                    amount=product.get("amount", 0.0),
                    min_amount=product.get("min_amount", 0.0),
                    max_amount=product.get("max_amount", 0.0),
                    probability=product.get("probability", 1),
                    temperature=product.get("temperature", self._fluid_repo[product["name"]].default_temperature),
                )
                for product in mine_prop["products"]
            )
            recipe = prototypes.Recipe(
                name=data["name"],
                available_from_start=True,
                hidden_from_player_crafting=True,
                base_time=mine_prop["mining_time"],
                category=data["resource_category"],
                ingredients=ingredients,
                products=products,
            )
            for product in products:
                self._recipe_per_product[product.obj.name].add(recipe)
            return recipe
        except KeyError:
            print(data)
            raise
    def get_recipes_making_stuff(
        self, stuff: prototypes.Object
    ) -> set[prototypes.Recipe]:
        return self._recipe_per_product[stuff.name]


class JSONFactorioBoilerRecipeRepository(
    repo_models.RecipeRepository,
    json_base.JSONFactorioRepository[prototypes.Recipe],
):
    def __init__(self, json_directory: pathlib.Path, fluid_repo: repo_models.FluidRepository):
        super().__init__("boiler.json")
        self._fluid_repo = fluid_repo
        self._recipe_per_product: dict[str, set[prototypes.Recipe]] = defaultdict(set)
        self._load_file(json_directory)

    def build_object(self, data: dict[str, Any]) -> prototypes.Recipe:
        assert len(data["energy_source"].keys()) < 2
        water_fluid = self._fluid_repo["water"]
        steam_fluid = self._fluid_repo["steam"]
        amount = data["max_energy_usage"] / ((data["target_temperature"] - 15) * 200)
        ingredients = (
            prototypes.FluidIngredient(
                obj=water_fluid,
                min_temperature=water_fluid.default_temperature,
                max_temperature=water_fluid.default_temperature,
                amount=amount
            ),
        )
        products = (
            prototypes.ProductFluid(
                obj=steam_fluid,
                amount=amount,
                temperature=data["target_temperature"]
            ),
        )
        recipe = prototypes.Recipe(
            name=f"steam-from-{data['name']}",
            ingredients=ingredients,
            products=products,
            base_time=1.0,
            hidden_from_player_crafting=True,
            available_from_start=True,
            category="boiling",
        )
        for product in products:
            self._recipe_per_product[product.obj.name].add(recipe)
        return recipe
    def get_recipes_making_stuff(
        self, stuff: prototypes.Object
    ) -> set[prototypes.Recipe]:
        return self._recipe_per_product[stuff.name]
