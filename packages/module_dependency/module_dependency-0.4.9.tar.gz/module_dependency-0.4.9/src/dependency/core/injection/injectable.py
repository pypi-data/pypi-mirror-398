import logging
from typing import Any, Callable, Iterable, Optional
from dependency_injector import containers, providers
from dependency.core.exceptions import InitializationError, CancelInitialization
_logger = logging.getLogger("DependencyLoader")

# TODO: Añadir soporte para más tipos de providers
class Injectable:
    """Injectable Class representing a injectable dependency.
    """
    def __init__(self,
        component_cls: type,
        provided_cls: type,
        provider_cls: type[providers.Provider[Any]] = providers.Singleton,
        imports: Iterable['Injectable'] = (),
        products: Iterable['Injectable'] = (),
        bootstrap: Optional[Callable[[], Any]] = None
    ) -> None:
        self.component_cls: type = component_cls
        self.provided_cls: type = provided_cls
        self.provider_cls: type[providers.Provider[Any]] = provider_cls
        self.modules_cls: set[type] = {component_cls, provided_cls}
        self.imports_gen: Iterable['Injectable'] = imports
        self.products_gen: Iterable['Injectable'] = products
        self.bootstrap: Optional[Callable[[], Any]] = bootstrap

        self._imports: Optional[list['Injectable']] = None
        self._products: Optional[list['Injectable']] = None
        self._provider: Optional[providers.Provider[Any]] = None
        self.is_resolved: bool = False

    @property
    def imports(self) -> list['Injectable']:
        if self._imports is None:
            self._imports = list(self.imports_gen)
        return self._imports

    @property
    def products(self) -> list['Injectable']:
        if self._products is None:
            self._products = list(self.products_gen)
        return self._products

    @property
    def import_resolved(self) -> bool:
        return all(
            implementation.is_resolved
            for implementation in self.imports
        )

    @property
    def provider(self) -> providers.Provider[Any]:
        """Return an instance from the provider."""
        if self._provider is None:
            self._provider = self.provider_cls(self.provided_cls) # type: ignore
        return self._provider

    def do_wiring(self, container: containers.DynamicContainer) -> "Injectable":
        """Wire the provider with the given container.

        Args:
            container (containers.DynamicContainer): Container to wire the provider with.

        Returns:
            Injectable: The current injectable instance.
        """
        container.wire(
            modules=self.modules_cls,
            warn_unresolved=True
        )
        self.is_resolved = True
        return self

    def do_bootstrap(self) -> None:
        """Execute the bootstrap function if it exists."""
        if not self.is_resolved:
            raise InitializationError(f"Component {self.component_cls.__name__} cannot be initialized before being resolved.")
        if self.bootstrap is not None:
            try:
                self.bootstrap()
            except CancelInitialization:
                _logger.warning(f"Initialization of Component {self.component_cls.__name__} was cancelled.")
            except Exception as e:
                raise InitializationError(f"Failed to initialize Component {self.component_cls.__name__}") from e

    def __repr__(self) -> str:
        return f"{self.provided_cls.__name__}"
