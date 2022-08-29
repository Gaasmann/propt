"""Implementations of optimization."""
import collections

import propt.domain.optimizer as model_opt
from propt.domain.optimizer import ProductionMap
import propt.domain.concepts as concepts
import itertools
from ortools.linear_solver import pywraplp  # type: ignore


class ORToolsOptimizer(model_opt.Optimizer):
    """Optimizer using Google OR-Tools."""

    def _build_item_index(self) -> dict[concepts.Item, int]:
        item_set = {
            qty.item
            for prod_unit in self._production_map.production_units
            for qty in itertools.chain(
                prod_unit.recipe.ingredients, prod_unit.recipe.products
            )
        }
        return {item: idx for idx, item in enumerate(item_set)}

    def _build_prod_unit_index(self) -> dict[model_opt.ProductionUnit, int]:
        return {
            prod_unit: idx
            for idx, prod_unit in enumerate(self._production_map.production_units)
        }

    def _build_nb_prod_unit_variables(
        self, solver: pywraplp.Solver
    ) -> list[pywraplp.Variable]:
        """Add the nb of prod unit variables to the solver."""
        len_prod_unit = len(self._production_map.production_units)
        infinity = solver.infinity()
        return [
            solver.IntVar(0, infinity, self._production_map.production_units[idx].name)
            for idx in range(len_prod_unit)
        ]

    def _build_constraints(
        self,
        solver: pywraplp.Solver,
        nb_prod_unit_vars: list[pywraplp.Variable],
    ) -> None:
        prod_unit_index = self._build_prod_unit_index()
        # Create the collection item -> qty on constraints
        external_constraints = {qty.item: qty.qty for qty in self._constraints}
        # Create a collection item -> index of prod unit using those
        map_item_prod_unit: dict[concepts.Item, list[int]] = collections.defaultdict(
            list
        )
        for prod_unit in self._production_map.production_units:
            for qty in itertools.chain(
                prod_unit.recipe.ingredients, prod_unit.recipe.products
            ):
                map_item_prod_unit[qty.item].append(prod_unit_index[prod_unit])
        # Create the variables for each item IN ORDER
        for item, prod_unit_indexes in map_item_prod_unit.items():
            lhs_constraints = [
                nb_prod_unit_vars[prod_unit_idx]
                * self._production_map.production_units[
                    prod_unit_idx
                ].get_item_net_quantity_by_unit_of_time(item)
                for prod_unit_idx in prod_unit_indexes
            ]

            solver.Add(sum(lhs_constraints) >= external_constraints.get(item, 0.0))

    def _build_objective(
        self, solver: pywraplp.Solver, nb_prod_unit_vars: list[pywraplp.Variable]
    ):
        """Build the objective function (min nb buildings)."""
        solver.Minimize(sum(nb_prod_unit_vars))

    def optimize(self) -> ProductionMap:
        solver: pywraplp.Solver = pywraplp.Solver.CreateSolver("SCIP")
        nb_prod_unit_vars = self._build_nb_prod_unit_variables(solver)
        self._build_constraints(solver, nb_prod_unit_vars)
        self._build_objective(solver, nb_prod_unit_vars)
        status = solver.Solve()
        if status != pywraplp.Solver.OPTIMAL:
            raise model_opt.SolutionNotFound
        print()
        print("Objective value =", solver.Objective().Value())
        for var in nb_prod_unit_vars:
            print(var.name(), " = ", var.solution_value())
        print()
        print("Problem solved in %f milliseconds" % solver.wall_time())
        print("Problem solved in %d iterations" % solver.iterations())
        print("Problem solved in %d branch-and-bound nodes" % solver.nodes())
        # Build the prod map

        prod_units: list[model_opt.ProductionUnit] = []
        for idx, prod_unit in enumerate(self._production_map.production_units):
            if (qty := int(round(nb_prod_unit_vars[idx].solution_value()))) != 0:
                prod_units.append(
                    model_opt.ProductionUnit(
                        recipe=prod_unit.recipe,
                        building=prod_unit.building,
                        quantity=qty,
                    )
                )
        return model_opt.ProductionMap(production_units=prod_units)
