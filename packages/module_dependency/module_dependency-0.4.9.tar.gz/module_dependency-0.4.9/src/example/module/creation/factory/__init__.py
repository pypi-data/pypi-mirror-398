from abc import ABC, abstractmethod
from dependency.core import Component, component

class Product(ABC):
    @abstractmethod
    def doStuff(self) -> None:
        pass

class Creator(ABC):
    def someOperation(self) -> None:
        instance = self.createProduct()
        instance.doStuff()

    @abstractmethod
    def createProduct(self) -> Product:
        pass

@component(
    interface=Creator
)
class CreatorComponent(Component):
    pass