from dependency.core import provider, providers
from example.module.creation.factory import Creator, CreatorComponent, Product

class ConcreteProductA(Product):
    def doStuff(self) -> None:
        print("ConcreteProductA works")

@provider(
    provider=providers.Factory,
    component=CreatorComponent
)
class ConcreteCreatorA(Creator):
    def createProduct(self) -> ConcreteProductA:
        return ConcreteProductA()