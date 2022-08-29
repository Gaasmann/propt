"""Tests for Concept."""
import pytest

import propt.domain.concepts as concepts


def test_concept_are_immutable():
    """Check the concepts are really immutable."""
    item = concepts.Item(code=concepts.Code("code"), name="quantum")
    with pytest.raises(TypeError):
        item.code = "tutu"


@pytest.fixture
def recipe() -> concepts.Recipe:
    ingredients = (
        concepts.Quantity(
            item=concepts.Item(code=concepts.Code("plate"), name="Plate"), qty=42
        ),
        concepts.Quantity(
            item=concepts.Item(code=concepts.Code("coke"), name="Coke"), qty=2
        ),
    )
    products = (
        concepts.Quantity(
            item=concepts.Item(code=concepts.Code("stick"), name="Stick"), qty=420
        ),
    )
    buildings = (
        concepts.Building(
            code=concepts.Code("factory"), name="Factory", speed_coef=2.0
        ),
    )
    return concepts.Recipe(
        code=concepts.Code("recipe"),
        name="Recipe",
        base_time=10,
        ingredients=ingredients,
        products=products,
        buildings=buildings,
    )


def test_recipe_net_qty_ingredient(recipe):
    assert recipe.get_net_quantity_per_unit_of_time(recipe.ingredients[0].item) < 0


def test_recipe_net_qty_product(recipe):
    assert recipe.get_net_quantity_per_unit_of_time(recipe.products[0].item) > 0


def test_recipe_net_qty_ingredients(recipe):
    with pytest.raises(concepts.ObjectNotFound):
        recipe.get_net_quantity_per_unit_of_time(
            concepts.Item(code=concepts.Code("osef"), name="Osef")
        )
