from dependency.core.injection.injectable import Injectable as Injectable
from dependency.core.resolution.container import Container as Container
from dependency.core.resolution.errors import raise_resolution_error as raise_resolution_error

class InjectionResolver:
    """Injection Resolver Class
    """
    container: Container
    injectables: list[Injectable]
    def __init__(self, container: Container, injectables: list[Injectable]) -> None: ...
    def resolve_dependencies(self) -> None:
        """Resolve all dependencies and initialize them."""
    def resolve_injectables(self) -> list[list[Injectable]]:
        """Resolve all injectables in layers."""
    def start_injectables(self, resolved_layers: list[list[Injectable]]) -> None:
        """Start all implementations by executing their bootstrap functions."""
