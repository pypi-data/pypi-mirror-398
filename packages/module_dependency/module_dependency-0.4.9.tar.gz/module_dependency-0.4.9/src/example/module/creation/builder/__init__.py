from abc import ABC, abstractmethod
from dependency.core import Component, component

class Product(ABC):
    @abstractmethod
    def doStuff(self) -> None:
        pass

class Builder(ABC):
    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def buildStepA(self) -> None:
        pass
    
    @abstractmethod
    def buildStepB(self) -> None:
        pass

    @abstractmethod
    def buildStepZ(self) -> None:
        pass

    @abstractmethod
    def result(self) -> Product:
        pass

@component(
    interface=Builder
)
class BuilderComponent(Component):
    pass