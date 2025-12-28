"""
Private helper methods for Scenario class.

This module contains internal implementation details that are not part of the public API.
These methods handle DataFrame transformation, value mapping, and statistics collection.
"""
from __future__ import annotations

import re
import warnings
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd
import pandera as pa
from brynq_sdk_functions import BrynQPanderaDataFrameModel
from pandera.typing import Series, String
from pydantic import ConfigDict

from .schemas.scenarios import (
    Scenario as ScenarioSchema,
)
from .schemas.scenarios_parsed import (
    Record,
)
from ._scenario_parser import (
    FieldPropertiesMap,
    _DummyRecord,
)


class _ScenarioTransformationEngine(ScenarioSchema):
    """Base class containing private helper methods for Scenario.

    Inherits from ScenarioSchema (API model) and provides all internal
    transformation and processing methods used by the Scenario class.
    """
    # Override parent's frozen config to allow mutation
    model_config = ConfigDict(frozen=False, strict=False, populate_by_name=True)

    # Missing value representations to detect in dataframes (literal strings, not regex)
    MISSING_VALUES: List[str] = [
        '<NA>', 'nan', 'None', 'NaN', 'null', 'NaT', '_NA_', '', '[]', '{ }'
    ]

    # ============================================================================
    # Static Helper Methods
    # ============================================================================

    def _update_field_props_language(self, field_props, language: str) -> None:
        """Update language on a single FieldProperties object.

        Args:
            field_props: The FieldProperties to update.
            language: Language code ('en' or 'nl').
        """
        if field_props.label_obj:
            field_props.label_obj.set_default_language(language)
        if field_props.question_obj:
            field_props.question_obj.set_default_language(language)

    @staticmethod
    def _build_custom_field_model(custom_fields: FieldPropertiesMap) -> Optional[type]:
        """Dynamically creates a Pandera Schema for custom fields validation.

        Uses the `custom_fields` dictionary to extract field metadata (technical_name, label, required)
        and create a Pandera schema model for validation.

        Args:
            custom_fields: Dictionary mapping field names to their FieldProperties objects (filtered to CUSTOM fields only)

        Returns:
            A dynamically generated BrynQ Pandera model class or None when no fields can be mapped
        """
        annotations = {}
        fields = {}
        for name, props in custom_fields.items():
            annotations[name] = Optional[Series[String]]
            # Use fallback, technical_name can be None by definition for CUSTOM fields if not found in data
            alias_value = props.technical_name or props.uuid or name
            fields[name] = pa.Field(
                coerce=True,
                nullable=not props.required,
                alias=alias_value,
                description=props.label
            )

        if not annotations:
            return None
        fields["__annotations__"] = annotations
        return type("CustomFieldModel", (BrynQPanderaDataFrameModel,), fields)

    # ============================================================================
    # rename_fields() Helpers - Logic Handlers
    # ============================================================================
    # These handlers implement specific logic types for the rename_fields() method.
    # Each handler processes records with a particular logic string (concat, fill, etc.)
    # or default relation type behavior (one_to_one, many_to_many, etc.).

    def _apply_keep_source(
        self,
        df: pd.DataFrame,
        record,
        stats_data: List[dict],
        kept_sources: Set[str]
    ) -> None:
        """Applies 'keep source' logic: preserves source columns without creating targets."""
        source_field_names = record.source.field_names
        for source_field in source_field_names:
            kept_sources.add(source_field)
            source_existed = source_field in df.columns
            self._log_transformation_stats(
                stats_data=stats_data,
                record=record,
                target_col=None,
                source_col=source_field,
                status='kept_source',
                mapping_type='keep_source',
                source_existed=source_existed,
                df_length=len(df) if source_existed else 0
            )

    def _apply_concat(
        self,
        df: pd.DataFrame,
        record,
        existing_sources: List[str],
        stats_data: List[dict],
        created_targets: Set[str],
    ) -> None:
        """Applies 'concat' logic: joins all sources and fills all targets."""
        target_field_names = record.target.field_names
        concatenated = self._concatenate_source_fields(df=df, source_fields=existing_sources)
        for target_field in target_field_names:
            created_targets.add(target_field)
            df[target_field] = concatenated
            self._log_transformation_stats(
                stats_data=stats_data, record=record, target_col=target_field,
                source_col=existing_sources, status='mapped', mapping_type='concat', df_length=len(df)
            )

    def _apply_fill(
        self,
        df: pd.DataFrame,
        record,
        existing_sources: List[str],
        stats_data: List[dict],
        created_targets: Set[str],
    ) -> None:
        """Applies 'fill' logic: maps source[i] to target[i] sequentially."""
        target_field_names = record.target.field_names
        n = min(len(existing_sources), len(target_field_names))

        for i in range(n):
            source_field = existing_sources[i]
            target_field = target_field_names[i]
            created_targets.add(target_field)
            df[target_field] = df[source_field]
            self._log_transformation_stats(
                stats_data=stats_data, record=record, target_col=target_field,
                source_col=source_field, status='mapped', mapping_type='fill', df_length=len(df)
            )

        if len(target_field_names) > len(existing_sources):
            for i in range(len(existing_sources), len(target_field_names)):
                target_field = target_field_names[i]
                created_targets.add(target_field)
                df[target_field] = ''
                self._log_transformation_stats(
                    stats_data=stats_data, record=record, target_col=target_field,
                    source_col=None, status='source_missing', mapping_type='fill',
                    source_existed=False, df_length=len(df)
                )

    def _apply_one_to_one(
        self,
        df: pd.DataFrame,
        record,
        existing_sources: List[str],
        stats_data: List[dict],
        created_targets: Set[str],
    ) -> None:
        """Applies default one-to-one logic: Direct value copy."""
        source_field = record.source.field_names[0]
        target_field = record.target.field_names[0]
        created_targets.add(target_field)
        df[target_field] = df[source_field]
        self._log_transformation_stats(
            stats_data=stats_data, record=record, target_col=target_field, source_col=source_field,
            status='mapped', mapping_type='one_to_one', default_logic='direct_mapping', df_length=len(df)
        )

    def _apply_one_to_many(
        self,
        df: pd.DataFrame,
        record,
        existing_sources: List[str],
        stats_data: List[dict],
        created_targets: Set[str],
    ) -> None:
        """Applies default one-to-many logic: Duplicate source value to all targets."""
        source_field = record.source.field_names[0]
        target_field_names = record.target.field_names

        for target_field in target_field_names:
            created_targets.add(target_field)
            df[target_field] = df[source_field]
            self._log_transformation_stats(
                stats_data=stats_data, record=record, target_col=target_field, source_col=source_field,
                status='mapped', mapping_type='one_to_many', default_logic='duplicate_to_all_targets', df_length=len(df)
            )

    def _apply_many_to_one(
        self,
        df: pd.DataFrame,
        record,
        existing_sources: List[str],
        stats_data: List[dict],
        created_targets: Set[str],
    ) -> None:
        """Applies default many-to-one logic: Concatenate sources with pipe separator."""
        source_field_names = record.source.field_names
        target_field = record.target.field_names[0]
        created_targets.add(target_field)
        concatenated = self._concatenate_source_fields(df=df, source_fields=source_field_names)
        df[target_field] = concatenated
        self._log_transformation_stats(
            stats_data=stats_data, record=record, target_col=target_field, source_col=source_field_names,
            status='mapped', mapping_type='many_to_one', default_logic='concatenate_with_pipe', df_length=len(df)
        )

    def _apply_many_to_many(
        self,
        df: pd.DataFrame,
        record,
        existing_sources: List[str],
        stats_data: List[dict],
        created_targets: Set[str],
        kept_sources: Optional[Set[str]] = None
    ) -> None:
        """Applies default many-to-many logic: Variable behavior based on field counts."""
        source_field_names = record.source.field_names
        target_field_names = record.target.field_names
        n_sources = len(source_field_names)
        n_targets = len(target_field_names)

        # Equal: 1:1 mapping
        if n_sources == n_targets:
            for i in range(n_sources):
                source_field = source_field_names[i]
                target_field = target_field_names[i]
                created_targets.add(target_field)
                df[target_field] = df[source_field]
                self._log_transformation_stats(
                    stats_data=stats_data, record=record, target_col=target_field, source_col=source_field,
                    status='mapped', mapping_type='many_to_many_equal', default_logic='direct_1_to_1_mapping', df_length=len(df)
                )

        # Less sources: Map 1:1 then fill remaining with last source
        elif n_sources < n_targets:
            for i in range(n_sources):
                source_field = source_field_names[i]
                target_field = target_field_names[i]
                created_targets.add(target_field)
                df[target_field] = df[source_field]
                self._log_transformation_stats(
                    stats_data=stats_data, record=record, target_col=target_field, source_col=source_field,
                    status='mapped', mapping_type='many_to_many_n_lt_m', default_logic='map_n_then_fill_remaining', df_length=len(df)
                )

            last_source = source_field_names[-1]
            for i in range(n_sources, n_targets):
                target_field = target_field_names[i]
                created_targets.add(target_field)
                df[target_field] = df[last_source]
                self._log_transformation_stats(
                    stats_data=stats_data, record=record, target_col=target_field, source_col=last_source,
                    status='mapped', mapping_type='many_to_many_n_lt_m', default_logic='map_n_then_fill_remaining', df_length=len(df)
                )

        # More sources: Concatenate all to each target
        else:
            concatenated = self._concatenate_source_fields(df=df, source_fields=source_field_names)
            for target_field in target_field_names:
                created_targets.add(target_field)
                df[target_field] = concatenated
                self._log_transformation_stats(
                    stats_data=stats_data, record=record, target_col=target_field, source_col=source_field_names,
                    status='mapped', mapping_type='many_to_many_n_gt_m', default_logic='concatenate_all_to_each_target', df_length=len(df)
                )

    # ============================================================================
    # rename_fields() Helpers - Statistics & Finalization
    # ============================================================================
    # These helpers handle statistics collection and DataFrame finalization
    # for the rename_fields() method.

    def _generate_statistics_dataframe(
        self,
        df: pd.DataFrame,
        stats_data: List[dict],
        source_fields_to_keep: Set[str]
    ) -> pd.DataFrame:
        """Generates the statistics DataFrame, including unmapped source columns."""
        all_scenario_sources = self.all_source_fields
        mapped_sources_from_records = set()
        for record in self.records:
            mapped_sources_from_records.update(record.source.field_names)

        unmapped_sources_in_df = (all_scenario_sources & set(df.columns)) - mapped_sources_from_records - source_fields_to_keep

        dummy_record = _DummyRecord()
        for unmapped_source in unmapped_sources_in_df:
            self._log_transformation_stats(
                stats_data=stats_data,
                record=dummy_record,
                target_col=None,
                source_col=unmapped_source,
                status='not_in_mapping',
                mapping_type='unknown',
                source_existed=True,
                df_length=len(df)
            )

        if stats_data:
            return pd.DataFrame(stats_data)

        return pd.DataFrame(columns=[
            'record_id', 'source_column', 'target_column', 'mapping_status',
            'source_existed', 'rows_affected', 'mapping_type', 'logic',
            'relation_type', 'source_count', 'target_count', 'default_logic'
        ])

    def _finalize_dataframe_columns(
        self,
        df: pd.DataFrame,
        drop_unmapped: bool,
        newly_created_target_fields: Set[str],
        source_fields_to_keep: Set[str]
    ) -> pd.DataFrame:
        """Drops unmapped source columns from the DataFrame.

        Only handles dropping unmapped columns. Filtering for scenario target fields
        is handled separately in apply() to separate concerns.
        """
        protected_columns = newly_created_target_fields | source_fields_to_keep

        if drop_unmapped:
            mapped_source_columns = set()
            for record in self.records:
                if record.mapping and hasattr(record.mapping, 'values'):
                    continue

                normalized_logic = self._normalize_logic(record.logic)
                is_keep_source = "keepsource" in normalized_logic or "onlysource" in normalized_logic

                if not is_keep_source:
                    mapped_source_columns.update(record.source.field_names)

            columns_to_drop = [col for col in mapped_source_columns if col not in protected_columns]
            df = df.drop(columns=columns_to_drop, errors='ignore')

        return df

    def _log_transformation_stats(
        self,
        stats_data: List[dict],
        record,
        target_col: Optional[str],
        source_col: Optional[Union[str, List[str]]],
        status: str,
        mapping_type: str,
        default_logic: Optional[str] = None,
        source_existed: bool = True,
        df_length: int = 0
    ) -> List[dict]:
        """Logs statistics for one field mapping operation."""
        if isinstance(source_col, list):
            src_str = '|'.join(source_col) if source_col else None
        else:
            src_str = source_col

        stats_data.append({
            'record_id': record.id,
            'source_column': src_str,
            'target_column': target_col,
            'mapping_status': status,
            'source_existed': source_existed,
            'rows_affected': df_length,
            'mapping_type': mapping_type,
            'logic': record.logic,
            'relation_type': record.relation_type,
            'source_count': len(record.source.field_names),
            'target_count': len(record.target.field_names),
            'default_logic': default_logic
        })
        return stats_data

    def _apply_value_mapping_logging(
        self,
        df: pd.DataFrame,
        record,
        stats_data: List[dict],
        created_targets: Set[str]
    ) -> None:
        """Logs statistics for records with explicit value mappings (skipping renaming)."""
        source_field_names = record.source.field_names
        target_field_names = record.target.field_names
        for target_field in target_field_names:
            created_targets.add(target_field)
            if target_field not in df.columns:
                df[target_field] = None
            self._log_transformation_stats(
                stats_data=stats_data,
                record=record,
                target_col=target_field,
                source_col=source_field_names,
                status='value_mapped',
                mapping_type='value_mapping',
                source_existed=any(s in df.columns for s in source_field_names),
                df_length=len(df)
            )

    def _apply_empty_source_logging(
        self,
        df: pd.DataFrame,
        record,
        stats_data: List[dict],
        created_targets: Set[str]
    ) -> None:
        """Logs statistics for records with EMPTY source types (handled by add_fixed_values)."""
        source_field_names = record.source.field_names
        target_field_names = record.target.field_names
        for target_field in target_field_names:
            created_targets.add(target_field)
            self._log_transformation_stats(
                stats_data=stats_data,
                record=record,
                target_col=target_field,
                source_col=source_field_names,
                status='empty_source',
                mapping_type='empty_source',
                source_existed=False,
                df_length=len(df)
            )

    # ============================================================================
    # Shared Utility Helpers
    # ============================================================================
    # General-purpose utilities used by multiple public methods.

    def _normalize_logic(self, logic: Optional[str]) -> str:
        """Normalizes logic string for flexible matching.

        Converts to lowercase and removes spaces/special characters so "Concat", "CONCAT", and "concat"
        all match the same logic type. Used by rename_fields() to match user-entered logic strings.

        Args:
            logic: Original logic string (e.g., "Concat", "fill", "keep source").

        Returns:
            Normalized string (e.g., "concat", "fill", "keepsource"). Empty string if None.
        """
        if not logic:
            return ""
        return re.sub(r'[^a-z0-9]', '', logic.lower())

    def _normalize_value_for_mapping(self, value: Any, strategy: str) -> str:
        """Normalizes a value according to the specified mapping strategy.

        Used by apply_value_mappings() to normalize both DataFrame source values and
        mapping source values before comparison, enabling flexible matching strategies.

        Args:
            value: The value to normalize (e.g., "John Doe", "F", "John|Doe").
            strategy: Mapping strategy name (exactValMap, ignoreCaseValMap, etc.).

        Returns:
            Normalized value ready for comparison.
        """
        # Handle None and pandas NA
        if value is None:
            return ""

        # Check for pandas NA (scalar check to avoid array ambiguity)
        try:
            if pd.isna(value):
                return ""
        except (ValueError, TypeError):
            # pd.isna fails on arrays/lists - convert to string representation
            pass

        # Handle pandas/numpy numeric types
        # int/np.integer → '40'
        # float/np.floating that represents integer (40.0) → '40' (strips .0)
        # This is needed because pandas converts int columns with NaN to float,
        # but mapping values from API are strings without .0 suffix
        if isinstance(value, (int, np.integer)):
            value_str = str(value)
        elif isinstance(value, (float, np.floating)) and value.is_integer():
            value_str = str(int(value))
        else:
            value_str = str(value).strip()

        # Check for empty or falsy string representations
        if value_str in ('', 'None', 'nan', 'NaN', 'NaT', '<NA>'):
            return value_str

        if strategy == 'exactValMap':
            return value_str
        elif strategy == 'ignoreCaseValMap':
            return value_str.lower()
        elif strategy == 'ignoreSpecialValMap':
            return re.sub(r'[^a-zA-Z0-9]', '', value_str)
        elif strategy == 'ignoreSpacesValMap':
            return value_str.replace(' ', '')
        elif strategy == 'flexValMap':
            return re.sub(r'[^a-z0-9]', '', value_str.lower())
        else:
            return value_str

    def _determine_mapping_strategy(self, record_logic: Optional[str], default_how: str) -> str:
        """Determines which mapping strategy to use for a record.

        Checks record.logic first (higher priority), then falls back to default_how kwarg.
        Uses _normalize_logic to match strategy names flexibly. Checks if normalized logic
        contains any strategy name as a substring (to handle cases where logic contains other text).

        Args:
            record_logic: The logic string from the record (may contain strategy name).
            default_how: Default strategy from how kwarg (e.g., 'exactValMap').

        Returns:
            Strategy name to use (exactValMap, ignoreCaseValMap, etc.).
        """
        if not record_logic:
            return default_how

        normalized_logic = self._normalize_logic(record_logic)

        strategies = [
            ('ignorecasevalmap', 'ignoreCaseValMap'),
            ('ignorespecialvalmap', 'ignoreSpecialValMap'),
            ('ignorespacesvalmap', 'ignoreSpacesValMap'),
            ('flexvalmap', 'flexValMap'),
            ('exactvalmap', 'exactValMap')
        ]

        for normalized_strategy, strategy_name in strategies:
            if normalized_strategy in normalized_logic:
                return strategy_name

        return default_how

    def _concatenate_source_fields(
        self,
        df: pd.DataFrame,
        source_fields: List[str]
    ) -> pd.Series:
        """Concatenates values from multiple source columns into a single Series with '|' separator.

        Combines the values from multiple columns (not the column names).
        Example: values from 'first_name' and 'last_name' columns → 'John|Doe'.
        Returns a Series of values; caller assigns this Series to target column name(s).
        If only one field provided, returns its values converted to string and stripped (no concatenation).
        Called by rename_fields() for 'concat' logic and many_to_one/many_to_many default behaviors.

        Args:
            df: DataFrame containing the source columns.
            source_fields: List of column names whose VALUES will be concatenated (e.g., ['first_name', 'last_name']).

        Returns:
            Series of concatenated VALUES (no column name). Caller assigns to target column(s).
        """
        if len(source_fields) == 1:
            return df[source_fields[0]].astype(str).str.strip()
        else:
            return df[source_fields].astype(str).apply(
                lambda row: '|'.join(val.strip() for val in row), axis=1
            )

    def _apply_mapping_to_target(
        self,
        df: pd.DataFrame,
        concatenated_source_series: pd.Series,
        target_field: str,
        replacements: dict,
        default_val: Optional[str] = None,
        original_source_series: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """Applies value mappings to create/populate a target column.

        Transforms source values → target values using lookup dictionary via pandas .map().
        Unmapped values use default_val if provided, otherwise keep original source value.
        Always creates target column (uses default if no mappings exist).
        Called by apply_value_mappings() for each target field in records with value mappings.

        Args:
            df: DataFrame to modify. Target column added/updated in-place.
            concatenated_source_series: Source values formatted for lookup (may be normalized for flexible matching).
            target_field: Name of target column to create/populate.
            replacements: Mapping dict {normalized_source_value: target_value} (e.g., {"f": "1", "m": "0"}).
            default_val: Default for unmapped values. If None, keeps original source value.
            original_source_series: Original (non-normalized) source series for fillna when default_val is None.

        Returns:
            Modified DataFrame with target column added/updated.
        """
        if not replacements:
            df[target_field] = default_val if default_val else None
            return df

        mapped_series = concatenated_source_series.map(replacements)

        if default_val:
            mapped_series = mapped_series.fillna(default_val)
        else:
            fill_series = original_source_series if original_source_series is not None else concatenated_source_series
            mapped_series = mapped_series.fillna(fill_series)

        df[target_field] = mapped_series
        return df

    def _detect_missing_values_in_fields(
        self,
        df: pd.DataFrame,
        source_field_names: List[str]
    ) -> Dict[str, int]:
        """Detects missing values in source fields used for value mapping."""
        missing_counts = {}
        missing_value_patterns = self.MISSING_VALUES

        for field_name in source_field_names:
            if field_name not in df.columns:
                continue

            series = df[field_name]
            missing_count = series.isna().sum()

            # Convert to string for safe comparison (handles arrays/lists in cells)
            str_series = series.astype(str)
            for pattern in missing_value_patterns:
                try:
                    missing_count += (str_series == pattern).sum()
                except (ValueError, TypeError):
                    # Skip patterns that cause comparison issues
                    continue

            if missing_count > 0:
                missing_counts[field_name] = missing_count

        return missing_counts

    # ============================================================================
    # apply_value_mappings() Helpers
    # ============================================================================
    # These helpers handle value transformation, normalization, and statistics
    # for the apply_value_mappings() method.

    def _warn_missing_values_in_mapping_fields(
        self,
        df: pd.DataFrame
    ) -> None:
        """Warns if source fields used for value mapping contain missing values.

        Collects all source fields from records with value mappings and checks
        for missing values (NA, None, NaN, etc.). Emits a warning if found.

        Args:
            df: DataFrame to check for missing values.
        """
        all_source_fields_to_check = set()
        for record in self.records:
            if record.mapping:
                all_source_fields_to_check.update(record.source.field_names)

        if not all_source_fields_to_check:
            return

        missing_value_counts = self._detect_missing_values_in_fields(
            df=df,
            source_field_names=list(all_source_fields_to_check)
        )

        if missing_value_counts:
            missing_details = [
                f"{field}: {count} occurrence(s)"
                for field, count in missing_value_counts.items()
            ]
            warnings.warn(
                f"DataFrame contains missing values (pd.NA or string representations) "
                f"in source fields used for value mapping: {', '.join(missing_details)}. "
                f"These may affect mapping accuracy.",
                UserWarning,
                stacklevel=3  # Account for extra call depth
            )

    def _handle_missing_source_fields(
        self,
        df: pd.DataFrame,
        record: Record,
        source_field_names: List[str],
        target_field_names: List[str],
        default_val: Optional[str],
        how: str,
        statistics_rows: List[dict]
    ) -> bool:
        """Handles case when source fields are missing from DataFrame.

        If any source fields are not in the DataFrame, creates target columns with
        default values, logs statistics, and returns True to signal skipping further
        processing for this record.

        Args:
            df: DataFrame to check and modify.
            record: The mapping record being processed.
            source_field_names: List of source field names to check.
            target_field_names: List of target field names to create if missing.
            default_val: Default value for target columns.
            how: Mapping strategy for statistics.
            statistics_rows: List to append statistics to.

        Returns:
            True if source fields were missing (caller should skip this record),
            False if all source fields are present (caller should continue processing).
        """
        missing_fields = [field for field in source_field_names if field not in df.columns]
        if not missing_fields:
            return False

        warnings.warn(
            f"Source fields {missing_fields} not found in dataframe for record {record.id}. "
            f"Creating target columns with default values.",
            stacklevel=3
        )

        for target_field in target_field_names:
            df[target_field] = default_val if default_val else None

        mapping_strategy = self._determine_mapping_strategy(record.logic, how)
        total_rows = len(df)

        statistics_rows.append({
            'record_id': record.id,
            'source_fields': '|'.join(source_field_names),
            'target_fields': '|'.join(target_field_names),
            'relation_type': record.relation_type,
            'mapping_strategy': mapping_strategy,
            'total_rows': total_rows,
            'mapped_rows': 0,
            'unmapped_rows': total_rows,
            'mapping_success_pct': 0.0,
            'successful_indices': [],
            'unsuccessful_indices': df.index.tolist(),
            'mapped_value_counts': {},
            'unmapped_value_counts': {},
            'used_mapping_values': [],
            'unused_mapping_values': []
        })

        return True

    def _build_normalized_value_mappings(
        self,
        record: Record,
        source_field_names: List[str],
        target_field_names: List[str],
        mapping_strategy: str
    ) -> Tuple[Dict[str, Dict[str, str]], List[dict]]:
        """Builds normalized value mappings from a record's mapping configuration.

        Processes mapping values to create lookup dictionaries for value transformation.
        Normalizes source values according to the mapping strategy for flexible matching.

        Args:
            record: The mapping record containing value mappings.
            source_field_names: List of source field names.
            target_field_names: List of target field names.
            mapping_strategy: Strategy for normalizing values (exactValMap, flexValMap, etc.).

        Returns:
            Tuple containing:
                - replacements_by_target: Dict mapping target field -> {normalized_source: target_value}
                - defined_mapping_values: List of mapping definitions with input/output pairs
        """
        replacements_by_target: Dict[str, Dict[str, str]] = {
            target_field: {} for target_field in target_field_names
        }
        defined_mapping_values: List[dict] = []

        if not record.mapping or not record.mapping.values:
            return replacements_by_target, defined_mapping_values

        for mapping_value in record.mapping.values:
            source_map_val = mapping_value.input
            target_map_val = mapping_value.output
            if not source_map_val or not target_map_val:
                continue

            # Extract and normalize source values
            source_values = []
            normalized_source_values = []
            for field_name in source_field_names:
                if field_name in source_map_val:
                    source_val = str(source_map_val[field_name]).strip()
                    source_values.append(source_val)
                    normalized_source_values.append(
                        self._normalize_value_for_mapping(source_val, mapping_strategy)
                    )
                else:
                    source_values = None
                    normalized_source_values = None
                    break

            if not source_values or len(source_values) != len(source_field_names):
                continue

            combined_source_val = '|'.join(source_values)
            normalized_combined_source_val = '|'.join(normalized_source_values)

            # Build mapping definition for statistics
            mapping_def = {
                'input': combined_source_val,
                'output': {
                    target_field: str(target_map_val.get(target_field, '')).strip()
                    for target_field in target_field_names if target_field in target_map_val
                }
            }
            defined_mapping_values.append(mapping_def)

            # Build replacement lookup for each target field
            for target_field in target_field_names:
                if target_field in target_map_val:
                    target_val = str(target_map_val[target_field]).strip()
                    replacements_by_target[target_field][normalized_combined_source_val] = target_val

        return replacements_by_target, defined_mapping_values

    def _normalize_dataframe_for_mapping(
        self,
        df: pd.DataFrame,
        source_field_names: List[str],
        mapping_strategy: str
    ) -> Tuple[pd.Series, pd.Series]:
        """Normalizes DataFrame source fields for value mapping comparison.

        Creates two concatenated series: one with normalized values (for matching)
        and one with original values (for fallback/statistics).

        Args:
            df: Input DataFrame containing source fields.
            source_field_names: List of source field names to normalize and concatenate.
            mapping_strategy: Strategy for normalizing values (exactValMap, flexValMap, etc.).

        Returns:
            Tuple containing:
                - concatenated_source_series: Concatenated series with normalized values for matching
                - original_source_series: Concatenated series with original values
        """
        # Create normalized copy
        normalized_df = df[source_field_names].copy()
        for field_name in source_field_names:
            if field_name in normalized_df.columns:
                normalized_df[field_name] = normalized_df[field_name].apply(
                    lambda val, strategy=mapping_strategy: self._normalize_value_for_mapping(val, strategy)
                )

        # Concatenate both normalized and original
        concatenated_source_series = self._concatenate_source_fields(df=normalized_df, source_fields=source_field_names)
        original_source_series = self._concatenate_source_fields(df=df, source_fields=source_field_names)

        return concatenated_source_series, original_source_series

    def _collect_value_mapping_statistics(
        self,
        df: pd.DataFrame,
        record: Record,
        source_field_names: List[str],
        target_field_names: List[str],
        replacements_by_target: Dict[str, Dict[str, str]],
        defined_mapping_values: List[dict],
        concatenated_source_series: pd.Series,
        original_source_series: pd.Series,
        mapping_strategy: str,
        total_rows: int
    ) -> Tuple[dict, pd.Series]:
        """Collects statistics about value mapping success for a single record.

        Calculates mapped/unmapped row counts, value distributions, and which
        mapping rules were used or unused.

        Args:
            df: DataFrame being processed.
            record: The mapping record.
            source_field_names: List of source field names.
            target_field_names: List of target field names.
            replacements_by_target: Dict mapping target field -> {normalized_source: target_value}.
            defined_mapping_values: List of mapping definitions with input/output pairs.
            concatenated_source_series: Concatenated series with normalized values for matching.
            original_source_series: Concatenated series with original values.
            mapping_strategy: Strategy used for normalization.
            total_rows: Total number of rows in DataFrame.

        Returns:
            Tuple containing:
                - Statistics row dict for this record
                - Boolean Series indicating which rows were successfully mapped
        """
        # Determine which rows were mapped
        all_mapped_source_values = set()
        for replacements in replacements_by_target.values():
            all_mapped_source_values.update(replacements.keys())

        is_mapped = concatenated_source_series.isin(all_mapped_source_values)
        mapped_rows = is_mapped.sum()
        unmapped_rows = (~is_mapped).sum()

        successful_indices = df.index[is_mapped].tolist()
        unsuccessful_indices = df.index[~is_mapped].tolist()

        # Count mapped and unmapped values
        mapped_values = original_source_series[is_mapped]
        unmapped_values = original_source_series[~is_mapped]
        mapped_value_counts_dict = dict(mapped_values.value_counts()) if len(mapped_values) > 0 else {}
        unmapped_value_counts_dict = dict(unmapped_values.value_counts()) if len(unmapped_values) > 0 else {}

        # Normalize mapped inputs for comparison with defined mappings
        normalized_mapped_inputs = {}
        for orig_val, count in mapped_value_counts_dict.items():
            normalized_val = self._normalize_value_for_mapping(orig_val, mapping_strategy)
            normalized_mapped_inputs[normalized_val] = normalized_mapped_inputs.get(normalized_val, 0) + count

        # Determine which mapping rules were used/unused
        unused_mapping_values = []
        used_mapping_values_with_counts = []
        for mapping_def in defined_mapping_values:
            mapping_input = mapping_def['input']
            normalized_mapping_input = self._normalize_value_for_mapping(mapping_input, mapping_strategy)
            if normalized_mapping_input in normalized_mapped_inputs:
                used_mapping_values_with_counts.append({
                    'input': mapping_input,
                    'output': mapping_def['output'],
                    'count': normalized_mapped_inputs.get(normalized_mapping_input, 0)
                })
            else:
                unused_mapping_values.append(mapping_def)

        mapping_success_pct = (mapped_rows / total_rows * 100) if total_rows > 0 else 0.0

        stats_row = {
            'record_id': record.id,
            'source_fields': '|'.join(source_field_names),
            'target_fields': '|'.join(target_field_names),
            'relation_type': record.relation_type,
            'mapping_strategy': mapping_strategy,
            'total_rows': total_rows,
            'mapped_rows': mapped_rows,
            'unmapped_rows': unmapped_rows,
            'mapping_success_pct': mapping_success_pct,
            'successful_indices': successful_indices,
            'unsuccessful_indices': unsuccessful_indices,
            'mapped_value_counts': mapped_value_counts_dict,
            'unmapped_value_counts': unmapped_value_counts_dict,
            'used_mapping_values': used_mapping_values_with_counts,
            'unused_mapping_values': unused_mapping_values
        }

        return stats_row, is_mapped

    def _build_value_mapping_stats_dataframe(
        self,
        statistics_rows: List[dict]
    ) -> pd.DataFrame:
        """Builds the final statistics DataFrame from collected rows.

        Args:
            statistics_rows: List of statistics row dicts from each record.

        Returns:
            DataFrame with value mapping statistics, or empty DataFrame with correct columns.
        """
        if statistics_rows:
            return pd.DataFrame(statistics_rows)

        return pd.DataFrame(columns=[
            'record_id', 'source_fields', 'target_fields', 'relation_type',
            'mapping_strategy', 'total_rows', 'mapped_rows', 'unmapped_rows', 'mapping_success_pct',
            'successful_indices', 'unsuccessful_indices',
            'mapped_value_counts', 'unmapped_value_counts',
            'used_mapping_values', 'unused_mapping_values'
        ])
