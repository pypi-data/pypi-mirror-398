from dependency.core import provider, providers
from example.module.structural.bridge.implementation import Implementation, ImplementationComponent

@provider(
    provider=providers.Singleton,
    component=ImplementationComponent
)
class ConcreteImplementation(Implementation):
    def method1(self):
        pass

    def method2(self):
        pass

    def method3(self):
        pass