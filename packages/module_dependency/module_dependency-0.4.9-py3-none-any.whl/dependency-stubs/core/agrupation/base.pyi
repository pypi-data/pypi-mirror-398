from abc import ABC

class ABCModule(ABC):
    """Abstract Base Class for Module.
    """
    name: str
    def __init__(self, name: str) -> None: ...
