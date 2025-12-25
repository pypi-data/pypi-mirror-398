from typing import Any, Callable
from dependency_injector import providers
from dependency.core.declaration.base import ABCInstance
from dependency.core.declaration.component import Component
from dependency.core.declaration.product import Product
from dependency.core.injection.injectable import Injectable

class Instance(ABCInstance):
    """Instance Base Class
    """
    def __init__(self,
        provided_cls: type,
    ) -> None:
        super().__init__(provided_cls=provided_cls)

def instance(
    component: Component,
    imports: list[Component] = [],
    products: list[Product] = [],
    provider: type[providers.Provider[Any]] = providers.Singleton,
    bootstrap: bool = False,
) -> Callable[[type], Instance]:
    """Decorator for instance class

    Args:
        component (Component): Component class to be used as a base class for the provider.
        imports (list[Component], optional): List of components to be imported by the provider. Defaults to [].
        products (list[type], optional): List of products to be declared by the provider. Defaults to [].
        provider (type[providers.Provider[Any]], optional): Provider class to be used. Defaults to providers.Singleton.
        bootstrap (bool, optional): Whether the provider should be bootstrapped. Defaults to False.

    Raises:
        TypeError: If the wrapped class is not a subclass of Component declared base class.

    Returns:
        Callable[[type], Instance]: Decorator function that wraps the instance class and returns an Instance object.
    """
    def wrap(cls: type) -> Instance:
        if not issubclass(cls, component.interface_cls):
            raise TypeError(f"Class {cls} is not a subclass of {component.interface_cls}")

        component.injection.set_instance(
            injectable = Injectable(
                component_cls=component.__class__,
                provided_cls=cls,
                provider_cls=provider,
                imports=(
                    component.injection.injectable
                    for component in imports
                ),
                products=(
                    product.injectable
                    for product in products
                ),
                bootstrap=component.provide if bootstrap else None,
            )
        )

        return Instance(
            provided_cls=cls
        )
    return wrap
