"""
Base classes for all SmartSense components.

This module defines abstract base classes that provide a consistent interface
and common functionality for all components in the SmartSense system.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Type
from datetime import datetime
import uuid

from models.events import Event, EventType
from models.config import SmartSenseConfig
from utils.logger import get_logger


class ComponentStatus(str):
    """Component status enumeration"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    OFFLINE = "offline"


class BaseComponent(ABC):
    """Abstract base class for all SmartSense components"""

    def __init__(self, name: str, config: Optional[SmartSenseConfig] = None):
        self.name = name
        self.config = config
        self.logger = get_logger(f"{__name__}.{name}")
        self._status = ComponentStatus.INITIALIZING
        self._message_bus = None
        self._subscriptions: Dict[str, str] = {}  # event_type -> subscription_id
        self._event_handlers: Dict[str, Callable] = {}
        self._initialized = False
        self._startup_time: Optional[datetime] = None
        self._error_count = 0
        self._last_error: Optional[Exception] = None

    @property
    def status(self) -> str:
        """Get component status"""
        return self._status

    @property
    def is_initialized(self) -> bool:
        """Check if component is initialized"""
        return self._initialized

    @property
    def uptime_seconds(self) -> Optional[float]:
        """Get component uptime in seconds"""
        if self._startup_time is None:
            return None
        return (datetime.now() - self._startup_time).total_seconds()

    @property
    def error_count(self) -> int:
        """Get number of errors encountered"""
        return self._error_count

    @property
    def last_error(self) -> Optional[Exception]:
        """Get last error encountered"""
        return self._last_error

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the component

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the component and clean up resources"""
        pass

    async def _register_with_message_bus(self, message_bus) -> None:
        """Register component with message bus"""
        self._message_bus = message_bus
        await self._setup_event_subscriptions()

    async def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions (override in subclasses)"""
        pass

    async def subscribe_to_event(self, event_type: EventType, handler: Callable) -> str:
        """
        Subscribe to an event type

        Args:
            event_type: Type of event to subscribe to
            handler: Handler function for the event

        Returns:
            Subscription ID
        """
        if self._message_bus is None:
            raise RuntimeError("Component not registered with message bus")

        subscription_id = await self._message_bus.subscribe(event_type, handler)
        self._subscriptions[event_type] = subscription_id
        self._event_handlers[event_type] = handler

        self.logger.debug(f"Subscribed to {event_type} with ID {subscription_id}")
        return subscription_id

    async def unsubscribe_from_event(self, event_type: EventType) -> None:
        """
        Unsubscribe from an event type

        Args:
            event_type: Type of event to unsubscribe from
        """
        if self._message_bus is None:
            return

        if event_type in self._subscriptions:
            subscription_id = self._subscriptions[event_type]
            await self._message_bus.unsubscribe(subscription_id)
            del self._subscriptions[event_type]
            del self._event_handlers[event_type]

            self.logger.debug(f"Unsubscribed from {event_type}")

    async def publish_event(self, event: Event) -> None:
        """
        Publish an event to the message bus

        Args:
            event: Event to publish
        """
        if self._message_bus is None:
            raise RuntimeError("Component not registered with message bus")

        event.source = self.name
        await self._message_bus.publish(event)

    def _set_status(self, status: str) -> None:
        """Set component status"""
        old_status = self._status
        self._status = status
        self.logger.debug(f"Status changed: {old_status} -> {status}")

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """
        Handle an error

        Args:
            error: The error that occurred
            context: Context where the error occurred
        """
        self._error_count += 1
        self._last_error = error
        self._set_status(ComponentStatus.ERROR)

        error_msg = f"Error in {self.name}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {error}"

        self.logger.error(error_msg, exc_info=True)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check

        Returns:
            Health check results
        """
        return {
            'component': self.name,
            'status': self._status,
            'initialized': self._initialized,
            'uptime_seconds': self.uptime_seconds,
            'error_count': self._error_count,
            'last_error': str(self._last_error) if self._last_error else None,
            'subscriptions': list(self._subscriptions.keys()),
            'timestamp': datetime.now().isoformat(),
        }


class BaseInputHandler(BaseComponent):
    """Base class for input handlers"""

    def __init__(self, name: str, config: Optional[SmartSenseConfig] = None):
        super().__init__(name, config)
        self._input_queue = asyncio.Queue(maxsize=100)
        self._processing = False

    @abstractmethod
    async def process_input(self, input_data: Any) -> Optional[Event]:
        """
        Process input data and create event

        Args:
            input_data: Raw input data

        Returns:
            Event or None if processing failed
        """
        pass

    async def start_processing(self) -> None:
        """Start processing input queue"""
        if self._processing:
            return

        self._processing = True
        self._set_status(ComponentStatus.BUSY)
        self.logger.info(f"Starting input processing for {self.name}")

        asyncio.create_task(self._process_queue())

    async def stop_processing(self) -> None:
        """Stop processing input queue"""
        self._processing = False
        self._set_status(ComponentStatus.READY)
        self.logger.info(f"Stopping input processing for {self.name}")

    async def _process_queue(self) -> None:
        """Process items from input queue"""
        while self._processing:
            try:
                # Wait for input with timeout
                input_data = await asyncio.wait_for(self._input_queue.get(), timeout=1.0)

                # Process input and publish event
                event = await self.process_input(input_data)
                if event:
                    await self.publish_event(event)

                self._input_queue.task_done()

            except asyncio.TimeoutError:
                # No input available, continue loop
                continue
            except Exception as e:
                self._handle_error(e, "processing input queue")

    async def add_input(self, input_data: Any) -> bool:
        """
        Add input data to processing queue

        Args:
            input_data: Input data to process

        Returns:
            True if added successfully, False if queue is full
        """
        try:
            self._input_queue.put_nowait(input_data)
            return True
        except asyncio.QueueFull:
            self.logger.warning("Input queue is full, dropping input")
            return False


class BaseProcessor(BaseComponent):
    """Base class for AI processors"""

    def __init__(self, name: str, config: Optional[SmartSenseConfig] = None):
        super().__init__(name, config)
        self._processing_semaphore = asyncio.Semaphore(5)  # Limit concurrent processing
        self._active_tasks: List[asyncio.Task] = []

    @abstractmethod
    async def process_event(self, event: Event) -> Optional[Event]:
        """
        Process an event and return result event

        Args:
            event: Input event to process

        Returns:
            Result event or None if processing failed
        """
        pass

    async def _process_with_semaphore(self, event: Event) -> None:
        """Process event with semaphore to limit concurrency"""
        async with self._processing_semaphore:
            try:
                self._set_status(ComponentStatus.BUSY)

                # Process the event
                result_event = await self.process_event(event)

                # Publish result if available
                if result_event:
                    await self.publish_event(result_event)

            except Exception as e:
                self._handle_error(e, f"processing {event.event_type}")
            finally:
                self._set_status(ComponentStatus.READY)

    async def get_queue_size(self) -> int:
        """Get the number of active processing tasks"""
        return len(self._active_tasks)

    async def cancel_all_tasks(self) -> None:
        """Cancel all active processing tasks"""
        for task in self._active_tasks:
            task.cancel()

        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
            self._active_tasks.clear()


class BaseOutputHandler(BaseComponent):
    """Base class for output handlers"""

    def __init__(self, name: str, config: Optional[SmartSenseConfig] = None):
        super().__init__(name, config)
        self._output_queue = asyncio.Queue(maxsize=100)
        self._processing = False

    @abstractmethod
    async def handle_output(self, event: Event) -> bool:
        """
        Handle output event

        Args:
            event: Output event to handle

        Returns:
            True if handled successfully, False otherwise
        """
        pass

    async def start_processing(self) -> None:
        """Start processing output queue"""
        if self._processing:
            return

        self._processing = True
        self._set_status(ComponentStatus.BUSY)
        self.logger.info(f"Starting output processing for {self.name}")

        asyncio.create_task(self._process_queue())

    async def stop_processing(self) -> None:
        """Stop processing output queue"""
        self._processing = False
        self._set_status(ComponentStatus.READY)
        self.logger.info(f"Stopping output processing for {self.name}")

    async def _process_queue(self) -> None:
        """Process items from output queue"""
        while self._processing:
            try:
                # Wait for output with timeout
                event = await asyncio.wait_for(self._output_queue.get(), timeout=1.0)

                # Handle output
                success = await self.handle_output(event)
                if not success:
                    self.logger.warning(f"Failed to handle output event: {event.event_id}")

                self._output_queue.task_done()

            except asyncio.TimeoutError:
                # No output available, continue loop
                continue
            except Exception as e:
                self._handle_error(e, "processing output queue")

    async def add_output(self, event: Event) -> bool:
        """
        Add output event to processing queue

        Args:
            event: Output event to handle

        Returns:
            True if added successfully, False if queue is full
        """
        try:
            self._output_queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            self.logger.warning("Output queue is full, dropping output")
            return False


class BaseActionHandler(BaseComponent):
    """Base class for action handlers"""

    def __init__(self, name: str, config: Optional[SmartSenseConfig] = None):
        super().__init__(name, config)
        self._action_history: List[Dict[str, Any]] = []
        self._max_history = 1000

    @abstractmethod
    async def execute_action(self, event: Event) -> Dict[str, Any]:
        """
        Execute action based on event

        Args:
            event: Action event

        Returns:
            Action execution result
        """
        pass

    async def _record_action(self, event: Event, result: Dict[str, Any]) -> None:
        """
        Record action execution in history

        Args:
            event: Action event
            result: Execution result
        """
        action_record = {
            'timestamp': datetime.now().isoformat(),
            'event_id': event.event_id,
            'event_type': event.event_type,
            'command': event.data.get('command', 'unknown'),
            'success': result.get('success', False),
            'execution_time': result.get('execution_time', 0.0),
            'result': result,
        }

        self._action_history.append(action_record)

        # Limit history size
        if len(self._action_history) > self._max_history:
            self._action_history = self._action_history[-self._max_history:]

    def get_action_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get action history

        Args:
            limit: Maximum number of records to return

        Returns:
            List of action records
        """
        if limit is None:
            return self._action_history.copy()
        return self._action_history[-limit:]

    def get_action_statistics(self) -> Dict[str, Any]:
        """
        Get action execution statistics

        Returns:
            Action statistics
        """
        if not self._action_history:
            return {
                'total_actions': 0,
                'successful_actions': 0,
                'failed_actions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
            }

        total_actions = len(self._action_history)
        successful_actions = sum(1 for record in self._action_history if record['success'])
        failed_actions = total_actions - successful_actions
        success_rate = successful_actions / total_actions if total_actions > 0 else 0.0

        execution_times = [record['execution_time'] for record in self._action_history]
        average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0

        return {
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'failed_actions': failed_actions,
            'success_rate': success_rate,
            'average_execution_time': average_execution_time,
        }