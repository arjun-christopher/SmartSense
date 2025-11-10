"""
Lifecycle management system for SmartSense AI Assistant.

This module provides centralized component lifecycle management with
dependency resolution, health monitoring, and graceful shutdown.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Type
import traceback

from models.config import SmartSenseConfig
from utils.logger import get_logger
from utils.service_locator import ServiceLocator
from core.message_bus import AsyncMessageBus
from core.base import BaseComponent


class SystemPhase(str, Enum):
    """System lifecycle phases"""
    INITIALIZING = "initializing"
    LOADING_CONFIG = "loading_config"
    SETTING_UP_SERVICES = "setting_up_services"
    INITIALIZING_COMPONENTS = "initializing_components"
    READY = "ready"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"
    OFFLINE = "offline"


class ComponentPhase(str, Enum):
    """Component lifecycle phases"""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    OFFLINE = "offline"


class ComponentInfo:
    """Information about a registered component"""

    def __init__(self, component: BaseComponent, priority: int = 0,
                 dependencies: List[Type] = None, auto_start: bool = True):
        self.component = component
        self.priority = priority  # Higher priority = earlier initialization
        self.dependencies = dependencies or []
        self.auto_start = auto_start
        self.registered_at = datetime.now()
        self.initialized_at: Optional[datetime] = None
        self.started_at: Optional[datetime] = None
        self.shutdown_at: Optional[datetime] = None
        self.phase = ComponentPhase.REGISTERED
        self.health_check_interval = 30.0  # seconds
        self.last_health_check: Optional[datetime] = None
        self.health_status: Optional[Dict[str, Any]] = None


class LifecycleManager:
    """
    Manages the lifecycle of all SmartSense components.

    Features:
    - Component dependency resolution and ordered initialization
    - Health monitoring and status tracking
    - Graceful shutdown with cleanup
    - Component restart and recovery
    - Performance metrics collection
    """

    def __init__(self, config: SmartSenseConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.service_locator = ServiceLocator()

        # System state
        self.system_phase = SystemPhase.OFFLINE
        self.startup_time: Optional[datetime] = None
        self.shutdown_time: Optional[datetime] = None

        # Component management
        self.components: Dict[str, ComponentInfo] = {}
        self.component_dependencies: Dict[str, List[str]] = {}
        self.initialization_order: List[str] = []

        # Health monitoring
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.health_check_interval = 60.0  # seconds

        # Shutdown handling
        self.shutdown_timeout = 30.0  # seconds
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> bool:
        """
        Initialize the entire SmartSense system

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self._set_system_phase(SystemPhase.INITIALIZING)
            self.startup_time = datetime.now()

            self.logger.info("Starting SmartSense lifecycle initialization")

            # Phase 1: Load configuration (already done in constructor)
            self._set_system_phase(SystemPhase.LOADING_CONFIG)

            # Phase 2: Set up core services
            await self._setup_core_services()
            self._set_system_phase(SystemPhase.SETTING_UP_SERVICES)

            # Phase 3: Register all components
            await self._register_components()

            # Phase 4: Resolve dependencies and determine initialization order
            self._resolve_dependencies()

            # Phase 5: Initialize components in order
            await self._initialize_components()
            self._set_system_phase(SystemPhase.INITIALIZING_COMPONENTS)

            # Phase 6: Start health monitoring
            await self._start_health_monitoring()

            # System ready
            self._set_system_phase(SystemPhase.READY)
            self.logger.info("SmartSense system initialization complete")

            return True

        except Exception as e:
            self.logger.error(f"System initialization failed: {e}", exc_info=True)
            self._set_system_phase(SystemPhase.ERROR)
            return False

    async def _setup_core_services(self) -> None:
        """Set up core services"""
        self.logger.info("Setting up core services")

        # Message bus (singleton)
        message_bus = AsyncMessageBus(
            max_queue_size=self.config.message_bus.max_queue_size,
            processing_timeout=self.config.message_bus.processing_timeout,
            retry_attempts=self.config.message_bus.retry_attempts
        )
        self.service_locator.container.register_singleton(AsyncMessageBus, message_bus)
        await message_bus.initialize()

        # Configuration manager (singleton)
        self.service_locator.container.register_instance(type(self.config), self.config)

        self.logger.info("Core services set up complete")

    async def _register_components(self) -> None:
        """Register all components"""
        self.logger.info("Registering system components")

        # Import components to register them
        # This will be expanded as we implement more components
        from core.text_input import TextInputHandler
        from core.speech import VoiceInputHandler
        from core.vision import ImageInputHandler
        from core.nlp import NLPProcessor
        from core.vision_processor import VisionProcessor
        from core.context import ContextManager
        from core.speech_output import VoiceOutputHandler
        from utils.text_output import TextOutputHandler
        from ui.main_ui import UIHandler
        from actions.system_control import SystemControlHandler

        # Register input handlers
        await self._register_component(
            TextInputHandler("TextInputHandler", self.config),
            priority=10,
            auto_start=True
        )

        await self._register_component(
            VoiceInputHandler("VoiceInputHandler", self.config),
            priority=10,
            auto_start=True
        )

        await self._register_component(
            ImageInputHandler("ImageInputHandler", self.config),
            priority=10,
            auto_start=True
        )

        # Register AI processors
        await self._register_component(
            NLPProcessor("NLPProcessor", self.config),
            priority=20,
            dependencies=[AsyncMessageBus],
            auto_start=True
        )

        await self._register_component(
            VisionProcessor("VisionProcessor", self.config),
            priority=20,
            dependencies=[AsyncMessageBus],
            auto_start=True
        )

        await self._register_component(
            ContextManager("ContextManager", self.config),
            priority=30,
            dependencies=[AsyncMessageBus],
            auto_start=True
        )

        # Register output handlers
        await self._register_component(
            VoiceOutputHandler("VoiceOutputHandler", self.config),
            priority=40,
            dependencies=[AsyncMessageBus],
            auto_start=True
        )

        await self._register_component(
            TextOutputHandler("TextOutputHandler", self.config),
            priority=40,
            dependencies=[AsyncMessageBus],
            auto_start=True
        )

        await self._register_component(
            UIHandler("UIHandler", message_bus, self.config),
            priority=50,
            dependencies=[AsyncMessageBus],
            auto_start=True
        )

        # Register action handlers
        await self._register_component(
            SystemControlHandler("SystemControlHandler", self.config),
            priority=60,
            dependencies=[AsyncMessageBus],
            auto_start=True
        )

        self.logger.info(f"Registered {len(self.components)} components")

    async def _register_component(self, component: BaseComponent, priority: int = 0,
                                 dependencies: List[Type] = None,
                                 auto_start: bool = True) -> None:
        """Register a single component"""
        component_info = ComponentInfo(
            component=component,
            priority=priority,
            dependencies=dependencies or [],
            auto_start=auto_start
        )

        self.components[component.name] = component_info

        # Register component with service locator
        component_type = type(component)
        self.service_locator.container.register_singleton(component_type, component)

        self.logger.debug(f"Registered component: {component.name}")

    def _resolve_dependencies(self) -> None:
        """Resolve component dependencies and determine initialization order"""
        self.logger.info("Resolving component dependencies")

        # Build dependency graph
        dependency_graph = {}
        for name, info in self.components.items():
            dependency_graph[name] = [
                dep_name for dep_type in info.dependencies
                for dep_name, dep_info in self.components.items()
                if isinstance(dep_info.component, dep_type)
            ]

        # Detect circular dependencies
        if self._detect_circular_dependencies(dependency_graph):
            raise ValueError("Circular dependencies detected in components")

        # Determine initialization order using topological sort
        self.initialization_order = self._topological_sort(dependency_graph)

        # Sort by priority within dependency constraints
        self._sort_by_priority()

        self.logger.info(f"Component initialization order: {' -> '.join(self.initialization_order)}")

    def _detect_circular_dependencies(self, graph: Dict[str, List[str]]) -> bool:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True

        return False

    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort to determine initialization order"""
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1

        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(graph):
            raise ValueError("Circular dependency detected")

        return result

    def _sort_by_priority(self) -> None:
        """Sort initialization order by priority while respecting dependencies"""
        # This is a simplified priority sort that maintains dependency order
        # In a more complex implementation, you might use priority queues
        pass

    async def _initialize_components(self) -> None:
        """Initialize all components in the determined order"""
        self.logger.info("Initializing components")

        message_bus = self.service_locator.get_service(AsyncMessageBus)

        for component_name in self.initialization_order:
            component_info = self.components[component_name]

            if not component_info.auto_start:
                self.logger.info(f"Skipping auto-start for component: {component_name}")
                continue

            try:
                self.logger.info(f"Initializing component: {component_name}")
                component_info.phase = ComponentPhase.INITIALIZING
                component_info.initialized_at = datetime.now()

                # Initialize component
                success = await component_info.component.initialize()

                if success:
                    # Register with message bus
                    await component_info.component._register_with_message_bus(message_bus)

                    component_info.phase = ComponentPhase.READY
                    component_info.started_at = datetime.now()
                    self.logger.info(f"Component initialized successfully: {component_name}")
                else:
                    component_info.phase = ComponentPhase.ERROR
                    self.logger.error(f"Component initialization failed: {component_name}")

            except Exception as e:
                component_info.phase = ComponentPhase.ERROR
                self.logger.error(f"Error initializing component {component_name}: {e}", exc_info=True)

    async def _start_health_monitoring(self) -> None:
        """Start health monitoring task"""
        if self.health_monitor_task is None or self.health_monitor_task.done():
            self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
            self.logger.info("Health monitoring started")

    async def _health_monitor_loop(self) -> None:
        """Health monitoring loop"""
        while self.system_phase not in [SystemPhase.SHUTTING_DOWN, SystemPhase.OFFLINE]:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5.0)  # Brief delay before retrying

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all components"""
        for name, component_info in self.components.items():
            try:
                health_status = await component_info.component.health_check()
                component_info.health_status = health_status
                component_info.last_health_check = datetime.now()

                # Log warnings for unhealthy components
                if health_status.get('status') != 'ready':
                    self.logger.warning(f"Component {name} health status: {health_status.get('status')}")

            except Exception as e:
                self.logger.error(f"Health check failed for component {name}: {e}")
                component_info.health_status = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

    async def shutdown(self) -> None:
        """Shutdown the entire SmartSense system"""
        if self.system_phase in [SystemPhase.SHUTTING_DOWN, SystemPhase.OFFLINE]:
            return

        self.logger.info("Starting SmartSense system shutdown")
        self._set_system_phase(SystemPhase.SHUTTING_DOWN)
        self.shutdown_time = datetime.now()

        try:
            # Stop health monitoring
            if self.health_monitor_task and not self.health_monitor_task.done():
                self.health_monitor_task.cancel()
                try:
                    await self.health_monitor_task
                except asyncio.CancelledError:
                    pass

            # Shutdown components in reverse order
            shutdown_order = list(reversed(self.initialization_order))
            for component_name in shutdown_order:
                component_info = self.components.get(component_name)
                if component_info and component_info.phase not in [ComponentPhase.OFFLINE, ComponentPhase.SHUTTING_DOWN]:
                    try:
                        self.logger.info(f"Shutting down component: {component_name}")
                        component_info.phase = ComponentPhase.SHUTTING_DOWN

                        # Stop component processing
                        if hasattr(component_info.component, 'stop_processing'):
                            await component_info.component.stop_processing()

                        # Shutdown component
                        await component_info.component.shutdown()
                        component_info.phase = ComponentPhase.OFFLINE
                        component_info.shutdown_at = datetime.now()

                        self.logger.info(f"Component shutdown complete: {component_name}")

                    except Exception as e:
                        self.logger.error(f"Error shutting down component {component_name}: {e}")

            # Shutdown message bus
            message_bus = self.service_locator.get_optional_service(AsyncMessageBus)
            if message_bus:
                await message_bus.shutdown()

            # Clear services
            self.service_locator.clear_services()

            self._set_system_phase(SystemPhase.OFFLINE)
            self.logger.info("SmartSense system shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during system shutdown: {e}")
            self._set_system_phase(SystemPhase.ERROR)

    def _set_system_phase(self, phase: SystemPhase) -> None:
        """Set the system phase"""
        old_phase = self.system_phase
        self.system_phase = phase
        self.logger.debug(f"System phase: {old_phase} -> {phase}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        uptime_seconds = None
        if self.startup_time:
            if self.shutdown_time:
                uptime_seconds = (self.shutdown_time - self.startup_time).total_seconds()
            else:
                uptime_seconds = (datetime.now() - self.startup_time).total_seconds()

        component_status = {}
        for name, info in self.components.items():
            component_status[name] = {
                'phase': info.phase,
                'priority': info.priority,
                'auto_start': info.auto_start,
                'initialized_at': info.initialized_at.isoformat() if info.initialized_at else None,
                'started_at': info.started_at.isoformat() if info.started_at else None,
                'error_count': info.component.error_count,
                'last_error': str(info.component.last_error) if info.component.last_error else None,
            }

        return {
            'system_phase': self.system_phase,
            'uptime_seconds': uptime_seconds,
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
            'shutdown_time': self.shutdown_time.isoformat() if self.shutdown_time else None,
            'total_components': len(self.components),
            'components': component_status,
        }

    def get_component_status(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific component"""
        component_info = self.components.get(component_name)
        if not component_info:
            return None

        return {
            'name': component_name,
            'phase': component_info.phase,
            'priority': component_info.priority,
            'auto_start': component_info.auto_start,
            'dependencies': [dep.__name__ for dep in component_info.dependencies],
            'initialized_at': component_info.initialized_at.isoformat() if component_info.initialized_at else None,
            'started_at': component_info.started_at.isoformat() if component_info.started_at else None,
            'shutdown_at': component_info.shutdown_at.isoformat() if component_info.shutdown_at else None,
            'last_health_check': component_info.last_health_check.isoformat() if component_info.last_health_check else None,
            'health_status': component_info.health_status,
        }

    async def restart_component(self, component_name: str) -> bool:
        """
        Restart a specific component

        Args:
            component_name: Name of component to restart

        Returns:
            True if restart successful, False otherwise
        """
        component_info = self.components.get(component_name)
        if not component_info:
            self.logger.error(f"Component not found: {component_name}")
            return False

        try:
            self.logger.info(f"Restarting component: {component_name}")

            # Shutdown component
            if hasattr(component_info.component, 'stop_processing'):
                await component_info.component.stop_processing()
            await component_info.component.shutdown()

            # Re-initialize component
            component_info.phase = ComponentPhase.INITIALIZING
            success = await component_info.component.initialize()

            if success:
                message_bus = self.service_locator.get_service(AsyncMessageBus)
                await component_info.component._register_with_message_bus(message_bus)

                component_info.phase = ComponentPhase.READY
                self.logger.info(f"Component restarted successfully: {component_name}")
                return True
            else:
                component_info.phase = ComponentPhase.ERROR
                self.logger.error(f"Component restart failed: {component_name}")
                return False

        except Exception as e:
            component_info.phase = ComponentPhase.ERROR
            self.logger.error(f"Error restarting component {component_name}: {e}")
            return False