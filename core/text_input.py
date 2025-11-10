"""
Text input handler for SmartSense AI Assistant.

This component processes text-based user input from various sources
and publishes text input events to the message bus.
"""

import asyncio
from typing import Optional
import sys

from models.events import Event, EventType, TextInputData
from models.config import SmartSenseConfig
from core.base import BaseInputHandler
from utils.logger import get_logger


class TextInputHandler(BaseInputHandler):
    """Handles text input from various sources"""

    def __init__(self, name: str, config: Optional[SmartSenseConfig] = None):
        super().__init__(name, config)
        self._running = False

    async def initialize(self) -> bool:
        """Initialize the text input handler"""
        try:
            self.logger.info("Initializing TextInputHandler")

            # Set up event subscriptions for text output display
            await self.subscribe_to_event(EventType.DISPLAY_TEXT_EVENT, self._handle_display_event)

            self._set_status("ready")
            self._initialized = True
            self.logger.info("TextInputHandler initialized successfully")
            return True

        except Exception as e:
            self._handle_error(e, "initialization")
            return False

    async def shutdown(self) -> None:
        """Shutdown the text input handler"""
        self.logger.info("Shutting down TextInputHandler")

        self._running = False
        await self.stop_processing()

        # Unsubscribe from events
        await self.unsubscribe_from_event(EventType.DISPLAY_TEXT_EVENT)

        self._set_status("offline")
        self.logger.info("TextInputHandler shutdown complete")

    async def process_input(self, input_data: str) -> Optional[Event]:
        """
        Process text input and create event

        Args:
            input_data: Raw text input

        Returns:
            Text input event or None if processing failed
        """
        try:
            # Validate input
            if not input_data or not input_data.strip():
                self.logger.warning("Empty text input received")
                return None

            text = input_data.strip()

            # Apply length limits
            max_length = 10000
            if self.config and hasattr(self.config.models, 'nlp'):
                max_length = self.config.models.nlp.max_tokens

            if len(text) > max_length:
                text = text[:max_length]
                self.logger.warning(f"Text truncated to {max_length} characters")

            # Create text input data
            text_data = TextInputData(
                text=text,
                source="cli",  # Default source
                metadata={
                    "original_length": len(input_data),
                    "encoding": "utf-8"
                }
            )

            # Create event
            event = Event(
                event_type=EventType.TEXT_INPUT_EVENT,
                data=text_data.dict(),
                source=self.name
            )

            self.logger.debug(f"Processed text input: {text[:50]}...")
            return event

        except Exception as e:
            self._handle_error(e, "processing text input")
            return None

    async def start_cli_input(self) -> None:
        """Start command line interface input"""
        if self._running:
            return

        self._running = True
        self.logger.info("Starting CLI input mode")

        # Start processing queue
        await self.start_processing()

        # CLI input loop
        while self._running:
            try:
                # Get user input
                if sys.stdin.isatty():
                    text = input("SmartSense> ")
                    if text.lower() in ['quit', 'exit', 'q']:
                        break
                    await self.add_input(text)
                else:
                    # Non-interactive mode
                    await asyncio.sleep(1.0)

            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                self.logger.error(f"CLI input error: {e}")

        self._running = False
        await self.stop_processing()

    async def add_text_input(self, text: str, source: str = "manual") -> bool:
        """
        Add text input for processing

        Args:
            text: Text to process
            source: Source of the input

        Returns:
            True if added successfully, False otherwise
        """
        if source != "cli":
            # Update source in data (will be handled in process_input)
            return await self.add_input({"text": text, "source": source})
        else:
            return await self.add_input(text)

    async def read_from_clipboard(self) -> None:
        """Read text from clipboard and process"""
        try:
            import pyperclip
            clipboard_text = pyperclip.paste()
            if clipboard_text and clipboard_text.strip():
                await self.add_text_input(clipboard_text, "clipboard")
                self.logger.info("Text processed from clipboard")
            else:
                self.logger.info("Clipboard is empty or contains no text")
        except ImportError:
            self.logger.warning("pyperclip not available for clipboard access")
        except Exception as e:
            self.logger.error(f"Error reading from clipboard: {e}")

    async def read_from_file(self, file_path: str) -> None:
        """
        Read text from file and process

        Args:
            file_path: Path to text file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            if text.strip():
                await self.add_text_input(text, f"file:{file_path}")
                self.logger.info(f"Text processed from file: {file_path}")
            else:
                self.logger.warning(f"File is empty: {file_path}")
        except Exception as e:
            self.logger.error(f"Error reading from file {file_path}: {e}")

    async def _handle_display_event(self, event: Event) -> None:
        """Handle display text events (for CLI output)"""
        try:
            if sys.stdin.isatty():  # Only display in interactive mode
                display_data = event.data
                text = display_data.get('text', '')
                destination = display_data.get('destination', 'console')

                if destination == 'console' and text:
                    print(f"\n{text}\nSmartSense> ", end='', flush=True)
        except Exception as e:
            self.logger.error(f"Error handling display event: {e}")