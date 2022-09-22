import pathlib

import more_itertools

import propt.adapters.factorio_repositories.json.buildings as building_repos
import propt.adapters.factorio_repositories.json.objects as obj_repos
import propt.adapters.factorio_repositories.json.recipes as recipe_repos
import propt.adapters.factorio_repositories.json.technologies as tech_repos
import propt.adapters.optimizers as optimizers
import propt.data.pyanodons as factorio_data
import propt.domain.factorio.prototypes as prototypes
import propt.domain.optimizer.model as new_opt_model


def main():
    data_path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    # buildings
    building_repo = building_repos.JSONFactorioAggregateBuildingRepository(
        (
            building_repos.JSONFactorioAssemblingMachineRepository(data_path),
            building_repos.JSONFactorioFurnaceRepository(data_path),
            building_repos.JSONFactorioMiningDrillRepository(data_path),
            building_repos.JSONFactorioRocketSiloRepository(data_path),
            building_repos.JSONFactorioBoilerBuildingRepository(data_path),
        )
    )
    # Objects
    item_repo = obj_repos.JSONFactorioItemRepository(data_path, building_repo)
    fluid_repo = obj_repos.JSONFactorioFluidRepository(data_path)
    # Recipe
    recipe_repo = recipe_repos.JSONFactorioAggregateRecipeRepository(
        (
            recipe_repos.JSONFactorioRecipeRepository(data_path, item_repo, fluid_repo),
            recipe_repos.JSONFactorioResourceRepository(
                data_path, item_repo, fluid_repo
            ),
            recipe_repos.JSONFactorioBoilerRecipeRepository(data_path, fluid_repo),
        )
    )
    # Techno
    tech_repo = tech_repos.JSONFactorioTechnologyRepository(data_path, recipe_repo)

    with open("techno.txt", "r") as f:
        technologies = prototypes.TechnologySet(
            tech_repo[code.strip()] for code in f.readlines()
        )
    # filter available recipes/buildings
    available_recipes = new_opt_model.RecipeSet.from_factorio_repositories(
        recipe_repo, technologies
    )
    available_buildings = new_opt_model.BuildingSet.from_factorio_repositories(
        building_repo, item_repo, recipe_repo, available_recipes
    )

    prod_map = new_opt_model.ProductionMap.from_repositories(
        available_recipes=available_recipes,
        available_buildings=available_buildings,
    )

    # prod_map.add_magic_unit()
    item_constraints = [
        (new_opt_model.Item(name="logistic-science-pack", temperature=None), 10),
    ]
    prod_unit_constraints = [
        (
            next(
                pu for pu in prod_map.production_units if pu.recipe_name == "oil-mk01-0"
            ),
            0,
        ),
        *[( pu, 0)
                 for pu in prod_map.production_units if pu.recipe_name == "coal-0"


        ],
    ]
    optim = optimizers.ORToolsOptimizer(
        prod_map, item_constraints, prod_unit_constraints
    )
    result = optim.optimize()

    graph_begin = optimizers.NetworkXProductionGraph(prod_map)
    graph_begin.write_dot(pathlib.Path("all.dot"))
    graph = optimizers.NetworkXProductionGraph(result)
    graph.write_dot(pathlib.Path("newnew.dot"))


if __name__ == "__main__":
    main()
