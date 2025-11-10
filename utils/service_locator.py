"""
Service locator and dependency injection system for SmartSense AI Assistant.

This module provides a centralized service locator with dependency injection
capabilities, component lifecycle management, and service discovery.
"""

import threading
from typing import Any, Dict, Type, TypeVar, Optional, Callable, List
from abc import ABC, abstractmethod
import inspect
import weakref
from dataclasses import dataclass
from enum import Enum

from utils.logger import get_logger

T = TypeVar('T')


class ServiceLifetime(str, Enum):
    """Service lifetime options"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Descriptor for a registered service"""
    interface: Type
    implementation: Optional[Type] = None
    instance: Optional[Any] = None
    factory: Optional[Callable] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[Type] = None
    initialized: bool = False
    thread_safe: bool = True

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ServiceContainer:
    """
    Dependency injection container with service registration and resolution.

    Features:
    - Support for singleton, transient, and scoped lifetimes
    - Automatic dependency resolution
    - Factory functions support
    - Circular dependency detection
    - Thread-safe operations
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._resolution_stack: List[Type] = []
        self._lock = threading.RLock()

    def register_singleton(self, interface: Type, implementation: Type = None,
                          instance: Any = None, factory: Callable = None) -> None:
        """
        Register a singleton service

        Args:
            interface: Service interface type
            implementation: Implementation class (optional if instance or factory provided)
            instance: Pre-created instance (optional)
            factory: Factory function to create instance (optional)
        """
        self._register_service(
            interface=interface,
            implementation=implementation,
            instance=instance,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON
        )

    def register_transient(self, interface: Type, implementation: Type = None,
                          factory: Callable = None) -> None:
        """
        Register a transient service

        Args:
            interface: Service interface type
            implementation: Implementation class (optional if factory provided)
            factory: Factory function to create instance (optional)
        """
        self._register_service(
            interface=interface,
            implementation=implementation,
            instance=None,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )

    def register_scoped(self, interface: Type, implementation: Type = None,
                       factory: Callable = None) -> None:
        """
        Register a scoped service

        Args:
            interface: Service interface type
            implementation: Implementation class (optional if factory provided)
            factory: Factory function to create instance (optional)
        """
        self._register_service(
            interface=interface,
            implementation=implementation,
            instance=None,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED
        )

    def register_factory(self, interface: Type, factory: Callable,
                        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """
        Register a service with a factory function

        Args:
            interface: Service interface type
            factory: Factory function
            lifetime: Service lifetime
        """
        self._register_service(
            interface=interface,
            implementation=None,
            instance=None,
            factory=factory,
            lifetime=lifetime
        )

    def register_instance(self, interface: Type, instance: Any) -> None:
        """
        Register a pre-created instance as a singleton

        Args:
            interface: Service interface type
            instance: Pre-created instance
        """
        self._register_service(
            interface=interface,
            implementation=None,
            instance=instance,
            factory=None,
            lifetime=ServiceLifetime.SINGLETON
        )

    def _register_service(self, interface: Type, implementation: Type = None,
                         instance: Any = None, factory: Callable = None,
                         lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Internal service registration method"""
        with self._lock:
            # Validate parameters
            if implementation is None and instance is None and factory is None:
                raise ValueError("Must provide either implementation, instance, or factory")

            if implementation is not None and not issubclass(implementation, interface):
                raise ValueError(f"Implementation {implementation} must implement {interface}")

            if instance is not None and not isinstance(instance, interface):
                raise ValueError(f"Instance must be of type {interface}")

            # Analyze dependencies
            dependencies = []
            if implementation is not None:
                dependencies = self._analyze_dependencies(implementation)
            elif factory is not None:
                dependencies = self._analyze_factory_dependencies(factory)

            # Create service descriptor
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=implementation,
                instance=instance,
                factory=factory,
                lifetime=lifetime,
                dependencies=dependencies,
                initialized=bool(instance)  # Consider pre-created instances as initialized
            )

            self._services[interface] = descriptor

            # Store singleton instance if provided
            if instance is not None and lifetime == ServiceLifetime.SINGLETON:
                self._singleton_instances[interface] = instance

            self.logger.debug(f"Registered {interface.__name__} with lifetime {lifetime.value}")

    def _analyze_dependencies(self, implementation: Type) -> List[Type]:
        """Analyze constructor dependencies of a class"""
        dependencies = []

        try:
            # Get constructor signature
            sig = inspect.signature(implementation.__init__)

            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                # Check if parameter has type annotation
                if param.annotation != inspect.Parameter.empty:
                    dependencies.append(param.annotation)

        except (ValueError, TypeError) as e:
            self.logger.warning(f"Could not analyze dependencies for {implementation}: {e}")

        return dependencies

    def _analyze_factory_dependencies(self, factory: Callable) -> List[Type]:
        """Analyze dependencies of a factory function"""
        dependencies = []

        try:
            # Get function signature
            sig = inspect.signature(factory)

            for param_name, param in sig.parameters.items():
                # Check if parameter has type annotation
                if param.annotation != inspect.Parameter.empty:
                    dependencies.append(param.annotation)

        except (ValueError, TypeError) as e:
            self.logger.warning(f"Could not analyze factory dependencies: {e}")

        return dependencies

    def get(self, interface: Type[T]) -> T:
        """
        Resolve a service instance

        Args:
            interface: Service interface type

        Returns:
            Service instance

        Raises:
            KeyError: If service is not registered
            ValueError: If there's a circular dependency
        """
        with self._lock:
            return self._resolve_service(interface)

    def _resolve_service(self, interface: Type[T]) -> T:
        """Internal service resolution method"""
        # Check for circular dependencies
        if interface in self._resolution_stack:
            cycle = " -> ".join([cls.__name__ for cls in self._resolution_stack] + [interface.__name__])
            raise ValueError(f"Circular dependency detected: {cycle}")

        # Check if service is registered
        if interface not in self._services:
            raise KeyError(f"Service {interface.__name__} is not registered")

        descriptor = self._services[interface]

        # Check for existing instances based on lifetime
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if interface in self._singleton_instances:
                return self._singleton_instances[interface]
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if interface in self._scoped_instances:
                return self._scoped_instances[interface]

        # Create new instance
        self._resolution_stack.append(interface)
        try:
            instance = self._create_instance(descriptor)
        finally:
            self._resolution_stack.pop()

        # Store instance based on lifetime
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            self._singleton_instances[interface] = instance
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            self._scoped_instances[interface] = instance

        return instance

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new service instance"""
        # Use pre-created instance if available
        if descriptor.instance is not None:
            return descriptor.instance

        # Use factory if available
        if descriptor.factory is not None:
            return self._create_with_factory(descriptor.factory)

        # Use implementation class
        if descriptor.implementation is not None:
            return self._create_with_constructor(descriptor.implementation)

        raise ValueError(f"No way to create instance for {descriptor.interface.__name__}")

    def _create_with_factory(self, factory: Callable) -> Any:
        """Create instance using factory function"""
        # Resolve factory dependencies
        sig = inspect.signature(factory)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                dependency = self._resolve_service(param.annotation)
                kwargs[param_name] = dependency

        return factory(**kwargs)

    def _create_with_constructor(self, implementation: Type) -> Any:
        """Create instance using constructor injection"""
        # Resolve constructor dependencies
        sig = inspect.signature(implementation.__init__)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            if param.annotation != inspect.Parameter.empty:
                dependency = self._resolve_service(param.annotation)
                kwargs[param_name] = dependency
            elif param.default != inspect.Parameter.empty:
                # Use default value if available
                kwargs[param_name] = param.default

        return implementation(**kwargs)

    def get_optional(self, interface: Type[T]) -> Optional[T]:
        """
        Resolve a service instance, returning None if not registered

        Args:
            interface: Service interface type

        Returns:
            Service instance or None
        """
        try:
            return self.get(interface)
        except KeyError:
            return None

    def is_registered(self, interface: Type) -> bool:
        """Check if a service is registered"""
        return interface in self._services

    def clear_scoped(self) -> None:
        """Clear all scoped instances"""
        with self._lock:
            self._scoped_instances.clear()
            self.logger.debug("Cleared all scoped instances")

    def clear_all(self) -> None:
        """Clear all instances and services"""
        with self._lock:
            self._singleton_instances.clear()
            self._scoped_instances.clear()
            self._services.clear()
            self.logger.debug("Cleared all services and instances")

    def get_service_info(self, interface: Type) -> Optional[Dict[str, Any]]:
        """Get information about a registered service"""
        if interface not in self._services:
            return None

        descriptor = self._services[interface]

        return {
            'interface': interface.__name__,
            'implementation': descriptor.implementation.__name__ if descriptor.implementation else None,
            'lifetime': descriptor.lifetime.value,
            'dependencies': [dep.__name__ for dep in descriptor.dependencies],
            'initialized': descriptor.initialized,
            'has_singleton_instance': interface in self._singleton_instances,
            'has_scoped_instance': interface in self._scoped_instances,
        }

    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered services"""
        return {
            interface.__name__: self.get_service_info(interface)
            for interface in self._services.keys()
        }


class ServiceLocator:
    """
    Global service locator with thread-safe access to the service container.

    This provides a singleton pattern for accessing services throughout the application.
    """

    _instance: Optional['ServiceLocator'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'ServiceLocator':
        """Singleton implementation with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = get_logger(__name__)
            self._container = ServiceContainer()
            self._initialized = True

    @property
    def container(self) -> ServiceContainer:
        """Get the underlying service container"""
        return self._container

    def register_service(self, interface: Type, instance: Any) -> None:
        """Register a service instance as a singleton (shortcut method)"""
        self._container.register_instance(interface, instance)

    def get_service(self, service_type: Type[T]) -> T:
        """Get a service instance (shortcut method)"""
        return self._container.get(service_type)

    def get_optional_service(self, service_type: Type[T]) -> Optional[T]:
        """Get a service instance, returning None if not registered (shortcut method)"""
        return self._container.get_optional(service_type)

    def clear_services(self) -> None:
        """Clear all services"""
        self._container.clear_all()

    def get_container(self) -> ServiceContainer:
        """Get the service container for advanced operations"""
        return self._container


# Global service locator instance
_service_locator: Optional[ServiceLocator] = None


def get_service_locator() -> ServiceLocator:
    """Get the global service locator instance"""
    global _service_locator
    if _service_locator is None:
        _service_locator = ServiceLocator()
    return _service_locator


def register_service(interface: Type, instance: Any) -> None:
    """Register a service instance (shortcut function)"""
    get_service_locator().register_service(interface, instance)


def get_service(service_type: Type[T]) -> T:
    """Get a service instance (shortcut function)"""
    return get_service_locator().get_service(service_type)


def get_optional_service(service_type: Type[T]) -> Optional[T]:
    """Get a service instance, returning None if not registered (shortcut function)"""
    return get_service_locator().container.get_optional(service_type)


def clear_services() -> None:
    """Clear all services (shortcut function)"""
    get_service_locator().clear_services()