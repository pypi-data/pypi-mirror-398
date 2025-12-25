from dependency.cli.generation.base import JENV as JENV
from dependency.cli.models.base import Component as Component, Instance as Instance
from jinja2 import Template as Template

class InstanceGenerator:
    @staticmethod
    def generate(component: Component, instance: Instance) -> str: ...
