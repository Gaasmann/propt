# """General conftest."""
# import pathlib
# from typing import Type
#
# import more_itertools
# import pytest
# import propt.data.pyanodons as factorio_data
# import propt.domain.factorio as factorio_model
# import propt.adapters.factorio_repositories.json as repos
#
# @pytest.fixture
# def resource_file() -> str:
#     return "testdata.yaml"
#
#
# @pytest.fixture
# def repositories(
#     resource_file,
# ) -> dict[Type[factorio_model.FactorioObject], factorio_model.FactorioRepository]:
#     path = pathlib.Path(more_itertools.first(factorio_data.__path__))
#     assmac_repo = repos.JSONFactorioAssemblingMachineRepository(path)
#     furnace_repo = repos.JSONFactorioFurnaceRepository(path)
#     rocket_silo_repo = repos.JSONFactorioRocketSiloRepository(path)
#     mining_drill_repo = repos.JSONFactorioMiningDrillRepository(path)
#     item_repo = repos.JSONFactorioItemRepository(path, assmac_repo, furnace_repo, rocket_silo_repo, mining_drill_repo)
#     fluid_repo = repos.JSONFactorioFluidRepository(path)
#     recipe_repo = repos.JSONFactorioRecipeRepository(path,item_repo, fluid_repo)
#     resource_repo = repos.JSONFactorioResourceRepository(path, item_repo, fluid_repo)
#     return {
#         factorio_model.FactorioAssemblingMachine: assmac_repo,
#         factorio_model.FactorioFurnace: furnace_repo,
#         factorio_model.FactorioRocketSilo: rocket_silo_repo,
#         factorio_model.FactorioMiningDrill: mining_drill_repo,
#         factorio_model.FactorioItem: item_repo,
#         factorio_model.FactorioFluid: fluid_repo,
#         factorio_model.FactorioRecipe: recipe_repo,
#         factorio_model.FactorioResource: resource_repo
#     }
