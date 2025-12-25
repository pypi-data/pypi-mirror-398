from abc import ABC, abstractmethod
from typing import Callable
from dependency.core import Component, component
from example.plugin.hardware.observer.interfaces import EventSubscriber, HardwareEventContext
from example.plugin.hardware import HardwarePlugin

class HardwareObserver(ABC):
    @abstractmethod
    def subscribe(self, listener: type[EventSubscriber]) -> Callable:
        pass

    @abstractmethod
    def update(self, context: HardwareEventContext) -> None:
        pass

@component(
    module=HardwarePlugin,
    interface=HardwareObserver,
)
class HardwareObserverComponent(Component):
    pass
