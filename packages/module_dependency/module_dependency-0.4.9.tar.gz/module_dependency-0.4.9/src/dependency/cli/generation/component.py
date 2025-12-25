from jinja2 import Template
from dependency.cli.models.base import Component, Module
from dependency.cli.generation.base import JENV

class ComponentGenerator:
    @staticmethod
    def generate(
        component: Component,
        module: Module,
    ) -> str:
        template: Template = JENV.get_template("component.py.j2")
        return template.render(
            component=component,
            module=module,
        )