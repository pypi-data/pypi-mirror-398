from dependency.core.agrupation.module import Module as Module
from dependency.core.exceptions import ResolutionError as ResolutionError
from dependency.core.injection.injectable import Injectable as Injectable
from dependency.core.resolution.container import Container as Container
from pydantic import BaseModel
from typing import override

class PluginConfig(BaseModel):
    """Empty configuration model for the plugin.
    """

class PluginMeta(BaseModel):
    """Metadata for the plugin.
    """
    name: str
    version: str

class Plugin(Module):
    """Plugin class for creating reusable components.
    """
    meta: PluginMeta
    config: BaseModel
    @override
    def resolve_providers(self, container: Container) -> list[Injectable]:
        """Resolve provider injections for the plugin.

        Args:
            container (Container): The application container.

        Returns:
            list[Injectable]: A list of injectable providers.
        """
