import abc
from abc import abstractmethod
from dependency.core.agrupation.module import Module as Module
from dependency.core.declaration.base import ABCComponent as ABCComponent
from dependency.core.exceptions import DeclarationError as DeclarationError
from dependency.core.injection.provider import ProviderInjection as ProviderInjection
from dependency_injector import providers as providers
from typing import Any, Callable, TypeVar

COMPONENT = TypeVar('COMPONENT', bound='Component')
INTERFACE = TypeVar('INTERFACE')

class Component(ABCComponent, metaclass=abc.ABCMeta):
    """Component Base Class
    """
    injection: ProviderInjection
    def __init__(self, interface_cls: type[INTERFACE], injection: ProviderInjection) -> None: ...
    def reference(self) -> str:
        """Return the reference name of the component."""
    @property
    @abstractmethod
    def provider(self) -> providers.Provider[Any]:
        """Provide the provider instance"""
    @abstractmethod
    def provide(self, **kwargs: Any) -> Any:
        """Provide an instance of the interface class"""

def component(module: Module, interface: type[INTERFACE]) -> Callable[[type[COMPONENT]], COMPONENT]:
    """Decorator for Component class

    Args:
        module (Module): Module instance to register the component.
        interface (type[T]): Interface class to be used as a base class for the component.

    Raises:
        TypeError: If the wrapped class is not a subclass of Component.

    Returns:
        Callable[[type[COMPONENT]], COMPONENT]: Decorator function that wraps the component class.
    """
