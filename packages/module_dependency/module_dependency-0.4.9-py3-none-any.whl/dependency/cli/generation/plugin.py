from jinja2 import Template
from dependency.cli.models.base import Module
from dependency.cli.generation.base import JENV

class PluginGenerator:
    @staticmethod
    def generate(
        module: Module,
    ) -> str:
        template: Template = JENV.get_template("plugin.py.j2")
        return template.render(
            module=module,
        )