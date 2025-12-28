"""
Scenarios schemas for an active template interface in BrynQ API (2.0.0).
By default, this endpoint returns the most recent live version. If the latest version is not yet published (still a draft), the draft version is returned instead.

These schemas represent the exact structure of the response schema (application/json).

For parsed/processed scenario models and business logic, see brynq_sdk_brynq.scenarios.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union, TypedDict

from pydantic import BaseModel, ConfigDict, Field, RootModel, EmailStr, field_validator
from pydantic.types import AwareDatetime
from typing_extensions import Annotated


# ============================================================================
# 1. Type Aliases & Enums
# ============================================================================

class FieldType(str, Enum):
    """Enumeration of field type.

    """
    CUSTOM = "CUSTOM"
    LIBRARY = "LIBRARY"
    FIXED = "FIXED"
    EMPTY = "EMPTY"
    CONFIGURATION = "CONFIGURATION"


class SystemType(str, Enum):
    """Enumeration of system type.

    """
    SOURCE = "source"
    TARGET = "target"


class RelationType(str, Enum):
    """Cardinality of the mapping.

    Defines if a record represents a simple 1:1 map or a complex N:N explosion.
    """
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class ConfigurationType(str, Enum):
    """Enumeration of configuration field types.

    Defines the type of configuration field used in ConfigFieldValues.
    """
    ATTACHMENT = "ATTACHMENT"
    TEXT = "TEXT"
    EMAIL = "EMAIL"
    NUMBER = "NUMBER"
    RICHTEXT = "RICHTEXT"
    DATEPICKER = "DATEPICKER"
    SELECTION = "SELECTION"


# ============================================================================
# 2. Value level API Models
# ============================================================================
# These classes define the shape of the values of the json returned by BrynQ API.

class MultiLanguageText(TypedDict):
    """Multi-language text dictionary with English and Dutch labels.

    Attributes:
        en: English text
        nl: Dutch text
    """
    en: str
    nl: str

# VALUES
class MappingValue(BaseModel):
    """Represents a single translation rule (e.g., 'CEO' -> '96').

    Both input and output dictionaries use field identifier keys (UUIDs or schema.name patterns)
    that need to be converted to readable field names. The values are the actual data values.

    Attributes:
        input: Dictionary mapping source field identifiers (UUIDs or schema.name patterns) to source values.
            Example: {"work_schema-title": "CEO"} means source field "work_schema-title" has value "CEO".
            The key is a field identifier (not a readable field name) and needs conversion.
        output: Dictionary mapping target field identifiers (UUIDs or schema.name patterns) to target values.
            Example: {"ea06ce9f-e10e-484e-bdf0-ec58087f15c5": "96"} means target field with UUID should get value "96".
            The key is a UUID (not a readable field name) and needs conversion.
    """
    input: Dict[str, str]
    output: Dict[str, str]
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class CustomDataValues(BaseModel):
    """Schema for custom fields from the source system.

    Attributes:
        uuid: Unique identifier
        name: Human-readable label
        technical_name: System ID (aliased as "technicalName" in API)
        source: Category bucket
        description: Business context
    """
    uuid: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Human-readable label")
    technical_name: str = Field(..., alias="technicalName", description="System ID")
    source: str = Field(..., description="Category bucket")
    description: str = Field(..., description="Business context")
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class LibraryFieldValues(BaseModel):
    """Schema for BrynQ Library fields.

    Attributes:
        id: integer identifier
        uuid: str or schema field identifier (e.g., "people_schema-work.employeeIdInCompany")
        required: Whether this field is required
        field: Field name/identifier
        field_label: Multi-language label dictionary (aliased as "fieldLabel" in API)
        app_id: Application ID (aliased as "appId" in API)
        category: Category metadata dictionary
    """
    id: Optional[int] = None
    uuid: Optional[str] = None
    required: Optional[bool] = None
    field: Optional[str] = None
    field_label: Optional[Dict[str, str]] = Field(default=None, alias="fieldLabel")
    app_id: Optional[int] = Field(default=None, alias="appId")
    category: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)

class ConfigFieldValuesSelection(BaseModel):
    """Configuration field of type SELECTION.

    Attributes:
        uuid: str identifier
        question: Multi-language question dictionary with "en" (English) and "nl" (Dutch) keys
        value: List of selection options, each with "en" and "nl" keys
        type: Always "SELECTION"
    """
    uuid: str
    question: MultiLanguageText = Field(..., description="Question asked to customer.")
    value: List[MultiLanguageText] = Field(..., description="List of selection options with en/nl labels")
    type: Literal[ConfigurationType.SELECTION] = ConfigurationType.SELECTION
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class ConfigFieldValuesText(BaseModel):
    """Configuration field of type TEXT.

    Attributes:
        uuid: str identifier
        question: Multi-language question dictionary with "en" (English) and "nl" (Dutch) keys
        value: Text string response
        type: Always "TEXT"
    """
    uuid: str
    question: MultiLanguageText = Field(..., description="Question asked to customer.")
    value: str = Field(..., description="Text response")
    type: Literal[ConfigurationType.TEXT] = ConfigurationType.TEXT
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class ConfigFieldValuesEmail(BaseModel):
    """Configuration field of type EMAIL.

    Attributes:
        uuid: str identifier
        question: Multi-language question dictionary with "en" (English) and "nl" (Dutch) keys
        value: Email address string (validated as email format)
        type: Always "EMAIL"
    """
    uuid: str
    question: MultiLanguageText = Field(..., description="Question asked to customer.")
    value: EmailStr = Field(..., description="Email address response")
    type: Literal[ConfigurationType.EMAIL] = ConfigurationType.EMAIL
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class ConfigFieldValuesNumber(BaseModel):
    """Configuration field of type NUMBER.

    Attributes:
        uuid: str identifier
        question: Multi-language question dictionary with "en" (English) and "nl" (Dutch) keys
        value: Numeric value (integer or float)
        type: Always "NUMBER"
    """
    uuid: str
    question: MultiLanguageText = Field(..., description="Question asked to customer.")
    value: Union[int, float] = Field(..., description="Numeric response")
    type: Literal[ConfigurationType.NUMBER] = ConfigurationType.NUMBER
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class ConfigFieldValuesRichtext(BaseModel):
    """Configuration field of type RICHTEXT.

    Attributes:
        uuid: str identifier
        question: Multi-language question dictionary with "en" (English) and "nl" (Dutch) keys
        value: Rich text string (may include HTML elements)
        type: Always "RICHTEXT"
    """
    uuid: str
    question: MultiLanguageText = Field(..., description="Question asked to customer.")
    value: str = Field(..., description="Rich text response (may include HTML)")
    type: Literal[ConfigurationType.RICHTEXT] = ConfigurationType.RICHTEXT
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class ConfigFieldValuesDatepicker(BaseModel):
    """Configuration field of type DATEPICKER.

    Handles both single dates and date ranges because the API
    does not distinguish between them in the 'type' field.
    """
    uuid: str
    question: MultiLanguageText = Field(..., description="Question asked to customer.")
    value: Union[AwareDatetime, List[AwareDatetime]] = Field(
        ...,
        description="Single datetime or list of 2 datetimes (ISO format with timezone)"
    )
    type: Literal[ConfigurationType.DATEPICKER] = ConfigurationType.DATEPICKER

    @field_validator('value')
    @classmethod
    def validate_range_length(cls, v: Union[datetime, List[datetime]]) -> Union[datetime, List[datetime]]:
        """Validate list length if input is a list."""
        if isinstance(v, list) and len(v) != 2:
            raise ValueError(f"Date range must contain exactly 2 datetime items, got {len(v)}")
        return v

    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class ConfigFieldValuesAttachment(BaseModel):
    """Configuration field of type ATTACHMENT.

    Attributes:
        uuid: str identifier
        question: Multi-language question dictionary with "en" (English) and "nl" (Dutch) keys
        value: Always None for attachment type
        type: Always "ATTACHMENT"
    """
    uuid: str
    question: MultiLanguageText = Field(..., description="Question asked to customer.")
    value: None = Field(None, description="Always None for attachment type")
    type: Literal[ConfigurationType.ATTACHMENT] = ConfigurationType.ATTACHMENT
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


# Discriminated union for ConfigFieldValues based on type field
ConfigFieldValues = Annotated[
    Union[
        ConfigFieldValuesSelection,
        ConfigFieldValuesText,
        ConfigFieldValuesEmail,
        ConfigFieldValuesNumber,
        ConfigFieldValuesRichtext,
        ConfigFieldValuesDatepicker,
        ConfigFieldValuesAttachment,
    ],
    Field(discriminator="type")
]


# ============================================================================
# 2. Field (or key) level API Models
# ============================================================================
# These classes define the shape of the fields of the json returned by BrynQ API. They contain values via data, and are a of a certain type.
class CustomSourceOrTargetField(BaseModel):
    """Custom field type from external system.

    Attributes:
        type: Always "CUSTOM" for this field type
        data: List of custom field descriptors
    """
    type: Literal["CUSTOM"] = "CUSTOM"
    data: List[CustomDataValues]
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class LibrarySourceOrTargetField(BaseModel):
    """Library field type from BrynQ library.

    Attributes:
        type: Always "LIBRARY" for this field type
        data: List of LibraryFieldValues objects
    """
    type: Literal["LIBRARY"] = "LIBRARY"
    data: List[LibraryFieldValues]
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class EmptySourceOrTargetField(BaseModel):
    """Empty field type (no value).

    Attributes:
        type: Always "EMPTY" for this field type
        data: Empty list (no data for empty fields)
    """
    type: Literal['EMPTY'] = "EMPTY"
    data: List[Any] = Field(default_factory=list)
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class FixedSourceOrTargetField(BaseModel):
    """Fixed/literal value field type.

    Attributes:
        type: Always "FIXED" for this field type
        data: The fixed literal value string
    """
    type: Literal["FIXED"] = "FIXED"
    data: str
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class ConfigurationSourceOrTargetField(BaseModel):
    """Configuration field type.

    Attributes:
        type: Always "CONFIGURATION" for this field type
        data: List of configuration field values
    """
    type: Literal["CONFIGURATION"] = "CONFIGURATION"
    data: List[ConfigFieldValues]
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True, extra="allow")

# General field class that can be any of the above types, distinguished by the 'type' value.
SourceOrTargetField = Annotated[
    Union[CustomSourceOrTargetField, LibrarySourceOrTargetField, FixedSourceOrTargetField, EmptySourceOrTargetField, ConfigurationSourceOrTargetField],
    Field(discriminator="type")
]

# ============================================================================
# 2. Scenario Structure API Models
# ============================================================================
class ScenarioMappingConfiguration(BaseModel):
    """Value mapping configuration for translating source values to target values.

    Attributes:
        values: Explicit mapping values when value mapping is required
        default_value: Fallback value applied when no mapping match is found (aliased as "defaultValue" in API)
    """
    values: List[MappingValue] = Field(default_factory=list)
    default_value: str = Field(default="", alias="defaultValue")
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


class ScenarioDetail(BaseModel):
    """Represents a single detail/mapping within a scenario. Called a 'record' when parsed.

    Represents the content fields of a scenario detail mapping:
        - id: Primary key of the detail record
        - logic: Optional transformation logic
        - unique: Whether this mapping must be unique across the scenario
        - required: Whether the field is mandatory
        - mapping_required: Indicates if an explicit mapping table is required (aliased as "mappingRequired" in API)
        - source: Source field definition
        - target: Target field definition
        - mapping: Mapping or value-translation configuration (may be absent)
    """
    id: str = Field(..., description="Primary key of the detail record")
    logic: str = Field(default="", description="Optional transformation logic")
    unique: bool = Field(default=False, description="Must this mapping be unique across the scenario?")
    required: bool = Field(default=False, description="Is the field mandatory?")
    mapping_required: Optional[bool] = Field(default=False, alias="mappingRequired", description="Flag indicating whether an explicit mapping table is needed")
    source: SourceOrTargetField = Field(..., description="One or more source fields, each of type 'CUSTOM', 'LIBRARY', 'FIXED', 'EMPTY', or 'CONFIGURATION'.")
    target: SourceOrTargetField = Field(..., description="One or more target fields, each of type 'CUSTOM', 'LIBRARY', 'FIXED', or 'CONFIGURATION'.")
    mapping: Optional[ScenarioMappingConfiguration] = Field(default=None, description="Mapping/value-translation configuration (may be absent)")
    model_config = ConfigDict(frozen=True, strict=False, populate_by_name=True)


# ============================================================================
# 3. Scenario API Model
# ============================================================================
class Scenario(BaseModel):
    """Raw scenario model as returned by the API.

    Attributes:
        id: Scenario identifier
        name: Scenario display name
        description: Scenario business context
        details: Collection of field-level mappings
    """
    id: str = Field(..., description="Scenario identifier")
    name: str = Field(..., description="Scenario display name")
    description: str = Field(default="", description="Scenario business context")
    details: List[ScenarioDetail] = Field(..., description="Collection of field-level mappings")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

# ============================================================================
# 4. Scenarios API Response Model
# ============================================================================
class Scenarios(RootModel[List[Scenario]]):
    """API response model representing a list of scenarios.

    In JSON format, this is represented as an array of scenario objects:
    [{scenario}, {scenario}, ...]

    The root value is a list of Scenario objects.
    """
    model_config = ConfigDict(frozen=True, strict=False)
