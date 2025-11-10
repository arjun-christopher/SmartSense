#!/usr/bin/env python3
"""
SmartSense AI Assistant - Main Entry Point

A modular, scalable AI assistant architecture using async message bus communication
for processing multimodal inputs (text, voice, image) through AI cores (NLP, vision, context)
to generate outputs (voice, text, UI) and execute system actions (Windows automation).

Author: SmartSense Team
Version: 1.0.0
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.config import ConfigManager
from utils.service_locator import ServiceLocator, register_service
from utils.lifecycle import LifecycleManager
from core.message_bus import AsyncMessageBus
from ui.main_ui import UIHandler


class SmartSense:
    """Main SmartSense application class"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager: Optional[ConfigManager] = None
        self.lifecycle_manager: Optional[LifecycleManager] = None
        self.message_bus: Optional[AsyncMessageBus] = None
        self.ui_handler: Optional[UIHandler] = None

    async def initialize(self) -> bool:
        """Initialize the SmartSense application"""
        try:
            self.logger.info("Initializing SmartSense AI Assistant...")

                        # Initialize configuration manager
            self.config_manager = ConfigManager()
            config = await self.config_manager.load_config("config.yaml")

            # Register core services using module-level function
            register_service(ConfigManager, self.config_manager)

            # Initialize lifecycle manager with the loaded config
            self.lifecycle_manager = LifecycleManager(config)
            await self.lifecycle_manager.initialize()

            # Get message bus from service locator
            self.message_bus = self.lifecycle_manager.service_locator.get_service(AsyncMessageBus)

            # Initialize UI handler with config
            self.ui_handler = UIHandler(self.message_bus, config)
            await self.ui_handler.initialize()

            self.logger.info("SmartSense AI Assistant initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize SmartSense: {e}")
            return False

    async def run(self) -> None:
        """Run the SmartSense application"""
        if not await self.initialize():
            self.logger.error("Failed to initialize. Exiting...")
            return

        try:
            self.logger.info("Starting SmartSense AI Assistant...")

            # Start the UI
            await self.ui_handler.run()

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt. Shutting down...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shutdown the SmartSense application"""
        try:
            self.logger.info("Shutting down SmartSense AI Assistant...")

            # Shutdown UI
            if self.ui_handler:
                await self.ui_handler.shutdown()

            # Shutdown lifecycle manager (will handle all components)
            if self.lifecycle_manager:
                await self.lifecycle_manager.shutdown()

            # Clear services
            service_locator = ServiceLocator()
            service_locator.clear_services()

            self.logger.info("SmartSense AI Assistant shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point"""
    # Set up event loop for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Create and run SmartSense
    smartsense = SmartSense()

    try:
        asyncio.run(smartsense.run())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()