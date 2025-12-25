from dependency.core.exceptions import DeclarationError as DeclarationError
from dependency.core.injection.base import BaseInjection as BaseInjection, ContainerInjection as ContainerInjection
from dependency.core.injection.injectable import Injectable as Injectable
from dependency.core.injection.utils import LazyProvide as LazyProvide
from dependency_injector import providers as providers
from typing import Any, Generator, override

class ProviderInjection(BaseInjection):
    """Provider Injection Class
    """
    def __init__(self, name: str, parent: ContainerInjection | None = None) -> None: ...
    @property
    def provider(self) -> providers.Provider[Any]:
        """Return the provider instance."""
    @property
    def injectable(self) -> Injectable:
        """Return the injectable instance."""
    def set_instance(self, injectable: Injectable) -> None:
        """Set the injectable instance and its imports."""
    @override
    def inject_cls(self) -> providers.Provider[Any]:
        """Return the provider instance."""
    @override
    def resolve_providers(self) -> Generator[Injectable, None, None]:
        """Inject all imports into the current injectable."""
