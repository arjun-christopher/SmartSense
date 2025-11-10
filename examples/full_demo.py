#!/usr/bin/env python3
"""
Complete system demo for SmartSense.

This example demonstrates the full system with all components working together.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import SmartSense


async def demo_conversation():
    """Run a demo conversation"""
    print("=" * 60)
    print("SmartSense - Full System Demo")
    print("=" * 60)
    print()
    print("This demo will start the full SmartSense system.")
    print("You can interact with it using text commands.")
    print()
    print("Example commands:")
    print("  - hello")
    print("  - what can you do?")
    print("  - help me with something")
    print("  - quit (to exit)")
    print()
    print("=" * 60)
    print()
    
    # Create and run SmartSense
    smartsense = SmartSense()
    await smartsense.run()


async def demo_automated():
    """Run an automated demo with pre-programmed interactions"""
    print("=" * 60)
    print("SmartSense - Automated Demo")
    print("=" * 60)
    print()
    
    from core.nlp import NLPProcessor
    from models.config import SmartSenseConfig, AppConfig, AIModelsConfig, NLPConfig, VisionConfig, SpeechConfig
    
    # Create configuration
    config = SmartSenseConfig(
        app=AppConfig(debug=False),
        models=AIModelsConfig(
            nlp=NLPConfig(),
            vision=VisionConfig(),
            speech=SpeechConfig()
        )
    )
    
    # Initialize NLP processor
    nlp = NLPProcessor("NLP", config)
    nlp._initialized = True
    nlp._set_status("ready")
    
    # Demo interactions
    interactions = [
        ("Hello SmartSense!", "Greeting"),
        ("What's the weather like today?", "Question"),
        ("I need help with my computer", "Help request"),
        ("Open my browser please", "Command"),
        ("This is amazing, thank you!", "Positive feedback"),
        ("Goodbye!", "Farewell"),
    ]
    
    print("Running automated demo interactions:\n")
    
    for user_input, description in interactions:
        print(f"[{description}]")
        print(f"User: {user_input}")
        
        # Process with NLP
        result = await nlp._analyze_text(user_input)
        
        print(f"SmartSense: {result.processed_text}")
        print(f"  (Intent: {result.intent}, Sentiment: {result.sentiment})")
        print()
        
        # Small delay for readability
        await asyncio.sleep(0.5)
    
    print("=" * 60)
    print("Automated demo complete!")
    print("\nTo try the interactive version, run: python main.py")
    print("=" * 60)


async def main():
    """Main demo entry point"""
    print()
    print("SmartSense Demo")
    print()
    print("Choose demo mode:")
    print("1. Automated demo (pre-programmed interactions)")
    print("2. Interactive mode (full system)")
    print()
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        print()
        
        if choice == "1":
            await demo_automated()
        elif choice == "2":
            await demo_conversation()
        else:
            print("Invalid choice. Running automated demo...")
            await demo_automated()
    except (KeyboardInterrupt, EOFError):
        print("\nDemo cancelled.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
