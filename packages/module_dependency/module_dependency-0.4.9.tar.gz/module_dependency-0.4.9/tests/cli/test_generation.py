from dependency.cli.models.base import Module, Component, Instance
from dependency.cli.generation.plugin import PluginGenerator
from dependency.cli.generation.module import ModuleGenerator
from dependency.cli.generation.component import ComponentGenerator
from dependency.cli.generation.instance import InstanceGenerator

def test_generation():
    plugin = Module(
        path="src.plugin",
        name="Plugin",
    )
    module = Module(
        path="src.plugin.module",
        name="Module",
    )
    component = Component(
        path="src.plugin.module.component",
        name="Component",
        interface="Interface",
    )
    instance = Instance(
        path="src.plugin.module.component.instance",
        name="ComponentA",
        imports=["Component"],
    )

    PluginGenerator.generate(
        module=plugin,
    )
    ModuleGenerator.generate(
        parent=plugin,
        module=module,
    )
    ComponentGenerator.generate(
        component=component,
        module=module,
    )
    InstanceGenerator.generate(
        component=component,
        instance=instance,
    )