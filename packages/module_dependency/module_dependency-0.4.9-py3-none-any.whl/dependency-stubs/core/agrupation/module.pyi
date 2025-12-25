from dependency.core.agrupation.base import ABCModule as ABCModule
from dependency.core.injection.base import ContainerInjection as ContainerInjection
from dependency.core.injection.injectable import Injectable as Injectable
from dependency.core.resolution.container import Container as Container
from typing import Callable, TypeVar

MODULE = TypeVar('MODULE', bound='Module')

class Module(ABCModule):
    """Module Base Class
    """
    injection: ContainerInjection
    def __init__(self, name: str, injection: ContainerInjection) -> None: ...
    def resolve_providers(self, container: Container) -> list[Injectable]:
        """Resolve provider injections for the plugin.

        Args:
            container (Container): The application container.

        Returns:
            list[Injectable]: A list of injectable providers.
        """

def module(module: Module | None = None) -> Callable[[type[MODULE]], MODULE]:
    """Decorator for Module class

    Args:
        module (Optional[Module]): Parent module class which this module belongs to.

    Raises:
        TypeError: If the wrapped class is not a subclass of Module.

    Returns:
        Callable[[type[MODULE]], MODULE]: Decorator function that wraps the module class.
    """
