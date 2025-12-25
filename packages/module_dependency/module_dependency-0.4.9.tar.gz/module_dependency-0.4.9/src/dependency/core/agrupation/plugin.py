import logging
from pydantic import BaseModel
from typing import get_type_hints, override
from dependency.core.agrupation.module import Module
from dependency.core.injection.injectable import Injectable
from dependency.core.resolution.container import Container
from dependency.core.exceptions import ResolutionError
_logger = logging.getLogger("DependencyLoader")

# TODO: Mejorar la forma en que se declara una configuración de plugin
class PluginConfig(BaseModel):
    """Empty configuration model for the plugin.
    """
    pass

class PluginMeta(BaseModel):
    """Metadata for the plugin.
    """
    name: str
    version: str

    def __str__(self) -> str:
        return f"Plugin {self.name} {self.version}"

class Plugin(Module):
    """Plugin class for creating reusable components.
    """
    meta: PluginMeta
    config: BaseModel

    def __resolve_config(self, container: Container) -> None:
        """Resolve the plugin configuration.

        Args:
            container (Container): The application container.

        Raises:
            ResolutionError: If the configuration is invalid.
        """
        try:
            config_cls = get_type_hints(self.__class__).get("config", BaseModel)
            config_cls = PluginConfig if config_cls is BaseModel else config_cls
            self.config = config_cls(**container.config())
        except Exception as e:
            raise ResolutionError(f"Failed to resolve plugin config for {self.meta}") from e

    @override
    def resolve_providers(self, container: Container) -> list[Injectable]:
        """Resolve provider injections for the plugin.

        Args:
            container (Container): The application container.

        Returns:
            list[Injectable]: A list of injectable providers.
        """
        self.__resolve_config(container=container)
        return super().resolve_providers(container=container)

    def __repr__(self) -> str:
        return f"{self.meta}: {self.config}"
