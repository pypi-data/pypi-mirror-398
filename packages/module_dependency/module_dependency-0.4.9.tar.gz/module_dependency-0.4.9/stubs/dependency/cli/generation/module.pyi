from dependency.cli.generation.base import JENV as JENV
from dependency.cli.models.base import Module as Module
from jinja2 import Template as Template

class ModuleGenerator:
    @staticmethod
    def generate(parent: Module, module: Module) -> str: ...
