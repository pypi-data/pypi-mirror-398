from abc import ABC, abstractmethod
from dependency.core import Component, component
from example.plugin.base import BasePlugin

class StringService(ABC):
    @abstractmethod
    def getRandomString(self) -> str:
        pass

@component(
    module=BasePlugin,
    interface=StringService,
)
class StringServiceComponent(Component):
    pass
