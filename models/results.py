"""
Result data models for processing outputs and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class ResultStatus(str, Enum):
    """Status of processing results"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ProcessingResult(BaseModel):
    """Base result structure for all processing operations"""

    status: ResultStatus
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_seconds: float = Field(..., ge=0.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    component: str = Field(..., description="Component that generated the result")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class IntentResult(BaseModel):
    """Intent recognition result"""

    intent: str = Field(..., description="Recognized intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in intent recognition")
    alternative_intents: List[Dict[str, Any]] = Field(default_factory=list)
    intent_parameters: Dict[str, Any] = Field(default_factory=dict)


class EntityResult(BaseModel):
    """Named entity recognition result"""

    entity_type: str = Field(..., description="Type of entity (person, place, organization, etc.)")
    entity_value: str = Field(..., description="Extracted entity value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in entity recognition")
    start_position: int = Field(..., ge=0, description="Start position in original text")
    end_position: int = Field(..., ge=0, description="End position in original text")
    context: Optional[str] = None


class SentimentResult(BaseModel):
    """Sentiment analysis result"""

    sentiment: str = Field(..., regex="^(positive|negative|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in sentiment analysis")
    score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score (-1 to 1)")
    emotions: Dict[str, float] = Field(default_factory=dict, description="Emotion scores")


class NLPProcessingResult(ProcessingResult):
    """NLP processing specific result"""

    original_text: str
    intent: IntentResult
    entities: List[EntityResult] = Field(default_factory=list)
    sentiment: SentimentResult
    language: Optional[str] = None
    processed_text: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class DetectionResult(BaseModel):
    """Object detection result"""

    class_name: str = Field(..., description="Detected object class")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    bounding_box: List[int] = Field(..., min_items=4, max_items=4, description="Bounding box [x, y, width, height]")
    area: Optional[int] = None

    @validator('bounding_box')
    def validate_bounding_box(cls, v):
        if any(coord < 0 for coord in v):
            raise ValueError("Bounding box coordinates must be non-negative")
        if v[2] <= 0 or v[3] <= 0:  # width and height
            raise ValueError("Bounding box width and height must be positive")
        return v


class OCRResult(BaseModel):
    """OCR processing result"""

    extracted_text: str = Field(..., description="Text extracted from image")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall OCR confidence")
    words: List[Dict[str, Any]] = Field(default_factory=list, description="Individual word results")
    lines: List[Dict[str, Any]] = Field(default_factory=list, description="Text lines")
    language: Optional[str] = None
    rotation_angle: Optional[float] = None


class SceneClassificationResult(BaseModel):
    """Scene classification result"""

    scene_class: str = Field(..., description="Classified scene")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    alternative_classes: List[Dict[str, Any]] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class VisionProcessingResult(ProcessingResult):
    """Vision processing specific result"""

    image_format: str
    image_dimensions: List[int] = Field(..., min_items=2, max_items=2)
    objects_detected: List[DetectionResult] = Field(default_factory=list)
    ocr_result: Optional[OCRResult] = None
    scene_classification: Optional[SceneClassificationResult] = None
    features: Dict[str, Any] = Field(default_factory=dict)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


class AudioMetadata(BaseModel):
    """Audio processing metadata"""

    sample_rate: int = Field(..., ge=8000, le=48000)
    channels: int = Field(..., ge=1, le=2)
    bit_depth: int = Field(..., ge=8, le=32)
    duration_seconds: float = Field(..., ge=0.0)
    format: str = Field(..., description="Audio format (WAV, MP3, etc.)")
    file_size_bytes: Optional[int] = None


class VoiceProcessingResult(ProcessingResult):
    """Voice processing specific result"""

    transcribed_text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    audio_metadata: AudioMetadata
    language_detected: Optional[str] = None
    alternative_transcriptions: List[Dict[str, Any]] = Field(default_factory=list)
    speaker_id: Optional[str] = None
    emotion_detected: Optional[str] = None


class ActionResult(BaseModel):
    """Action execution result"""

    command: str = Field(..., description="Executed command")
    success: bool
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_seconds: float = Field(..., ge=0.0)
    output: Optional[str] = None
    return_code: Optional[int] = None
    affected_items: Optional[List[str]] = None
    requires_rollback: bool = False
    rollback_available: bool = False


class SystemActionResult(ProcessingResult):
    """System action specific result"""

    action_result: ActionResult
    permission_level: str = Field(..., description="Permission level required/used")
    confirmation_required: bool = Field(default=False)
    confirmation_granted: bool = Field(default=True)
    audit_logged: bool = Field(default=True)
    affected_windows: Optional[List[str]] = None
    affected_processes: Optional[List[str]] = None


class ContextResult(BaseModel):
    """Context retrieval result"""

    context_items: List[Dict[str, Any]] = Field(default_factory=list)
    relevance_scores: List[float] = Field(default_factory=list)
    context_type: str = Field(..., description="Type of context retrieved")
    total_matches: int = Field(default=0, ge=0)
    query_time_seconds: float = Field(..., ge=0.0)
    cache_hit: bool = Field(default=False)


class ContextProcessingResult(ProcessingResult):
    """Context management specific result"""

    operation: str = Field(..., description="Context operation performed")
    context_result: Optional[ContextResult] = None
    memory_type: str = Field(..., description="Type of memory affected")
    items_affected: int = Field(default=0, ge=0)
    context_updated: bool = Field(default=False)


class UIActionResult(BaseModel):
    """UI action result"""

    component: str = Field(..., description="UI component affected")
    action: str = Field(..., description="Action performed")
    success: bool
    updated_state: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    user_interaction: bool = Field(default=False)


class UIUpdateResult(ProcessingResult):
    """UI update specific result"""

    ui_actions: List[UIActionResult] = Field(default_factory=list)
    window_state: Optional[Dict[str, Any]] = None
    user_inputs: List[Dict[str, Any]] = Field(default_factory=list)
    display_time_seconds: Optional[float] = None


class BatchResult(BaseModel):
    """Batch processing result"""

    total_commands: int = Field(..., ge=0)
    successful_commands: int = Field(..., ge=0)
    failed_commands: int = Field(..., ge=0)
    results: List[Union[NLPProcessingResult, VisionProcessingResult, SystemActionResult]] = Field(default_factory=list)
    batch_execution_time: float = Field(..., ge=0.0)
    parallel_execution: bool = Field(default=False)
    error_summary: List[str] = Field(default_factory=list)


class ValidationErrorResult(BaseModel):
    """Validation error result"""

    field_name: str = Field(..., description="Field that failed validation")
    validation_rule: str = Field(..., description="Validation rule that failed")
    error_message: str = Field(..., description="Detailed error message")
    invalid_value: Any = Field(..., description="The invalid value")
    suggested_fix: Optional[str] = None


class ValidationResult(BaseModel):
    """Validation result"""

    is_valid: bool = Field(..., description="Overall validation status")
    validation_errors: List[ValidationErrorResult] = Field(default_factory=list)
    validation_warnings: List[ValidationErrorResult] = Field(default_factory=list)
    validated_fields: List[str] = Field(default_factory=list)
    validation_time_seconds: float = Field(..., ge=0.0)