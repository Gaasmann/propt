import pathlib
import pprint

import more_itertools

import propt.adapters.factorio_repositories.json as factorio_repos
import propt.adapters.optimizers as optimizers
import propt.data.pyanodons as factorio_data
import propt.domain.factorio
import propt.domain.optimizer as model_opt


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
    prod_map = model_opt.ProductionMap.from_repositories(
        recipe_repository=recipe_repo,
        item_repository=item_repo,
        assembly_machine_repository=assmac_repo,
        furnace_repository=furnace_repository,
        rocket_silo_repository=rocket_silo_repository,
        resource_repository=resource_repository,
        mining_drill_repository=mining_drill_repository,
        boiler_repository=boiler_repository,
        technology_set=technologies,
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
            item=model_opt.Item.from_factorio_item_or_fluid(item_repo["cdna"]), qty=1
        ),
        # model_opt.Amount(
        #     item=model_opt.Item.from_factorio_item_or_fluid(item_repo["retrovirus"]), qty=-35000
        # )
    ]
    prod_unit_constraints = [
        (
            model_opt.ProductionUnit(
                recipe=model_opt.Recipe.from_factorio_resource(
                    resource_repository["coal"]
                ),
                building=model_opt.Building.from_factorio_mining_drill(
                    mining_drill_repository["electric-mining-drill"]
                ),
            ),
            0,
        ),
        (
            model_opt.ProductionUnit(
                recipe=model_opt.Recipe.from_factorio_resource(
                    resource_repository["salt-rock"]
                ),
                building=model_opt.Building.from_factorio_mining_drill(
                    mining_drill_repository["salt-mine"]
                ),
            ),
            0,
        )
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


# def debug():
#     repo_building = json_repo.JSONBuildingRepository(pathlib.Path("pyanodons"))
#     repo_item = json_repo.JSONItemRepository(pathlib.Path("pyanodons"))
#     repo_recipe = json_repo.JSONRecipeRepository(
#         repo_item, repo_building, pathlib.Path("pyanodons")
#     )
#     prod_map = model_opt.ProductionMap.from_repositories(repo_recipe)
#     pprint.pprint(prod_map)
#     return prod_map


if __name__ == "__main__":
    main()
    # debug()
