import abc
from abc import ABC, abstractmethod
from typing import Any

class PluginHandler(ABC, metaclass=abc.ABCMeta):
    """Base interface for classes that can provide injections to the plugin system."""
    @classmethod
    @abstractmethod
    def create_injections(cls, instance: Any) -> dict[type, Any]:
        """Create injection mappings for this interface.

        Args:
            instance: The instance that will provide the injections

        Returns:
            Dictionary mapping service types to their instances
        """
    @classmethod
    @abstractmethod
    def initialize_plugin(cls, instance: Any, plugin: Any) -> None:
        """Initialize plugin-specific resources for this interface.

        This method is called after the plugin is created and services are injected.
        Override this method to perform any plugin-specific initialization.

        Args:
            instance: The instance that provides the initialization
            plugin: The plugin instance to initialize
        """
    @classmethod
    async def ainitialize_plugin(cls, instance: Any, plugin: Any) -> None:
        """Initialize plugin-specific resources for this interface.

        This method is called after the plugin is created and services are injected.
        Override this method to perform any plugin-specific initialization. This method is
        provided for compatibility with async plugins. By default it just calls the sync
        version of the method.

        Args:
            instance: The instance that provides the initialization
            plugin: The plugin instance to initialize
        """
