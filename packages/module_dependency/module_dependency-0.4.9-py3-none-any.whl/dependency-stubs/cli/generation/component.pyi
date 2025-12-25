from dependency.cli.generation.base import JENV as JENV
from dependency.cli.models.base import Component as Component, Module as Module
from jinja2 import Template as Template

class ComponentGenerator:
    @staticmethod
    def generate(component: Component, module: Module) -> str: ...
