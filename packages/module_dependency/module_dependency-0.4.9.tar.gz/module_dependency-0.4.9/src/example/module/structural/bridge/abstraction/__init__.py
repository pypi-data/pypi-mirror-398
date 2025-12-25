from abc import ABC, abstractmethod
from dependency.core import Component, component

class Abstraction(ABC):
    @abstractmethod
    def feature1(self):
        pass

    @abstractmethod
    def feature2(self):
        pass 

@component(
    interface=Abstraction
)
class AbstractionComponent(Component):
    pass