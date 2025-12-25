from jinja2 import Template
from dependency.cli.models.base import Component, Instance
from dependency.cli.generation.base import JENV

class InstanceGenerator:
    @staticmethod
    def generate(
        component: Component,
        instance: Instance,
    ) -> str:
        template: Template = JENV.get_template("instance.py.j2")
        return template.render(
            component=component,
            instance=instance,
        )