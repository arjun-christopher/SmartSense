"""
Data models package for SmartSense AI Assistant.

This package contains Pydantic models for all data structures used throughout
the SmartSense system, including events, configuration, commands, and results.
"""

from .events import (
    Event,
    EventType,
    TextInputData,
    VoiceInputData,
    ImageInputData,
    NLPResponseData,
    VisionResponseData,
    ContextData,
    SpeakData,
    DisplayTextData,
    UIUpdateData,
    ExecuteActionData,
    ActionResultData,
    SystemStatusData,
    ErrorData,
    MemoryUpdateData,
)

from .config import (
    AppConfig,
    MessageBusConfig,
    NLPConfig,
    VisionConfig,
    SpeechConfig,
    AIModelsConfig,
    UIConfig,
    SecurityConfig,
    SystemConfig,
    SmartSenseConfig,
    EnvironmentConfig,
)

from .commands import (
    Command,
    CommandType,
    PermissionLevel,
    WindowCommand,
    MouseCommand,
    KeyboardCommand,
    ApplicationCommand,
    FileCommand,
    CommandBatch,
    CommandTemplate,
)

from .results import (
    ResultStatus,
    ProcessingResult,
    IntentResult,
    EntityResult,
    SentimentResult,
    NLPProcessingResult,
    DetectionResult,
    OCRResult,
    SceneClassificationResult,
    VisionProcessingResult,
    AudioMetadata,
    VoiceProcessingResult,
    ActionResult,
    SystemActionResult,
    ContextResult,
    ContextProcessingResult,
    UIActionResult,
    UIUpdateResult,
    BatchResult,
    ValidationErrorResult,
    ValidationResult,
)

__all__ = [
    # Event models
    "Event",
    "EventType",
    "TextInputData",
    "VoiceInputData",
    "ImageInputData",
    "NLPResponseData",
    "VisionResponseData",
    "ContextData",
    "SpeakData",
    "DisplayTextData",
    "UIUpdateData",
    "ExecuteActionData",
    "ActionResultData",
    "SystemStatusData",
    "ErrorData",
    "MemoryUpdateData",

    # Config models
    "AppConfig",
    "MessageBusConfig",
    "NLPConfig",
    "VisionConfig",
    "SpeechConfig",
    "AIModelsConfig",
    "UIConfig",
    "SecurityConfig",
    "SystemConfig",
    "SmartSenseConfig",
    "EnvironmentConfig",

    # Command models
    "Command",
    "CommandType",
    "PermissionLevel",
    "WindowCommand",
    "MouseCommand",
    "KeyboardCommand",
    "ApplicationCommand",
    "FileCommand",
    "CommandBatch",
    "CommandTemplate",

    # Result models
    "ResultStatus",
    "ProcessingResult",
    "IntentResult",
    "EntityResult",
    "SentimentResult",
    "NLPProcessingResult",
    "DetectionResult",
    "OCRResult",
    "SceneClassificationResult",
    "VisionProcessingResult",
    "AudioMetadata",
    "VoiceProcessingResult",
    "ActionResult",
    "SystemActionResult",
    "ContextResult",
    "ContextProcessingResult",
    "UIActionResult",
    "UIUpdateResult",
    "BatchResult",
    "ValidationErrorResult",
    "ValidationResult",
]