from abc import ABC, abstractmethod
from dependency_injector import containers, providers
from dependency.core.agrupation import Module, module
from dependency.core.declaration import Component, component, instance

class TInterface(ABC):
    @abstractmethod
    def method(self) -> str:
        pass

@module(
    module=None,
)
class TModule(Module):
    pass

@component(
    module=TModule,
    interface=TInterface,
)
class TComponent(Component):
    pass

@instance(
    component=TComponent,
    imports=[],
    provider=providers.Singleton,
)
class TInstance(TInterface):
    def method(self) -> str:
        return "Hello, World!"

def test_declaration():
    container = containers.DynamicContainer()
    setattr(container, TModule.injection.name, TModule.injection.inject_cls()) # type: ignore
    for provider in list(TModule.injection.resolve_providers()): # type: ignore
        provider.do_wiring(container)

    assert str(TModule) == "TModule"
    assert str(TComponent) == "TInterface"
    assert str(TInstance) == "TInstance"

    component: TInterface = TComponent.provide()
    assert isinstance(component, TInterface)
    assert component.method() == "Hello, World!"
