from dependency.core import provider, providers
from example.module.creation.factory import Creator, CreatorComponent, Product

class ConcreteProductB(Product):
    def doStuff(self) -> None:
        print("ConcreteProductA works")

@provider(
    provider=providers.Factory,
    component=CreatorComponent
)
class ConcreteCreatorB(Creator):
    def createProduct(self) -> ConcreteProductB:
        return ConcreteProductB()