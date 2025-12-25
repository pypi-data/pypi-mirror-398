from abc import ABC, abstractmethod
from dependency.core import Component, component
from example.plugin.hardware import HardwarePlugin

class HardwareAbstraction(ABC):
    @abstractmethod
    def someOperation(self, product: str) -> None:
        pass

    @abstractmethod
    def otherOperation(self, product: str) -> None:
        pass

@component(
    module=HardwarePlugin,
    interface=HardwareAbstraction,
)
class HardwareAbstractionComponent(Component):
    pass
