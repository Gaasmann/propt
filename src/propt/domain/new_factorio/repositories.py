"""The repositories for the prototypes."""
import abc
from typing import TypeVar

import propt.domain.new_factorio.prototypes as prototypes

T = TypeVar("T", bound=prototypes.Prototype)


class Repository(dict[str, T], metaclass=abc.ABCMeta):
    """An abstract Factorio repository."""


class ItemRepository(Repository[prototypes.Item]):
    """Get Items."""


class FluidRepository(Repository[prototypes.Fluid]):
    """Get Fluids."""


class BuildingRepository(Repository[prototypes.Building]):
    """Get buildings."""


class RecipeRepository(Repository[prototypes.Recipe]):
    """Get Recipes."""
    @abc.abstractmethod
    def get_recipes_making_stuff(
            self, stuff: prototypes.Object
    ) -> set[prototypes.Recipe]:
        """Return the recipe that can make a given stuff."""


class TechnologyRepository(Repository[prototypes.Technology]):
    """A repository for factorio technologies."""
