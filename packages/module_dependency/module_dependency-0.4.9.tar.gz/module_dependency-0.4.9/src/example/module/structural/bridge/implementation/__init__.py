from abc import ABC, abstractmethod
from dependency.core import Component, component

class Implementation(ABC):
    @abstractmethod
    def method1(self):
        pass

    @abstractmethod
    def method2(self):
        pass

    @abstractmethod
    def method3(self):
        pass

@component(
    interface=Implementation
)
class ImplementationComponent(Component):
    pass