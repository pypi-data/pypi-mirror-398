from abc import abstractmethod
from typing import Any, Callable, TypeVar
from dependency_injector import providers
from dependency.core.agrupation.module import Module
from dependency.core.declaration.base import ABCComponent
from dependency.core.injection.provider import ProviderInjection
from dependency.core.exceptions import DeclarationError

COMPONENT = TypeVar('COMPONENT', bound='Component')
INTERFACE = TypeVar('INTERFACE')

class Component(ABCComponent):
    """Component Base Class
    """
    def __init__(self,
        interface_cls: type[INTERFACE],
        injection: ProviderInjection,
    ) -> None:
        super().__init__(interface_cls=interface_cls)
        self.injection: ProviderInjection = injection

    def reference(self) -> str:
        """Return the reference name of the component."""
        return self.injection.reference

    @property
    @abstractmethod
    def provider(self) -> providers.Provider[Any]:
        """Provide the provider instance"""
        pass

    @abstractmethod
    def provide(self, **kwargs: Any) -> Any:
        """Provide an instance of the interface class"""
        pass

def component(
    module: Module,
    interface: type[INTERFACE],
) -> Callable[[type[COMPONENT]], COMPONENT]:
    """Decorator for Component class

    Args:
        module (Module): Module instance to register the component.
        interface (type[T]): Interface class to be used as a base class for the component.

    Raises:
        TypeError: If the wrapped class is not a subclass of Component.

    Returns:
        Callable[[type[COMPONENT]], COMPONENT]: Decorator function that wraps the component class.
    """
    def wrap(cls: type[COMPONENT]) -> COMPONENT:
        if not issubclass(cls, Component):
            raise TypeError(f"Class {cls} is not a subclass of Component")

        injection = ProviderInjection(
            name=cls.__name__,
            parent=module.injection,
        )

        class WrapComponent(cls): # type: ignore
            @property
            def provider(self) -> providers.Provider[Any]:
                if not self.injection.injectable.is_resolved:
                    raise DeclarationError(f"Component {cls.__name__} injectable was not resolved")
                return self.injection.injectable.provider # type: ignore

            def provide(self, **kwargs: Any) -> INTERFACE:
                if not self.injection.injectable.is_resolved:
                    raise DeclarationError(f"Component {cls.__name__} injectable was not resolved")
                return self.injection.injectable.provider(**kwargs) # type: ignore

            #@inject
            #def provide(self, service: INTERFACE = injection.provider) -> INTERFACE:
            #    if not injection.injectable.is_resolved:
            #        raise DeclarationError(f"Component {cls.__name__} injectable was not resolved")
            #    return service

        return WrapComponent(
            interface_cls=interface,
            injection=injection,
        )
    return wrap
