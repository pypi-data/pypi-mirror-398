import pytest
from dependency.core.agrupation import Plugin, PluginMeta, module
from dependency.core.declaration import Component, component, Product, product, instance
from dependency.core.resolution import Container, InjectionResolver
from dependency.core.exceptions import CancelInitialization

BOOTSTRAPED: list[str] = []

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
    products=[TProduct1],
    bootstrap=True,
)
class TInstance1(TInterface):
    def __init__(self) -> None:
        BOOTSTRAPED.append("TInstance1")

@instance(
    component=TComponent2,
    imports=[TComponent1],
    bootstrap=True,
)
class TInstance2(TInterface):
    def __init__(self) -> None:
        BOOTSTRAPED.append("TInstance2")
        raise CancelInitialization("Failed to initialize TInstance2")

def test_exceptions():
    container = Container.from_json("example/config.json")
    providers = TPlugin.resolve_providers(container) # type: ignore
    loader = InjectionResolver(container, providers)
    assert "TInstance1" not in BOOTSTRAPED

    layers = loader.resolve_injectables()
    assert "TInstance1" not in BOOTSTRAPED

    loader.start_injectables(layers)
    assert "TInstance1" in BOOTSTRAPED
    assert "TInstance2" in BOOTSTRAPED

    assert TComponent1.provide() is not None

    with pytest.raises(CancelInitialization):
        TComponent2.provide()
