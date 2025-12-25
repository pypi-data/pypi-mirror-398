from dependency.core import provider, providers
from example.module.structural.bridge.abstraction import Abstraction, AbstractionComponent
from example.module.structural.bridge.implementation import Implementation, ImplementationComponent

@provider(
    component=AbstractionComponent,
    dependencies=[
        ImplementationComponent
    ]
)
class AbstractionImplementation(Abstraction):
    def __init__(self):
        self.implementation: Implementation = ImplementationComponent.provide()

    def feature1(self):
        self.implementation.method1()

    def feature2(self):
        self.implementation.method2()
        self.implementation.method3()