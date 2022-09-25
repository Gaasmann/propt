"""Service about optimizer."""
from collections import defaultdict
from typing import Iterable

import more_itertools

import propt.domain.factorio.object_set
import propt.domain.factorio.prototypes
import propt.domain.optimizer.model as opt_model
import propt.domain.factorio as factorio_model


def _filter_out_unavailable_factorio_recipes(
    factorio_recipes: factorio_model.FactorioRecipeRepository,
    available_techologies: factorio_model.TechnologySet,
) -> set[factorio_model.FactorioRecipe]:
    """Return a set of available factorio recipe."""

    available_recipes: set[factorio_model.FactorioRecipe] = {
        recipe for recipe in factorio_recipes.values() if recipe.available_from_start
    }.union(available_techologies.unlocked_recipes)

    # Exclude the recycling factory recipes
    def recipe_to_include(recipe: factorio_model.FactorioRecipe) -> bool:
        return not recipe.category.startswith("recycle-")

    available_recipes = set(filter(recipe_to_include, available_recipes))

    return available_recipes


def _gather_produced_item_temperatures(
    recipes: Iterable[opt_model.Recipe],
) -> dict[str, set[int]]:
    """Return a dict[item_name, set[temperature]] for fluids with multiple temperature."""
    result: dict[str, set[int]] = defaultdict(set)
    for recipe in recipes:
        for product in recipe.products:
            if product.item.temperature is not None:
                result[product.item.name].add(product.item.temperature)
    # remove items with only one temperature
    key_to_pop = [key for key, temps in result.items() if len(temps) == 1]
    for key in key_to_pop:
        result.pop(key)
    return result


def _convert_amount_with_new_temperature(
    amount: opt_model.Amount, new_temp: int
) -> opt_model.Amount:
    """Return an amount with a new item representing the temperature."""
    item_values = amount.item.dict(exclude={"temperature"})
    item_values["temperature"] = new_temp
    item = opt_model.Item(**item_values)
    return opt_model.Amount(item=item, qty=amount.qty)


def _expend_recipes_by_temperature(
    input_recipes: Iterable[opt_model.Recipe], temperatures: dict[str, set[int]]
) -> set[opt_model.Recipe]:
    """expend the list of recipes by adding a recipe per temperature acceptable as input."""
    expended_recipes: set[opt_model.Recipe] = set()
    item_with_temps_names = set(temperatures.keys())
    for input_recipe in input_recipes:
        ingredient_names = {
            ingredient.item.name for ingredient in input_recipe.ingredients
        }
        target_ingredients = item_with_temps_names.intersection(ingredient_names)
        assert (
            len(target_ingredients) < 2
        )  # no sure how to deal with several inputs to expand
        if not target_ingredients:  # No multiple temperature => push the recipe as-is
            expended_recipes.add(input_recipe)
        else:  # expension
            target_name = more_itertools.first(target_ingredients)
            target_ingredient = more_itertools.first(
                filter(
                    lambda x: x.item.name == target_name,
                    input_recipe.ingredients,
                )
            )
            other_ingredients = list(input_recipe.ingredients)
            other_ingredients.remove(target_ingredient)
            for temperature in temperatures[target_name]:
                print(input_recipe)
                if target_ingredient.item.temperature is None or temperature >= target_ingredient.item.temperature:
                    new_recipe_info = input_recipe.dict(exclude={"ingredients"})
                    ingredient = _convert_amount_with_new_temperature(
                        target_ingredient, temperature
                    )
                    new_recipe_info["ingredients"] = (*other_ingredients, ingredient)
                    new_recipe = opt_model.Recipe(**new_recipe_info)
                    expended_recipes.add(new_recipe)
    return expended_recipes


def convert_factorio_recipes(
    factorio_recipes: factorio_model.FactorioRecipeRepository,
    resource_repository: factorio_model.FactorioResourceRepository,
    boiler_repository: factorio_model.FactorioBoilerRepository,
    available_techologies: factorio_model.TechnologySet,
) -> propt.domain.factorio.object_set.RecipeSet:
    """Convert the factorio recipes to optimizer recipes."""
    available_recipes = _filter_out_unavailable_factorio_recipes(
        factorio_recipes, available_techologies
    )
    recipes: set[opt_model.Recipe] = {
        opt_model.Recipe.from_factorio_recipe(recipe) for recipe in available_recipes
    }
    # add resource recipes
    recipes.update(
        opt_model.Recipe.from_factorio_resource(resource)
        for resource in resource_repository.values()
    )
    # add boilers recipe
    recipes.update(
        opt_model.Recipe.from_factorio_boiler(boiler)
        for boiler in boiler_repository.values()
    )
    # get temperatures and expand
    temperatures = _gather_produced_item_temperatures(recipes)
    return propt.domain.factorio.object_set.RecipeSet(_expend_recipes_by_temperature(recipes, temperatures))
