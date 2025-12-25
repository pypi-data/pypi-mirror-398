from abc import ABC

class ABCComponent(ABC):
    """Abstract base class for all components.
    """
    def __init__(self, interface_cls: type) -> None:
        self.interface_cls: type = interface_cls

    def __repr__(self) -> str:
        return self.interface_cls.__name__

class ABCInstance(ABC):
    """Abstract base class for all instances.
    """
    def __init__(self, provided_cls: type) -> None:
        self.provided_cls: type = provided_cls

    def __repr__(self) -> str:
        return self.provided_cls.__name__
