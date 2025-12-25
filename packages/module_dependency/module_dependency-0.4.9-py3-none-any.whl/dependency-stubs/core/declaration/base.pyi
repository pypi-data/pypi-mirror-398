from abc import ABC

class ABCComponent(ABC):
    """Abstract base class for all components.
    """
    interface_cls: type
    def __init__(self, interface_cls: type) -> None: ...

class ABCInstance(ABC):
    """Abstract base class for all instances.
    """
    provided_cls: type
    def __init__(self, provided_cls: type) -> None: ...
