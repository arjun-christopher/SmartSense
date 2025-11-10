#!/usr/bin/env python3
"""
Event bus demonstration for SmartSense.

This example shows how the asynchronous message bus works.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.message_bus import AsyncMessageBus
from models.events import Event, EventType


class DemoSubscriber:
    """Demo subscriber that handles events"""
    
    def __init__(self, name: str):
        self.name = name
        self.events_received = 0
    
    async def handle_event(self, event: Event):
        """Handle an event"""
        self.events_received += 1
        print(f"[{self.name}] Received {event.event_type}")
        print(f"  Event ID: {event.event_id}")
        print(f"  Source: {event.source}")
        print(f"  Data: {event.data}")
        print()


async def main():
    """Run the message bus demo"""
    print("=" * 60)
    print("SmartSense - Message Bus Demo")
    print("=" * 60)
    print()

    # Create and initialize message bus
    print("Initializing message bus...")
    message_bus = AsyncMessageBus(max_queue_size=100, processing_timeout=10)
    await message_bus.initialize()
    print("Message bus ready!\n")

    # Create demo subscribers
    subscriber1 = DemoSubscriber("Subscriber 1")
    subscriber2 = DemoSubscriber("Subscriber 2")
    subscriber3 = DemoSubscriber("Subscriber 3")

    # Subscribe to different event types
    print("Setting up subscriptions...")
    await message_bus.subscribe(
        EventType.TEXT_INPUT_EVENT,
        subscriber1.handle_event,
        "Subscriber 1"
    )
    
    await message_bus.subscribe(
        EventType.TEXT_INPUT_EVENT,
        subscriber2.handle_event,
        "Subscriber 2"
    )
    
    await message_bus.subscribe(
        EventType.NLP_RESPONSE_EVENT,
        subscriber3.handle_event,
        "Subscriber 3"
    )
    
    print("Subscriptions complete!\n")
    print("-" * 60)
    print()

    # Publish some events
    print("Publishing events...\n")

    # Event 1: Text input
    event1 = Event(
        event_type=EventType.TEXT_INPUT_EVENT,
        data={"text": "Hello, SmartSense!"},
        source="Demo",
        event_id="demo-001"
    )
    await message_bus.publish(event1)
    await asyncio.sleep(0.5)  # Give time for processing

    # Event 2: Another text input
    event2 = Event(
        event_type=EventType.TEXT_INPUT_EVENT,
        data={"text": "How are you?"},
        source="Demo",
        event_id="demo-002"
    )
    await message_bus.publish(event2)
    await asyncio.sleep(0.5)

    # Event 3: NLP response
    event3 = Event(
        event_type=EventType.NLP_RESPONSE_EVENT,
        data={
            "intent": "greeting",
            "sentiment": "positive",
            "processed_text": "Hi there!"
        },
        source="NLPProcessor",
        event_id="demo-003"
    )
    await message_bus.publish(event3)
    await asyncio.sleep(0.5)

    # Event 4: High priority event
    event4 = Event(
        event_type=EventType.TEXT_INPUT_EVENT,
        data={"text": "Emergency!"},
        source="Demo",
        event_id="demo-004"
    )
    await message_bus.publish(event4, priority=10)  # High priority
    await asyncio.sleep(0.5)

    print("-" * 60)
    print()
    print("Event publishing complete!\n")

    # Display statistics
    print("Message Bus Statistics:")
    print(f"  Events published: {message_bus._stats['events_published']}")
    print(f"  Events processed: {message_bus._stats['events_processed']}")
    print(f"  Events failed: {message_bus._stats['events_failed']}")
    print(f"  Active subscriptions: {len(message_bus._subscriptions)}")
    print()

    print("Subscriber Statistics:")
    print(f"  {subscriber1.name}: {subscriber1.events_received} events")
    print(f"  {subscriber2.name}: {subscriber2.events_received} events")
    print(f"  {subscriber3.name}: {subscriber3.events_received} events")
    print()

    # Shutdown
    print("Shutting down message bus...")
    await message_bus.shutdown()
    print("Message bus stopped.\n")

    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
