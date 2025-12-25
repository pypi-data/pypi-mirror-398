import logging
from pprint import pformat
from dependency.core.injection.injectable import Injectable
from dependency.core.resolution.container import Container
from dependency.core.resolution.errors import raise_resolution_error
_logger = logging.getLogger("DependencyLoader")

# TODO: Separar los pasos de inicialización
# TODO: añadir API meta con acceso al framework
class InjectionResolver:
    """Injection Resolver Class
    """
    def __init__(self,
        container: Container,
        injectables: list[Injectable],
    ) -> None:
        self.container: Container = container
        self.injectables: list[Injectable] = injectables

    def resolve_dependencies(self) -> None:
        """Resolve all dependencies and initialize them."""
        providers = self.resolve_injectables()
        self.start_injectables(resolved_layers=providers)
        _logger.info("Dependencies resolved and initialized")

    def resolve_injectables(self,
    ) -> list[list[Injectable]]:
        """Resolve all injectables in layers."""
        unresolved: list[Injectable] = self.injectables
        resolved_layers: list[list[Injectable]] = []

        while unresolved:
            new_layer = [
                injectable.do_wiring(container=self.container)
                for injectable in unresolved
                if injectable.import_resolved
            ]

            if len(new_layer) == 0:
                raise_resolution_error(
                    injectables=self.injectables,
                    unresolved=unresolved
                )
            resolved_layers.append(new_layer)

            for resolved in new_layer:
                unresolved.extend(resolved.products)

            unresolved = [
                injectable
                for injectable in unresolved
                if not injectable.is_resolved
            ]
        named_layers = pformat(resolved_layers)
        _logger.info(f"Resolved layers:\n{named_layers}")
        return resolved_layers

    def start_injectables(self,
        resolved_layers: list[list[Injectable]],
    ) -> None:
        """Start all implementations by executing their bootstrap functions."""
        self.container.check_dependencies()
        self.container.init_resources()
        for layer in resolved_layers:
            for implementation in layer:
                implementation.do_bootstrap()
