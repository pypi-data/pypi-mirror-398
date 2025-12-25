from dependency.core.declaration.component import Component as Component
from dependency.core.injection.injectable import Injectable as Injectable
from dependency_injector import providers
from typing import Any, Callable, TypeVar

PRODUCT = TypeVar('PRODUCT', bound='Product')

class Product:
    """Product Base Class
    """
    injectable: Injectable

def product(imports: list[Component] = [], products: list[Product] = [], provider: type[providers.Provider[Any]] = ...) -> Callable[[type[PRODUCT]], type[PRODUCT]]:
    """Decorator for Product class

    Args:
        imports (Sequence[type[Component]], optional): List of components to be imported by the product. Defaults to [].

    Raises:
        TypeError: If the wrapped class is not a subclass of Dependent.

    Returns:
        Callable[[type[Dependent]], type[Dependent]]: Decorator function that wraps the dependent class.
    """
