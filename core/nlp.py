"""
Natural Language Processing (NLP) component for SmartSense AI Assistant.

This component processes text input using NLP techniques including
intent recognition, entity extraction, and sentiment analysis.
"""

import asyncio
import re
from typing import Optional, Dict, Any, List

from models.events import Event, EventType, NLPResponseData
from models.config import SmartSenseConfig
from core.base import BaseProcessor
from utils.logger import get_logger


class NLPProcessor(BaseProcessor):
    """Natural Language Processing component"""

    def __init__(self, name: str, config: Optional[SmartSenseConfig] = None):
        super().__init__(name, config)
        self._intents = {
            "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
            "goodbye": ["bye", "goodbye", "see you", "farewell"],
            "question": ["what", "how", "why", "when", "where", "who"],
            "command": ["open", "close", "start", "stop", "launch", "exit"],
            "help": ["help", "assist", "support", "guide"],
            "unknown": []
        }

    async def initialize(self) -> bool:
        """Initialize the NLP processor"""
        try:
            self.logger.info("Initializing NLPProcessor")

            # Set up event subscriptions
            await self.subscribe_to_event(EventType.TEXT_INPUT_EVENT, self._handle_text_input)
            await self.subscribe_to_event(EventType.VOICE_INPUT_EVENT, self._handle_voice_input)

            # Initialize NLP models (placeholder)
            self._set_status("ready")
            self._initialized = True
            self.logger.info("NLPProcessor initialized successfully (placeholder implementation)")
            return True

        except Exception as e:
            self._handle_error(e, "initialization")
            return False

    async def shutdown(self) -> None:
        """Shutdown the NLP processor"""
        self.logger.info("Shutting down NLPProcessor")

        # Cancel active tasks
        await self.cancel_all_tasks()

        # Unsubscribe from events
        await self.unsubscribe_from_event(EventType.TEXT_INPUT_EVENT)
        await self.unsubscribe_from_event(EventType.VOICE_INPUT_EVENT)

        self._set_status("offline")
        self.logger.info("NLPProcessor shutdown complete")

    async def process_event(self, event: Event) -> Optional[Event]:
        """Process text/voice input events"""
        try:
            if event.event_type == EventType.TEXT_INPUT_EVENT:
                return await self._process_text_input(event)
            elif event.event_type == EventType.VOICE_INPUT_EVENT:
                return await self._process_voice_input(event)
            else:
                return None

        except Exception as e:
            self._handle_error(e, f"processing {event.event_type}")
            return None

    async def _handle_text_input(self, event: Event) -> None:
        """Handle text input events"""
        await self._process_with_semaphore(event)

    async def _handle_voice_input(self, event: Event) -> None:
        """Handle voice input events"""
        await self._process_with_semaphore(event)

    async def _process_text_input(self, event: Event) -> Optional[Event]:
        """Process text input event"""
        try:
            text_data = event.data
            text = text_data.get('text', '')

            if not text:
                return None

            # Process text
            nlp_result = await self._analyze_text(text)

            # Create response event
            response_event = Event(
                event_type=EventType.NLP_RESPONSE_EVENT,
                data=nlp_result.dict(),
                source=self.name,
                correlation_id=event.event_id
            )

            self.logger.debug(f"Processed text input: {text[:50]}...")
            return response_event

        except Exception as e:
            self.logger.error(f"Error processing text input: {e}")
            return None

    async def _process_voice_input(self, event: Event) -> Optional[Event]:
        """Process voice input event"""
        try:
            voice_data = event.data
            text = voice_data.get('transcribed_text', '')

            if not text:
                return None

            # Process transcribed text
            nlp_result = await self._analyze_text(text)

            # Create response event
            response_event = Event(
                event_type=EventType.NLP_RESPONSE_EVENT,
                data=nlp_result.dict(),
                source=self.name,
                correlation_id=event.event_id
            )

            self.logger.debug(f"Processed voice input: {text[:50]}...")
            return response_event

        except Exception as e:
            self.logger.error(f"Error processing voice input: {e}")
            return None

    async def _analyze_text(self, text: str) -> NLPResponseData:
        """Analyze text using NLP techniques"""
        try:
            # Clean and normalize text
            cleaned_text = self._clean_text(text)

            # Extract intent
            intent, confidence = self._extract_intent(cleaned_text)

            # Extract entities (placeholder)
            entities = self._extract_entities(cleaned_text)

            # Analyze sentiment (placeholder)
            sentiment, sentiment_score = self._analyze_sentiment(cleaned_text)

            # Generate response
            response_text = self._generate_response(intent, cleaned_text, entities)

            return NLPResponseData(
                original_text=text,
                intent=intent,
                entities=entities,
                sentiment=sentiment,
                confidence=confidence,
                processed_text=response_text,
                language="en"
            )

        except Exception as e:
            self.logger.error(f"Error analyzing text: {e}")
            # Return fallback response
            return NLPResponseData(
                original_text=text,
                intent="unknown",
                entities=[],
                sentiment="neutral",
                confidence=0.0,
                processed_text="I'm sorry, I had trouble processing that. Could you please try again?",
                language="en"
            )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        return text.lower()

    def _extract_intent(self, text: str) -> tuple[str, float]:
        """Extract intent from text"""
        text_lower = text.lower()

        # Check each intent
        for intent, keywords in self._intents.items():
            if intent == "unknown":
                continue

            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                confidence = min(matches / len(keywords), 1.0)
                return intent, confidence

        return "unknown", 0.0

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text (placeholder)"""
        entities = []

        # Simple pattern matching for common entities
        # Numbers
        numbers = re.findall(r'\b\d+\b', text)
        for num in numbers:
            entities.append({
                "entity_type": "number",
                "entity_value": num,
                "confidence": 0.9,
                "start_position": text.find(num),
                "end_position": text.find(num) + len(num)
            })

        # Time patterns
        time_patterns = re.findall(r'\b\d{1,2}:\d{2}\b', text)
        for time in time_patterns:
            entities.append({
                "entity_type": "time",
                "entity_value": time,
                "confidence": 0.8,
                "start_position": text.find(time),
                "end_position": text.find(time) + len(time)
            })

        return entities

    def _analyze_sentiment(self, text: str) -> tuple[str, float]:
        """Analyze sentiment (placeholder)"""
        positive_words = ["good", "great", "excellent", "happy", "love", "wonderful", "amazing"]
        negative_words = ["bad", "terrible", "hate", "awful", "horrible", "sad", "angry"]

        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())

        if positive_count > negative_count:
            return "positive", min(positive_count / (positive_count + negative_count + 1), 1.0)
        elif negative_count > positive_count:
            return "negative", min(negative_count / (positive_count + negative_count + 1), 1.0)
        else:
            return "neutral", 0.5

    def _generate_response(self, intent: str, text: str, entities: List[Dict[str, Any]]) -> str:
        """Generate response based on intent and entities"""
        responses = {
            "greeting": [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Greetings! I'm ready to assist you."
            ],
            "goodbye": [
                "Goodbye! Have a great day!",
                "See you later! Feel free to come back anytime.",
                "Farewell! It was nice helping you."
            ],
            "question": [
                "That's an interesting question. Let me think about that.",
                "I understand you're asking about something. I'll do my best to help.",
                "Thank you for your question. Here's what I can tell you."
            ],
            "command": [
                "I understand you want me to do something. I'm working on implementing command execution.",
                "Command detected! I'm still learning how to execute system commands safely.",
                "I see you've given me a command. Command execution will be available soon."
            ],
            "help": [
                "I'm here to help! I can process text, analyze images, and eventually execute commands.",
                "You can ask me questions, give me commands, or just chat with me!",
                "I'm your AI assistant. I'm still learning but I'm ready to help!"
            ],
            "unknown": [
                "I'm not sure I understand. Could you please rephrase that?",
                "That's interesting! I'm still learning and might not have understood correctly.",
                "I'm processing what you said, but I may need more context to help you better."
            ]
        }

        import random
        return random.choice(responses.get(intent, responses["unknown"]))