# SmartSense: Multimodal AI Assistant for Windows

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Under Development](https://img.shields.io/badge/status-under%20development-orange.svg)](https://github.com/arjun-christopher/SmartSense)
[![Work in Progress](https://img.shields.io/badge/WIP-🚧-yellow.svg)](https://github.com/arjun-christopher/SmartSense)

> **⚠︎ PROJECT STATUS: UNDER ACTIVE DEVELOPMENT**
> 
> This project is currently in active development and is **not yet production-ready**. Features are being implemented and tested. Expect breaking changes, incomplete functionality, and ongoing improvements.
> 
> - Core architecture implemented
> - Component integration in progress
> - Vision and speech modules under development
> - UI/UX being refined
> - Testing and documentation ongoing
> 
> **Contributions, feedback, and testing are welcome!** See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Overview

SmartSense is a Windows-based intelligent assistant that seamlessly understands **text**, **voice**, and **images**, responds naturally, and can perform smart actions like reading documents aloud, summarizing files, understanding screenshots, and chatting contextually.

### Key Features

- **Voice Input/Output**: Speech recognition using Whisper and TTS synthesis
- **Computer Vision**: Object detection, OCR, and scene classification
- **Natural Language Processing**: Intent recognition, entity extraction, and sentiment analysis
- **System Automation**: Windows automation via pyautogui and pywinauto
- **Context Management**: Short-term and long-term memory for contextual conversations
- **Asynchronous Architecture**: High-performance event-driven message bus
- **Security**: Action whitelisting and permission management

## Architecture

SmartSense follows a **modular, event-driven architecture** with the following components:

```
┌─────────────────────────────────────────────────────────────┐
│                     SmartSense System                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Text Input   │  │ Voice Input  │  │ Image Input  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                       │
│                    │  Message Bus   │                       │
│                    │  (Async Queue) │                       │
│                    └───────┬────────┘                       │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         │                  │                  │             │
│  ┌──────▼───────┐  ┌──────▼──────┐  ┌───────▼──────┐     │
│  │ NLP          │  │   Vision    │  │   Context    │     │
│  │ Processor    │  │  Processor  │  │   Manager    │     │
│  └──────┬───────┘  └──────┬──────┘  └───────┬──────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                 │
│                    ┌───────▼────────┐                       │
│                    │  Message Bus   │                       │
│                    └───────┬────────┘                       │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         │                  │                  │             │
│  ┌──────▼───────┐  ┌──────▼──────┐  ┌───────▼──────┐     │
│  │ Voice        │  │    Text     │  │   System     │     │
│  │ Output       │  │   Output    │  │   Control    │     │
│  └──────────────┘  └─────────────┘  └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Description

#### Input Handlers
- **TextInputHandler**: Processes text input from CLI/GUI
- **VoiceInputHandler**: Speech recognition using Whisper
- **ImageInputHandler**: Screenshot and image file processing

#### AI Processors
- **NLPProcessor**: Intent recognition, entity extraction, sentiment analysis
- **VisionProcessor**: Object detection (YOLOv5), OCR (Tesseract), scene classification
- **ContextManager**: Maintains conversation history and context

#### Output Handlers
- **VoiceOutputHandler**: Text-to-speech synthesis (pyttsx3/gTTS)
- **TextOutputHandler**: Formatted text display
- **UIHandler**: User interface (CLI/GUI)

#### Action Handlers
- **SystemControlHandler**: Windows automation and system control

#### Core Services
- **AsyncMessageBus**: High-performance async event routing
- **LifecycleManager**: Component lifecycle and dependency management
- **ServiceLocator**: Dependency injection container

## Installation

### Prerequisites

- **Python 3.8 or higher**
- **Windows OS** (for full system automation features)
- **Git** (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/arjun-christopher/SmartSense.git
cd SmartSense
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Additional System Dependencies

#### For OCR (Tesseract)
Download and install Tesseract OCR from:
https://github.com/UB-Mannheim/tesseract/wiki

Add Tesseract to your system PATH.

#### For Speech Recognition (Whisper)
Whisper will be installed automatically with the requirements, but you may need FFmpeg:

Download FFmpeg from: https://ffmpeg.org/download.html
Extract and add to system PATH.

### Step 5: Configure the Application

Edit `config.yaml` to customize settings:

```yaml
app:
  name: "SmartSense"
  version: "1.0.0"
  debug: false
  log_level: "INFO"

models:
  nlp:
    primary_model: "distilbert-base-uncased"
    confidence_threshold: 0.7
  
  vision:
    object_detector: "yolov5"
    ocr_engine: "tesseract"
  
  speech:
    recognition_model: "whisper-base"
    synthesis_engine: "pyttsx3"
```

## Usage

### Running SmartSense

```bash
python main.py
```

### Basic Commands

Once SmartSense is running, you can interact with it through text commands:

```
SmartSense> hello
SmartSense: Hi there! What can I do for you?

SmartSense> what's the weather like?
SmartSense: That's an interesting question. Let me think about that.

SmartSense> quit
```

### Example Use Cases

#### 1. Text Analysis
```python
from core.nlp import NLPProcessor
from models.config import SmartSenseConfig

processor = NLPProcessor("NLP", config)
await processor.initialize()
result = await processor._analyze_text("I love this product!")
# Returns: intent, entities, sentiment
```

#### 2. Image Processing
```python
from core.vision_processor import VisionProcessor

processor = VisionProcessor("Vision", config)
await processor.initialize()
# Process image and get object detection results
```

#### 3. Voice Interaction
```python
from core.speech import VoiceInputHandler
from core.speech_output import VoiceOutputHandler

# Voice input
voice_input = VoiceInputHandler("Voice", config)
await voice_input.start_listening()

# Voice output
voice_output = VoiceOutputHandler("TTS", config)
await voice_output.speak("Hello, how can I help you?")
```

## Configuration

### Environment Variables

You can override configuration using environment variables:

```bash
set SMARTSENSE_LOG_LEVEL=DEBUG
set SMARTSENSE_DEBUG=true
set SMARTSENSE_DATA_DIR=./data
```

### Security Settings

Control system automation permissions:

```yaml
security:
  action_whitelist_enabled: true
  confirmation_required: true
  permission_level: "moderate"  # safe, moderate, elevated, restricted
  audit_logging: true
```

## Development

### Project Structure

```
SmartSense/
├── main.py                 # Application entry point
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── setup.py               # Package installation
├── actions/               # Action handlers
│   └── system_control.py  # Windows automation
├── core/                  # Core components
│   ├── base.py           # Base classes
│   ├── message_bus.py    # Event bus
│   ├── nlp.py           # NLP processor
│   ├── vision_processor.py  # Vision processor
│   ├── speech.py         # Voice input
│   ├── speech_output.py  # Voice output
│   ├── text_input.py     # Text input
│   └── context.py        # Context manager
├── models/                # Data models
│   ├── events.py         # Event definitions
│   ├── config.py         # Config models
│   ├── commands.py       # Command models
│   └── results.py        # Result models
├── ui/                    # User interface
│   └── main_ui.py        # UI handler
├── utils/                 # Utilities
│   ├── logger.py         # Logging
│   ├── config.py         # Config loader
│   ├── lifecycle.py      # Lifecycle manager
│   └── service_locator.py  # DI container
├── data/                  # Data directory
│   ├── temp/             # Temporary files
│   └── cache/            # Model cache
├── logs/                  # Log files
└── examples/              # Example scripts
```

### Running Tests

```bash
pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines:

```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy .
```

## API Reference

### Event Types

SmartSense uses an event-driven architecture. Key event types:

- `TEXT_INPUT_EVENT`: Text user input
- `VOICE_INPUT_EVENT`: Voice user input
- `IMAGE_INPUT_EVENT`: Image input
- `NLP_RESPONSE_EVENT`: NLP processing result
- `VISION_RESPONSE_EVENT`: Vision processing result
- `SPEAK_EVENT`: Text-to-speech request
- `EXECUTE_ACTION_EVENT`: System action request
- `ACTION_RESULT_EVENT`: System action result

### Base Classes

All components inherit from base classes:

- `BaseComponent`: Foundation for all components
- `BaseInputHandler`: Input processing
- `BaseProcessor`: AI processing
- `BaseOutputHandler`: Output handling
- `BaseActionHandler`: Action execution

## Troubleshooting

### Common Issues

#### 1. Tesseract Not Found
```
Error: Tesseract not found in PATH
Solution: Install Tesseract and add to system PATH
```

#### 2. Whisper Model Download
```
Info: First run will download Whisper models (~150MB)
```

#### 3. Permission Errors
```
Error: Permission denied for system action
Solution: Check security.permission_level in config.yaml
```

#### 4. Port Already in Use
```
Error: Message bus initialization failed
Solution: Check if another instance is running
```

### Debug Mode

Enable debug logging:

```yaml
app:
  debug: true
  log_level: "DEBUG"
```

Or via environment:
```bash
set SMARTSENSE_DEBUG=true
set SMARTSENSE_LOG_LEVEL=DEBUG
python main.py
```

## Roadmap

### Version 1.1 (Planned)
- [ ] Full GUI implementation with Tkinter/CustomTkinter
- [ ] Enhanced voice commands with wake word detection
- [ ] Multi-language support
- [ ] Plugin system for extensions

### Version 1.2 (Planned)
- [ ] Cloud model integration (GPT-4, Claude)
- [ ] Advanced automation workflows
- [ ] Mobile companion app
- [ ] Web dashboard

### Version 2.0 (Future)
- [ ] Cross-platform support (macOS, Linux)
- [ ] Distributed processing
- [ ] Advanced RAG (Retrieval Augmented Generation)
- [ ] Integration with IoT devices

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Add docstrings to all public methods
- Write unit tests for new features
- Update README for significant changes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Hugging Face Transformers** for NLP models
- **OpenAI Whisper** for speech recognition
- **YOLOv5** for object detection
- **Tesseract** for OCR
- **pyttsx3** for text-to-speech

## Contact

**Project Maintainer**: Arjun Christopher
**GitHub**: [arjun-christopher](https://github.com/arjun-christopher)
**Repository**: [SmartSense](https://github.com/arjun-christopher/SmartSense)

## Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review [existing issues](https://github.com/arjun-christopher/SmartSense/issues)
3. Open a [new issue](https://github.com/arjun-christopher/SmartSense/issues/new)