from dependency.core import provider, providers
from example.module.creation.builder import Builder, BuilderComponent, Product

class Product2(Product):
    def __init__(self):
        self.__steps = set()
    
    def setStep(self, step: str) -> None:
        self.__steps.add(step)
    
    def doStuff(self) -> None:
        print(self.__steps)

@provider(
    component=BuilderComponent
)
class ConcreteBuilder1(Builder):
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.__product = Product2()

    def buildStepA(self) -> None:
        self.__product.setStep('A2')
    
    def buildStepB(self) -> None:
        self.__product.setStep('B2')

    def buildStepZ(self) -> None:
        self.__product.setStep('Z2')

    def result(self) -> Product:
        product = self.__product
        self.reset()
        return product