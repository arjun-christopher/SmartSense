"""
Main UI handler for SmartSense AI Assistant.

This component provides the user interface, supporting both GUI and CLI modes.
"""

import asyncio
import sys
import threading
from typing import Optional, Dict, Any
from pathlib import Path

from models.events import Event, EventType
from models.config import SmartSenseConfig
from core.message_bus import AsyncMessageBus
from core.base import BaseOutputHandler
from utils.logger import get_logger


class UIHandler(BaseOutputHandler):
    """Main user interface handler"""

    def __init__(self, message_bus: AsyncMessageBus, config: Optional[SmartSenseConfig] = None):
        super().__init__("UIHandler", config)
        self._message_bus = message_bus
        self._gui_mode = False
        self._cli_mode = False
        self._running = False
        self._ui_thread: Optional[threading.Thread] = None

    async def initialize(self) -> bool:
        """Initialize the UI handler"""
        try:
            self.logger.info("Initializing UIHandler")

            # Determine UI mode based on environment and configuration
            self._determine_ui_mode()

            # Set up event subscriptions
            await self.subscribe_to_event(EventType.UI_UPDATE_EVENT, self._handle_ui_update)
            await self.subscribe_to_event(EventType.NLP_RESPONSE_EVENT, self._handle_nlp_response)
            await self.subscribe_to_event(EventType.VISION_RESPONSE_EVENT, self._handle_vision_response)
            await self.subscribe_to_event(EventType.SYSTEM_STATUS_EVENT, self._handle_system_status)

            # Initialize based on mode
            if self._gui_mode:
                success = await self._initialize_gui()
            else:
                success = await self._initialize_cli()

            if success:
                self._set_status("ready")
                self._initialized = True
                self.logger.info(f"UIHandler initialized in {'GUI' if self._gui_mode else 'CLI'} mode")
            else:
                self._set_status("error")
                self.logger.error("UIHandler initialization failed")

            return success

        except Exception as e:
            self._handle_error(e, "initialization")
            return False

    async def shutdown(self) -> None:
        """Shutdown the UI handler"""
        self.logger.info("Shutting down UIHandler")

        self._running = False

        # Stop processing
        await self.stop_processing()

        # Shutdown based on mode
        if self._gui_mode:
            await self._shutdown_gui()
        else:
            await self._shutdown_cli()

        # Unsubscribe from events
        await self.unsubscribe_from_event(EventType.UI_UPDATE_EVENT)
        await self.unsubscribe_from_event(EventType.NLP_RESPONSE_EVENT)
        await self.unsubscribe_from_event(EventType.VISION_RESPONSE_EVENT)
        await self.unsubscribe_from_event(EventType.SYSTEM_STATUS_EVENT)

        self._set_status("offline")
        self.logger.info("UIHandler shutdown complete")

    def _determine_ui_mode(self) -> None:
        """Determine UI mode based on environment"""
        # Check if GUI is available
        gui_available = self._check_gui_availability()

        # Check configuration
        prefer_gui = True  # Default preference
        if self.config:
            # Could check config for UI preference here
            pass

        # Check if running in terminal
        is_tty = sys.stdin.isatty() and sys.stdout.isatty()

        self._gui_mode = gui_available and prefer_gui and not is_tty
        self._cli_mode = not self._gui_mode

        self.logger.debug(f"UI mode determined: {'GUI' if self._gui_mode else 'CLI'}")

    def _check_gui_availability(self) -> bool:
        """Check if GUI is available"""
        try:
            # Try importing tkinter
            import tkinter
            return True
        except ImportError:
            return False

    async def _initialize_gui(self) -> bool:
        """Initialize GUI mode"""
        try:
            self.logger.info("Initializing GUI mode")

            # GUI initialization would go here
            # For now, we'll fall back to CLI mode
            self.logger.warning("GUI mode not yet implemented, falling back to CLI")
            self._gui_mode = False
            self._cli_mode = True
            return await self._initialize_cli()

        except Exception as e:
            self.logger.error(f"Error initializing GUI: {e}")
            # Fall back to CLI mode
            self._gui_mode = False
            self._cli_mode = True
            return await self._initialize_cli()

    async def _initialize_cli(self) -> bool:
        """Initialize CLI mode"""
        try:
            self.logger.info("Initializing CLI mode")

            # Set up CLI interface
            self._running = True

            # Start processing queue
            await self.start_processing()

            # Display welcome message
            await self._display_welcome_message()

            return True

        except Exception as e:
            self.logger.error(f"Error initializing CLI: {e}")
            return False

    async def _shutdown_gui(self) -> None:
        """Shutdown GUI mode"""
        self.logger.info("Shutting down GUI mode")
        # GUI shutdown would go here

    async def _shutdown_cli(self) -> None:
        """Shutdown CLI mode"""
        self.logger.info("Shutting down CLI mode")
        self._running = False

    async def handle_output(self, event: Event) -> bool:
        """
        Handle output event

        Args:
            event: Output event to handle

        Returns:
            True if handled successfully, False otherwise
        """
        try:
            if self._gui_mode:
                return await self._handle_gui_output(event)
            else:
                return await self._handle_cli_output(event)

        except Exception as e:
            self._handle_error(e, f"handling UI output {event.event_type}")
            return False

    async def _handle_gui_output(self, event: Event) -> bool:
        """Handle output in GUI mode"""
        # GUI output handling would go here
        self.logger.debug(f"GUI output: {event.event_type}")
        return True

    async def _handle_cli_output(self, event: Event) -> bool:
        """Handle output in CLI mode"""
        try:
            if event.event_type == EventType.UI_UPDATE_EVENT:
                return await self._process_ui_update(event)
            elif event.event_type == EventType.NLP_RESPONSE_EVENT:
                return await self._process_nlp_response(event)
            elif event.event_type == EventType.VISION_RESPONSE_EVENT:
                return await self._process_vision_response(event)
            elif event.event_type == EventType.SYSTEM_STATUS_EVENT:
                return await self._process_system_status(event)
            else:
                return True  # Ignore other events in CLI mode

        except Exception as e:
            self.logger.error(f"Error handling CLI output: {e}")
            return False

    async def run(self) -> None:
        """Run the UI"""
        if self._gui_mode:
            await self._run_gui()
        else:
            await self._run_cli()

    async def _run_gui(self) -> None:
        """Run GUI mode"""
        self.logger.info("Running GUI mode")
        # GUI main loop would go here

    async def _run_cli(self) -> None:
        """Run CLI mode"""
        self.logger.info("Running CLI mode")

        try:
            while self._running:
                await asyncio.sleep(1.0)
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt in CLI mode")

    # Event handlers
    async def _handle_ui_update(self, event: Event) -> None:
        """Handle UI update events"""
        await self.add_output(event)

    async def _handle_nlp_response(self, event: Event) -> None:
        """Handle NLP response events"""
        await self.add_output(event)

    async def _handle_vision_response(self, event: Event) -> None:
        """Handle vision response events"""
        await self.add_output(event)

    async def _handle_system_status(self, event: Event) -> None:
        """Handle system status events"""
        await self.add_output(event)

    # Event processors
    async def _process_ui_update(self, event: Event) -> bool:
        """Process UI update event"""
        ui_data = event.data
        component = ui_data.get('component', 'unknown')
        action = ui_data.get('action', 'unknown')

        if sys.stdout.isatty():
            print(f"[UI] {component}: {action}")

        return True

    async def _process_nlp_response(self, event: Event) -> bool:
        """Process NLP response event"""
        nlp_data = event.data
        processed_text = nlp_data.get('processed_text') or nlp_data.get('original_text', '')

        if processed_text and sys.stdout.isatty():
            print(f"\nSmartSense: {processed_text}\n")

        return True

    async def _process_vision_response(self, event: Event) -> bool:
        """Process vision response event"""
        vision_data = event.data
        objects_detected = vision_data.get('objects_detected', [])
        text_found = vision_data.get('text_found')

        if sys.stdout.isatty():
            if objects_detected:
                print(f"\nI detected {len(objects_detected)} objects:")
                for obj in objects_detected[:3]:
                    class_name = obj.get('class_name', 'unknown')
                    confidence = obj.get('confidence', 0.0)
                    print(f"  - {class_name} (confidence: {confidence:.2f})")

            if text_found:
                print(f"\nText found: {text_found}")
            print()

        return True

    async def _process_system_status(self, event: Event) -> bool:
        """Process system status event"""
        status_data = event.data
        component = status_data.get('component', 'unknown')
        status = status_data.get('status', 'unknown')
        message = status_data.get('message', '')

        if self.config and self.config.app.debug and sys.stdout.isatty():
            print(f"[Status] {component}: {status}")
            if message:
                print(f"[Status] Message: {message}")

        return True

    async def _display_welcome_message(self) -> None:
        """Display welcome message"""
        if sys.stdout.isatty():
            print("=" * 60)
            print("SmartSense AI Assistant")
            print("=" * 60)
            print("Welcome! I'm ready to help you with:")
            print("- Text processing and analysis")
            print("- Voice commands (when enabled)")
            print("- Image analysis (when enabled)")
            print("- System automation (when enabled)")
            print("\nType 'quit' or 'exit' to leave, or just start talking!")
            print("=" * 60)

    # UI interaction methods
    async def show_status(self, status_data: Dict[str, Any]) -> None:
        """Show system status"""
        if self._gui_mode:
            # Update GUI status
            pass
        else:
            # CLI status display
            if sys.stdout.isatty():
                print("\n=== System Status ===")
                for key, value in status_data.items():
                    print(f"{key}: {value}")
                print("====================\n")

    async def show_error(self, error_message: str) -> None:
        """Show error message"""
        if self._gui_mode:
            # Show GUI error dialog
            pass
        else:
            # CLI error display
            if sys.stdout.isatty():
                print(f"Error: {error_message}")

    async def get_user_input(self, prompt: str = "SmartSense> ") -> Optional[str]:
        """Get user input"""
        if self._gui_mode:
            # Get GUI input
            return None  # Would be implemented in GUI
        else:
            # CLI input
            try:
                if sys.stdin.isatty():
                    return input(prompt)
                else:
                    return None
            except (KeyboardInterrupt, EOFError):
                return None