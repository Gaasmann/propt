"""Implementations of optimization."""
import collections
import itertools
import pathlib

import networkx as nx  # type: ignore
from networkx.drawing.nx_agraph import write_dot  # type: ignore
from ortools.linear_solver import pywraplp  # type: ignore

import propt.domain.optimizer.model as model_opt


class ORToolsOptimizer(model_opt.Optimizer):
    """Optimizer using Google OR-Tools."""

    def _build_item_index(self) -> dict[model_opt.Item, int]:
        item_set = {
            item
            for prod_unit in self._production_map.production_units
            for item in itertools.chain(
                prod_unit.ingredients.keys(), prod_unit.products.keys()
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
            # solver.IntVar(0, infinity, self._production_map.production_units[idx].name)
            solver.NumVar(0, infinity, self._production_map.production_units[idx].name)
            for idx in range(len_prod_unit)
        ]

    def _build_constraints(
        self,
        solver: pywraplp.Solver,
        nb_prod_unit_vars: list[pywraplp.Variable],
    ) -> list[pywraplp.Constraint]:
        prod_unit_index = self._build_prod_unit_index()
        # Create the collection item -> qty on constraints
        external_constraints = dict(self._item_constraints)
        # Create a collection item -> index of prod unit using those
        map_item_prod_unit: dict[model_opt.Item, list[int]] = collections.defaultdict(
            list
        )
        for prod_unit in self._production_map.production_units:
            for item in itertools.chain(
                prod_unit.ingredients.keys(), prod_unit.products.keys()
            ):
                map_item_prod_unit[item].append(prod_unit_index[prod_unit])
        # Create the variables for each item IN ORDER
        constraints: list[pywraplp.Constraint] = []
        for item, prod_unit_indexes in map_item_prod_unit.items():
            lhs_constraints = [
                nb_prod_unit_vars[prod_unit_idx]
                * self._production_map.production_units[
                    prod_unit_idx
                ].get_item_net_quantity_by_unit_of_time(item)
                for prod_unit_idx in prod_unit_indexes
            ]
            min_items = external_constraints.get(item, 0.0)
            if min_items == 0.0:
                constraint = solver.Add(sum(lhs_constraints) >= min_items, name=f"{item.name}-{item.temperature}")
                #constraint = solver.Add(sum(lhs_constraints) == min_items, name=f"{item.name}-{item.temperature}")
            else:  # Target constraints
                constraint = solver.Add(sum(lhs_constraints) >= min_items, name=item.name)
            constraints.append(constraint)
            if min_items == 0.0:
                constraint.set_is_lazy(True)
        # prod_unit_constraints
        for prod_unit_constraint in self._prod_unit_constraints:
            constraint = solver.Add(
                nb_prod_unit_vars[prod_unit_index[prod_unit_constraint[0]]]
                <= prod_unit_constraint[1],
                name=f"{prod_unit_constraint[0].name}-chier",
            )
            constraints.append(constraint)
        return constraints

    def _build_objective(
        self, solver: pywraplp.Solver, nb_prod_unit_vars: list[pywraplp.Variable]
    ):
        """Build the objective function (min nb buildings)."""
        solver.Minimize(sum(nb_prod_unit_vars))

    def optimize(self) -> model_opt.ProductionMap:
        # solver: pywraplp.Solver = pywraplp.Solver.CreateSolver("GLOP")
        # solver.SetSolverSpecificParametersAsString("display/verblevel=5")
        # solver.SetSolverSpecificParametersAsString("display/lpiterations/active=2")
        # solver.SetSolverSpecificParametersAsString("display/lpinfo=TRUE")
        solver: pywraplp.Solver = pywraplp.Solver.CreateSolver("CLP")
        solver.EnableOutput()
        solver.SetNumThreads(3)
        # solver
        # solver.set_time_limit(1*60*1000)
        nb_prod_unit_vars = self._build_nb_prod_unit_variables(solver)
        constraints = self._build_constraints(solver, nb_prod_unit_vars)
        self._build_objective(solver, nb_prod_unit_vars)
        print("Ready to solve")
        print(type(solver))
        print(f"Number of variables: {len(solver.variables())}")
        print(f"Number of constraints: {len(solver.constraints())}")
        # solver.
        status = solver.Solve()
        if status != pywraplp.Solver.OPTIMAL:
            raise model_opt.SolutionNotFound
        print()
        print("Objective value =", solver.Objective().Value())
        # for var in nb_prod_unit_vars:
        #     print(var.name(), " = ", var.solution_value())
        # for constraint in constraints:
        #     print(constraint.name(), " = ", constraint.dual_value())
        print()
        print("Problem solved in %f milliseconds" % solver.wall_time())
        print("Problem solved in %d iterations" % solver.iterations())
        print("Problem solved in %d branch-and-bound nodes" % solver.nodes())
        # Build the prod map

        prod_units: list[model_opt.ProductionUnit] = []
        for idx, prod_unit in enumerate(self._production_map.production_units):
            if (qty := nb_prod_unit_vars[idx].solution_value()) > 0.00001:
                prod_units.append(
                    model_opt.ProductionUnit(
                        recipe_name=prod_unit.recipe_name,
                        building_name=prod_unit.building_name,
                        ingredients=prod_unit.ingredients,
                        products=prod_unit.products,
                        quantity=qty,
                    )
                )
        return model_opt.ProductionMap(production_units=prod_units)


class NetworkXProductionGraph:
    """A production graph."""

    def __init__(self, production_map: model_opt.ProductionMap):
        self.production_map = production_map
        self.graph = self._build_graph()

    @staticmethod
    def _item_node_name(item: model_opt.Item) -> str:
        return f"item\n{item.name}{f'-{item.temperature}' if item.temperature else ''}"

    def _build_graph(self) -> nx.DiGraph:
        g = nx.DiGraph(splines="false")
        g.add_nodes_from(
            (self._item_node_name(item) for item in self.production_map.items),
            node_type="item"
        )
        for prod_unit in self.production_map.production_units:
            pu_node = f"Prod unit\n{prod_unit.name}\nqty {prod_unit.quantity}"
            g.add_node(pu_node, node_type="pu")
            for ingredient in prod_unit.ingredients.keys():
                if ingredient in (
                        model_opt.Item(name="Electricity"),
                        model_opt.Item(name="drill-head"),
                        model_opt.Item(name="water", temperature=15),
                        model_opt.Item(name="pressured-air", temperature=15),
                ):
                    continue  # skipping ubiquitous items
                qty = -prod_unit.get_item_consumed_quantity_by_unit_of_time(ingredient)*prod_unit.quantity
                g.add_edge(self._item_node_name(ingredient), pu_node, headlabel=f"{self._item_node_name(ingredient)[5:]}\n{qty:.3f}")
            for product in prod_unit.products:

                qty = prod_unit.get_item_produced_quantity_by_unit_of_time(product)*prod_unit.quantity
                g.add_edge(pu_node, self._item_node_name(product), taillabel=f"{self._item_node_name(product)[5:]}\n{qty:.3f}")
        return g

    def write_dot(self, filepath: pathlib.Path) -> None:
        write_dot(self.graph, filepath)


