from dependency.core import instance, providers
from example.plugin.hardware import HardwarePlugin
from example.plugin.hardware.bridge import HardwareAbstraction, HardwareAbstractionComponent
from example.plugin.hardware.factory import HardwareFactory, HardwareFactoryComponent
from example.plugin.hardware.observer import HardwareObserver, HardwareObserverComponent
from example.plugin.hardware.observer.interfaces import EventHardwareOperation

@instance(
    component=HardwareAbstractionComponent,
    imports=[
        HardwareFactoryComponent,
    ],
    provider=providers.Singleton,
)
class HardwareAbstractionBridgeA(HardwareAbstraction):
    def __init__(self) -> None:
        self.__factory: HardwareFactory = HardwareFactoryComponent.provide()
        self.__observer: HardwareObserver = HardwareObserverComponent.provide()
        assert HardwarePlugin.config.config == True
        print("AbstractionBridgeA initialized")

    def someOperation(self, product: str) -> None:
        instance = self.__factory.createHardware(product=product)
        instance.doStuff("someOperation")
        self.__observer.update(
            context=EventHardwareOperation(
                product=product,
                operation="someOperation"))

    def otherOperation(self, product: str) -> None:
        instance = self.__factory.createHardware(product=product)
        instance.doStuff("otherOperation")
        self.__observer.update(
            context=EventHardwareOperation(
                product=product,
                operation="otherOperation"))
