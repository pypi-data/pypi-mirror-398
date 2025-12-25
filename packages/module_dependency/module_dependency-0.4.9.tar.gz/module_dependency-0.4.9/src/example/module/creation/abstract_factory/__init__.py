from abc import ABC, abstractmethod
from dependency.core import Component, component

class AbtractProductA(ABC):
    @abstractmethod
    def doStuff(self) -> None:
        pass

class AbtractProductB(ABC):
    @abstractmethod
    def doStuff(self) -> None:
        pass

class AbtractFactory(ABC):
    def work(self) -> None:
        instance1 = self.createProductA()
        instance2 = self.createProductB()
        instance1.doStuff()
        instance2.doStuff()

    @abstractmethod
    def createProductA(self) -> AbtractProductA:
        pass

    @abstractmethod
    def createProductB(self) -> AbtractProductB:
        pass

@component(
    interface=AbtractFactory
)
class AbtractFactoryComponent(Component):
    pass