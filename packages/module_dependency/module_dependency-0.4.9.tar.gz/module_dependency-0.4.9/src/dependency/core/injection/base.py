from abc import ABC, abstractmethod
from typing import Any, Generator, Optional, override
from dependency_injector import containers
from dependency.core.injection.injectable import Injectable

class BaseInjection(ABC):
    """Base Injection Class
    """
    def __init__(self,
        name: str,
        parent: Optional['ContainerInjection'] = None
    ) -> None:
        self.name: str = name
        self.parent: Optional['ContainerInjection'] = parent

    @property
    def reference(self) -> str:
        """Return the reference for dependency injection."""
        if not self.parent:
            return self.name
        return f"{self.parent.reference}.{self.name}"

    def change_parent(self, parent: 'ContainerInjection') -> None:
        """Change the parent injection of this injection.

        Args:
            parent (ContainerInjection): The new parent injection.
        """
        if self.parent:
            self.parent.childs.remove(self)
        self.parent = parent
        parent.childs.add(self)

    @abstractmethod
    def inject_cls(self) -> Any:
        """Return the class to be injected."""
        pass

    @abstractmethod
    def resolve_providers(self) -> Generator[Injectable, None, None]:
        """Inject all children into the current injection context."""
        pass

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return self.name

class ContainerInjection(BaseInjection):
    """Container Injection Class
    """
    def __init__(self,
        name: str,
        parent: Optional['ContainerInjection'] = None
    ) -> None:
        super().__init__(name=name, parent=parent)
        self.childs: set[BaseInjection] = set()
        self.container: containers.Container = containers.DynamicContainer()
        if self.parent:
            self.parent.childs.add(self)

    @override
    def inject_cls(self) -> containers.Container:
        """Return the container instance."""
        return self.container

    @override
    def resolve_providers(self) -> Generator[Injectable, None, None]:
        """Inject all children into the current container."""
        for child in self.childs:
            setattr(self.container, child.name, child.inject_cls())
            yield from child.resolve_providers()
