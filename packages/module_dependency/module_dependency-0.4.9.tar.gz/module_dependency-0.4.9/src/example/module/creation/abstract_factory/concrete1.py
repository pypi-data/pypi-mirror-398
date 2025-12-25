from dependency.core import provider, providers
from example.module.creation.abstract_factory import AbtractFactory, AbtractFactoryComponent, AbtractProductA, AbtractProductB

class ConcreteProductA1(AbtractProductA):
    def doStuff(self) -> None:
        print("ConcreteProductA1 works")

class ConcreteProductB1(AbtractProductB):
    def doStuff(self) -> None:
        print("ConcreteProductB1 works")

@provider(
    provider=providers.Factory,
    component=AbtractFactoryComponent
)
class ConcreteAbtractFactory1(AbtractFactory):
    def createProductA(self) -> ConcreteProductA1:
        return ConcreteProductA1()
    
    def createProductB(self) -> ConcreteProductB1:
        return ConcreteProductB1()