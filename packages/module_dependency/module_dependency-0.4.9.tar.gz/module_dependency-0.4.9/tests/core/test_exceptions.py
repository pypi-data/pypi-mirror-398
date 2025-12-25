import pytest
from dependency_injector import containers
from dependency.core.agrupation import Plugin, PluginMeta, module
from dependency.core.declaration import Component, component, Product, product, instance
from dependency.core.resolution import Container, InjectionResolver
from dependency.core.exceptions import DeclarationError, ResolutionError

@module()
class TPlugin(Plugin):
    meta = PluginMeta(name="test_plugin", version="0.1.0")

class TInterface:
    pass

@component(
    module=TPlugin,
    interface=TInterface,
)
class TComponent1(Component):
    pass

@component(
    module=TPlugin,
    interface=TInterface,
)
class TComponent2(Component):
    pass

@product(
    imports=[TComponent1],
)
class TProduct1(Product):
    pass

@instance(
    component=TComponent1,
    imports=[TComponent2],
    products=[TProduct1],
)
class TInstance1(TInterface):
    pass

@instance(
    component=TComponent2,
    imports=[TComponent1],
)
class TInstance2(TInterface):
    pass

def test_exceptions():
    container = containers.DynamicContainer()
    with pytest.raises(ResolutionError):
        TPlugin.resolve_providers(container) # type: ignore

    container = Container()
    providers = TPlugin.resolve_providers(container) # type: ignore
    loader = InjectionResolver(container, providers)

    with pytest.raises(DeclarationError):
        print(TComponent1.provider())
    with pytest.raises(DeclarationError):
        print(TComponent1.provide())
    with pytest.raises(ResolutionError):
        loader.resolve_injectables()
