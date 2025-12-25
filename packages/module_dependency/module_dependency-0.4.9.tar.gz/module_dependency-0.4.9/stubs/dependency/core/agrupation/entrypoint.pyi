from dependency.core.agrupation.plugin import Plugin as Plugin
from dependency.core.resolution.container import Container as Container
from dependency.core.resolution.resolver import InjectionResolver as InjectionResolver

class Entrypoint:
    """Entrypoint for the application.
    """
    init_time: float
    resolver: InjectionResolver
    def __init__(self, container: Container, plugins: list[Plugin]) -> None: ...
    def main_loop(self) -> None: ...
