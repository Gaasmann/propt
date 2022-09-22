import pathlib
import pprint

import more_itertools

import propt.adapters.new_factorio_repositories.json as factorio_repos
import propt.adapters.optimizers as optimizers
import propt.data.pyanodons as factorio_data
import propt.domain.factorio
import propt.domain.optimizer.model as model_opt
import propt.domain.optimizer.service as opt_service
from propt.adapters.new_factorio_repositories.json import buildings as json_buildings

import propt.domain.new_optimizer.model as new_opt_model
import propt.adapters.new_optimizers as new_optimizers
import propt.adapters.new_factorio_repositories.json.objects as obj_repos
import propt.adapters.new_factorio_repositories.json.recipes as recipe_repos
import propt.adapters.new_factorio_repositories.json.buildings as building_repos
import propt.adapters.new_factorio_repositories.json.technologies as tech_repos
import propt.domain.new_factorio.prototypes as prototypes


def main():
    data_path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    furnace_repository = factorio_repos.JSONFactorioFurnaceRepository(data_path)
    rocket_silo_repository = factorio_repos.JSONFactorioRocketSiloRepository(data_path)
    mining_drill_repository = factorio_repos.JSONFactorioMiningDrillRepository(
        data_path
    )
    print("pick")
    assmac_repo = factorio_repos.JSONFactorioAssemblingMachineRepository(data_path)
    print("pick")
    item_repo = factorio_repos.JSONFactorioItemRepository(
        data_path,
        assmac_repo,
        furnace_repository,
        rocket_silo_repository,
        mining_drill_repository,
    )
    print("pick")
    fluid_repo = factorio_repos.JSONFactorioFluidRepository(data_path)
    print("pick")
    recipe_repo = factorio_repos.JSONFactorioRecipeRepository(
        data_path, item_repo, fluid_repo
    )
    print("pick")
    tech_repo = factorio_repos.JSONFactorioTechnologyRepository(data_path, recipe_repo)
    print("pick")
    resource_repository = factorio_repos.JSONFactorioResourceRepository(
        data_path, item_repo, fluid_repo
    )
    boiler_repository = factorio_repos.JSONFactorioBoilerRepository(data_path)
    with open("techno.txt", "r") as f:
        technologies = propt.domain.factorio.TechnologySet(
            tech_repo[code.strip()] for code in f.readlines()
        )
    print("tech")
    # technologies = concepts.TechnologySet([tech_repo.by_code("automation")])
    recipes = opt_service.convert_factorio_recipes(
        factorio_recipes=recipe_repo,
        resource_repository=resource_repository,
        boiler_repository=boiler_repository,
        available_techologies=technologies,
    )
    s = pprint.pformat(recipes)
    with open("blah.txt", "w") as f:
        f.write(s)
    # return
    prod_map = model_opt.ProductionMap.from_repositories(
        available_recipes=recipes,
        recipe_repository=recipe_repo,
        item_repository=item_repo,
        assembly_machine_repository=assmac_repo,
        furnace_repository=furnace_repository,
        rocket_silo_repository=rocket_silo_repository,
        mining_drill_repository=mining_drill_repository,
        boiler_repository=boiler_repository,
    )
    print("prodmap")
    # prod_map.add_magic_unit()
    print("magic")
    item_constraints = [
        # model_opt.Amount(
        #     item=model_opt.Item.from_factorio_item_or_fluid(item_repo["automation-science-pack"]), qty=1
        # )
        # model_opt.Amount(
        #     item=model_opt.Item.from_factorio_item_or_fluid(item_repo["logistic-science-pack"]), qty=1
        # )
        model_opt.Amount(
            item=model_opt.Item.from_factorio_item_or_fluid(
                item_repo["logistic-science-pack"], temperature=None
            ),
            qty=1.0,
        ),
        # model_opt.Amount(
        #     item=model_opt.Item.from_factorio_item_or_fluid(item_repo["retrovirus"], temperature=None), qty=-35000
        # )
    ]
    prod_unit_constraints = [
        # (
        #     model_opt.ProductionUnit(
        #         recipe=model_opt.Recipe.from_factorio_resource(
        #             resource_repository["coal"]
        #         ),
        #         building=model_opt.Building.from_factorio_mining_drill(
        #             mining_drill_repository["electric-mining-drill"]
        #         ),
        #     ),
        #     0,
        # ),
        # (
        #     model_opt.ProductionUnit(
        #         recipe=model_opt.Recipe.from_factorio_resource(
        #             resource_repository["salt-rock"]
        #         ),
        #         building=model_opt.Building.from_factorio_mining_drill(
        #             mining_drill_repository["salt-mine"]
        #         ),
        #     ),
        #     0,
        # )
    ]
    blah = model_opt.ProductionUnit(
        recipe=model_opt.Recipe.from_factorio_resource(
            resource_repository["ore-quartz"]
        ),
        building=model_opt.Building.from_factorio_mining_drill(
            mining_drill_repository["borax-mine"]
        ),
    )
    print(
        f"TUTUTUTU: {blah.get_item_net_quantity_by_unit_of_time(model_opt.Item(name='ore-quartz', type='item'))}"
    )
    print("constraints")
    print(len(prod_map.production_units))
    optim = optimizers.ORToolsOptimizer(
        prod_map, item_constraints, prod_unit_constraints
    )
    print("optimizer built")
    result = optim.optimize()
    print("solved!")

    pprint.pprint(result.production_units)
    graph_begin = optimizers.NetworkXProductionGraph(prod_map)
    graph_begin.write_dot(pathlib.Path("all.dot"))
    graph = optimizers.NetworkXProductionGraph(result)
    graph.write_dot(pathlib.Path("newnew.dot"))


def debug():
    data_path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    assmat = json_buildings.JSONFactorioAssemblingMachineRepository(data_path)
    furnace = json_buildings.JSONFactorioFurnaceRepository(data_path)
    agg = json_buildings.JSONFactorioAggregateBuildingRepository((assmat, furnace))
    print(agg["kicalk-plantation-mk01"], agg["stone-furnace"])
    # return prod_map


def new_main():
    data_path = pathlib.Path(more_itertools.first(factorio_data.__path__))
    # buildings
    building_repo = building_repos.JSONFactorioAggregateBuildingRepository(
        (
            building_repos.JSONFactorioAssemblingMachineRepository(data_path),
            building_repos.JSONFactorioFurnaceRepository(data_path),
            building_repos.JSONFactorioMiningDrillRepository(data_path),
            building_repos.JSONFactorioRocketSiloRepository(data_path),
            # building_repos.JSONFactorioSolarPanelRepository(data_path),
            # building_repos.JSONFactorioReactorRepository(data_path),
            # building_repos.JSONFactorioGeneratorRepository(data_path),
            building_repos.JSONFactorioBoilerBuildingRepository(data_path),
        )
    )

    item_repo = obj_repos.JSONFactorioItemRepository(data_path, building_repo)
    fluid_repo = obj_repos.JSONFactorioFluidRepository(data_path)
    recipe_repo = recipe_repos.JSONFactorioAggregateRecipeRepository(
        (
            recipe_repos.JSONFactorioRecipeRepository(data_path, item_repo, fluid_repo),
            recipe_repos.JSONFactorioResourceRepository(
                data_path, item_repo, fluid_repo
            ),
            recipe_repos.JSONFactorioBoilerRecipeRepository(data_path, fluid_repo),
        )
    )
    tech_repo = tech_repos.JSONFactorioTechnologyRepository(data_path, recipe_repo)

    with open("techno.txt", "r") as f:
        technologies = prototypes.TechnologySet(
            tech_repo[code.strip()] for code in f.readlines()
        )
    print("tech")
    # technologies = concepts.TechnologySet([tech_repo.by_code("automation")])
    # return
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

    s = pprint.pformat(prod_map.production_units)
    with open("blah.txt", "w") as f:
        f.write(s)

    print("prodmap")
    # prod_map.add_magic_unit()
    print("magic")
    item_constraints = [
        # model_opt.Amount(
        #     item=model_opt.Item.from_factorio_item_or_fluid(item_repo["automation-science-pack"]), qty=1
        # )
        # model_opt.Amount(
        #     item=model_opt.Item.from_factorio_item_or_fluid(item_repo["logistic-science-pack"]), qty=1
        # )
        (new_opt_model.Item(name="logistic-science-pack", temperature=None), 10),
        # model_opt.Amount(
        #     item=model_opt.Item.from_factorio_item_or_fluid(item_repo["retrovirus"], temperature=None), qty=-35000
        # )
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
    # blah = model_opt.ProductionUnit(
    #     recipe=model_opt.Recipe.from_factorio_resource(
    #         resource_repository["ore-quartz"]
    #     ),
    #     building=model_opt.Building.from_factorio_mining_drill(
    #         mining_drill_repository["borax-mine"]
    #     ),
    # )
    # print(
    #     f"TUTUTUTU: {blah.get_item_net_quantity_by_unit_of_time(model_opt.Item(name='ore-quartz', type='item'))}"
    # )
    print("constraints")
    print(len(prod_map.production_units))
    optim = new_optimizers.ORToolsOptimizer(
        prod_map, item_constraints, prod_unit_constraints
    )
    print("optimizer built")
    result = optim.optimize()
    print("solved!")

    pprint.pprint(result.production_units)
    graph_begin = new_optimizers.NetworkXProductionGraph(prod_map)
    graph_begin.write_dot(pathlib.Path("all.dot"))
    graph = new_optimizers.NetworkXProductionGraph(result)
    graph.write_dot(pathlib.Path("newnew.dot"))


if __name__ == "__main__":
    new_main()
    # main()
    # debug()
