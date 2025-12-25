from dependency.core import instance, providers
from example.plugin.hardware.factory import HardwareFactory, HardwareFactoryComponent
from example.plugin.hardware.factory.interfaces import Hardware
from example.plugin.hardware.factory.products.productB import HardwareB
from example.plugin.hardware.factory.products.productC import HardwareC
from example.plugin.hardware.observer import HardwareObserver, HardwareObserverComponent
from example.plugin.hardware.observer.interfaces import EventHardwareCreated

@instance(
    component=HardwareFactoryComponent,
    imports=[
        HardwareObserverComponent,
    ],
    products=[
        HardwareB,
        HardwareC
    ],
    provider=providers.Singleton,
)
class HardwareFactoryCreatorB(HardwareFactory):
    def __init__(self):
        self.__observer: HardwareObserver = HardwareObserverComponent.provide()
        print("FactoryCreatorB initialized")

    def createProduct(self, product: str) -> Hardware:
        match product:
            case "B":
                self.__observer.update(
                    context=EventHardwareCreated(product="B"))
                return HardwareB()
            case "C":
                self.__observer.update(
                    context=EventHardwareCreated(product="C"))
                return HardwareC()
            case _:
                raise ValueError(f"Unknown product type: {product}")
