"""
Context manager for SmartSense AI Assistant.

This component maintains conversation and application context,
including short-term memory, long-term memory, and context retrieval.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from models.events import Event, EventType, ContextData
from models.config import SmartSenseConfig
from core.base import BaseProcessor
from utils.logger import get_logger


class ContextManager(BaseProcessor):
    """Context management component"""

    def __init__(self, name: str, config: Optional[SmartSenseConfig] = None):
        super().__init__(name, config)
        self._short_term_memory: List[Dict[str, Any]] = []
        self._long_term_memory: List[Dict[str, Any]] = []
        self._max_short_term = 20
        self._max_long_term = 1000

    async def initialize(self) -> bool:
        """Initialize the context manager"""
        try:
            self.logger.info("Initializing ContextManager")

            # Set up event subscriptions
            await self.subscribe_to_event(EventType.CONTEXT_UPDATE_EVENT, self._handle_context_update)
            await self.subscribe_to_event(EventType.NLP_RESPONSE_EVENT, self._handle_nlp_response)
            await self.subscribe_to_event(EventType.VISION_RESPONSE_EVENT, self._handle_vision_response)

            self._set_status("ready")
            self._initialized = True
            self.logger.info("ContextManager initialized successfully")
            return True

        except Exception as e:
            self._handle_error(e, "initialization")
            return False

    async def shutdown(self) -> None:
        """Shutdown the context manager"""
        self.logger.info("Shutting down ContextManager")

        # Cancel active tasks
        await self.cancel_all_tasks()

        # Unsubscribe from events
        await self.unsubscribe_from_event(EventType.CONTEXT_UPDATE_EVENT)
        await self.unsubscribe_from_event(EventType.NLP_RESPONSE_EVENT)
        await self.unsubscribe_from_event(EventType.VISION_RESPONSE_EVENT)

        self._set_status("offline")
        self.logger.info("ContextManager shutdown complete")

    async def process_event(self, event: Event) -> Optional[Event]:
        """Process context-related events"""
        try:
            if event.event_type == EventType.CONTEXT_UPDATE_EVENT:
                return await self._process_context_update(event)
            elif event.event_type == EventType.NLP_RESPONSE_EVENT:
                return await self._process_nlp_context(event)
            elif event.event_type == EventType.VISION_RESPONSE_EVENT:
                return await self._process_vision_context(event)
            else:
                return None

        except Exception as e:
            self._handle_error(e, f"processing {event.event_type}")
            return None

    async def _handle_context_update(self, event: Event) -> None:
        """Handle context update events"""
        await self._process_with_semaphore(event)

    async def _handle_nlp_response(self, event: Event) -> None:
        """Handle NLP response events for context"""
        await self._process_with_semaphore(event)

    async def _handle_vision_response(self, event: Event) -> None:
        """Handle vision response events for context"""
        await self._process_with_semaphore(event)

    async def _process_context_update(self, event: Event) -> Optional[Event]:
        """Process context update event"""
        try:
            context_data = event.data

            # Store in appropriate memory
            await self._store_context(context_data)

            # Create context response event
            response_event = Event(
                event_type=EventType.CONTEXT_RESPONSE_EVENT,
                data={
                    "context_stored": True,
                    "memory_type": context_data.get("context_type", "unknown"),
                    "total_items": len(self._short_term_memory) + len(self._long_term_memory)
                },
                source=self.name,
                correlation_id=event.event_id
            )

            return response_event

        except Exception as e:
            self.logger.error(f"Error processing context update: {e}")
            return None

    async def _process_nlp_context(self, event: Event) -> Optional[Event]:
        """Process NLP response for context"""
        try:
            nlp_data = event.data

            # Store conversation context
            context_item = {
                "type": "conversation",
                "timestamp": datetime.now().isoformat(),
                "intent": nlp_data.get("intent"),
                "sentiment": nlp_data.get("sentiment"),
                "text": nlp_data.get("original_text"),
                "response": nlp_data.get("processed_text")
            }

            await self._add_to_short_term_memory(context_item)

            return None  # No response needed for context storage

        except Exception as e:
            self.logger.error(f"Error processing NLP context: {e}")
            return None

    async def _process_vision_context(self, event: Event) -> Optional[Event]:
        """Process vision response for context"""
        try:
            vision_data = event.data

            # Store visual context
            context_item = {
                "type": "vision",
                "timestamp": datetime.now().isoformat(),
                "objects": vision_data.get("objects_detected", []),
                "scene": vision_data.get("scene_classification"),
                "text_found": vision_data.get("text_found")
            }

            await self._add_to_short_term_memory(context_item)

            return None  # No response needed for context storage

        except Exception as e:
            self.logger.error(f"Error processing vision context: {e}")
            return None

    async def _store_context(self, context_data: Dict[str, Any]) -> None:
        """Store context data in appropriate memory"""
        context_type = context_data.get("context_type", "short_term")

        if context_type == "long_term":
            await self._add_to_long_term_memory(context_data)
        else:
            await self._add_to_short_term_memory(context_data)

    async def _add_to_short_term_memory(self, context_item: Dict[str, Any]) -> None:
        """Add item to short-term memory"""
        self._short_term_memory.append(context_item)

        # Limit size
        if len(self._short_term_memory) > self._max_short_term:
            # Move oldest to long-term memory
            oldest = self._short_term_memory.pop(0)
            await self._add_to_long_term_memory(oldest)

    async def _add_to_long_term_memory(self, context_item: Dict[str, Any]) -> None:
        """Add item to long-term memory"""
        self._long_term_memory.append(context_item)

        # Limit size
        if len(self._long_term_memory) > self._max_long_term:
            # Remove oldest items
            self._long_term_memory = self._long_term_memory[-self._max_long_term:]

    async def get_relevant_context(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant context items based on query"""
        # Simple relevance scoring based on text matching
        relevant_items = []

        # Search short-term memory first
        for item in self._short_term_memory:
            score = self._calculate_relevance(item, query)
            if score > 0:
                relevant_items.append({**item, "relevance_score": score})

        # Search long-term memory if needed
        if len(relevant_items) < limit:
            for item in self._long_term_memory:
                score = self._calculate_relevance(item, query)
                if score > 0:
                    relevant_items.append({**item, "relevance_score": score})

        # Sort by relevance and limit
        relevant_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_items[:limit]

    def _calculate_relevance(self, item: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for context item"""
        query_lower = query.lower()
        score = 0.0

        # Check text fields
        for field in ["text", "response", "intent"]:
            if field in item and item[field]:
                if query_lower in str(item[field]).lower():
                    score += 1.0

        # Check recent items higher
        if "timestamp" in item:
            try:
                item_time = datetime.fromisoformat(item["timestamp"])
                age_hours = (datetime.now() - item_time).total_seconds() / 3600
                if age_hours < 1:
                    score += 0.5
                elif age_hours < 24:
                    score += 0.2
            except:
                pass

        return score

    async def clear_session(self) -> None:
        """Clear session context"""
        self._short_term_memory.clear()
        self.logger.info("Session context cleared")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "short_term_count": len(self._short_term_memory),
            "long_term_count": len(self._long_term_memory),
            "max_short_term": self._max_short_term,
            "max_long_term": self._max_long_term,
            "total_memory_items": len(self._short_term_memory) + len(self._long_term_memory)
        }