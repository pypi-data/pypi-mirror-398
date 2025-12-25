from typing import Any, TypeVar

T = TypeVar('T')

class ServiceRegistry:
    """Registry for core services that can be injected into plugins."""
    def __init__(self) -> None:
        """Initialize an empty service registry."""
    def register(self, service_type: type[T], instance: T) -> None:
        """Register a service instance for a given type.

        Args:
            service_type: The type of the service (usually its class)
            instance: The service instance
        """
    def get(self, service_type: type[T]) -> T:
        """Get a service instance by its type.

        Args:
            service_type: The type of service to retrieve

        Returns:
            The service instance

        Raises:
            TypeError: If the service type is a built-in type
            KeyError: If the service type is not registered
        """
    def inject_services(self, target: Any) -> None:
        """Inject registered services into an object based on its type hints.

        This will look for class-level type hints and inject matching services.
        If a service is registered that is a subclass of the requested type,
        it will be injected. Handles both regular and generic types.

        Args:
            target: The object to inject services into
        """
