from bosa_core.plugin.handler import PluginHandler as PluginHandler
from bosa_core.plugin.registry import ServiceRegistry as ServiceRegistry
from typing import Callable

class Plugin:
    """Base class for BOSA Plugins."""
    name: str
    description: str
    version: str
    def __init__(self, *args, **kwargs) -> None:
        """Initialize plugin instance.

        Raises:
            ValueError: If required class attributes are not set
        """
    @classmethod
    def get_handler_type(cls) -> type['PluginHandler'] | None:
        """Get the handler type for this plugin class.

        This method walks up the inheritance chain to find the handler_type.

        Returns:
            The handler type for this plugin, or None if not set
        """
    @classmethod
    def for_handler(cls, handler_type: type['PluginHandler']) -> Callable[[type['Plugin']], type['Plugin']]:
        """Decorator to specify which handler this plugin is designed for.

        Args:
            handler_type: The type of handler this plugin works with

        Returns:
            A decorator function that sets the handler type on the plugin class
        """
    @classmethod
    def set_registry(cls, registry: ServiceRegistry) -> None:
        """Set the service registry for this plugin class.

        Args:
            registry: Service registry to use for dependency injection
        """
    @property
    def handler_type(self) -> type['PluginHandler'] | None:
        """Get the handler type for this plugin instance.

        Returns:
            The handler type for this plugin, or None if not set
        """
    def __new__(cls, *args, **kwargs):
        """Create a new plugin instance with injected services.

        This is called before __init__ and allows us to inject services
        before the instance is initialized.
        """
