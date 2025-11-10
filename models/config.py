"""
Configuration data models using Pydantic for validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class AppConfig(BaseModel):
    """Application configuration"""
    name: str = "SmartSense"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")


class MessageBusConfig(BaseModel):
    """Message bus configuration"""
    max_queue_size: int = Field(default=1000, ge=1, le=10000)
    processing_timeout: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)


class NLPConfig(BaseModel):
    """NLP model configuration"""
    primary_model: str = "distilbert-base-uncased"
    fallback_model: str = "rule-based"
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4000, ge=100, le=32000)

    @validator('primary_model')
    def validate_primary_model(cls, v):
        allowed_models = [
            "distilbert-base-uncased",
            "bert-base-uncased",
            "roberta-base",
            "gpt-3.5-turbo",
            "gpt-4"
        ]
        if v not in allowed_models and v != "rule-based":
            raise ValueError(f"Model {v} not in allowed list")
        return v


class VisionConfig(BaseModel):
    """Vision model configuration"""
    object_detector: str = Field(default="yolov5", pattern="^(yolov5|yolov8|faster_rcnn|ssd)$")
    ocr_engine: str = Field(default="tesseract", pattern="^(tesseract|easyocr|paddleocr)$")
    image_max_size: List[int] = Field(default=[1920, 1080], min_length=2, max_length=2)

    @validator('image_max_size')
    def validate_image_size(cls, v):
        if v[0] < 100 or v[1] < 100:
            raise ValueError("Image dimensions must be at least 100x100")
        if v[0] > 4096 or v[1] > 4096:
            raise ValueError("Image dimensions must not exceed 4096x4096")
        return v


class SpeechConfig(BaseModel):
    """Speech processing configuration"""
    recognition_model: str = Field(default="whisper-base", pattern="^(whisper-base|whisper-small|whisper-medium)$")
    synthesis_engine: str = Field(default="pyttsx3", pattern="^(pyttsx3|gtts|edge-tts)$")
    sample_rate: int = Field(default=16000, ge=8000, le=48000)

    @validator('sample_rate')
    def validate_sample_rate(cls, v):
        valid_rates = [8000, 11025, 16000, 22050, 44100, 48000]
        if v not in valid_rates:
            raise ValueError(f"Sample rate {v} not in valid rates: {valid_rates}")
        return v


class AIModelsConfig(BaseModel):
    """AI models configuration"""
    nlp: NLPConfig
    vision: VisionConfig
    speech: SpeechConfig


class UIConfig(BaseModel):
    """User interface configuration"""
    theme: str = Field(default="light", pattern="^(light|dark|auto)$")
    window_size: List[int] = Field(default=[800, 600], min_length=2, max_length=2)
    font_size: int = Field(default=12, ge=8, le=24)
    auto_save: bool = True

    @validator('window_size')
    def validate_window_size(cls, v):
        if v[0] < 400 or v[1] < 300:
            raise ValueError("Window size must be at least 400x300")
        if v[0] > 2560 or v[1] > 1440:
            raise ValueError("Window size must not exceed 2560x1440")
        return v


class SecurityConfig(BaseModel):
    """Security configuration"""
    action_whitelist_enabled: bool = True
    confirmation_required: bool = True
    permission_level: str = Field(default="moderate", pattern="^(safe|moderate|elevated|restricted)$")
    audit_logging: bool = True


class SystemConfig(BaseModel):
    """System configuration"""
    temp_dir: str = "./data/temp"
    cache_dir: str = "./data/cache"
    model_cache_size: str = Field(default="2GB", pattern=r"^\d+[KMGT]?B$")
    log_rotation: str = Field(default="daily", pattern="^(daily|weekly|monthly|size)$")

    @validator('model_cache_size')
    def validate_cache_size(cls, v):
        # Convert to bytes for validation
        size_str = v.upper()
        if size_str.endswith('KB'):
            size = int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            size = int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            size = int(size_str[:-2]) * 1024 * 1024 * 1024
        elif size_str.endswith('TB'):
            size = int(size_str[:-2]) * 1024 * 1024 * 1024 * 1024
        else:
            size = int(size_str[:-1])  # Assume bytes

        if size < 100 * 1024 * 1024:  # 100MB minimum
            raise ValueError("Model cache size must be at least 100MB")
        if size > 100 * 1024 * 1024 * 1024:  # 100GB maximum
            raise ValueError("Model cache size must not exceed 100GB")

        return v


class SmartSenseConfig(BaseModel):
    """Main configuration container"""
    app: AppConfig = Field(default_factory=AppConfig)
    message_bus: MessageBusConfig = Field(default_factory=MessageBusConfig)
    models: AIModelsConfig
    ui: UIConfig = Field(default_factory=UIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)

    class Config:
        extra = "forbid"  # Prevent extra fields
        validate_assignment = True


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration overrides"""
    SMARTSENSE_CONFIG_PATH: Optional[str] = None
    SMARTSENSE_LOG_LEVEL: Optional[str] = None
    SMARTSENSE_DATA_DIR: Optional[str] = None
    SMARTSENSE_MODEL_DIR: Optional[str] = None
    SMARTSENSE_CACHE_SIZE: Optional[str] = None
    SMARTSENSE_API_KEY: Optional[str] = None
    SMARTSENSE_DEBUG: Optional[str] = None

    @validator('SMARTSENSE_LOG_LEVEL')
    def validate_log_level(cls, v):
        if v is not None:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if v.upper() not in valid_levels:
                raise ValueError(f"Log level {v} not in valid levels: {valid_levels}")
        return v

    @validator('SMARTSENSE_DEBUG')
    def validate_debug(cls, v):
        if v is not None:
            return v.lower() in ('true', '1', 'yes', 'on')
        return v