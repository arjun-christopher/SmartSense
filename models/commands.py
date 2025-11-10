"""
Command data models for system automation and actions.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator


class CommandType(str, Enum):
    """Types of commands that can be executed"""

    # Window management
    WINDOW_FOCUS = "window_focus"
    WINDOW_CLOSE = "window_close"
    WINDOW_MINIMIZE = "window_minimize"
    WINDOW_MAXIMIZE = "window_maximize"
    WINDOW_MOVE = "window_move"

    # Mouse actions
    CLICK = "click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    DRAG = "drag"
    SCROLL = "scroll"

    # Keyboard actions
    TYPE = "type"
    HOTKEY = "hotkey"
    PRESS = "press"
    KEY_SEQUENCE = "key_sequence"

    # Application control
    LAUNCH = "launch"
    CLOSE_APP = "close_app"
    RESTART_APP = "restart_app"
    SWITCH_TO = "switch_to"

    # File operations
    OPEN_FILE = "open_file"
    DELETE_FILE = "delete_file"
    COPY_FILE = "copy_file"
    MOVE_FILE = "move_file"


class PermissionLevel(str, Enum):
    """Permission levels for command execution"""
    SAFE = "safe"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    RESTRICTED = "restricted"


class Command(BaseModel):
    """Base command structure"""

    command_type: CommandType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    permission_level: PermissionLevel = PermissionLevel.MODERATE
    requires_confirmation: bool = False
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    description: Optional[str] = None
    command_id: Optional[str] = None

    class Config:
        use_enum_values = True


class WindowCommand(BaseModel):
    """Window management command"""

    command_type: CommandType = Field(..., regex="^(window_focus|window_close|window_minimize|window_maximize|window_move)$")
    window_title: str = Field(..., description="Title or partial title of the window")
    window_class: Optional[str] = None
    process_name: Optional[str] = None
    x_position: Optional[int] = Field(default=None, ge=-32768, le=32767)
    y_position: Optional[int] = Field(default=None, ge=-32768, le=32767)
    bring_to_front: bool = True

    @validator('window_title')
    def validate_window_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Window title cannot be empty")
        return v.strip()


class MouseCommand(BaseModel):
    """Mouse action command"""

    command_type: CommandType = Field(..., regex="^(click|right_click|double_click|drag|scroll)$")
    x_coordinate: int = Field(..., ge=0, le=9999)
    y_coordinate: int = Field(..., ge=0, le=9999)
    button: str = Field(default="left", regex="^(left|right|middle)$")
    x_end_coordinate: Optional[int] = Field(default=None, ge=0, le=9999)
    y_end_coordinate: Optional[int] = Field(default=None, ge=0, le=9999)
    scroll_direction: Optional[str] = Field(default=None, regex="^(up|down|left|right)$")
    scroll_amount: Optional[int] = Field(default=1, ge=-100, le=100)
    move_duration: float = Field(default=0.1, ge=0.01, le=5.0)

    @validator('x_end_coordinate', 'y_end_coordinate')
    def validate_drag_coordinates(cls, v, values):
        if v is not None and values.get('command_type') != 'drag':
            raise ValueError("End coordinates only valid for drag commands")
        return v

    @validator('scroll_direction', 'scroll_amount')
    def validate_scroll_parameters(cls, v, values):
        if values.get('command_type') != 'scroll' and v is not None:
            raise ValueError("Scroll parameters only valid for scroll commands")
        return v


class KeyboardCommand(BaseModel):
    """Keyboard action command"""

    command_type: CommandType = Field(..., regex="^(type|hotkey|press|key_sequence)$")
    text: Optional[str] = None
    key: Optional[str] = None
    modifier: Optional[str] = Field(default=None, regex="^(ctrl|alt|shift|win)$")
    key_sequence: Optional[List[str]] = None
    target_window: Optional[str] = None
    typing_speed: float = Field(default=0.05, ge=0.001, le=1.0)

    @validator('text')
    def validate_type_text(cls, v, values):
        if values.get('command_type') == 'type' and (not v or len(v) == 0):
            raise ValueError("Text is required for type commands")
        return v

    @validator('key')
    def validate_press_key(cls, v, values):
        if values.get('command_type') == 'press' and not v:
            raise ValueError("Key is required for press commands")
        return v

    @validator('modifier')
    def validate_hotkey_modifier(cls, v, values):
        if values.get('command_type') == 'hotkey' and not v:
            raise ValueError("Modifier is required for hotkey commands")
        return v

    @validator('key_sequence')
    def validate_key_sequence(cls, v, values):
        if values.get('command_type') == 'key_sequence' and (not v or len(v) == 0):
            raise ValueError("Key sequence is required for key_sequence commands")
        return v


class ApplicationCommand(BaseModel):
    """Application control command"""

    command_type: CommandType = Field(..., regex="^(launch|close_app|restart_app|switch_to)$")
    application_name: str = Field(..., description="Name of the application")
    executable_path: Optional[str] = None
    arguments: List[str] = Field(default_factory=list)
    working_directory: Optional[str] = None
    wait_for_startup: bool = True
    startup_timeout: int = Field(default=30, ge=1, le=120)

    @validator('executable_path')
    def validate_executable_path(cls, v, values):
        if values.get('command_type') == 'launch' and not v:
            raise ValueError("Executable path is required for launch commands")
        return v


class FileCommand(BaseModel):
    """File operation command"""

    command_type: CommandType = Field(..., regex="^(open_file|delete_file|copy_file|move_file)$")
    file_path: str = Field(..., description="Path to the file")
    destination_path: Optional[str] = None
    use_default_app: bool = True
    confirm_destructive: bool = True

    @validator('destination_path')
    def validate_destination_path(cls, v, values):
        command_type = values.get('command_type')
        if command_type in ['copy_file', 'move_file'] and not v:
            raise ValueError("Destination path is required for copy/move commands")
        return v

    @validator('file_path')
    def validate_file_path(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("File path cannot be empty")
        return v.strip()


class CommandBatch(BaseModel):
    """Batch of commands to execute sequentially"""

    commands: List[Union[WindowCommand, MouseCommand, KeyboardCommand, ApplicationCommand, FileCommand]]
    batch_name: Optional[str] = None
    continue_on_error: bool = False
    parallel_execution: bool = False
    batch_timeout: int = Field(default=120, ge=1, le=600)

    @validator('commands')
    def validate_commands_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Commands list cannot be empty")
        return v


class CommandTemplate(BaseModel):
    """Reusable command template"""

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    command_template: Union[WindowCommand, MouseCommand, KeyboardCommand, ApplicationCommand, FileCommand]
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    category: str = Field(default="general", description="Template category")
    tags: List[str] = Field(default_factory=list)
    is_enabled: bool = True

    @validator('name')
    def validate_template_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Template name cannot be empty")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Template name must contain only alphanumeric characters, hyphens, and underscores")
        return v.strip().lower()