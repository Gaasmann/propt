import pathlib
import pickle

import more_itertools

import propt.adapters.debug as debug
import propt.adapters.factorio_repositories.json.buildings as building_repos
import propt.adapters.factorio_repositories.json.objects as obj_repos
import propt.adapters.factorio_repositories.json.recipes as recipe_repos
import propt.adapters.factorio_repositories.json.technologies as tech_repos
import propt.adapters.optimizers as optimizers
import propt.data.pyanodons as factorio_data
import propt.domain.factorio.object_set
import propt.domain.factorio.prototypes
import propt.domain.optimizer.model as new_opt_model


def add_mining_constraint(
    prod_map: new_opt_model.ProductionMap,
        ore_name: str,
        capa_elec_drill: int,
        capa_burning_drill: int,
):
    array1 = [
        (pu, capa_elec_drill)
        for pu in prod_map.production_units
        if pu.recipe_name.startswith(ore_name)
           and pu.building_name == "electric-mining-drill"
    ]
    array2 = [
        (pu, capa_burning_drill)
        for pu in prod_map.production_units
        if pu.recipe_name.startswith(ore_name)
           and pu.building_name == "burner-mining-drill"
    ]
    return [*array1, *array2]

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
            building_repos.JSONFactorioGeneratorRepository(data_path),
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
        technologies = propt.domain.factorio.object_set.TechnologySet(
            tech_repo[code.strip()] for code in f.readlines()
        )
    # filter available recipes/buildings
    available_recipes = (
        propt.domain.factorio.object_set.RecipeSet.from_factorio_repositories(
            recipe_repo, technologies
        )
    )
    gen_repo = recipe_repos.JSONFactorioGeneratorRecipeRepository(
        json_directory=data_path,
        available_recipes=available_recipes,
        fluid_repo=fluid_repo,
    )
    debug.dump("generators", gen_repo)
    recipe_repo = recipe_repos.JSONFactorioAggregateRecipeRepository(
        (
            recipe_repos.JSONFactorioRecipeRepository(data_path, item_repo, fluid_repo),
            recipe_repos.JSONFactorioResourceRepository(
                data_path, item_repo, fluid_repo
            ),
            recipe_repos.JSONFactorioBoilerRecipeRepository(data_path, fluid_repo),
            gen_repo,
        )
    )
    available_recipes = (
        propt.domain.factorio.object_set.RecipeSet.from_factorio_repositories(
            recipe_repo, technologies
        )
    )

    debug.dump("available_recipe2", available_recipes)

    available_buildings = new_opt_model.BuildingSet.from_factorio_repositories(
        building_repo, item_repo, recipe_repo, available_recipes
    )
    debug.dump("avail_buildings", available_buildings)

    prod_map = new_opt_model.ProductionMap.from_repositories(
        available_recipes=available_recipes,
        available_buildings=available_buildings,
        item_repo=item_repo,
        fluid_repo=fluid_repo,
    )
    debug.dump("prod_units", prod_map.production_units)

    # prod_map.add_magic_unit()
    item_constraints = [
        (new_opt_model.Item(name="automation-science-pack", temperature=None), 4/6),
        (new_opt_model.Item(name="logistic-science-pack", temperature=None), 2/6),
        (new_opt_model.Item(name="py-science-pack", temperature=None), 2/6),
        # (new_opt_model.Item(name="Electricity", temperature=None), 770_478_563),
        (new_opt_model.Item(name="Electricity", temperature=None), 63_000_000), # TODO tests
        (new_opt_model.Item(name="big-electric-pole", temperature=None), 1),
        (new_opt_model.Item(name="reo", temperature=None), 1),
        (new_opt_model.Item(name="small-parts-02", temperature=None), 3),
        (new_opt_model.Item(name="electronic-circuit", temperature=None), 2),
        # (new_opt_model.Item(name="aramid", temperature=None), 5),
        # (new_opt_model.Item(name="syngas", temperature=15), -10000000),
        # (new_opt_model.Item(name="ash", temperature=None), -10000000),
    ]
    prod_unit_constraints = [
        (
            next(
                pu for pu in prod_map.production_units if pu.recipe_name == "oil-mk01-0"
            ),
            0,
        ),
        # (
        #     next(
        #         pu
        #         for pu in prod_map.production_units
        #         if pu.recipe_name == "raw-coal-0"
        #         and pu.building_name == "electric-mining-drill"
        #     ),
        #     64,
        # ),
        # *add_mining_constraint(prod_map, "raw-coal", 64+74, 0),
        *add_mining_constraint(prod_map, "raw-coal", 200, 0),  # TODO test
        *add_mining_constraint(prod_map, "coal", 0, 0),
        *add_mining_constraint(prod_map, "copper-ore", 45, 0),
        *add_mining_constraint(prod_map, "ore-lead", 48, 0),
        *add_mining_constraint(prod_map, "ore-titanium", 37, 0), # not enough
        *add_mining_constraint(prod_map, "ore-aluminium", 22, 0),
        *add_mining_constraint(prod_map, "ore-tin", 26, 0), # not enough
        *add_mining_constraint(prod_map, "ore-iron", 125, 0),
        *add_mining_constraint(prod_map, "ore-nickel", 96, 0),
        *add_mining_constraint(prod_map, "ore-zinc", 87, 0),  # need some


        *[(pu, 0) for pu in prod_map.production_units if pu.building_name.startswith("bitumen-seep-mk")],
        *[(pu, 0) for pu in prod_map.production_units if pu.building_name.startswith("natural-gas-seep-mk")],
        *[(pu, 0) for pu in prod_map.production_units if pu.building_name.endswith("-mk02")],
        *[(pu, 0) for pu in prod_map.production_units if pu.building_name == "titanium-mine"],
        *[(pu, 0) for pu in prod_map.production_units if pu.building_name == "aluminium-mine"],
        *[(pu, 0) for pu in prod_map.production_units if pu.building_name == "iron-mine"],
        *[(pu, 3) for pu in prod_map.production_units if pu.building_name == "phosphate-mine"],
        *[(pu, 3) for pu in prod_map.production_units if pu.building_name == "salt-mine"],
        *[(pu, 0) for pu in prod_map.production_units if pu.building_name == "copper-mine"],
        *[(pu, 0) for pu in prod_map.production_units if pu.building_name == "lead-mine"],
        *[(pu, 0) for pu in prod_map.production_units if pu.building_name == "tin-mine"],
        *[(pu, 0) for pu in prod_map.production_units if pu.building_name == "coal-mine"],
        *[(pu, 13) for pu in prod_map.production_units if pu.building_name == "oil-sand-extractor-mk01"],
        # *[(pu, 0) for pu in prod_map.production_units if pu.recipe_name == "coal-1"],
        *[
            (pu, 0)
            for pu in prod_map.production_units
            if pu.recipe_name == "tar-patch-0"
        ],
        *[
            (pu, 0)
            for pu in prod_map.production_units
            if pu.building_name == "natural-gas-seep-mk01"
        ],
    ]
    optim = optimizers.ORToolsOptimizer(
        prod_map, item_constraints, prod_unit_constraints
    )
    result = optim.optimize()
    debug.dump("results", result.production_units)

    graph_begin = optimizers.NetworkXProductionGraph(prod_map)
    graph_begin.write_dot(pathlib.Path("all.dot"))
    graph = optimizers.NetworkXProductionGraph(result)
    graph.write_dot(pathlib.Path("newnew.dot"))
    with open("graphou", "wb") as f:
        pickle.dump(graph.graph, f)


if __name__ == "__main__":
    main()
