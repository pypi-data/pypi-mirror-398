from dependency.core import provider, providers
from example.module.creation.abstract_factory import AbtractFactory, AbtractFactoryComponent, AbtractProductA, AbtractProductB

class ConcreteProductA2(AbtractProductA):
    def doStuff(self) -> None:
        print("ConcreteProductA2 works")

class ConcreteProductB2(AbtractProductB):
    def doStuff(self) -> None:
        print("ConcreteProductB2 works")

@provider(
    component=AbtractFactoryComponent,
    provider=providers.Factory
)
class ConcreteAbtractFactory2(AbtractFactory):
    def createProductA(self) -> ConcreteProductA2:
        return ConcreteProductA2()
    
    def createProductB(self) -> ConcreteProductB2:
        return ConcreteProductB2()