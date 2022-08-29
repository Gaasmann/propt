"""Test Optimizer implementation."""

import propt.adapters.optimizers as opt_impl
import propt.domain.optimizer as model_opt
import propt.domain.concepts as concepts


def test_google_optimizer(repositories):
    """Test the Google OR-tools optimizer."""
    production_map = model_opt.ProductionMap.from_repositories(
        repositories[concepts.Recipe]
    )
    plates = concepts.Quantity(
        item=repositories[concepts.Item].by_code(concepts.Code("plate")), qty=50
    )
    optimizer = opt_impl.ORToolsOptimizer(production_map, [plates])
    prod_map = optimizer.optimize()
    print(prod_map.production_units)
