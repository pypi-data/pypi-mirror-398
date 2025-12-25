from typing import Generic, TypeVar

T = TypeVar('T')

class Decorator(Generic[T]):
    def __init__(self, component: T) -> None:
        self._wrappee = component