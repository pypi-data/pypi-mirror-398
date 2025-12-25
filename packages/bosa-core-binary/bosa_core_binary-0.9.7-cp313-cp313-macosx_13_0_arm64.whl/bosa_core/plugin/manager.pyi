from bosa_core.plugin.handler import PluginHandler as PluginHandler
from bosa_core.plugin.plugin import Plugin as Plugin
from bosa_core.plugin.registry import ServiceRegistry as ServiceRegistry
from bosa_core.services.config import ConfigService as ConfigService
from typing import Any, Callable, TypeVar

T = TypeVar('T', bound=PluginHandler)

class HandlerNotFoundError(RuntimeError):
    """Raised when a requested plugin handler is not found."""

class PluginManager:
    """Manages plugin lifecycle and service injection.

    This manager can handle different types of plugins based on the services provided.
    Services are automatically registered based on the plugin handler interfaces provided.

    This class follows the singleton pattern - only one instance will ever exist.
    Thread-safe implementation using double-checked locking pattern.
    """
    def __new__(cls, *, handlers: list[PluginHandler] | None = None, env_file: str | None = None, global_services: list[Any] = (), key_instance: str | None = None) -> PluginManager:
        """Create or return the singleton instance or multi-instance.

        Args:
            handlers: List of plugin handlers that provide injections
            env_file: Optional environment file for loading environment variables
            global_services: List of services to register globally
            key_instance: Optional key for multi-instance pattern. If None, uses singleton.

        Returns:
            The singleton PluginManager instance or specified multi-instance

        Raises:
            ValueError: If handlers is not provided during first initialization
        """
    def __init__(self, *, handlers: list[PluginHandler] | None = None, env_file: str | None = None, global_services: list[Any] = (), key_instance: str | None = None) -> None:
        """Initialize plugin manager.

        This will only run once per instance (singleton or multi-instance).

        Args:
            handlers: List of plugin handlers that provide injections
            env_file: Optional environment file for loading environment variables
            global_services: List of custom services to be injected into the global registry
            key_instance: Optional key for multi-instance pattern
        """
    def register_plugin(self, plugin_class: type[Plugin], custom_initializer: Callable[[Plugin], None] | None = None, additional_params: dict[str, Any] | None = None) -> None:
        """Register and initialize a plugin.

        Args:
            plugin_class: Plugin class to register
            custom_initializer: Optional callable that will be called with the plugin instance after initialization
            additional_params: Optional dictionary of keyword arguments to pass to the plugin constructor

        Raises:
            ValueError: If plugin doesn't specify a handler type
        """
    async def aregister_plugin(self, plugin_class: type[Plugin], custom_initializer: Callable[[Plugin], Any] | None = None, additional_params: dict[str, Any] | None = None) -> None:
        """Register and initialize a plugin asynchronously.

        This is backwards compatible with the synchronous version;
        passing a synchronous plugin will be handled appropriately.

        Args:
            plugin_class: Plugin class to register
            custom_initializer: Optional callable that will be called with the plugin instance after initialization.
                               Can be either a synchronous or asynchronous function.
            additional_params: Optional dictionary of keyword arguments to pass to the plugin constructor

        Raises:
            ValueError: If plugin doesn't specify a handler type
        """
    def get_plugin(self, name: str) -> Plugin | None:
        """Get a plugin by name.

        Args:
            name: Name of plugin to get

        Returns:
            Plugin instance if found, None otherwise
        """
    def get_plugins(self, handler_type: type[PluginHandler] | None = None, plugin_names: list[str] | None = None) -> list[Plugin]:
        """Get all registered plugins, optionally filtered by handler type and names.

        Args:
            handler_type: Optional handler type to filter plugins by. If provided,
                        only returns plugins that have this handler type registered.
            plugin_names: Optional list of plugin names to filter by. If provided,
                        only returns plugins whose names are in this list.

        Returns:
            List of plugin instances
        """
    def get_handlers(self, handler_type: type[PluginHandler] | None = None) -> list[PluginHandler]:
        """Get all registered handlers, optionally filtered by type.

        Args:
            handler_type: Optional handler type to filter by. If provided,
                        only returns handlers that are instances of this type.

        Returns:
            List of handler instances
        """
    def get_handler(self, handler_type: type[T]) -> T:
        """Get a handler of the specified type.

        Args:
            handler_type: The type of handler to get

        Returns:
            The handler instance of the specified type

        Raises:
            HandlerNotFoundError: If no handler of the specified type is found
        """
