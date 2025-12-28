"""
Scenarios SDK for BrynQ.

This module provides the `Scenarios` class for fetching, parsing, and applying
data transformation scenarios from the BrynQ API.
"""
# imports
from __future__ import annotations

from functools import cached_property
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Literal

import pandas as pd
from pydantic import ConfigDict, Field

from .schemas.scenarios import (
    Scenario as ScenarioSchema,
    ScenarioMappingConfiguration,
    Scenarios as ScenariosSchema,
)

# Import parsed models from schemas/scenarios_parsed.py
from .schemas.scenarios_parsed import (
    FieldProperties,
    SourceTargetFields,
    Record,
)

# Import internal helpers
from ._scenario_parser import (
    FieldPropertiesMap,
    SourceToTargetMap,
    TargetToSourceMap,
    _ScenarioParser,
)

# Import private helper base class
from ._scenario_transformer import _ScenarioTransformationEngine


class Scenario(_ScenarioTransformationEngine):
    """Representation of a Scenario from the BrynQ API.

    This is the main class users interact with. It provides public methods to transform
    DataFrames according to the scenario's field mappings and value transformations.
    It also exposes all records, fields, and their properties for fine-grained access and inspection.

    Example:
        >>> scenario.name
        'Personal Information'

        >>> scenario.source.field_names
        ['first_name', 'last_name', 'email']

        >>> for record in scenario.records:
        ...     print(record.relation_type)
        one_to_one

    Inherited from ScenarioSchema:
        id: Scenario identifier
        name: Scenario display name
        description: Scenario business context
        details: Raw ScenarioDetail objects from API (list of field-level mappings) (will be parsed into 'Records')

    Enriched attributes:
        records: List of Record objects (transformed from details)
        records_count: Number of records (computed from len(details))
        source_to_target_map: Dictionary mapping source field names to target field names
        target_to_source_map: Dictionary mapping target field names to source field names
        field_properties: Dictionary mapping field names to FieldProperties objects
        all_source_fields: Set of all source field names
        all_target_fields: Set of all target field names
        source: SourceTargetFields object containing source unique_key_fields and required_fields
        target: SourceTargetFields object containing target unique_key_fields and required_fields
        unique_key_fields: List of field names that are part of unique constraints (deprecated)
        required_fields: List of field names that are required (deprecated)
        custom_fields: Dictionary of custom field properties (filtered from field_properties)
        custom_fields_model: Dynamically generated Pandera schema model for custom fields
        source_to_value_mappings: Dictionary mapping source fields to value mapping configurations
        target_fields_to_ignore_in_compare: Set of target field names to ignore in compare
    """
    # Override parent's frozen config to allow mutation
    model_config = ConfigDict(frozen=False, strict=False, populate_by_name=True)

    # Missing value representations to detect in dataframes (literal strings, not regex)
    MISSING_VALUES: List[str] = [
        '<NA>', 'nan', 'None', 'NaN', 'null', 'NaT', '_NA_', '', '[]', '{ }'
    ]

    # Mapping Data
    records: List[Record]
    source_to_target_map: SourceToTargetMap
    target_to_source_map: TargetToSourceMap

    # Field Metadata
    field_properties: FieldPropertiesMap
    all_source_fields: Set[str]
    all_target_fields: Set[str]
    source: SourceTargetFields
    target: SourceTargetFields
    unique_key_fields: List[str]
    required_fields: List[str]

    # Custom Field Data
    custom_fields: FieldPropertiesMap
    custom_fields_model: Optional[type] = None

    # Value Mappings
    source_to_value_mappings: Dict[str, List[ScenarioMappingConfiguration]]

    # Compare Configuration
    target_fields_to_ignore_in_compare: Set[str] = Field(default_factory=set)

    @property
    def records_count(self) -> int:
        """Number of records in this scenario."""
        return len(self.records)

    @classmethod
    def from_schema(cls, schema: ScenarioSchema, language: str = 'en') -> "Scenario":
        """Factory method to create a Scenario from a validated ScenarioSchema.

        Args:
            schema: Validated ScenarioSchema object from the BrynQ API
            language: Default language code ('en' or 'nl') for label and question.
        Returns:
            Scenario object with all parsed data
        """
        # Parse the schema into a data dict
        parsed = _ScenarioParser().parse(schema, language=language)

        # Build custom fields model
        custom_model = cls._build_custom_field_model(parsed["custom_fields"]) if parsed["custom_fields"] else None

        # Construct and return the Scenario
        return cls(
            **schema.model_dump(),  # id, name, description, details
            **parsed,
            custom_fields_model=custom_model
        )

    def set_language(self, language: str) -> None:
        """Update the default language for all Label and Question objects in this scenario.

        Args:
            language: Language code ('en' or 'nl').
        """
        # Update scenario-level field properties
        for field_props in self.field_properties.values():
            self._update_field_props_language(field_props, language)

        # Update source and target field properties
        for field_props in self.source.field_properties:
            self._update_field_props_language(field_props, language)
        for field_props in self.target.field_properties:
            self._update_field_props_language(field_props, language)

        # Update field properties in each record
        for record in self.records:
            for field_props in record.source.field_properties:
                self._update_field_props_language(field_props, language)
            for field_props in record.target.field_properties:
                self._update_field_props_language(field_props, language)

    def get_source_fields_with_value_mappings(self) -> List[str]:
        """Returns a list of source fields that have value mappings.

        Example:
            >>> scenario.get_source_fields_with_value_mappings()
            ['gender', 'status']

        Returns:
            List of source field names that have value mappings
        """
        return list(self.source_to_value_mappings.keys())

    def get_target_fields_with_value_mappings(self) -> List[str]:
        """Returns a list of target fields that have value mappings (via their mapped source fields).

        Uses `source_to_value_mappings` and `source_to_target_map` attributes internally.

        Example:
            >>> scenario.get_target_fields_with_value_mappings()
            ['gender_code', 'status_code']

        Returns:
            List of target field names that have value mappings
        """
        target_fields_with_mappings: Set[str] = set()
        for source_key in self.source_to_value_mappings.keys():
            # Handle keys that might be multiple source fields joined with '|'
            source_fields = source_key.split('|') if '|' in source_key else [source_key]
            for source_field in source_fields:
                # Find target fields mapped from this source field
                target_fields = self.source_to_target_map.get(source_field, [])
                target_fields_with_mappings.update(target_fields)
        return sorted(list(target_fields_with_mappings))

    def has_field(self, field_name: str, field_type: Optional[str] = None) -> bool:
        """Check field existence in scenario. Can denote source or target, else looks for both.

        Example:
            >>> scenario.has_field('email')
            True

        Args:
            field_name: The field name to check
            field_type: Optional field type filter ("source" or "target")
        """
        if field_type == "source":
            return field_name in self.all_source_fields
        if field_type == "target":
            return field_name in self.all_target_fields
        return field_name in self.all_source_fields or field_name in self.all_target_fields

    def __iter__(self):
        """Enable iteration over records.

        Example:
            >>> for record in Scenario:
            ...     print(f"Record {record.id}: {len(record.source.field_names)} source fields")
        """
        return iter(self.records)

    def __len__(self) -> int:
        """Return the number of records in this scenario.

        Example:
            >>> len(scenario)
            15

        Returns:
            int: The number of records in the scenario
        """
        return len(self.records)

    def __getitem__(self, field_id: str) -> FieldProperties:
        """Enable dict-style access to field properties.

        Looks up field in both source and target. For unambiguous access,
        use `scenario.source[field_id]` or `scenario.target[field_id]`.

        Example:
            >>> scenario['customer_id']
            FieldProperties(alias='customer_id', uuid='...', label='Customer ID', ...)

        Args:
            field_id: The field name to look up

        Returns:
            FieldProperties object for the field
        """
        in_source = field_id in self.source.field_properties_map
        in_target = field_id in self.target.field_properties_map

        if in_source and in_target:
            raise KeyError(
                f"Field '{field_id}' exists in both source and target. "
                f"Use scenario.source['{field_id}'] or scenario.target['{field_id}'] for explicit access."
            )
        if in_source:
            return self.source[field_id]
        if in_target:
            return self.target[field_id]
        raise KeyError(f"Field '{field_id}' not found in scenario '{self.name}'.")

    def __getattr__(self, name: str) -> FieldProperties:
        """Enable attribute-style access to field properties (e.g., `scenario.customer_id`).

        Looks up field in both source and target. For unambiguous access,
        use `scenario.source.field_name` or `scenario.target.field_name`.
        """
        in_source = name in self.source.field_properties_map
        in_target = name in self.target.field_properties_map

        if in_source and in_target:
            raise AttributeError(
                f"'{name}' exists in both source and target. "
                f"Use scenario.source.{name} or scenario.target.{name} for explicit access."
            )
        if in_source:
            return self.source[name]
        if in_target:
            return self.target[name]
        raise AttributeError(f"'{name}' is not a valid field in scenario '{self.name}'.")

    def __repr__(self) -> str:
        """A human-friendly string representation.

        Example:
            >>> repr(Scenario)
            "<Scenario name='Personal Information' records=5 unique=2 required=3>"

        Returns:
            String representation of the Scenario
        """
        return (
            f"<Scenario "
            f"name='{self.name}' "
            f"records={self.records_count} unique={len(self.unique_key_fields)} "
            f"required={len(self.required_fields)}>"
        )

    def __str__(self) -> str:
        """String representation (used by print()). Delegates to __repr__."""
        return self.__repr__()

    # ============================================================================
    # Public Transformation Methods
    # ============================================================================

    def apply(self, df: pd.DataFrame, drop_unmapped_values: bool = True, value_mapping_strategy: Literal[
            'exactValMap',
            'ignoreCaseValMap',
            'ignoreSpecialValMap',
            'ignoreSpacesValMap',
            'flexValMap'
        ] = 'exactValMap'
    ) -> pd.DataFrame:
        """Applies the scenario to the DataFrame, adding fixed values, mapping field names and mapping values.

        Args:
            df (pd.DataFrame): Input DataFrame to which the scenario will be applied.
            drop_unmapped_values (bool, optional): If True, rows with unmapped values in value mappings will be dropped. Defaults to True.
            value_mapping_strategy (Literal[
                'exactValMap',
                'ignoreCaseValMap',
                'ignoreSpecialValMap',
                'ignoreSpacesValMap',
                'flexValMap'
            ], optional): Strategy for how values are matched during value mapping. Defaults to 'exactValMap'.

        Returns:
            Tuple[pd.DataFrame, dict, dict]:
                - Output DataFrame with the scenario applied and columns filtered to include all scenario target fields (missing columns set to None).
                - Dictionary with statistics or information about any field renaming that occurred.
                - Dictionary with statistics or information about value mapping performed.
        """
        df = self.add_fixed_values(df)
        df, df_stats_map = self.apply_value_mappings(df, drop_unmapped_values, value_mapping_strategy)
        df, df_stats_renamed = self.rename_fields(df)


        all_scenario_target_fields = set(self.target.field_names)
        available_columns = [col for col in df.columns if col in all_scenario_target_fields]
        df = df[available_columns].copy()

        missing_columns = [col for col in all_scenario_target_fields if col not in df.columns]
        for col in missing_columns:
            df[col] = None

        return df, df_stats_renamed, df_stats_map

    def add_fixed_values(
        self,
        df: pd.DataFrame,
        ignore_empty_source: bool = False
    ) -> pd.DataFrame:
        """Adds fixed literal values to DataFrame columns based on scenario mappings.

        Creates new columns with target field names, fills all rows with the fixed value.
        Only processes records with relation_type 'one_to_one' or 'one_to_many'.
        Supports both FIXED and CONFIGURATION source field types.

        Args:
            df (pd.DataFrame): Input DataFrame to add fixed value columns to.
            ignore_empty_source (bool): If True, skip records with EMPTY source types. Defaults to False.

        Returns:
            pd.DataFrame: Copy of input DataFrame with fixed value columns added.

        Examples
        --------
        Adding a fixed value column from a scenario with FIXED source type.

        >>> df = pd.DataFrame({'id': [1, 2, 3], 'name': ['John', 'Jane', 'Bob']})
        >>> df.columns.tolist()
        ['id', 'name']
        >>> df
           id   name
        0   1   John
        1   2   Jane
        2   3    Bob

        Scenario has a record with FIXED source value 'NL' mapping to target 'country_code'.

        >>> df = scenario.add_fixed_values(df)
        >>> df
           id   name   country_code
        0   1   John             NL
        1   2   Jane             NL
        2   3    Bob             NL

        The 'country_code' column is added and filled with the fixed value 'NL' for all rows.

        Also supports CONFIGURATION source types. Config values are parsed according to
        their type (TEXT, EMAIL, NUMBER, SELECTION, DATEPICKER, etc.) during record creation.

        Note:
            For many_to_one/many_to_many mappings, use rename_fields() instead.
        """
        df_fixed = df.copy()

        for record in self.records:
            if (record.relation_type not in ("one_to_one", "one_to_many")) or (record.fixed_source_value is None):
                continue

            # Skip if ignore_empty_source is True and source type is EMPTY
            # TODO: tbd if this is needed, pending with Jop. More logical to just set these columns to (a configurable) empty value.
            if ignore_empty_source and record.has_empty_source:
                continue

            for target_field in record.target.field_names:
                df_fixed[target_field] = record.fixed_source_value

        return df_fixed

    def apply_value_mappings(
        self,
        df: pd.DataFrame,
        drop_unmapped: bool = False,
        how: Literal[
            'exactValMap',
            'ignoreCaseValMap',
            'ignoreSpecialValMap',
            'ignoreSpacesValMap',
            'flexValMap'
        ] = 'exactValMap'
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Transforms source values to target values based on scenario mappings.

        Processes records with value mapping configurations (e.g., "M" -> "1").
        Handles various relation types by preparing source values appropriately (direct vs concatenated).

        Strategy selection priority:
            1. Check record.logic for 'matching strategy' (higher priority), evaluate if correspond to the strategy names above.
            2. Fall back to how kwarg if no match in logic

        Mapping strategies (how parameter/record.logic field):
            - exactValMap: Precise matching (default)
            - ignoreCaseValMap: Case-insensitive matching
            - ignoreSpecialValMap: Ignores special characters including spaces
            - ignoreSpacesValMap: Ignores spaces only
            - flexValMap: Case-insensitive + ignores special characters including spaces

        Examples
        --------
        Example 1: Basic value mapping with exactValMap (default).

        >>> df = pd.DataFrame({'gender': ['F', 'M', 'F']})
        >>> # Scenario mapping configuration:
        >>> #   {'gender': 'F'} -> {'gender_code': '1'}
        >>> #   {'gender': 'M'} -> {'gender_code': '0'}
        >>> df, stats = scenario.apply_value_mappings(df)
        >>> df
           gender  gender_code
        0       F            1
        1       M            0
        2       F            1

        Example 2: Flexible matching with flexValMap (ignores case and special chars).

        >>> df = pd.DataFrame({
        ...     'product_code': ['ABC-123', 'xyz_456', 'MNO 789', 'PQR@#$%']
        ... })
        >>> # Scenario mapping (source values normalized: lowercase + remove special chars):
        >>> #   {'product_code': 'abc123'} -> {'product_id': 'P001'}  # Matches 'ABC-123'
        >>> #   {'product_code': 'xyz456'} -> {'product_id': 'P002'}  # Matches 'xyz_456'
        >>> #   {'product_code': 'mno789'} -> {'product_id': 'P003'}  # Matches 'MNO 789'
        >>> #   {'product_code': 'pqr'} -> {'product_id': 'P004'}     # Matches 'PQR@#$%'
        >>> df, stats = scenario.apply_value_mappings(df, how='flexValMap')
        >>> df
          product_code product_id
        0      ABC-123       P001
        1      xyz_456       P002
        2      MNO 789       P003
        3      PQR@#$%       P004

        Args:
            df: Input DataFrame.
            drop_unmapped: If True (and no default value exists), drops rows that couldn't be mapped.
            how: Mapping strategy to use (default: 'exactValMap'). Can be overridden per record via logic.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]:
                1. Transformed DataFrame.
                2. Statistics DataFrame detailing mapping success rates and value distributions.

        """
        # Warn about missing values before processing
        self._warn_missing_values_in_mapping_fields(df=df)

        statistics_rows = []

        # Process each record to apply value mappings
        for record in self.records:
            if not record.mapping:
                continue

            source_field_names = record.source.field_names
            target_field_names = record.target.field_names
            total_rows = len(df)
            default_val = record.mapping.default_value

            # Ensure source fields are present in the dataframe
            if self._handle_missing_source_fields(
                df=df,
                record=record,
                source_field_names=source_field_names,
                target_field_names=target_field_names,
                default_val=default_val,
                how=how,
                statistics_rows=statistics_rows
            ):
                continue

            # Source fields are not missing, log and follow strategy
            mapping_strategy = self._determine_mapping_strategy(record.logic, how)

            # Normalize dataframe according to mapping strategy
            concatenated_source_series, original_source_series = self._normalize_dataframe_for_mapping(
                df=df,
                source_field_names=source_field_names,
                mapping_strategy=mapping_strategy
            )

            replacements_by_target, defined_mapping_values = self._build_normalized_value_mappings(
                record=record,
                source_field_names=source_field_names,
                target_field_names=target_field_names,
                mapping_strategy=mapping_strategy
            )

            # Apply mappings to target columns
            for target_field in target_field_names:
                df = self._apply_mapping_to_target(
                    df=df,
                    concatenated_source_series=concatenated_source_series,
                    target_field=target_field,
                    replacements=replacements_by_target[target_field],
                    default_val=default_val,
                    original_source_series=original_source_series
                )

            # Collect statistics and optionally drop unmapped rows
            stats_row, is_mapped = self._collect_value_mapping_statistics(
                df=df,
                record=record,
                source_field_names=source_field_names,
                target_field_names=target_field_names,
                replacements_by_target=replacements_by_target,
                defined_mapping_values=defined_mapping_values,
                concatenated_source_series=concatenated_source_series,
                original_source_series=original_source_series,
                mapping_strategy=mapping_strategy,
                total_rows=total_rows
            )
            statistics_rows.append(stats_row)

            if drop_unmapped and not default_val:
                df = df[is_mapped]

        stats_df = self._build_value_mapping_stats_dataframe(statistics_rows)

        return df, stats_df

    def rename_fields(
        self,
        df: pd.DataFrame,
        drop_unmapped: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Renames and transforms DataFrame columns based on scenario field mappings.

        Handles complex mappings like concatenation (many-to-one) and splitting (one-to-many).
        Records with value mappings are logged but skipped (use `apply_value_mappings` for those).
        All target fields defined in the scenario are automatically kept in the output DataFrame.

        Args:
            df: Input DataFrame.
            drop_unmapped: If True, drops source columns that were successfully mapped (target fields are always kept).

        Returns:
            Tuple containing:
                - Modified DataFrame with renamed/transformed columns based on scenario mappings.
                - Statistics DataFrame (stats_df) with detailed mapping information

        Logic types:
            - "concat": Concatenate all sources with '|', fill all targets
            - "fill": Map source[i] → target[i] in order
            - "keep source": Keep source fields unchanged, no target columns
            - Default (no logic): Uses relation_type:
                * one_to_one: Direct mapping source[0] → target[0]
                * one_to_many: Duplicate single source value to all target fields
                * many_to_one: Concatenate all source fields with '|' into single target
                * many_to_many (n:m): Behavior depends on field counts:
                  - n == m: Direct 1:1 mapping source[i] → target[i]
                  - n < m: Map first n sources to first n targets, fill remaining with last source
                  - n > m: Concatenate all sources to each target field

        Examples
        --------
        Example 1: Renaming columns using one_to_one mapping (no logic, uses default).

        >>> df = pd.DataFrame({'id': [1, 2], 'first_name': ['John', 'Jane']})
        >>> df
           id  first_name
        0   1        John
        1   2        Jane

        Scenario maps 'first_name' → 'firstname' (one_to_one, no logic specified).
        Default behavior: direct mapping source[0] → target[0].

        >>> df, stats_df = scenario.rename_fields(df)
        >>> df
           id  firstname
        0   1       John
        1   2       Jane


        Example 2: Using many_to_one mapping (no logic, uses default).

        >>> df = pd.DataFrame({'id': [1, 2], 'street': ['Main St', 'Oak Ave'], 'city': ['Amsterdam', 'Rotterdam']})
        >>> df
           id     street          city
        0   1    Main St     Amsterdam
        1   2    Oak Ave     Rotterdam

        Scenario maps 'street'|'city' → 'address' (many_to_one, no logic specified).
        Default behavior: concatenate all source fields with '|' separator into single target.

        >>> df, stats_df = scenario.rename_fields(df)
        >>> df
           id              address
        0   1    Main St|Amsterdam
        1   2    Oak Ave|Rotterdam

        """
        # objects for tracking statistics
        newly_created_target_fields = set()
        source_fields_to_keep = set()
        stats_data = []

        # Handler dictionaries route records to transformation methods
        logic_handlers = {
            'concat': self._apply_concat,
            'fill': self._apply_fill,
            'keepsource': self._apply_keep_source,
            'onlysource': self._apply_keep_source
        }

        default_handlers = {
            'one_to_one': self._apply_one_to_one,
            'one_to_many': self._apply_one_to_many,
            'many_to_one': self._apply_many_to_one,
            'many_to_many': self._apply_many_to_many
        }

        for record in self.records:
            source_field_names = record.source.field_names

            # Skip records with value mappings
            if record.mapping:
                self._apply_value_mapping_logging(df, record, stats_data, newly_created_target_fields)
                continue

            # Skip records handled by add_fixed_values (EMPTY, FIXED, CONFIG source types)
            # These don't have actual source columns in the DataFrame
            if record.has_empty_source or record.fixed_source_value is not None or len(source_field_names) == 0:
                self._apply_empty_source_logging(df, record, stats_data, newly_created_target_fields)
                continue

            normalized_logic = self._normalize_logic(record.logic)
            existing_sources = [s for s in source_field_names if s in df.columns]

            # Skip if none of the source fields exist in the DataFrame
            if len(existing_sources) == 0:
                self._apply_empty_source_logging(df, record, stats_data, newly_created_target_fields)
                continue

            # Check if normalized logic contains any handler key
            matched_handler_key = None
            for handler_key in logic_handlers.keys():
                if handler_key in normalized_logic:
                    matched_handler_key = handler_key
                    break

            if matched_handler_key:
                logic_handler = logic_handlers[matched_handler_key]
                if matched_handler_key in ('keepsource', 'onlysource'):
                    logic_handler(
                        df=df,
                        record=record,
                        stats_data=stats_data,
                        kept_sources=source_fields_to_keep
                    )
                else:
                    logic_handler(
                        df=df,
                        record=record,
                        existing_sources=existing_sources,
                        stats_data=stats_data,
                        created_targets=newly_created_target_fields
                    )
            else:
                default_handler = default_handlers.get(record.relation_type)
                if default_handler:
                    if record.relation_type == 'many_to_many':
                        default_handler(
                            df=df,
                            record=record,
                            existing_sources=existing_sources,
                            stats_data=stats_data,
                            created_targets=newly_created_target_fields,
                            kept_sources=source_fields_to_keep
                        )
                    else:
                        default_handler(
                            df=df,
                            record=record,
                            existing_sources=existing_sources,
                            stats_data=stats_data,
                            created_targets=newly_created_target_fields
                        )
                else:
                    raise ValueError(
                        f"Unknown relation_type '{record.relation_type}' for record {record.id}. "
                        f"Supported types: {', '.join(default_handlers.keys())}"
                    )

        # Generate statistics
        stats_df = self._generate_statistics_dataframe(
            df=df,
            stats_data=stats_data,
            source_fields_to_keep=source_fields_to_keep
        )

        # Clean up
        df = self._finalize_dataframe_columns(
            df=df,
            drop_unmapped=drop_unmapped,
            newly_created_target_fields=newly_created_target_fields,
            source_fields_to_keep=source_fields_to_keep
        )

        return df, stats_df

# ============================================================================
# Main Scenarios Class
# ============================================================================
class Scenarios():
    """
    Provides convenient access to BrynQ Scenarios corresponding to an interface
    """

    def __init__(self, brynq_instance: Any):
        """Initializes the Scenarios manager.

        Fetches and parses scenarios from the BrynQ API. Scenarios are cached after first fetch.
        Dunder methods (__getitem__, __iter__, __len__) auto-fetch if not loaded.

        **Core Methods:**
            - get(): Fetches/returns Scenario objects (cached after first call)

        **Dunder Methods:**
            - __getitem__: Dict access `Scenarios['Name']`
            - __iter__: Iterate scenarios `for scenario in Scenarios:`
            - __len__: Count scenarios `len(Scenarios)`

        Args:
            brynq_instance: Authenticated BrynQ client instance.
        """
        self._brynq = brynq_instance

        # Attributes populated by get()
        self.raw_scenarios: Optional[List[ScenarioSchema]] = None
        self._scenarios: Optional[Dict[str, Scenario]] = None
        self._current_language: str = 'en'

    # ============================================================================
    # Public API Methods
    # ============================================================================

    def get(self, language: str = 'en') -> "Scenarios":
        """Fetches all scenarios from the API and parses them.

        Results are cached after the first call. Changing language updates all cached scenarios.

        Args:
            language: Language code ('en' or 'nl') for label and question access.

        Returns:
            Scenarios: Self

        Example:
            >>> scenarios = brynq.interfaces.scenarios.get(language='nl')
            >>> scenarios['Personal']  # dict-style access
            >>> scenarios.scenarios  # dict of all scenarios
        """
        # Fetch and parse scenarios if not cached
        if self._scenarios is None:
            if self.raw_scenarios is None:
                self.raw_scenarios = self._fetch_from_api()
            self._scenarios = {
                s.name: Scenario.from_schema(schema=s, language=language)
                for s in self.raw_scenarios if s.name
            }

        # Update language on all scenarios
        self._current_language = language
        for scenario in self._scenarios.values():
            scenario.set_language(language)

        return self

    @property
    def scenarios(self) -> Dict[str, Scenario]:
        """Return the scenarios dict.

        Example:
            >>> scenarios.get(language='nl').scenarios
            {'Personal': <Scenario ...>, 'Address': <Scenario ...>, ...}
        """
        if self._scenarios is None:
            self.get()
        return self._scenarios

    # ============================================================================
    # Properties
    # ============================================================================

    @cached_property
    def scenario_names(self) -> List[str]:
        """A list of all scenario names.

        Example:
            >>> scenarios.scenario_names
            ['Personal information', 'Adres', 'Bank Account', 'Contract Information', ...]

        Returns:
            List[str]: List of all scenario names.
        """
        return list(self.scenarios.keys())

    # ============================================================================
    # Dunder Methods
    # ============================================================================

    def __getitem__(self, scenario_name: str) -> Scenario:
        """Returns scenario by name using dict-style access.

        Example:
            >>> scenarios.get()['Personal']
            >>> scenarios['Personal']  # Same as above

        Args:
            scenario_name: Name of the scenario to retrieve.

        Returns:
            Scenario object with records, mappings, and field properties.

        Raises:
            KeyError: If scenario name not found.
        """
        if scenario_name not in self.scenarios:
            raise KeyError(f"Scenario '{scenario_name}' not found.")
        return self.scenarios[scenario_name]

    def __iter__(self) -> Iterator[Scenario]:
        """Iterates over scenarios"""
        return iter(self.values())

    def keys(self):
        """Return scenario names."""
        return self.scenario_names

    def values(self) -> List[Scenario]:
        """Return scenario instances."""
        return list(self.scenarios.values())

    def __len__(self) -> int:
        """Return the number of parsed scenarios.

        Example:
            >>> len(scenarios)
            13

        Returns:
            int: The number of available scenarios.
        """
        return len(self.scenarios)

    def __repr__(self) -> str:
        """Return a concise string representation of the Scenarios collection.

        Example:
            >>> repr(scenarios)
            "<Scenarios(13): Personal information, Work, Address, ...>"

        Returns:
            str
        """
        scenarios_dict = self.scenarios
        if not scenarios_dict:
            return "Scenarios(0)"
        names = list(scenarios_dict.keys())[:5]
        suffix = ", ..." if len(scenarios_dict) > 5 else ""
        return f"<Scenarios({len(scenarios_dict)}): {', '.join(names)}{suffix}>"

    def __str__(self) -> str:
        """Return a concise string representation of the Scenarios collection.

        Returns:
            str
        """
        return self.__repr__()

    # ============================================================================
    # Internal API Helpers
    # ============================================================================
    def _fetch_from_api(self) -> List[ScenarioSchema]:
        """Fetches scenario data from BrynQ API and validates it.

        Makes HTTP GET request, validates JSON against ScenariosSchema.

        Returns:
            List[ScenarioSchema]: Validated scenario objects (Pydantic models).

        Raises:
            requests.HTTPError: API request failed (non-2xx status).
            ValidationError: Schema validation failed.
        """
        response = self._brynq.brynq_session.get(
            url=(
                f"{self._brynq.url}interfaces/"
                f"{self._brynq.data_interface_id}/scenarios"
            ),
            timeout=self._brynq.timeout,
        )
        response.raise_for_status()

        # Validate and return Pydantic objects directly (no conversion to dict)
        validated = ScenariosSchema.model_validate(response.json())
        return list(validated.root)
