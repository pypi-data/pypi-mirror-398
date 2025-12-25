from dependency_injector import containers as containers, providers as providers
from dependency_injector.wiring import Closing, Modifier as Modifier, Provide, Provider
from typing import Any, Callable

class BaseLazy:
    """Base Lazy Class for deferred provider resolution.
    """
    modifier: Modifier | None
    def __init__(self, provider: Callable[[], providers.Provider[Any] | containers.Container | str], modifier: Modifier | None = None) -> None: ...
    @property
    def provider(self) -> providers.Provider[Any] | containers.Container | str: ...

class LazyProvide(BaseLazy, Provide):
    """Lazy Provide Class for deferred provider resolution.
    """
class LazyProvider(BaseLazy, Provider):
    """Lazy Provide Class for deferred provider resolution.
    """
class LazyClosing(BaseLazy, Closing):
    """Lazy Closing Class for deferred provider resolution.
    """
