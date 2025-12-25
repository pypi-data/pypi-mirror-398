from abc import ABC, abstractmethod
from dependency.core import Component, component
from example.plugin.base import BasePlugin

class NumberService(ABC):
    @abstractmethod
    def getRandomNumber(self) -> int:
        pass

@component(
    module=BasePlugin,
    interface=NumberService,
)
class NumberServiceComponent(Component):
    pass
