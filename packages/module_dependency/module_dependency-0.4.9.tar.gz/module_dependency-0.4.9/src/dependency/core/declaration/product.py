from typing import Any, Callable, TypeVar
from dependency_injector import providers
from dependency.core.declaration.component import Component
from dependency.core.injection.injectable import Injectable

PRODUCT = TypeVar('PRODUCT', bound='Product')

class Product:
    """Product Base Class
    """
    injectable: Injectable

def product(
    imports: list[Component] = [],
    products: list[Product] = [],
    provider: type[providers.Provider[Any]] = providers.Singleton,
) -> Callable[[type[PRODUCT]], type[PRODUCT]]:
    """Decorator for Product class

    Args:
        imports (Sequence[type[Component]], optional): List of components to be imported by the product. Defaults to [].

    Raises:
        TypeError: If the wrapped class is not a subclass of Dependent.

    Returns:
        Callable[[type[Dependent]], type[Dependent]]: Decorator function that wraps the dependent class.
    """
    def wrap(cls: type[PRODUCT]) -> type[PRODUCT]:
        if not issubclass(cls, Product):
            raise TypeError(f"Class {cls} is not a subclass of Product")

        cls.injectable = Injectable(
            component_cls=cls,
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
        )
        return cls
    return wrap
