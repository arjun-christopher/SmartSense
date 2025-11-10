"""
Text output handler for SmartSense AI Assistant.

This component displays text responses in various formats and destinations.
"""

import asyncio
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from models.events import Event, EventType
from models.config import SmartSenseConfig
from core.base import BaseOutputHandler
from utils.logger import get_logger


class TextOutputHandler(BaseOutputHandler):
    """Handles text output display and formatting"""

    def __init__(self, name: str, config: Optional[SmartSenseConfig] = None):
        super().__init__(name, config)
        self._log_file: Optional[Path] = None

    async def initialize(self) -> bool:
        """Initialize the text output handler"""
        try:
            self.logger.info("Initializing TextOutputHandler")

            # Set up event subscriptions
            await self.subscribe_to_event(EventType.DISPLAY_TEXT_EVENT, self._handle_display_text)
            await self.subscribe_to_event(EventType.NLP_RESPONSE_EVENT, self._handle_nlp_response)
            await self.subscribe_to_event(EventType.VISION_RESPONSE_EVENT, self._handle_vision_response)

            # Set up log file
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            self._log_file = logs_dir / "responses.log"

            # Start processing queue
            await self.start_processing()

            self._set_status("ready")
            self._initialized = True
            self.logger.info("TextOutputHandler initialized successfully")
            return True

        except Exception as e:
            self._handle_error(e, "initialization")
            return False

    async def shutdown(self) -> None:
        """Shutdown the text output handler"""
        self.logger.info("Shutting down TextOutputHandler")

        await self.stop_processing()

        # Unsubscribe from events
        await self.unsubscribe_from_event(EventType.DISPLAY_TEXT_EVENT)
        await self.unsubscribe_from_event(EventType.NLP_RESPONSE_EVENT)
        await self.unsubscribe_from_event(EventType.VISION_RESPONSE_EVENT)

        self._set_status("offline")
        self.logger.info("TextOutputHandler shutdown complete")

    async def handle_output(self, event: Event) -> bool:
        """
        Handle output event

        Args:
            event: Output event to handle

        Returns:
            True if handled successfully, False otherwise
        """
        try:
            if event.event_type == EventType.DISPLAY_TEXT_EVENT:
                return await self._process_display_text(event)
            elif event.event_type == EventType.NLP_RESPONSE_EVENT:
                return await self._process_nlp_response(event)
            elif event.event_type == EventType.VISION_RESPONSE_EVENT:
                return await self._process_vision_response(event)
            else:
                self.logger.warning(f"Unhandled event type: {event.event_type}")
                return False

        except Exception as e:
            self._handle_error(e, f"handling output event {event.event_type}")
            return False

    async def _handle_display_text(self, event: Event) -> None:
        """Handle display text events"""
        await self.add_output(event)

    async def _handle_nlp_response(self, event: Event) -> None:
        """Handle NLP response events"""
        # Convert NLP response to display event
        nlp_data = event.data
        processed_text = nlp_data.get('processed_text') or nlp_data.get('original_text', '')

        if processed_text:
            display_event = Event(
                event_type=EventType.DISPLAY_TEXT_EVENT,
                data={
                    'text': processed_text,
                    'destination': 'console',
                    'format_type': 'plain',
                    'color': 'green' if nlp_data.get('sentiment') == 'positive' else None
                },
                source=self.name
            )
            await self.add_output(display_event)

    async def _handle_vision_response(self, event: Event) -> None:
        """Handle vision response events"""
        # Convert vision response to display event
        vision_data = event.data
        objects_detected = vision_data.get('objects_detected', [])
        text_found = vision_data.get('text_found')

        response_parts = []
        if objects_detected:
            response_parts.append(f"I detected {len(objects_detected)} objects:")
            for obj in objects_detected[:5]:  # Limit to first 5 objects
                response_parts.append(f"  - {obj.get('class_name', 'unknown')} (confidence: {obj.get('confidence', 0):.2f})")

        if text_found:
            response_parts.append(f"Text found in image: {text_found}")

        if response_parts:
            display_event = Event(
                event_type=EventType.DISPLAY_TEXT_EVENT,
                data={
                    'text': '\n'.join(response_parts),
                    'destination': 'console',
                    'format_type': 'plain'
                },
                source=self.name
            )
            await self.add_output(display_event)

    async def _process_display_text(self, event: Event) -> bool:
        """Process display text event"""
        try:
            display_data = event.data
            text = display_data.get('text', '')
            destination = display_data.get('destination', 'console')
            format_type = display_data.get('format_type', 'plain')

            if not text:
                return True  # Nothing to display

            # Format text based on type
            formatted_text = self._format_text(text, format_type)

            # Display based on destination
            if destination == 'console':
                await self._display_to_console(formatted_text, display_data)
            elif destination == 'log':
                await self._log_to_file(formatted_text)

            # Always log responses
            await self._log_response(event)

            return True

        except Exception as e:
            self.logger.error(f"Error processing display text: {e}")
            return False

    async def _process_nlp_response(self, event: Event) -> bool:
        """Process NLP response event"""
        try:
            nlp_data = event.data
            response_parts = []

            # Add processed text
            processed_text = nlp_data.get('processed_text') or nlp_data.get('original_text', '')
            if processed_text:
                response_parts.append(f"Response: {processed_text}")

            # Add analysis details if in debug mode
            if self.config and self.config.app.debug:
                intent = nlp_data.get('intent', 'unknown')
                confidence = nlp_data.get('confidence', 0.0)
                sentiment = nlp_data.get('sentiment', 'unknown')

                response_parts.append(f"Analysis (debug):")
                response_parts.append(f"  Intent: {intent} (confidence: {confidence:.2f})")
                response_parts.append(f"  Sentiment: {sentiment}")

                entities = nlp_data.get('entities', [])
                if entities:
                    response_parts.append(f"  Entities: {', '.join([e.get('entity_value', '') for e in entities[:3]])}")

            if response_parts:
                display_event = Event(
                    event_type=EventType.DISPLAY_TEXT_EVENT,
                    data={
                        'text': '\n'.join(response_parts),
                        'destination': 'console',
                        'format_type': 'plain'
                    },
                    source=self.name
                )
                await self.add_output(display_event)

            return True

        except Exception as e:
            self.logger.error(f"Error processing NLP response: {e}")
            return False

    async def _process_vision_response(self, event: Event) -> bool:
        """Process vision response event"""
        try:
            vision_data = event.data
            response_parts = []

            # Add objects detected
            objects_detected = vision_data.get('objects_detected', [])
            if objects_detected:
                response_parts.append(f"Objects detected: {len(objects_detected)}")
                for obj in objects_detected[:3]:  # Limit to first 3 objects
                    class_name = obj.get('class_name', 'unknown')
                    confidence = obj.get('confidence', 0.0)
                    response_parts.append(f"  - {class_name} (confidence: {confidence:.2f})")

            # Add text found
            text_found = vision_data.get('text_found')
            if text_found:
                response_parts.append(f"Text found: {text_found}")

            # Add scene classification
            scene_class = vision_data.get('scene_classification')
            if scene_class:
                response_parts.append(f"Scene: {scene_class}")

            if response_parts:
                display_event = Event(
                    event_type=EventType.DISPLAY_TEXT_EVENT,
                    data={
                        'text': '\n'.join(response_parts),
                        'destination': 'console',
                        'format_type': 'plain'
                    },
                    source=self.name
                )
                await self.add_output(display_event)

            return True

        except Exception as e:
            self.logger.error(f"Error processing vision response: {e}")
            return False

    def _format_text(self, text: str, format_type: str) -> str:
        """Format text based on type"""
        if format_type == 'markdown':
            # Basic markdown formatting (could be enhanced)
            return text
        elif format_type == 'json':
            # JSON formatting (would need proper implementation)
            return str(text)
        else:  # plain
            return text

    async def _display_to_console(self, text: str, display_data: Dict[str, Any]) -> None:
        """Display text to console"""
        try:
            # Add timestamp if configured
            timestamp = datetime.now().strftime('%H:%M:%S')
            color = display_data.get('color')

            if color and sys.stdout.isatty():
                # Basic color support (could be enhanced)
                color_codes = {
                    'red': '\033[91m',
                    'green': '\033[92m',
                    'yellow': '\033[93m',
                    'blue': '\033[94m',
                    'reset': '\033[0m'
                }
                color_code = color_codes.get(color, '')
                reset_code = color_codes['reset']
                print(f"[{timestamp}] {color_code}{text}{reset_code}")
            else:
                print(f"[{timestamp}] {text}")

        except Exception as e:
            self.logger.error(f"Error displaying to console: {e}")

    async def _log_to_file(self, text: str) -> None:
        """Log text to file"""
        if not self._log_file:
            return

        try:
            timestamp = datetime.now().isoformat()
            with open(self._log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {text}\n")
        except Exception as e:
            self.logger.error(f"Error logging to file: {e}")

    async def _log_response(self, event: Event) -> None:
        """Log response for audit trail"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                'timestamp': timestamp,
                'event_type': event.event_type,
                'source': event.source,
                'data': event.data
            }

            if self._log_file:
                import json
                with open(self._log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{json.dumps(log_entry, default=str)}\n")

        except Exception as e:
            self.logger.error(f"Error logging response: {e}")