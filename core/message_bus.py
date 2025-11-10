"""
Async message bus implementation for SmartSense AI Assistant.

This module provides a high-performance, async message bus that enables
loose coupling between components through event-driven communication.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional, Set
from collections import defaultdict
import weakref

from models.events import Event, EventType
from utils.logger import get_logger


class SubscriptionInfo:
    """Information about an event subscription"""

    def __init__(self, subscription_id: str, event_type: EventType, handler: Callable,
                 component_name: str, filter_func: Optional[Callable] = None):
        self.subscription_id = subscription_id
        self.event_type = event_type
        self.handler = handler
        self.component_name = component_name
        self.filter_func = filter_func
        self.created_at = datetime.now()
        self.events_processed = 0
        self.last_processed = None
        self.error_count = 0
        self.is_active = True

    def should_process_event(self, event: Event) -> bool:
        """Check if event should be processed by this subscription"""
        if not self.is_active:
            return False

        if self.filter_func:
            try:
                return self.filter_func(event)
            except Exception:
                # If filter fails, process the event
                return True

        return True

    def record_processed_event(self) -> None:
        """Record that an event was processed"""
        self.events_processed += 1
        self.last_processed = datetime.now()

    def record_error(self) -> None:
        """Record an error in processing"""
        self.error_count += 1


class EventQueue:
    """Queue for events with priority support"""

    def __init__(self, max_size: int = 1000):
        self._queue = asyncio.PriorityQueue(maxsize=max_size)
        self._counter = 0  # Counter for maintaining insertion order

    async def put(self, event: Event, priority: int = 0) -> None:
        """Put an event in the queue with priority"""
        # Use counter to maintain FIFO order for same priority
        self._counter += 1
        priority_tuple = (-priority, self._counter, event)
        await self._queue.put(priority_tuple)

    async def get(self) -> Event:
        """Get the next event from the queue"""
        _, _, event = await self._queue.get()
        return event

    def task_done(self) -> None:
        """Mark a task as done"""
        self._queue.task_done()

    def qsize(self) -> int:
        """Get queue size"""
        return self._queue.qsize()

    def empty(self) -> bool:
        """Check if queue is empty"""
        return self._queue.empty()

    def full(self) -> bool:
        """Check if queue is full"""
        return self._queue.full()


class AsyncMessageBus:
    """
    High-performance asynchronous message bus for event-driven communication.

    Features:
    - Async event publishing and processing
    - Event filtering and routing
    - Priority queue support
    - Performance monitoring and statistics
    - Automatic cleanup of failed handlers
    - Event replay capabilities
    """

    def __init__(self, max_queue_size: int = 1000, processing_timeout: int = 30,
                 retry_attempts: int = 3):
        self.logger = get_logger(__name__)

        # Configuration
        self.max_queue_size = max_queue_size
        self.processing_timeout = processing_timeout
        self.retry_attempts = retry_attempts

        # Event queues
        self._event_queue = EventQueue(max_size=max_queue_size)
        self._priority_queue = EventQueue(max_size=max_queue_size // 4)  # Smaller priority queue

        # Subscriptions management
        self._subscriptions: Dict[str, SubscriptionInfo] = {}
        self._event_subscriptions: Dict[EventType, Set[str]] = defaultdict(set)
        self._component_subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Processing state
        self._processing = False
        self._processor_tasks: List[asyncio.Task] = []
        self._num_processors = 4  # Number of concurrent processor tasks

        # Statistics
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'events_dropped': 0,
            'subscriptions_created': 0,
            'subscriptions_removed': 0,
            'start_time': None,
        }

        # Event history for replay (limited size)
        self._event_history: List[Event] = []
        self._max_history_size = 1000

    async def initialize(self) -> None:
        """Initialize the message bus and start processing"""
        if self._processing:
            return

        self.logger.info("Initializing AsyncMessageBus")
        self._stats['start_time'] = datetime.now()
        self._processing = True

        # Start processor tasks
        for i in range(self._num_processors):
            task = asyncio.create_task(self._process_events(f"processor-{i}"))
            self._processor_tasks.append(task)

        self.logger.info(f"Message bus initialized with {self._num_processors} processors")

    async def shutdown(self) -> None:
        """Shutdown the message bus"""
        if not self._processing:
            return

        self.logger.info("Shutting down AsyncMessageBus")
        self._processing = False

        # Cancel processor tasks
        for task in self._processor_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._processor_tasks:
            await asyncio.gather(*self._processor_tasks, return_exceptions=True)

        self._processor_tasks.clear()
        self.logger.info("Message bus shutdown complete")

    async def publish(self, event: Event, priority: int = 0) -> None:
        """
        Publish an event to the message bus

        Args:
            event: Event to publish
            priority: Event priority (higher = more important)
        """
        if not self._processing:
            raise RuntimeError("Message bus not initialized")

        # Ensure event has ID and timestamp
        if not hasattr(event, 'event_id') or not event.event_id:
            event.event_id = str(uuid.uuid4())

        if not hasattr(event, 'timestamp') or not event.timestamp:
            event.timestamp = datetime.now()

        # Add to event history
        self._add_to_history(event)

        # Choose queue based on priority
        if priority > 5:  # High priority events
            queue = self._priority_queue
        else:
            queue = self._event_queue

        try:
            await queue.put(event, priority)
            self._stats['events_published'] += 1
            self.logger.debug(f"Published event {event.event_type} ({event.event_id})")
        except asyncio.QueueFull:
            self._stats['events_dropped'] += 1
            self.logger.warning(f"Event queue full, dropping event {event.event_id}")

    async def subscribe(self, event_type: EventType, handler: Callable,
                       component_name: str = "unknown",
                       filter_func: Optional[Callable] = None) -> str:
        """
        Subscribe to an event type

        Args:
            event_type: Type of event to subscribe to
            handler: Async handler function
            component_name: Name of the component subscribing
            filter_func: Optional filter function for events

        Returns:
            Subscription ID
        """
        subscription_id = str(uuid.uuid4())

        subscription = SubscriptionInfo(
            subscription_id=subscription_id,
            event_type=event_type,
            handler=handler,
            component_name=component_name,
            filter_func=filter_func
        )

        # Store subscription
        self._subscriptions[subscription_id] = subscription
        self._event_subscriptions[event_type].add(subscription_id)
        self._component_subscriptions[component_name].add(subscription_id)

        self._stats['subscriptions_created'] += 1

        self.logger.debug(f"Component {component_name} subscribed to {event_type} "
                         f"with ID {subscription_id}")

        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from events

        Args:
            subscription_id: Subscription ID to remove
        """
        if subscription_id not in self._subscriptions:
            return

        subscription = self._subscriptions[subscription_id]
        subscription.is_active = False

        # Remove from mappings
        self._event_subscriptions[subscription.event_type].discard(subscription_id)
        self._component_subscriptions[subscription.component_name].discard(subscription_id)
        del self._subscriptions[subscription_id]

        self._stats['subscriptions_removed'] += 1
        self.logger.debug(f"Removed subscription {subscription_id}")

    async def _process_events(self, processor_name: str) -> None:
        """Process events from the queues"""
        self.logger.debug(f"Starting event processor: {processor_name}")

        while self._processing:
            try:
                # Try to get from priority queue first (shorter timeout)
                event = None
                try:
                    event = await asyncio.wait_for(
                        self._priority_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    # Try regular queue
                    try:
                        event = await asyncio.wait_for(
                            self._event_queue.get(),
                            timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        continue  # No events available

                if event:
                    await self._handle_event(event, processor_name)
                    # Mark task as done (we don't track which queue it came from)

            except Exception as e:
                self.logger.error(f"Error in processor {processor_name}: {e}")
                await asyncio.sleep(0.1)  # Brief delay before retrying

        self.logger.debug(f"Event processor {processor_name} stopped")

    async def _handle_event(self, event: Event, processor_name: str) -> None:
        """Handle a single event"""
        # Get subscriptions for this event type
        subscription_ids = self._event_subscriptions.get(event.event_type, set())

        if not subscription_ids:
            self.logger.debug(f"No subscriptions for event type {event.event_type}")
            return

        # Create tasks for all subscriptions
        handler_tasks = []
        for subscription_id in subscription_ids:
            subscription = self._subscriptions.get(subscription_id)
            if subscription and subscription.should_process_event(event):
                task = asyncio.create_task(
                    self._call_handler(subscription, event, processor_name)
                )
                handler_tasks.append(task)

        # Wait for all handlers to complete (with timeout)
        if handler_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*handler_tasks, return_exceptions=True),
                    timeout=self.processing_timeout
                )
                self._stats['events_processed'] += 1
            except asyncio.TimeoutError:
                self._stats['events_failed'] += 1
                self.logger.warning(f"Timeout processing event {event.event_id}")

    async def _call_handler(self, subscription: SubscriptionInfo,
                           event: Event, processor_name: str) -> None:
        """Call a subscription handler with error handling and retries"""
        for attempt in range(self.retry_attempts + 1):
            try:
                # Call the handler
                if asyncio.iscoroutinefunction(subscription.handler):
                    await subscription.handler(event)
                else:
                    # Run sync function in executor
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, subscription.handler, event)

                # Record successful processing
                subscription.record_processed_event()
                break

            except Exception as e:
                subscription.record_error()

                if attempt < self.retry_attempts:
                    # Retry with exponential backoff
                    delay = 0.1 * (2 ** attempt)
                    self.logger.warning(
                        f"Handler error (attempt {attempt + 1}/{self.retry_attempts + 1}) "
                        f"for subscription {subscription.subscription_id}: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    # All retries failed
                    self.logger.error(
                        f"Handler failed after {self.retry_attempts + 1} attempts "
                        f"for subscription {subscription.subscription_id}: {e}",
                        exc_info=True
                    )

    def _add_to_history(self, event: Event) -> None:
        """Add event to history buffer"""
        self._event_history.append(event)

        # Limit history size
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]

    async def replay_events(self, event_type: Optional[EventType] = None,
                           component_name: Optional[str] = None,
                           since: Optional[datetime] = None) -> int:
        """
        Replay events from history

        Args:
            event_type: Filter by event type
            component_name: Filter by component name
            since: Filter events since this time

        Returns:
            Number of events replayed
        """
        replayed_count = 0

        for event in self._event_history:
            # Apply filters
            if event_type and event.event_type != event_type:
                continue
            if since and event.timestamp < since:
                continue

            # Republish event with low priority to avoid conflicts
            await self.publish(event, priority=-1)
            replayed_count += 1

        self.logger.info(f"Replayed {replayed_count} events")
        return replayed_count

    def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        current_time = datetime.now()
        uptime_seconds = None
        if self._stats['start_time']:
            uptime_seconds = (current_time - self._stats['start_time']).total_seconds()

        active_subscriptions = sum(1 for sub in self._subscriptions.values() if sub.is_active)

        return {
            'uptime_seconds': uptime_seconds,
            'processing': self._processing,
            'queue_sizes': {
                'regular': self._event_queue.qsize(),
                'priority': self._priority_queue.qsize(),
            },
            'subscriptions': {
                'total': len(self._subscriptions),
                'active': active_subscriptions,
                'by_event_type': {
                    event_type.value: len(subs)
                    for event_type, subs in self._event_subscriptions.items()
                },
                'by_component': {
                    component: len(subs)
                    for component, subs in self._component_subscriptions.items()
                },
            },
            'statistics': self._stats.copy(),
            'history_size': len(self._event_history),
        }

    def get_subscription_info(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a subscription"""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None

        return {
            'subscription_id': subscription.subscription_id,
            'event_type': subscription.event_type.value,
            'component_name': subscription.component_name,
            'created_at': subscription.created_at.isoformat(),
            'events_processed': subscription.events_processed,
            'error_count': subscription.error_count,
            'last_processed': subscription.last_processed.isoformat() if subscription.last_processed else None,
            'is_active': subscription.is_active,
        }

    def get_component_subscriptions(self, component_name: str) -> List[Dict[str, Any]]:
        """Get all subscriptions for a component"""
        subscription_ids = self._component_subscriptions.get(component_name, set())
        return [
            self.get_subscription_info(sub_id)
            for sub_id in subscription_ids
            if sub_id in self._subscriptions
        ]

    async def clear_queue(self, queue_type: str = "all") -> int:
        """
        Clear event queues

        Args:
            queue_type: Type of queue to clear ("regular", "priority", "all")

        Returns:
            Number of events cleared
        """
        cleared_count = 0

        if queue_type in ("regular", "all"):
            cleared_count += self._event_queue.qsize()
            while not self._event_queue.empty():
                try:
                    self._event_queue.get_nowait()
                    self._event_queue.task_done()
                except asyncio.QueueEmpty:
                    break

        if queue_type in ("priority", "all"):
            cleared_count += self._priority_queue.qsize()
            while not self._priority_queue.empty():
                try:
                    self._priority_queue.get_nowait()
                    self._priority_queue.task_done()
                except asyncio.QueueEmpty:
                    break

        self.logger.info(f"Cleared {cleared_count} events from {queue_type} queue(s)")
        return cleared_count