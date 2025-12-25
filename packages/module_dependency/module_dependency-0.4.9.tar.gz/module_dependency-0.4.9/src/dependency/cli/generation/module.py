from jinja2 import Template
from dependency.cli.models.base import Module
from dependency.cli.generation.base import JENV

class ModuleGenerator:
    @staticmethod
    def generate(
        parent: Module,
        module: Module,
    ) -> str:
        template: Template = JENV.get_template("module.py.j2")
        return template.render(
            parent=parent,
            module=module,
        )