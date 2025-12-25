from dependency.core import instance, providers
from example.plugin.hardware.factory import HardwareFactory, HardwareFactoryComponent
from example.plugin.hardware.factory.interfaces import Hardware
from example.plugin.hardware.factory.products.productA import HardwareA
from example.plugin.hardware.factory.products.productB import HardwareB
from example.plugin.hardware.observer import HardwareObserver, HardwareObserverComponent
from example.plugin.hardware.observer.interfaces import EventHardwareCreated

@instance(
    component=HardwareFactoryComponent,
    imports=[
        HardwareObserverComponent,
    ],
    products=[
        HardwareA,
        HardwareB,
    ],
    provider=providers.Singleton,
)
class HardwareFactoryCreatorA(HardwareFactory):
    def __init__(self):
        self.__observer: HardwareObserver = HardwareObserverComponent.provide()
        print("FactoryCreatorA initialized")

    def createHardware(self, product: str) -> Hardware:
        instance: Hardware
        match product:
            case "A":
                instance = HardwareA()
                self.__observer.update(
                    context=EventHardwareCreated(product="A"))
                return instance
            case "B":
                instance = HardwareB()
                self.__observer.update(
                    context=EventHardwareCreated(product="B"))
                return instance
            case _:
                raise ValueError(f"Unknown product type: {product}")
