import propt.adapters.json_repositories as json_repo
import propt.domain.concepts as concepts
import propt.adapters.optimizers as optimizers
import propt.domain.optimizer as model_opt
import pathlib
import pprint
import pickle


def main():
    pickle_path = pathlib.Path("/tmp/result.pickle")
    if not pickle_path.exists():
        repo_building = json_repo.JSONBuildingRepository(pathlib.Path("pyanodons"))
        repo_item = json_repo.JSONItemRepository(pathlib.Path("pyanodons"), repo_building)
        repo_recipe = json_repo.JSONRecipeRepository(
            repo_item, repo_building, pathlib.Path("pyanodons")
        )
        tech_repo = json_repo.JSONTechnologyRepository(repo_recipe, pathlib.Path("pyanodons"))
        with open("techno.txt", "r") as f:
            technologies = concepts.TechnologySet([tech_repo.by_code(concepts.Code(code.strip())) for code in f.readlines()])
        # technologies = concepts.TechnologySet([tech_repo.by_code("automation")])
        prod_map = model_opt.ProductionMap.from_repositories(repo_recipe, repo_item, technologies)
        prod_map.add_magic_unit()
        constraints = [
            # concepts.Quantity(
            #     item=repo_item.by_code(concepts.Code("automation-science-pack")), qty=0.4
            # ),
            # concepts.Quantity(
            #     item=repo_item.by_code(concepts.Code("logistic-science-pack")), qty=0.33
            # )
            concepts.Quantity(
                item=repo_item.by_code(concepts.Code("rubber")), qty=1
            )
        ]
        print(len(prod_map.production_units))
        optim = optimizers.ORToolsOptimizer(prod_map, constraints)
        result = optim.optimize()
        with open(pickle_path, "wb") as f:
            pickle.dump(result, f)
    else:
        with open(pickle_path, "rb") as f:
            result = pickle.load(f)
    pprint.pprint(result.production_units)
    graph = optimizers.NetworkXProductionGraph(result)
    graph.write_dot(pathlib.Path("tata.dot"))


def debug():
    repo_building = json_repo.JSONBuildingRepository(pathlib.Path("pyanodons"))
    repo_item = json_repo.JSONItemRepository(pathlib.Path("pyanodons"))
    repo_recipe = json_repo.JSONRecipeRepository(
        repo_item, repo_building, pathlib.Path("pyanodons")
    )
    prod_map = model_opt.ProductionMap.from_repositories(repo_recipe)
    pprint.pprint(prod_map)
    return prod_map


if __name__ == "__main__":
    main()
    # debug()

