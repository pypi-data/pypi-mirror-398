from dependency_injector import containers, providers
from typing import Any

class Container(containers.DynamicContainer):
    """Container Class extending DynamicContainer with additional methods.
    """
    config: providers.Configuration
    @staticmethod
    def from_dict(config: dict[str, Any], required: bool = False) -> Container:
        """Create a Container instance from a dictionary configuration.

        Args:
            config (dict[str, Any]): Configuration dictionary.
            required (bool, optional): Whether the configuration is required. Defaults to False.

        Returns:
            Container: A new Container instance configured with the provided dictionary.
        """
    @staticmethod
    def from_json(file: str, required: bool = False, envs_required: bool = False) -> Container:
        """Create a Container instance from a JSON file configuration.

        Args:
            file (str): Path to the JSON configuration file.
            required (bool, optional): Whether the configuration is required. Defaults to False.
            envs_required (bool, optional): Whether environment variables are required. Defaults to False.

        Returns:
            Container: A new Container instance configured with the provided JSON file.
        """
