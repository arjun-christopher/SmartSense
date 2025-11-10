#!/usr/bin/env python3
"""
Simple text interaction example with SmartSense.

This example demonstrates basic text processing and conversation.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nlp import NLPProcessor
from models.events import Event, EventType
from models.config import SmartSenseConfig, AppConfig, AIModelsConfig, NLPConfig, VisionConfig, SpeechConfig


async def main():
    """Run the text interaction example"""
    print("=" * 60)
    print("SmartSense - Text Interaction Example")
    print("=" * 60)
    print()

    # Create configuration
    config = SmartSenseConfig(
        app=AppConfig(),
        models=AIModelsConfig(
            nlp=NLPConfig(),
            vision=VisionConfig(),
            speech=SpeechConfig()
        )
    )

    # Initialize NLP processor
    print("Initializing NLP processor...")
    nlp_processor = NLPProcessor("NLPProcessor", config)
    
    # Since we're not using the full message bus, manually initialize
    nlp_processor._initialized = True
    nlp_processor._set_status("ready")
    
    print("NLP processor ready!\n")

    # Example texts to process
    example_texts = [
        "Hello! How are you today?",
        "I love this product, it's amazing!",
        "What time is the meeting at 3:30 PM?",
        "Can you help me with something?",
        "This is terrible, I'm very disappointed.",
        "Goodbye, have a nice day!",
    ]

    for text in example_texts:
        print(f"Input: {text}")
        
        # Analyze the text
        result = await nlp_processor._analyze_text(text)
        
        # Display results
        print(f"  Intent: {result.intent} (confidence: {result.confidence:.2f})")
        print(f"  Sentiment: {result.sentiment}")
        if result.entities:
            print(f"  Entities: {[e['entity_type'] for e in result.entities]}")
        print(f"  Response: {result.processed_text}")
        print()

    print("=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
