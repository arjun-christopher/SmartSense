#!/usr/bin/env python3
"""
Image processing example with SmartSense.

This example demonstrates object detection and OCR on images.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vision_processor import VisionProcessor
from models.events import Event, EventType
from models.config import SmartSenseConfig, AppConfig, AIModelsConfig, NLPConfig, VisionConfig, SpeechConfig


async def main():
    """Run the image processing example"""
    print("=" * 60)
    print("SmartSense - Image Processing Example")
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

    # Initialize vision processor
    print("Initializing vision processor...")
    vision_processor = VisionProcessor("VisionProcessor", config)
    
    # Since we're not using the full message bus, manually initialize
    vision_processor._initialized = True
    vision_processor._set_status("ready")
    
    print("Vision processor ready!\n")

    # Create a dummy image (in real usage, you'd load an actual image file)
    print("Processing sample image...")
    print("Note: This is a placeholder implementation.")
    print("In production, it would use actual YOLOv5 and Tesseract models.\n")
    
    # Simulate image data
    dummy_image_data = b"dummy_image_bytes"
    metadata = {
        "format": "PNG",
        "dimensions": [1920, 1080],
        "source": "screenshot"
    }

    # Process the image
    result = await vision_processor._analyze_image(dummy_image_data, metadata)
    
    # Display results
    print("Vision Analysis Results:")
    print(f"  Image format: {result.image_format}")
    print(f"  Dimensions: {result.image_dimensions[0]}x{result.image_dimensions[1]}")
    print(f"  Scene: {result.scene_classification}")
    print(f"\n  Objects detected: {len(result.objects_detected)}")
    
    for obj in result.objects_detected:
        print(f"    - {obj.class_name} (confidence: {obj.confidence:.2f})")
    
    if result.ocr_result:
        print(f"\n  Text extracted (OCR):")
        print(f"    {result.ocr_result.extracted_text}")
        print(f"    Language: {result.ocr_result.language}")
        print(f"    Confidence: {result.ocr_result.confidence:.2f}")
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)
    print("\nTo process real images:")
    print("1. Install Tesseract OCR and add to PATH")
    print("2. Ensure YOLOv5 model weights are downloaded")
    print("3. Use the full SmartSense system with: python main.py")


if __name__ == "__main__":
    asyncio.run(main())
