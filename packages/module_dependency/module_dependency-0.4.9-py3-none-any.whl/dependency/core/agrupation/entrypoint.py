import logging
import time
from threading import Event
from dependency.core.agrupation.plugin import Plugin
from dependency.core.resolution.container import Container
from dependency.core.resolution.resolver import InjectionResolver
_logger = logging.getLogger("DependencyLoader")

# TODO: Permitir configurar el comportamiento del framework desde el entrypoint
class Entrypoint:
    """Entrypoint for the application.
    """
    init_time: float = time.time()

    def __init__(self, container: Container, plugins: list[Plugin]) -> None:
        injectables = [
            provider
            for plugin in plugins
            for provider in plugin.resolve_providers(container)
        ]

        self.resolver: InjectionResolver = InjectionResolver(
            container=container,
            injectables=injectables
        )
        self.resolver.resolve_dependencies()
        _logger.info(f"Application started in {time.time() - self.init_time} seconds")

    def main_loop(self) -> None:
        Event().wait()
