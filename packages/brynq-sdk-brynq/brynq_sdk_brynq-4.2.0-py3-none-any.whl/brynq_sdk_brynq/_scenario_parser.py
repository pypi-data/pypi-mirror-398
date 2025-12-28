"""
Internal helpers for scenario parsing and transformation.

This module contains implementation details that are not part of the public API.
Users should interact with the Scenarios class and Scenario objects from scenarios.py.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict

from pydantic.types import AwareDatetime

from .schemas.scenarios import (
    Scenario as ScenarioSchema,
    ScenarioDetail,
    SourceOrTargetField,
    ScenarioMappingConfiguration,
    FieldType,
    SystemType,
    RelationType,
    CustomSourceOrTargetField,
    LibrarySourceOrTargetField,
    ConfigurationSourceOrTargetField,
    MappingValue,
    ConfigurationType,
    ConfigFieldValues,
)

from .schemas.scenarios_parsed import FieldProperties, Record, SourceTargetFields, Label, Question

# ============================================================================
# Type Aliases
# ============================================================================
FieldName = str
PythonicName = str
FieldPropertiesMap = Dict[FieldName, FieldProperties]
SourceToTargetMap = Dict[FieldName, List[FieldName]]
TargetToSourceMap = Dict[FieldName, List[FieldName]]


class ParsedScenarioData(TypedDict):
    """Data returned by _ScenarioParser.parse() for Scenario.from_schema() to construct a Scenario."""
    records: List[Record]
    source_to_target_map: SourceToTargetMap
    target_to_source_map: TargetToSourceMap
    field_properties: FieldPropertiesMap
    source: SourceTargetFields
    target: SourceTargetFields
    unique_key_fields: List[str]
    required_fields: List[str]
    custom_fields: FieldPropertiesMap
    all_source_fields: Set[str]
    all_target_fields: Set[str]
    source_to_value_mappings: Dict[str, List[ScenarioMappingConfiguration]]
    target_fields_to_ignore_in_compare: Set[str]


# ============================================================================
# Field Extractor
# ============================================================================

def _sanitize_alias(alias: str) -> str:
    """Converts a raw string into a valid Python variable name.

    Converts names like "User ID" or "1st_Name" to "user_id" and "field_1st_name".

    Args:
        alias: The raw string to sanitize.

    Returns:
        A snake_case string safe for use as a class attribute.
    """
    pythonic_name = re.sub(r"\W|^(?=\d)", "_", alias)
    pythonic_name = re.sub(r"_+", "_", pythonic_name).strip("_").lower()
    if pythonic_name[0].isdigit():
        pythonic_name = f"field_{pythonic_name}"
    return pythonic_name


class _FieldPropExtractor:
    """Extracts field properties from SourceOrTargetField objects.

    Consolidates all extraction logic for different field types (CUSTOM, LIBRARY, CONFIGURATION).
    The API stores field metadata in different places depending on the field type, and this class
    provides a unified interface to extract that metadata.

    Example:
        >>> extractor = _FieldPropExtractor(source_field)
        >>> names = extractor.get_names()
        >>> uuid = extractor.get_uuid('employee_id')
        >>> label, label_en, label_nl = extractor.get_label('employee_id')
    """

    def __init__(self, fields: SourceOrTargetField):
        """Initialize the extractor with a SourceOrTargetField object.

        Args:
            fields: The SourceOrTargetField object to extract from.
        """
        self.fields = fields
        self._field_type = fields.type if hasattr(fields, 'type') else None

    @property
    def is_custom(self) -> bool:
        """Check if the field is a CUSTOM field."""
        return isinstance(self.fields, CustomSourceOrTargetField)

    @property
    def is_library(self) -> bool:
        """Check if the field is a LIBRARY field."""
        return isinstance(self.fields, LibrarySourceOrTargetField)

    @property
    def is_configuration(self) -> bool:
        """Check if the field is a CONFIGURATION field."""
        return isinstance(self.fields, ConfigurationSourceOrTargetField)

    @property
    def field_type_str(self) -> str:
        """Return the field type as a string."""
        if hasattr(self._field_type, 'value'):
            return self._field_type.value
        return str(self._field_type) if self._field_type else ""

    def get_names(self) -> List[str]:
        """Extract a list of field names, preserving order.

        The API stores names in different places by field type:
        - CUSTOM: technical_name
        - LIBRARY: field
        - CONFIGURATION: uuid

        Returns:
            List of field names in API order. Empty list for FIXED/EMPTY fields.
        """
        if self.is_custom:
            names: List[str] = []
            seen = set()
            for item in self.fields.data:
                if item.technical_name not in seen:
                    names.append(item.technical_name)
                    seen.add(item.technical_name)
            return names

        if self.is_library:
            names: List[str] = []
            seen = set()
            for entry in self.fields.data:
                if entry.field not in seen:
                    names.append(entry.field)
                    seen.add(entry.field)
            return names

        if self.is_configuration:
            names: List[str] = []
            seen = set()
            for config_item in self.fields.data:
                uuid_str = str(config_item.uuid)
                if uuid_str not in seen:
                    names.append(uuid_str)
                    seen.add(uuid_str)
            return names

        return []

    def get_label(self, field_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract human-readable labels for a field.

        CUSTOM fields use 'name' directly; LIBRARY fields have multi-language 'field_label'.

        Args:
            field_name: The field name to look up.

        Returns:
            Tuple of (Preferred Label, English Label, Dutch Label).
        """
        if self.is_custom:
            for item in self.fields.data:
                if item.technical_name == field_name:
                    return (item.name, None, None)

        if self.is_library:
            for entry in self.fields.data:
                if entry.field == field_name and entry.field_label:
                    l_en = entry.field_label.get("en")
                    return (l_en or next(iter(entry.field_label.values()), None), l_en, entry.field_label.get("nl"))

        return (None, None, None)

    def get_uuid(self, field_name: str) -> Optional[str]:
        """Extract UUID for a field.

        The API's mappingValues reference fields by UUID.

        Args:
            field_name: The field name to look up.

        Returns:
            UUID string if found, None otherwise.
        """
        if self.is_custom:
            for item in self.fields.data:
                if item.technical_name == field_name:
                    return item.uuid

        if self.is_library:
            for entry in self.fields.data:
                if entry.field == field_name:
                    return entry.uuid

        return None

    def get_schema(self, field_name: str) -> Optional[str]:
        """Extract schema name identifying the source system or category.

        Args:
            field_name: The field name to look up.

        Returns:
            Schema name string if found, None otherwise.
            - For CUSTOM fields: returns CustomDataValues.source
            - For LIBRARY fields: returns category.technicalName
        """
        if self.is_custom:
            for item in self.fields.data:
                if item.technical_name == field_name:
                    return item.source

        if self.is_library:
            for entry in self.fields.data:
                if entry.field == field_name:
                    return entry.category.get("technicalName") if entry.category else None

        return None

    def get_technical_name(self, field_name: str) -> Optional[str]:
        """Extract technical_name for a field.

        Technical names are system-specific identifiers. Only CUSTOM fields have them.

        Args:
            field_name: The field name to look up.

        Returns:
            Technical name string if found, None otherwise.
        """
        if self.is_custom:
            for item in self.fields.data:
                if item.technical_name == field_name:
                    return item.technical_name
        return None

    def get_description(self, field_name: str) -> Optional[str]:
        """Extract description for a field.

        Only CUSTOM fields have descriptions.

        Args:
            field_name: The field name to look up.

        Returns:
            Description string for CUSTOM fields, None otherwise.
        """
        if self.is_custom:
            for item in self.fields.data:
                if item.technical_name == field_name:
                    return item.description
        return None

    def get_config_props(self, field_name: str) -> Dict[str, Any]:
        """Extract configuration field properties (question, type, value).

        Args:
            field_name: The field name to look up (UUID for CONFIGURATION fields).

        Returns:
            Dictionary with config properties: question_obj, config_type, config_value.
            Returns dict with None values if not a CONFIGURATION field.
        """
        if self.is_configuration:
            for config_item in self.fields.data:
                if str(config_item.uuid) == field_name:
                    question_dict = config_item.question
                    question_en = question_dict.get("en")
                    question_nl = question_dict.get("nl")
                    question_obj = Question(en=question_en, nl=question_nl) if (question_en or question_nl) else None

                    return {
                        "question_obj": question_obj,
                        "config_type": config_item.type.value,
                        "config_value": config_item.value,
                    }

        return {
            "question": None,
            "config_type": None,
            "config_value": None,
        }

    def get_all_properties(self, field_name: str) -> Dict[str, Any]:
        """Extract all properties for a field in one call.

        Args:
            field_name: The field name to look up.

        Returns:
            Dictionary with all field properties.
        """
        label, label_en, label_nl = self.get_label(field_name)
        config_props = self.get_config_props(field_name)

        return {
            "label": label,
            "label_en": label_en,
            "label_nl": label_nl,
            "uuid": self.get_uuid(field_name),
            "schema_name": self.get_schema(field_name),
            "technical_name": self.get_technical_name(field_name),
            "description": self.get_description(field_name),
            **config_props
        }


def _parse_config_value(config_item: ConfigFieldValues) -> Optional[str]:
    """Convert a ConfigFieldValues object into a normalized string representation."""
    cfg_type = config_item.type.value
    value = config_item.value

    # Attachment: explicitly suppressed
    if cfg_type == ConfigurationType.ATTACHMENT.value:
        return None

    # Selection: extract English labels if the payload is a list of dicts
    if cfg_type == ConfigurationType.SELECTION.value:
        if isinstance(value, list):
            labels = [v.get("en", "") for v in value if isinstance(v, dict) and "en" in v]
            return ", ".join(labels) if labels else str(value)
        return str(value)

    # Datepicker: normalize single or range
    if cfg_type == ConfigurationType.DATEPICKER.value:
        def fmt(dt):
            return dt.isoformat() if isinstance(dt, (datetime, AwareDatetime)) else str(dt)

        if isinstance(value, list):
            parts = [fmt(v) for v in value]
            return " - ".join(parts) if parts else None
        return fmt(value) if value is not None else None

    # Simple scalar types: TEXT, EMAIL, NUMBER, RICHTEXT
    if cfg_type in {
        ConfigurationType.TEXT.value,
        ConfigurationType.EMAIL.value,
        ConfigurationType.NUMBER.value,
        ConfigurationType.RICHTEXT.value,
    }:
        return str(value) if value is not None else None

    # Fallback
    return str(value) if value is not None else None


# ============================================================================
# UUID to Field Name Conversion
# ============================================================================

@dataclass
class _UuidToFieldNameConverter:
    """Bundles all data needed to convert value mapping keys from UUIDs/schema patterns to field names.

    The API returns value mappings where BOTH input and output dictionaries use field identifier
    keys (UUIDs like "ea06ce9f-e10e-484e-bdf0-ec58087f15c5" or schema.name patterns like "work_schema-title").
    We MUST convert these identifier keys to readable field names (like {"title": "CEO"}) because
    the rest of the code expects field names, not UUIDs or schema patterns. This dataclass groups
    all the lookup data needed for that conversion, avoiding passing 5+ separate arguments.

    Created in _ScenarioParser.parse() and passed to _UuidToFieldNameMapper.__init__().

    Attributes:
        uuid_keyed_value_mappings: The value mappings that currently use field identifier keys (UUIDs/schema patterns)
            and need conversion to field names. Both input and output dictionaries have identifier keys.
        source_names: List of source field names (used to resolve UUIDs and validate keys), preserving API order.
        target_names: List of target field names (used to resolve UUIDs and validate keys), preserving API order.
        props: Dictionary mapping field names to FieldProperties (contains UUID-to-name lookups).
        detail_model: The scenario detail model with source/target field definitions.
    """
    uuid_keyed_value_mappings: Optional[ScenarioMappingConfiguration]
    source_names: List[str]
    target_names: List[str]
    props: FieldPropertiesMap
    detail_model: ScenarioDetail


class _UuidToFieldNameMapper:
    """Converts value mapping keys from UUIDs/schema patterns to readable field names.

    The API returns value mappings where BOTH input and output dictionaries use field identifier
    keys (UUIDs like "ea06ce9f-e10e-484e-bdf0-ec58087f15c5" or schema.name patterns like "work_schema-title").
    This class converts those identifier keys to field names (like {"title": "CEO"}) because
    the rest of the codebase expects field names, not UUIDs or schema patterns. Uses multiple
    lookup strategies to handle API inconsistencies.
    """

    def __init__(self, uuid_converter: _UuidToFieldNameConverter):
        """Initialize the converter with all data needed to convert UUID/schema pattern keys to field names.

        Args:
            uuid_converter: Contains UUID-keyed value mappings, field names, properties, and detail model.
                Created in _ScenarioParser.parse() and provides all lookup data needed to convert
                field identifier keys (UUIDs like "ea06ce9f..." or schema patterns like "work_schema-title")
                to readable field names (like "title"). Used to convert keys in BOTH input and output dictionaries.
        """
        # Store all data needed to convert UUID/schema pattern keys in value mappings to field names
        self.uuid_converter = uuid_converter
        self.source_uuid_to_field: Dict[str, str] = {}
        self.target_uuid_to_field: Dict[str, str] = {}
        self.source_technical_to_pythonic: Dict[str, str] = {}
        self.target_technical_to_pythonic: Dict[str, str] = {}
        self._build_mappings()

    def _build_mappings(self) -> None:
        """Builds the lookup dictionaries needed for translation.

        Strategies:
        1. Technical Names -> Python Aliases (for CUSTOM fields).
        2. UUIDs -> Python Aliases (for all fields using props as source of truth).
        """
        # Strategy 1: Map Technical Names -> Python Aliases
        self._map_technical_names(
            model=self.uuid_converter.detail_model.source,
            names=self.uuid_converter.source_names,
            mapping=self.source_technical_to_pythonic,
            system_type=SystemType.SOURCE
        )
        self._map_technical_names(
            model=self.uuid_converter.detail_model.target,
            names=self.uuid_converter.target_names,
            mapping=self.target_technical_to_pythonic,
            system_type=SystemType.TARGET
        )

        # Strategy 2: Map UUIDs -> Python Aliases
        self._map_uuids(
            names=self.uuid_converter.source_names,
            tech_map=self.source_technical_to_pythonic,
            uuid_map=self.source_uuid_to_field
        )
        self._map_uuids(
            names=self.uuid_converter.target_names,
            tech_map=self.target_technical_to_pythonic,
            uuid_map=self.target_uuid_to_field
        )

    def _map_technical_names(
        self,
        model: SourceOrTargetField,
        names: List[str],
        mapping: Dict[str, str],
        system_type: SystemType
    ) -> None:
        """Maps technical names to python aliases for custom fields."""
        if not isinstance(model, CustomSourceOrTargetField):
            return

        names_set = set(names)  # Convert to set for fast lookup
        for item in model.data:
            if item.technical_name not in names_set:
                continue

            # Find matching pythonic name in props via UUID
            for py_name, props in self.uuid_converter.props.items():
                if props.system_type == system_type.value and props.uuid == item.uuid:
                    mapping[item.technical_name] = py_name
                    break

    def _map_uuids(
        self,
        names: List[str],
        tech_map: Dict[str, str],
        uuid_map: Dict[str, str]
    ) -> None:
        """Maps UUIDs to python aliases using props."""
        for name in names:
            py_name = tech_map.get(name, name)
            props = self.uuid_converter.props.get(py_name)
            if props:
                uuid_map[props.uuid] = py_name

    def convert_key(self, key: str, direction: str) -> str:
        """Converts a single API mapping key to a pythonic field name.

        This helper method handles API inconsistency by trying multiple fallback strategies:
        1. UUID lookup (most reliable - direct match)
        2. Name lookup (handles technical names and pythonic names)
        3. Pattern matching (handles schema.name or schema-name patterns)

        Uses internal lookup maps (`source_uuid_to_field`, etc.) populated during initialization.

        Example:
            >>> mapper.convert_key('be3a4c1e...', 'source')
            'gender'

        Args:
            key: The raw key from the API (could be UUID, Name, or Schema.Name).
            direction: 'source' or 'target'.

        Returns:
            The best matching Pythonic field name.
        """
        if direction == "source":
            uuid_map = self.source_uuid_to_field
            tech_map = self.source_technical_to_pythonic
            valid_names = self.uuid_converter.source_names
        else:
            uuid_map = self.target_uuid_to_field
            tech_map = self.target_technical_to_pythonic
            valid_names = self.uuid_converter.target_names

        # Strategy 1: Direct UUID Lookup (Most reliable)
        if key in uuid_map:
            return uuid_map[key]

        # Strategy 2: Direct Name Lookup
        if key in valid_names:
            return tech_map.get(key, key)
        if key in tech_map.values():
            return key

        # Strategy 3: Pattern Matching (Heuristic)
        # Handles keys like 'schema_name.email' by checking suffixes
        all_names = set(tech_map.values()) | set(valid_names)
        for fname in all_names:
            if key.endswith(f'.{fname}') or key.endswith(f'-{fname}'):
                return tech_map.get(fname, fname)

        # Fallback: Return original key
        return key

    def convert_mapping_config(self) -> Optional[ScenarioMappingConfiguration]:
        """Converts value mapping keys from field identifiers to field names.

        The API returns value mappings where BOTH input and output dictionaries use field identifier
        keys (UUIDs like "ea06ce9f-e10e-484e-bdf0-ec58087f15c5" or schema.name patterns like "work_schema-title").
        This method converts all identifier keys to readable field names (like {"title": "CEO"})
        because the rest of the codebase expects field names, not UUIDs or schema patterns.

        Example:
            >>> converted = mapper.convert_mapping_config()
            >>> converted.values[0].input
            {'title': 'CEO'}  # Field identifier key converted to field name
            >>> converted.values[0].output
            {'job_code': '96'}  # UUID key converted to field name

        Returns:
            ScenarioMappingConfiguration with field name keys (not UUIDs or schema patterns),
            or None if no mapping config exists.
        """
        if not self.uuid_converter.uuid_keyed_value_mappings or not self.uuid_converter.uuid_keyed_value_mappings.values:
            return self.uuid_converter.uuid_keyed_value_mappings

        # Convert UUID/schema pattern keys to field names in each value mapping
        converted_values = []
        for val in self.uuid_converter.uuid_keyed_value_mappings.values:
            # Convert source field identifier keys (UUIDs/schema patterns) to field names
            new_in = {
                self.convert_key(key=k, direction="source"): v
                for k, v in val.input.items()
            }
            # Convert target field identifier keys (UUIDs/schema patterns) to field names
            new_out = {
                self.convert_key(key=k, direction="target"): v
                for k, v in val.output.items()
            }
            converted_values.append(MappingValue(input=new_in, output=new_out))

        return ScenarioMappingConfiguration(
            values=converted_values,
            default_value=self.uuid_converter.uuid_keyed_value_mappings.default_value
        )


# ============================================================================
# Scenario Parser
# ============================================================================

class _ScenarioParser:
    """Orchestrates the parsing of a validated ScenarioSchema.

    This class breaks the logic into three distinct phases:
    1. Extraction: Get raw names from the polymorphic API response.
    2. Property Building: Create metadata objects (`FieldProperties`) for every field.
    3. Linking: Create `Record` objects that link Sources to Targets.
    """

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse(self, scenario: ScenarioSchema, language: str = 'en') -> ParsedScenarioData:
        """Parse a validated ScenarioSchema into data for constructing a Scenario.

        Args:
            scenario: Validated ScenarioSchema object from the BrynQ API
            language: Default language code ('en' or 'nl') for label and question access.
                     Defaults to 'en'. This sets the default language for all Label and Question
                     objects in FieldProperties.

        Returns:
            ParsedScenarioData dict with all parsed data for Scenario construction
        """
        # Accumulators
        props: FieldPropertiesMap = {}
        value_mappings = defaultdict(list)
        aliases = set()
        alias_order = []
        records = []

        # details is the 'raw' api name for what is essentially called 'records' here.
        # No need to validate - scenario.details are already ScenarioDetail objects
        for detail_model in scenario.details:

            # Phase 1: extract names using _FieldPropExtractor
            source_extractor = _FieldPropExtractor(detail_model.source)
            target_extractor = _FieldPropExtractor(detail_model.target)
            source_names = source_extractor.get_names()
            target_names = target_extractor.get_names()

            # Phase 2: Property Building
            # Identify reserved keys from target (Library fields) to avoid collisions with Source Custom fields
            reserved_keys = set()
            if detail_model.target.type == FieldType.LIBRARY.value:
                reserved_keys = set(target_names)  # Convert list to set for fast lookup

            # Extract base properties from ScenarioDetail via model_dump()
            base_props = FieldProperties(
                **detail_model.model_dump(include={'logic', 'unique', 'required'}),
                mapping={}  # Mappings are stored at Record level, not Field level
            )
            self._build_field_properties(
                fields=detail_model.source,
                names=source_names,
                sys_type=SystemType.SOURCE,
                base=base_props,
                props=props,
                aliases=aliases,
                alias_order=alias_order,
                reserved=reserved_keys,
                language=language
            )
            self._build_field_properties(
                fields=detail_model.target,
                names=target_names,
                sys_type=SystemType.TARGET,
                base=base_props,
                props=props,
                aliases=aliases,
                alias_order=alias_order,
                language=language
            )

            # Phase 3: Linking & Mapping Conversion
            # Convert value mapping keys from UUIDs/schema patterns to field names (API uses UUIDs/schema patterns, code expects field names)
            uuid_converter = _UuidToFieldNameConverter(
                uuid_keyed_value_mappings=detail_model.mapping,
                source_names=source_names,
                target_names=target_names,
                props=props,
                detail_model=detail_model
            )
            converted_map = _UuidToFieldNameMapper(uuid_converter).convert_mapping_config()

            if converted_map:
                # If values exist, store them in the lookup map
                if converted_map.values:
                    # Preserve order from API, but sort for consistent key generation
                    key = '|'.join(sorted(source_names)) if source_names else detail_model.id
                    value_mappings[key].append(converted_map)
                # If map exists but is empty, treat as False
                else:
                    converted_map = False

            records.append(
                self._build_record(
                    detail=detail_model,
                    source_names=source_names,
                    target_names=target_names,
                    base=base_props,
                    props=props,
                    mapping_cfg=converted_map
                )
            )

        # Phase 4: Build source_to_target and target_to_source maps using resolved keys from records
        # This ensures collision-renamed fields (e.g., 'email' -> 'email_target') are properly mapped
        source_to_target: Dict[str, Set[str]] = defaultdict(set)
        target_to_source: Dict[str, Set[str]] = defaultdict(set)
        for record in records:
            source_keys = record.source.field_names
            target_keys = record.target.field_names
            for source_key in source_keys:
                source_to_target[source_key].update(target_keys)
            for target_key in target_keys:
                target_to_source[target_key].update(source_keys)

        # Final Phase: Assembly
        return self._build_parsed_scenario(
            schema=scenario,
            records=records,
            source_to_target_map=source_to_target,
            target_to_source_map=target_to_source,
            props=props,
            source_to_value_mappings=value_mappings
        )

    def _build_field_properties(
        self,
        fields: SourceOrTargetField,
        names: List[str],
        sys_type: SystemType,
        base: "FieldProperties",
        props: FieldPropertiesMap,
        aliases: Set[str],
        alias_order: List[str],
        reserved: Optional[Set[str]] = None,
        language: str = 'en'
    ) -> None:
        """Creates FieldProperties for a set of fields and registers them.

        Args:
            fields:      SourceOrTargetField object containing field definitions
            names:       Set of field names to process
            sys_type:    Either SystemType.SOURCE or SystemType.TARGET
            base:        Base FieldProperties shared across fields in this mapping
            props:       Dictionary to store field properties (modified in place)
            aliases:     Set to track custom field aliases (modified in place)
            alias_order: List to maintain custom alias order (modified in place)
            reserved:    Set of reserved keys to avoid collisions (e.g. target library names)
            language:    Default language code ('en' or 'nl') for label and question access
        """
        extractor = _FieldPropExtractor(fields)

        for name in names:
            label, l_en, l_nl = extractor.get_label(name)
            # Create Label object: use l_en/l_nl if available, otherwise use label as en
            if l_en or l_nl:
                label_obj = Label(en=l_en, nl=l_nl)
            elif label:
                label_obj = Label(en=label)
            else:
                label_obj = None

            # Set default language on Label object
            if label_obj:
                label_obj.set_default_language(language)

            # Determine Python Alias
            is_custom = extractor.is_custom

            # Custom fields: sanitize label; Library/Config fields: use name directly
            alias = _sanitize_alias(label) if is_custom else name
            key = alias if is_custom else name

            # Handle collisions for Custom fields if key is reserved (e.g. used by Target Library field)
            if is_custom and reserved and key in reserved:
                alias = f"{alias}_{sys_type.value}"
                key = alias

            # Handle collisions when same field name exists in both source and target
            # Target gets priority - source fields get renamed to `name_source`
            if sys_type == SystemType.SOURCE:
                if key in props and props[key].system_type == SystemType.TARGET.value:
                    key = f"{key}_source"
                elif f"{key}_source" in props:
                    key = f"{key}_source"
            else:
                if key in props and props[key].system_type == SystemType.SOURCE.value:
                    source_key = f"{key}_source"
                    if source_key not in props:
                        existing_source_prop = props.pop(key)
                        props[source_key] = existing_source_prop

            config_props = extractor.get_config_props(name)

            # Set default language on Question object if present
            if config_props.get('question_obj'):
                config_props['question_obj'].set_default_language(language)

            # Merge unique/required with existing entry if it exists (OR logic)
            existing_unique = props[key].unique if key in props else False
            existing_required = props[key].required if key in props else False

            props[key] = base.model_copy(update={
                "system_type": sys_type.value,
                "field_type": extractor.field_type_str,
                "alias": alias,
                "uuid": extractor.get_uuid(name),
                "schema_name": extractor.get_schema(name),
                "technical_name": extractor.get_technical_name(name),
                "label_obj": label_obj,
                "description": extractor.get_description(name),
                "mapping": {},  # Mappings are stored at Record level, not Field level
                "unique": base.unique or existing_unique,  # OR: if ANY record is unique
                "required": base.required or existing_required,  # OR: if ANY record is required
                # config fields
                **config_props
            })

            if is_custom and key not in aliases:
                aliases.add(key)
                alias_order.append(key)

    def _build_record(
        self,
        detail: ScenarioDetail,
        source_names: List[str],
        target_names: List[str],
        base: "FieldProperties",
        props: FieldPropertiesMap,
        mapping_cfg
    ) -> "Record":
        """Creates a Record object representing the relationship.

        Args:
            detail: Validated ScenarioDetail object
            source_names: List of source field names (preserving API order)
            target_names: List of target field names (preserving API order)
            base: Base FieldProperties for this mapping
            props: Dictionary of field properties
            mapping_cfg: Converted mapping configuration

        Returns:
            Record object representing this mapping
        """

        # Helper to retrieve field aliases (original names) for field_names lists
        # Also returns internal keys for props lookup
        def _get_aliases_and_internal_keys(names, field_obj, sys_type: SystemType):
            extractor = _FieldPropExtractor(field_obj)
            aliases = []
            internal_keys = []
            for n in names:
                if extractor.is_custom:
                    # For custom fields, find by UUID (unique identifier)
                    uuid = extractor.get_uuid(n)
                    for key, prop in props.items():
                        if prop.system_type == sys_type.value and prop.uuid == uuid:
                            aliases.append(prop.alias)
                            internal_keys.append(key)
                            break
                else:
                    # For library/configuration fields, check if name was renamed due to collision
                    # Target gets priority: SOURCE fields are renamed to `name_source`
                    if sys_type == SystemType.SOURCE:
                        # SOURCE: check original name first, then `name_source`
                        if n in props and props[n].system_type == SystemType.SOURCE.value:
                            aliases.append(props[n].alias)
                            internal_keys.append(n)
                        elif f"{n}_source" in props:
                            internal_key = f"{n}_source"
                            aliases.append(props[internal_key].alias)
                            internal_keys.append(internal_key)
                        else:
                            # name might not be in props (e.g., FIXED/EMPTY types)
                            aliases.append(n)
                            internal_keys.append(n)
                    else:
                        # TARGET: check original name (TARGET has priority, keeps original key)
                        if n in props and props[n].system_type == SystemType.TARGET.value:
                            aliases.append(props[n].alias)
                            internal_keys.append(n)
                        else:
                            aliases.append(n)
                            internal_keys.append(n)
            return aliases, internal_keys

        source_aliases, source_internal_keys = _get_aliases_and_internal_keys(source_names, detail.source, SystemType.SOURCE)
        target_aliases, target_internal_keys = _get_aliases_and_internal_keys(target_names, detail.target, SystemType.TARGET)

        # Determine Cardinality
        rel = RelationType.ONE_TO_ONE.value
        if len(source_names) > 1 and len(target_names) > 1:
            rel = RelationType.MANY_TO_MANY.value
        elif len(source_names) > 1:
            rel = RelationType.MANY_TO_ONE.value
        elif len(target_names) > 1:
            rel = RelationType.ONE_TO_MANY.value

        # Extract fixed_source_value based on source type
        fixed_source_value = None
        if detail.source.type == "FIXED":
            # For FIXED type, use the data directly (it's a string)
            fixed_source_value = detail.source.data
        elif detail.source.type == "EMPTY":
            # For EMPTY type, use empty string
            fixed_source_value = ''
        elif detail.source.type == "CONFIGURATION":
            # For CONFIGURATION type, parse the config value according to its type
            if isinstance(detail.source, ConfigurationSourceOrTargetField) and detail.source.data:
                # Get the first config item (for one_to_one/one_to_many, there's typically one)
                config_item = detail.source.data[0]
                fixed_source_value = _parse_config_value(config_item)

        # Build FieldProperties lists using internal keys for props lookup
        source_field_props = [props[k] for k in source_internal_keys if k in props]
        target_field_props = [props[k] for k in target_internal_keys if k in props]

        # Build SourceTargetFields instances
        # Use aliases (original names) for field_names and related lists
        # Use internal_keys for props lookup
        source_unique_key_fields = [props[k].alias for k in source_internal_keys if k in props and props[k].unique]
        source_required_fields = [props[k].alias for k in source_internal_keys if k in props and props[k].required]
        source_custom_fields = [props[k].alias for k in source_internal_keys if k in props and props[k].field_type == FieldType.CUSTOM.value]
        source_library_fields = [props[k].alias for k in source_internal_keys if k in props and props[k].field_type == FieldType.LIBRARY.value]
        source_fields_with_logic = [props[k].alias for k in source_internal_keys if k in props and props[k].logic is not None]

        target_unique_key_fields = [props[k].alias for k in target_internal_keys if k in props and props[k].unique]
        target_required_fields = [props[k].alias for k in target_internal_keys if k in props and props[k].required]
        target_custom_fields = [props[k].alias for k in target_internal_keys if k in props and props[k].field_type == FieldType.CUSTOM.value]
        target_library_fields = [props[k].alias for k in target_internal_keys if k in props and props[k].field_type == FieldType.LIBRARY.value]
        target_fields_with_logic = [props[k].alias for k in target_internal_keys if k in props and props[k].logic is not None]

        source_stf = SourceTargetFields(
            type="source",
            field_names=source_aliases,  # Use aliases (original names)
            unique_key_fields=source_unique_key_fields,
            required_fields=source_required_fields,
            field_properties=source_field_props,
            custom_fields=source_custom_fields,
            library_fields=source_library_fields,
            fields_with_logic=source_fields_with_logic
        )

        target_stf = SourceTargetFields(
            type="target",
            field_names=target_aliases,  # Use aliases (original names)
            unique_key_fields=target_unique_key_fields,
            required_fields=target_required_fields,
            field_properties=target_field_props,
            custom_fields=target_custom_fields,
            library_fields=target_library_fields,
            fields_with_logic=target_fields_with_logic
        )

        # Check if source has EMPTY type
        has_empty_source = detail.source.type == "EMPTY"

        # Use ScenarioDetail fields directly via model_dump()
        return Record(
            **detail.model_dump(include={'id', 'logic', 'unique', 'required'}),
            source_field_types={alias: detail.source.type for alias in source_aliases},
            target_field_types={alias: detail.target.type for alias in target_aliases},
            source=source_stf,
            target=target_stf,
            relation_type=rel,
            mapping=mapping_cfg,
            fixed_source_value=fixed_source_value,
            has_empty_source=has_empty_source
        )

    def _build_parsed_scenario(
        self,
        schema: ScenarioSchema,
        records,
        source_to_target_map,
        target_to_source_map,
        props,
        source_to_value_mappings
    ) -> ParsedScenarioData:
        """Constructs the parsed scenario data dict.

        Args:
            schema: Validated ScenarioSchema object
            records: List of Record objects
            source_to_target_map: Source to target mapping dictionary
            target_to_source_map: Target to source mapping dictionary
            props: Field properties dictionary
            source_to_value_mappings: Source field to value mappings dictionary

        Returns:
            ParsedScenarioData dict for Scenario construction
        """
        s_to_t = {k: sorted(v) for k, v in source_to_target_map.items()}
        t_to_s = {k: sorted(v) for k, v in target_to_source_map.items()}

        # Only include custom fields that are source fields (based on system_type)
        custom_fields = {k: v for k, v in props.items()
                        if v.field_type == FieldType.CUSTOM.value
                        and v.system_type == SystemType.SOURCE.value}

        # Build unique and required fields (all fields, regardless of source/target)
        unique_key_fields = [fid for fid, props_item in props.items() if props_item.unique]
        required_fields = [fid for fid, props_item in props.items() if props_item.required]

        # Build source and target unique/required fields separately
        # Use v.alias (original name) not k (internal key that might have suffix)
        source_field_names = [v.alias for k, v in props.items() if v.system_type == SystemType.SOURCE.value]
        source_unique_key_fields = [v.alias for k, v in props.items() if v.unique and v.system_type == SystemType.SOURCE.value]
        source_required_fields = [v.alias for k, v in props.items() if v.required and v.system_type == SystemType.SOURCE.value]
        source_field_properties = [v for k, v in props.items() if v.system_type == SystemType.SOURCE.value]
        source_custom_fields = [v.alias for k, v in props.items() if v.system_type == SystemType.SOURCE.value and v.field_type == FieldType.CUSTOM.value]
        source_library_fields = [v.alias for k, v in props.items() if v.system_type == SystemType.SOURCE.value and v.field_type == FieldType.LIBRARY.value]
        source_fields_with_logic = [v.alias for k, v in props.items() if v.system_type == SystemType.SOURCE.value and v.logic is not None]

        target_field_names = [v.alias for k, v in props.items() if v.system_type == SystemType.TARGET.value]
        target_unique_key_fields = [v.alias for k, v in props.items() if v.unique and v.system_type == SystemType.TARGET.value]
        target_required_fields = [v.alias for k, v in props.items() if v.required and v.system_type == SystemType.TARGET.value]
        target_field_properties = [v for k, v in props.items() if v.system_type == SystemType.TARGET.value]
        target_custom_fields = [v.alias for k, v in props.items() if v.system_type == SystemType.TARGET.value and v.field_type == FieldType.CUSTOM.value]
        target_library_fields = [v.alias for k, v in props.items() if v.system_type == SystemType.TARGET.value and v.field_type == FieldType.LIBRARY.value]
        target_fields_with_logic = [v.alias for k, v in props.items() if v.system_type == SystemType.TARGET.value and v.logic is not None]

        # Build nested structures
        source = SourceTargetFields(
            type="source",
            field_names=source_field_names,
            unique_key_fields=source_unique_key_fields,
            required_fields=source_required_fields,
            field_properties=source_field_properties,
            custom_fields=source_custom_fields,
            library_fields=source_library_fields,
            fields_with_logic=source_fields_with_logic
        )
        target = SourceTargetFields(
            type="target",
            field_names=target_field_names,
            unique_key_fields=target_unique_key_fields,
            required_fields=target_required_fields,
            field_properties=target_field_properties,
            custom_fields=target_custom_fields,
            library_fields=target_library_fields,
            fields_with_logic=target_fields_with_logic
        )

        all_source_fields = set(source_to_target_map.keys())
        all_target_fields = set(target_to_source_map.keys())

        # Collect target fields from records where logic contains 'ignoreCompare'
        target_fields_to_ignore_in_compare = set()
        for record in records:
            if record.logic and 'ignoreCompare' in record.logic:
                target_fields_to_ignore_in_compare.update(record.target.field_names)

        # Return parsed data for Scenario.from_schema() to construct the Scenario
        return {
            "records": records,
            "source_to_target_map": s_to_t,
            "target_to_source_map": t_to_s,
            "field_properties": props,
            "source": source,
            "target": target,
            "unique_key_fields": unique_key_fields,
            "required_fields": required_fields,
            "custom_fields": custom_fields,
            "all_source_fields": all_source_fields,
            "all_target_fields": all_target_fields,
            "source_to_value_mappings": dict(source_to_value_mappings),
            "target_fields_to_ignore_in_compare": target_fields_to_ignore_in_compare
        }


# ============================================================================
# Dummy Record for Logging
# ============================================================================

class _DummyRecord:
    """Dummy record for logging unmapped sources that don't belong to any record.

    Used internally by Scenarios.rename_fields to track source columns present in
    the DataFrame but not mapped by the scenario.
    """
    def __init__(self):
        """Initialize a dummy record with empty attributes."""
        self.id = None
        self.logic = None
        self.relation_type = None
        self.source = SourceTargetFields(
            type="source",
            field_names=[],
            unique_key_fields=[],
            required_fields=[],
            field_properties=[],
            custom_fields=[],
            library_fields=[],
            fields_with_logic=[]
        )
        self.target = SourceTargetFields(
            type="target",
            field_names=[],
            unique_key_fields=[],
            required_fields=[],
            field_properties=[],
            custom_fields=[],
            library_fields=[],
            fields_with_logic=[]
        )
