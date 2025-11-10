"""
Data models for events in the SmartSense message bus system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types used in the message bus system"""

    # Input events
    TEXT_INPUT_EVENT = "text_input_event"
    VOICE_INPUT_EVENT = "voice_input_event"
    IMAGE_INPUT_EVENT = "image_input_event"

    # AI processing events
    NLP_RESPONSE_EVENT = "nlp_response_event"
    VISION_RESPONSE_EVENT = "vision_response_event"
    CONTEXT_UPDATE_EVENT = "context_update_event"
    CONTEXT_RESPONSE_EVENT = "context_response_event"

    # Output events
    SPEAK_EVENT = "speak_event"
    DISPLAY_TEXT_EVENT = "display_text_event"
    UI_UPDATE_EVENT = "ui_update_event"

    # Action events
    EXECUTE_ACTION_EVENT = "execute_action_event"
    ACTION_RESULT_EVENT = "action_result_event"

    # System events
    SYSTEM_STATUS_EVENT = "system_status_event"
    ERROR_EVENT = "error_event"
    MEMORY_UPDATE_EVENT = "memory_update_event"


class Event(BaseModel):
    """Base event structure for all message bus communications"""

    event_type: EventType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = Field(description="Component that generated the event")
    event_id: str = Field(description="Unique identifier for this event")
    correlation_id: Optional[str] = Field(default=None, description="Correlates related events")

    class Config:
        use_enum_values = True


class TextInputData(BaseModel):
    """Data structure for text input events"""

    text: str = Field(..., max_length=10000, description="The input text")
    source: str = Field(..., description="Source of the text input (cli, gui, file, clipboard)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceInputData(BaseModel):
    """Data structure for voice input events"""

    transcribed_text: str = Field(..., description="Transcribed speech text")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in transcription")
    audio_metadata: Dict[str, Any] = Field(default_factory=dict, description="Audio processing metadata")
    duration_seconds: Optional[float] = Field(default=None, description="Audio duration in seconds")


class ImageInputData(BaseModel):
    """Data structure for image input events"""

    image_data: bytes = Field(..., description="Raw image data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Image metadata")
    file_path: Optional[str] = Field(default=None, description="Original file path if applicable")
    format: str = Field(..., description="Image format (JPEG, PNG, etc.)")
    dimensions: Optional[List[int]] = Field(default=None, description="Image dimensions [width, height]")


class NLPResponseData(BaseModel):
    """Data structure for NLP processing results"""

    original_text: str = Field(..., description="Original input text")
    intent: str = Field(..., description="Recognized intent")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted entities")
    sentiment: str = Field(..., description="Sentiment analysis result")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in analysis")
    processed_text: Optional[str] = Field(default=None, description="Processed/normalized text")
    language: Optional[str] = Field(default=None, description="Detected language")


class VisionResponseData(BaseModel):
    """Data structure for vision processing results"""

    objects_detected: List[Dict[str, Any]] = Field(default_factory=list, description="Objects detected in image")
    text_found: Optional[str] = Field(default=None, description="Text extracted via OCR")
    scene_classification: Optional[str] = Field(default=None, description="Scene classification")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores for various detections")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextData(BaseModel):
    """Data structure for context information"""

    context_type: str = Field(..., description="Type of context (conversation, user, session, knowledge)")
    content: Dict[str, Any] = Field(..., description="Context content")
    relevance_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Relevance to current query")
    timestamp: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(default=None, description="When this context expires")


class SpeakData(BaseModel):
    """Data structure for text-to-speech requests"""

    text: str = Field(..., description="Text to be spoken")
    voice_type: str = Field(default="default", description="Voice type or ID")
    rate: Optional[int] = Field(default=None, description="Speech rate (WPM)")
    volume: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Speech volume")
    priority: int = Field(default=1, description="Priority level (1=highest)")


class DisplayTextData(BaseModel):
    """Data structure for text display requests"""

    text: str = Field(..., description="Text to display")
    destination: str = Field(default="console", description="Display destination")
    format_type: str = Field(default="plain", description="Formatting type (plain, markdown, json)")
    color: Optional[str] = Field(default=None, description="Text color")
    style: Optional[str] = Field(default=None, description="Text style")


class UIUpdateData(BaseModel):
    """Data structure for UI update requests"""

    component: str = Field(..., description="UI component to update")
    action: str = Field(..., description="Action to perform (update, show, hide, enable, disable)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Update data")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")


class ExecuteActionData(BaseModel):
    """Data structure for action execution requests"""

    command: str = Field(..., description="Command to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    permission_level: str = Field(default="moderate", description="Required permission level")
    requires_confirmation: bool = Field(default=False, description="Whether user confirmation is required")
    timeout_seconds: int = Field(default=30, description="Action timeout in seconds")


class ActionResultData(BaseModel):
    """Data structure for action execution results"""

    command: str = Field(..., description="Original command that was executed")
    success: bool = Field(..., description="Whether the action was successful")
    result_data: Optional[Dict[str, Any]] = Field(default=None, description="Result data")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_seconds: float = Field(..., description="Time taken to execute")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SystemStatusData(BaseModel):
    """Data structure for system status updates"""

    component: str = Field(..., description="Component reporting status")
    status: str = Field(..., description="Status (ready, busy, error, offline)")
    message: Optional[str] = Field(default=None, description="Status message")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorData(BaseModel):
    """Data structure for error reporting"""

    component: str = Field(..., description="Component where error occurred")
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Detailed error message")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if available")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    severity: str = Field(default="error", description="Error severity (warning, error, critical)")
    timestamp: datetime = Field(default_factory=datetime.now)


class MemoryUpdateData(BaseModel):
    """Data structure for memory updates"""

    memory_type: str = Field(..., description="Type of memory (short_term, long_term, knowledge)")
    operation: str = Field(..., description="Operation (add, update, delete, retrieve)")
    data: Dict[str, Any] = Field(..., description="Memory data")
    key: Optional[str] = Field(default=None, description="Memory key for operations")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration time")