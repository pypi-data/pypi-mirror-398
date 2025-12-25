import logging
from typing import Any, Generator, Optional, override
from dependency_injector import providers
from dependency.core.injection.base import BaseInjection, ContainerInjection
from dependency.core.injection.injectable import Injectable
from dependency.core.injection.utils import LazyProvide
from dependency.core.exceptions import DeclarationError
_logger = logging.getLogger("DependencyLoader")

class ProviderInjection(BaseInjection):
    """Provider Injection Class
    """
    def __init__(self,
        name: str,
        parent: Optional['ContainerInjection'] = None
    ) -> None:
        super().__init__(name=name, parent=parent)
        self.__injectable: Optional[Injectable] = None

    @property
    def provider(self) -> providers.Provider[Any]:
        """Return the provider instance."""
        return LazyProvide(lambda: self.reference)

    @property
    def injectable(self) -> Injectable:
        """Return the injectable instance."""
        if not self.__injectable:
            raise DeclarationError(f"Implementation for Component {self.name} was not set")
        return self.__injectable

    def set_instance(self,
        injectable: Injectable,
    ) -> None:
        """Set the injectable instance and its imports."""
        _logger.debug(f"Component {self.name} implementation set: {injectable.provided_cls.__name__}")
        self.__injectable = injectable
        if self.parent:
            self.parent.childs.add(self)

    @override
    def inject_cls(self) -> providers.Provider[Any]:
        """Return the provider instance."""
        return self.injectable.provider

    @override
    def resolve_providers(self) -> Generator[Injectable, None, None]:
        """Inject all imports into the current injectable."""
        _logger.debug(f"Component {self.name} added to the injection context")
        yield self.injectable
