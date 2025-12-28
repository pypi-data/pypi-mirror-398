"""
Parsed scenario models for BrynQ SDK.

These models represent the parsed/processed scenario data used in business logic.
They are NOT raw API response models - for those, see schemas/scenarios.py.

Classes:
    - Label: Multi-language label with language-specific access
    - LabelValue: String-like wrapper for Label
    - Question: Multi-language question with language-specific access
    - QuestionValue: String-like wrapper for Question
    - FieldProperties: Metadata for a single field in a mapping
    - SourceTargetFields: Collection of source or target fields
    - Record: Represents a relationship between source and target fields
"""
from __future__ import annotations

from typing import Any, Dict, Iterator, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

# Import ScenarioMappingConfiguration for Record.mapping type hint
from .scenarios import ScenarioMappingConfiguration


class Label(BaseModel):
    """Multi-language label with language-specific access.

    Examples:
        >>> label = Label(en="Customer ID", nl="Klant ID")
        >>> label.en
        'Customer ID'
        >>> label.nl
        'Klant ID'
        >>> str(label)  # Returns based on default language ('en')
        'Customer ID'
    """
    en: Optional[str] = None
    nl: Optional[str] = None
    _default_language: PrivateAttr = PrivateAttr(default='en')

    def __call__(self) -> Optional[str]:
        """Return the label for the default language set during initialization.

        Returns:
            Label string for the default language, or English if not available, or None if neither exists.
        """
        # Try to get the attribute for default language
        value = getattr(self, self._default_language, None)
        # If not available and not already English, fallback to English
        if value is None and self._default_language != 'en':
            value = getattr(self, 'en', None)
        return value

    def setup_languages(self, languages: list[str] = None) -> None:
        """Dynamically add language attributes for all detected languages.

        Args:
            languages (list[str], optional): List of detected language codes, e.g., ['en', 'nl', 'fr'].
                If None, defaults to ['en', 'nl'].

        Side effects:
            - Sets an instance attribute for each language code with initial value None if not already set.
            - Populates self.languages with the available language codes.
        """
        if languages is None:
            languages = ['en', 'nl']  # Default supported languages; can be replaced/extended
        self.languages = []
        for lang_code in languages:
            if not hasattr(self, lang_code):
                setattr(self, lang_code, None)
            self.languages.append(lang_code)

    def set_default_language(self, language: str) -> None:
        """Set the default language for __call__.

        Args:
            language: Language code ('en' or 'nl').
        """
        self._default_language = language

    def __str__(self) -> str:
        """Return the label as a string based on default language."""
        return str(self() or '')


class LabelValue(str):
    """String-like object that also exposes .en and .nl attributes from a Label object.

    This allows field.label to return a string directly while still allowing
    field.label.en and field.label.nl to work.
    """
    def __new__(cls, label_obj: Label):
        value = str(label_obj() or '')
        instance = super().__new__(cls, value)
        instance.label_obj = label_obj
        return instance

    def __repr__(self) -> str:
        """Return repr for debugger display."""
        return f"'{str(self)}'"

    def __getattr__(self, name: str):
        """Delegate attribute access to the underlying Label object for language codes."""
        # Dynamically check if the attribute exists on the Label object
        if hasattr(self.label_obj, name):
            return getattr(self.label_obj, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class Question(BaseModel):
    """Multi-language question with language-specific access.

    Example:
        >>> question = Question(en="What is your name?", nl="Wat is uw naam?")
        >>> question.en
        'What is your name?'
        >>> question.nl
        'Wat is uw naam?'
        >>> str(question)  # Returns based on default language set during initialization
        'What is your name?'
    """
    en: Optional[str] = None
    nl: Optional[str] = None
    _default_language: PrivateAttr = PrivateAttr(default='en')

    def __call__(self) -> Optional[str]:
        """Return the question for the default language set during initialization.

        Returns:
            Question string for the default language, or English if not available, or None if neither exists.
        """
        # Try to get the attribute for default language
        value = getattr(self, self._default_language, None)
        # If not available and not already English, fallback to English
        if value is None and self._default_language != 'en':
            value = getattr(self, 'en', None)
        return value

    def set_default_language(self, language: str) -> None:
        """Set the default language for __call__.

        Args:
            language: Language code ('en' or 'nl').
        """
        self._default_language = language

    def __str__(self) -> str:
        """Return the question as a string based on default language."""
        return str(self() or '')


class QuestionValue(str):
    """String-like object that also exposes .en and .nl attributes from a Question object.

    This allows field.question to return a string directly while still allowing
    field.question.en and field.question.nl to work.
    """
    def __new__(cls, question_obj: Question):
        value = str(question_obj() or '')
        instance = super().__new__(cls, value)
        instance.question_obj = question_obj
        return instance

    def __repr__(self) -> str:
        """Return repr for debugger display."""
        return f"'{str(self)}'"

    def __getattr__(self, name: str):
        """Delegate attribute access to the underlying Question object for language codes."""
        # Dynamically check if the attribute exists on the Question object
        if hasattr(self.question_obj, name):
            return getattr(self.question_obj, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class FieldProperties(BaseModel):
    """Metadata for a single field in a mapping.

    How to use:
        Access this via `scenario.field_name`. It provides details on
        validation (unique, required) and origins (schema, uuid).

    Example:
        >>> scenario = Scenario(...)
        >>> scenario.customer_id.required
        True
        >>> scenario.customer_id.unique
        False
        >>> scenario['customer_id'].label
        'Customer ID'

    Attributes:
        logic: Transformation logic string as defined in the BrynQ template
        unique: Whether this field is part of the unique key constraint
        required: Whether this field is required (cannot be empty/null)
        mapping: Value mapping dictionary (empty for individual fields, actual mapping is at Record level)
        system_type: Indicates whether this is a 'source' or 'target' field
        field_type: Indicates the field origin type: 'CUSTOM' or 'LIBRARY'
        alias: The technical field name/identifier (pythonic name for the field)
        uuid: The UUID identifier used in mapping values
        schema_name: For LIBRARY fields: category.technicalName. For CUSTOM fields: CustomDataValues.source
        technical_name: For CUSTOM fields: CustomDataValues.technical_name. Not populated for LIBRARY fields
        label: Human-readable field name displayed in BrynQ
        label_en: English human-readable field name
        label_nl: Dutch human-readable field name
        description: Business description/purpose of the field (for custom fields)
    """
    model_config = ConfigDict(extra="allow", frozen=True, populate_by_name=True)

    # Core Mapping Properties, straight from api
    logic: Optional[str] = None
    unique: bool = False
    required: bool = False
    mapping: Dict[str, Any] = Field(default_factory=dict)

    # Identification
    system_type: Optional[Literal["source", "target"]] = None
    field_type: Optional[Literal["CUSTOM", "LIBRARY", "FIXED", "EMPTY", "CONFIGURATION"]] = None
    alias: Optional[str] = None        # Python variable name
    uuid: Optional[str] = None         # API ID

    # Context
    schema_name: Optional[str] = Field(default=None, alias="schema")
    technical_name: Optional[str] = None
    label_obj: Optional[Label] = Field(default=None, alias="label", exclude=True)
    description: Optional[str] = None

    # config related optional fields
    question_obj: Optional[Question] = Field(default=None, alias="question", exclude=True)
    config_type: Optional[str] = None
    config_value: Optional[Any] = None
    _default_language: PrivateAttr = PrivateAttr(default='en')

    @property
    def label(self) -> Optional[LabelValue]:
        """Return the label as a string (default language) with .en and .nl attributes.

        Returns a LabelValue object which behaves as a string but also exposes
        .en and .nl attributes. Returns None if no label exists.

        Example:
            >>> field.label
            'Customer ID'
            >>> field.label.en
            'Customer ID'
            >>> field.label.nl
            'Klant ID'
        """
        if self.label_obj:
            return LabelValue(self.label_obj)
        return None

    @property
    def label_dict(self) -> Optional[Dict[str, Optional[str]]]:
        """Return the label as a dictionary with language codes as keys.

        Dynamically includes all language properties.

        Example:
            >>> field.label_dict
            {'en': 'Customer ID', 'nl': 'Klant ID'}
        """
        if self.label_obj:
            return self.label_obj.model_dump(exclude={'_default_language'})
        return None

    @property
    def question(self) -> Optional[QuestionValue]:
        """Return the question as a string (default language) with .en and .nl attributes.

        Returns a QuestionValue object which behaves as a string but also exposes
        .en and .nl attributes. Returns None if no question exists.

        Example:
            >>> field.question
            'What is your name?'
            >>> field.question.en
            'What is your name?'
            >>> field.question.nl
            'Wat is uw naam?'
        """
        if self.question_obj:
            return QuestionValue(self.question_obj)
        return None

    @property
    def question_dict(self) -> Optional[Dict[str, Optional[str]]]:
        """Return the question as a dictionary with language codes as keys.

        Dynamically includes all language properties.

        Example:
            >>> field.question_dict
            {'en': 'What is your name?', 'nl': 'Wat is uw naam?'}
        """
        if self.question_obj:
            return self.question_obj.model_dump(exclude={'_default_language'})
        return None

    def __repr__(self) -> str:
        """A human-friendly string representation.

        Example:
            >>> repr(field_props)
            "<FieldProperties alias='customer_id' system_type='source' field_type='CUSTOM'>"

        Returns:
            String representation showing the pythonic field name/alias, system type, and field type
        """
        alias_str = self.alias if self.alias else 'unnamed'
        system_type_str = self.system_type if self.system_type else 'unknown'
        field_type_str = self.field_type if self.field_type else 'unknown'
        return f"<FieldProperties alias='{alias_str}' system_type='{system_type_str}' field_type='{field_type_str}'>"

    def __str__(self) -> str:
        """String representation (used by print()). Delegates to __repr__."""
        return self.__repr__()


class SourceTargetFields(BaseModel):
    """Source or target field collection.

    Access via `scenario.source` or `scenario.target`.

    Example:
        >>> scenario.source.field_names
        ['employee_id', 'first_name', 'last_name']


    Attributes:
        type: Either 'source' or 'target' indicating the system type
        field_names: List of all field names for this system type (source or target)
        unique_key_fields: List of field names that are unique key fields
        required_fields: List of field names that are required
        field_properties: List of FieldProperties objects containing full metadata for all fields
        custom_fields: List of field names that are custom fields (field_type='CUSTOM')
        library_fields: List of field names that are library fields (field_type='LIBRARY')
        fields_with_logic: List of field names that have transformation logic defined
    """
    type: Literal["source", "target"]
    field_names: List[str]
    unique_key_fields: List[str]
    required_fields: List[str]
    field_properties: List[FieldProperties]
    custom_fields: List[str]
    library_fields: List[str]
    fields_with_logic: List[str]

    @property
    def field_properties_map(self) -> Dict[str, FieldProperties]:
        """Return field properties as a dict keyed by alias for fast lookup."""
        return {fp.alias: fp for fp in self.field_properties}

    def __getitem__(self, field_name: str) -> FieldProperties:
        """Enable dict-style access to field properties.

        Example:
            >>> scenario.source['first_name']
            FieldProperties(alias='first_name', ...)
        """
        props_map = self.field_properties_map
        if field_name not in props_map:
            raise KeyError(f"Field '{field_name}' not found in {self.type} fields.")
        return props_map[field_name]

    def __getattr__(self, name: str) -> FieldProperties:
        """Enable attribute-style access to field properties.

        Example:
            >>> scenario.source.first_name
            FieldProperties(alias='first_name', ...)
        """
        # Avoid recursion for Pydantic internal attributes
        if name.startswith('_') or name in ('type', 'field_names', 'unique_key_fields',
                                             'required_fields', 'field_properties',
                                             'custom_fields', 'library_fields',
                                             'fields_with_logic', 'field_properties_map',
                                             'model_fields', 'model_config'):
            raise AttributeError(f"'{name}' not found")
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{name}' is not a valid {self.type} field.")

    def __iter__(self) -> Iterator[FieldProperties]:
        """Yield FieldProperties objects.

        Example:
            >>> for field in scenario.source:
            ...     print(f"{field.alias} (required: {field.required})")
            employee_id (required: True)

        Yields:
            FieldProperties objects for each field
        """
        return iter(self.field_properties)

    def __len__(self) -> int:
        """Return the number of fields.

        Example:
            >>> len(scenario.source)
            3

        Returns:
            Number of fields
        """
        return len(self.field_names)

    def __str__(self) -> str:
        """Return a string representation for print().

        Example:
            >>> print(scenario.source)
            SourceTargetFields(type='source', fields=3)

        Returns:
            String representation
        """
        return f"SourceTargetFields(type={self.type!r}, fields={len(self.field_names)})"

    def __repr__(self) -> str:
        """Return a string representation of SourceTargetFields.

        Example:
            >>> scenario.source
            "SourceTargetFields(type='source', fields=3)"

        Returns:
            String representation
        """
        return f"SourceTargetFields(type={self.type!r}, fields={len(self.field_names)})"


class Record(BaseModel):
    """Represents a relationship between Source and Target fields.

    It's the unit of the Scenarios, and Scenario is a collection of records.

    How to use:
        Iterate over `scenario.records`. Each record can tell:
        "Take these source fields, apply this logic/mapping, and put result in these target fields."

    Example:
        >>> scenario = Scenario(...)
        >>> for record in scenario.records:
        ...     print(f"Source: {record.source.field_names} -> Target: {record.target.field_names}")
        Source: ['first_name'] -> Target: ['firstname']
        >>> record = scenario.records[0]
        >>> for field in record.source:
        ...     print(f"{field.alias} (required: {field.required})")
        first_name (required: True)
        >>> record.source.unique_key_fields
        ['first_name']
        >>> record.target.required_fields
        ['firstname']

    Attributes:
        logic: Transformation logic string as defined in the BrynQ template
        unique: Whether this mapping is part of the unique key constraint
        required: Whether this mapping is required (cannot be empty/null)
        source: SourceTargetFields object containing source field metadata
        target: SourceTargetFields object containing target field metadata
        source_field_types: Maps source field name to its type (CUSTOM, LIBRARY, FIXED, EMPTY)
        target_field_types: Maps target field name to its type (CUSTOM, LIBRARY, FIXED, EMPTY)
        relation_type: Type of mapping relationship: 'one_to_one', 'one_to_many', 'many_to_one', or 'many_to_many'
        mapping: Value mapping configuration for translating source values to target values
        id: Unique identifier for this mapping record
        fixed_source_value: If source type is FIXED, this contains the fixed literal value
        has_empty_source: Whether any source field has type EMPTY
    """
    model_config = ConfigDict(extra="allow", frozen=True)

    # Inherited properties applied to the whole group
    logic: Optional[str] = None
    unique: bool = False
    required: bool = False
    mapping: Union[ScenarioMappingConfiguration, bool, None] = None
    id: Optional[str] = None
    fixed_source_value: Optional[str] = None

    # The fields involved in this relationship
    source: SourceTargetFields
    target: SourceTargetFields
    source_field_types: Dict[str, str] = Field(default_factory=dict)
    target_field_types: Dict[str, str] = Field(default_factory=dict)

    # inferred
    relation_type: Literal["one_to_one", "one_to_many", "many_to_one", "many_to_many"]
    has_empty_source: bool = False

    # Record dunders
    def __iter__(self):
        """Enable iteration over all fields (both source and target).

        Uses `source` and `target` attributes internally.

        Example:
            >>> for field in record:
            ...     print(field.label)
            First Name
            Last Name
            >>> list(record)
            [FieldProperties(...), FieldProperties(...)]

        """
        return iter(list(self.source.field_properties) + list(self.target.field_properties))

    def __repr__(self) -> str:
        """A human-friendly string representation.

        Example:
            >>> repr(record)
            "<Record relation_type='one_to_one' source=['first_name', 'last_name'] -> target=['firstname', 'lastname']>"

        Returns:
            String representation of the Record
        """
        source_str = str(self.source.field_names)
        target_str = str(self.target.field_names)
        return (
            f"<Record relation_type='{self.relation_type}' "
            f"source={source_str} -> target={target_str}>"
        )

    def __str__(self) -> str:
        """String representation (used by print()). Delegates to __repr__."""
        return self.__repr__()
