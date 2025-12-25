from dependency_injector.wiring import inject
from dependency.core import Product, product
from dependency.core.injection import LazyProvide
from example.plugin.hardware.factory.interfaces import Hardware
from example.plugin.base.number import NumberService, NumberServiceComponent


@product(
    imports=[
        NumberServiceComponent,
    ],
)
class HardwareA(Hardware, Product):
    @inject
    def doStuff(self,
            operation: str,
            number: NumberService = LazyProvide(NumberServiceComponent.reference),
        ) -> None:
        random_number = number.getRandomNumber()
        print(f"HardwareA {random_number} works with operation: {operation}")
