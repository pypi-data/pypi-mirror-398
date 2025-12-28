from typing import Dict, List, Any, Optional, Union, Annotated
from datetime import datetime
from enum import Enum
import re
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, StringConstraints

SDK_PREFIX = "brynq_sdk_"
VERSION_PATTERN = r'^\d+\.\d+\.\d+$'

# strips whitespace from strings before validation
CleanStr = Annotated[str, StringConstraints(strip_whitespace=True)]


class InterfaceType(str, Enum):
    """Enumeration of interface types."""
    TEMPLATE = "TEMPLATE"
    ADVANCED = "ADVANCED"

class Frequency(BaseModel):
    """Schema for task schedule frequency"""
    day: int = Field(..., description="Day of frequency")
    hour: int = Field(..., description="Hour of frequency")
    month: int = Field(..., description="Month of frequency")
    minute: int = Field(..., description="Minute of frequency")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class TaskSchedule(BaseModel):
    """Schema for interface task schedule"""
    id: int = Field(..., description="Task schedule ID")
    task_type: str = Field(..., alias="taskType", description="Type of task")
    trigger_type: str = Field(..., alias="triggerType", description="Type of trigger")
    trigger_pattern: str = Field(..., alias="triggerPattern", description="Pattern of trigger")
    timezone: str = Field(..., description="Timezone for the task")
    next_reload: Optional[str] = Field(None, alias="nextReload", description="Next reload time")
    frequency: Frequency = Field(..., description="Frequency settings")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Task variables")
    start_after_preceding_task: Optional[bool] = Field(None, alias="startAfterPrecedingTask", description="Whether to start after preceding task")
    start_after_task_id: Optional[int] = Field(None, alias="startAfterTaskId", description="ID of task to start after")
    last_reload: str = Field(..., alias="lastReload", description="Last reload time")
    last_error_message: str = Field(..., alias="lastErrorMessage", description="Last error message")
    status: str = Field(..., description="Current status")
    disabled: bool = Field(..., description="Whether task is disabled")
    run_instant: bool = Field(..., alias="runInstant", description="Whether to run instantly")
    stopped_by_user: bool = Field(..., alias="stoppedByUser", description="Whether stopped by user")
    stepnr: int = Field(..., description="Step number")
    created_at: str = Field(..., alias="createdAt", description="Creation time")
    updated_at: str = Field(..., alias="updatedAt", description="Last update time")

    @field_validator('last_reload', 'created_at', 'updated_at', 'next_reload')
    def validate_datetime(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the string is a valid ISO format datetime"""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid datetime format: {str(e)}")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class Interface(BaseModel):
    """Schema for interface data"""
    id: int = Field(..., description="Interface ID")
    name: str = Field(..., description="Interface name")
    description: str = Field(..., description="Interface description")
    source_systems: List[int] = Field(..., alias="sourceSystems", description="List of source system IDs")
    target_systems: List[int] = Field(..., alias="targetSystems", description="List of target system IDs")
    task_schedule: TaskSchedule = Field(..., alias="taskSchedule", description="Task schedule details")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class InterfaceAppConfig(BaseModel):
    """Schema for individual app configuration within interface apps.

    Attributes:
        app: Application name
        sdk: SDK package name (must start with "brynq_sdk_")
        sdk_version: SDK version in format digits.digits.digits (aliased as "sdkVersion" in API)
    """
    model_config = ConfigDict(frozen=True, strict=True, populate_by_name=True)

    app: CleanStr = Field(..., description="Application name")
    sdk: CleanStr = Field(default="", description="SDK package name (may be empty for ADVANCED interfaces)")
    sdk_version: CleanStr = Field(default="", alias="sdkVersion", description="SDK version (may be empty for ADVANCED interfaces)")

    @field_validator('sdk')
    @classmethod
    def validate_sdk_prefix(cls, v: str) -> str:
        """Validate that SDK name starts with 'brynq_sdk_' or is empty."""
        if v and not v.startswith(SDK_PREFIX):
            raise ValueError(f"SDK name must start with '{SDK_PREFIX}' or be empty, got: {v}")
        return v

    @field_validator('sdk_version')
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Validate that version follows digits.digits.digits format or is empty."""
        if v and not re.match(VERSION_PATTERN, v):
            raise ValueError(f"SDK version must be 'digits.digits.digits' (e.g., '2.8.2'), got: {v}")
        return v


class InterfaceApps(BaseModel):
    """Schema for interface apps configuration"""
    source: InterfaceAppConfig = Field(..., description="Source application configuration")
    target: InterfaceAppConfig = Field(..., description="Target application configuration")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class InterfaceDetail(BaseModel):
    """Schema for detailed interface information"""
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)

    id: int = Field(..., description="Interface id")
    uuid: str = Field(..., description="Interace uid")
    name: str = Field(..., description="Interface name")
    type: InterfaceType = Field(..., description="Interface type (TEMPLATE or ADVANCED)")
    in_development: bool = Field(..., description="Whether interface is in development.", alias="inDevelopment")
    apps: InterfaceApps = Field(..., description="Interface applications configuration")

    @model_validator(mode='after')
    def validate_apps_for_type(self) -> 'InterfaceDetail':
        """Validate that sdk and sdk_version are non-empty unless type is ADVANCED."""
        if self.type == InterfaceType.TEMPLATE:
            for app_name in ['source', 'target']:
                config = getattr(self.apps, app_name)
                if not config.sdk:
                    raise ValueError(f"{app_name}.sdk must be non-empty for interface type {self.type.value}")
                if not config.sdk_version:
                    raise ValueError(f"{app_name}.sdk_version must be non-empty for interface type {self.type.value}")
        return self


class MappingValue(BaseModel):
    """Schema for a single mapping value"""
    input: Dict[Any, Any] = Field(..., description="Input mapping key-value pairs")
    output: Dict[Any, Any] = Field(..., description="Output mapping key-value pairs")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class MappingItem(BaseModel):
    """Schema for a single mapping configuration"""
    guid: str = Field(..., description="Unique identifier for the mapping")
    name: str = Field(..., description="Name of the mapping")
    values: List[MappingValue] = Field(default_factory=list, description="List of mapping values")
    default_value: Optional[str] = Field(None, alias="defaultValue", description="Default value if no mapping matches")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class InterfaceConfig(BaseModel):
    """Schema for interface configuration"""
    mapping: List[Dict[str, Any]] = Field(default_factory=list, description="List of mappings")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Configuration variables")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class Schedule(BaseModel):
    """Schema for interface schedule configuration"""
    id: int = Field(..., description="Schedule ID")
    trigger_type: str = Field(..., alias="triggerType", description="Type of trigger")
    trigger_pattern: str = Field(..., alias="triggerPattern", description="Pattern for the trigger")
    timezone: str = Field(..., description="Timezone setting")
    next_reload: Optional[str] = Field(None, alias="nextReload", description="Next scheduled reload time")
    frequency: Frequency = Field(..., description="Frequency settings")
    start_after_preceding_task: Optional[bool] = Field(None, alias="startAfterPrecedingTask", description="Whether to start after preceding task")
    last_reload: str = Field(..., alias="lastReload", description="Last reload time")
    last_error_message: str = Field(..., alias="lastErrorMessage", description="Last error message")

    @field_validator('last_reload', 'next_reload')
    def validate_datetime(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the string is a valid ISO format datetime"""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid datetime format: {str(e)}")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class Scope(BaseModel):
    """Schema for interface scope data"""
    live: Optional[Dict[str, Any]] = Field(None, description="Live scope configuration")
    draft: Optional[Dict[str, Any]] = Field(None, description="Draft scope configuration")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class DevSettings(BaseModel):
    """Schema for interface dev settings"""
    docker_image: str = Field(..., alias="dockerImage", description="Docker image name")
    sftp_mapping: List[dict] = Field(..., alias="sftpMapping", description="SFTP mapping configuration")
    runfile_path: str = Field(..., alias="runfilePath", description="Path to the runfile")
    stop_is_allowed: bool = Field(..., alias="stopIsAllowed", description="Whether stopping is allowed")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True
