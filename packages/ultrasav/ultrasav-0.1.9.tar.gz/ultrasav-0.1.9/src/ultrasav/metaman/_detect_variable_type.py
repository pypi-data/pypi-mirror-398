"""
Multi-Select Variable Detection Algorithm v3
===========================================

Returns one of:
- 'multi-select'
- 'single-select'
- 'numeric'
- 'text'
- 'date'

New in v3:
- Centralized MR set lookup via create_mr_set_lookup
- Safer binary detection (fixed operator precedence)
- Optional unique_value_map for performance
- Optional strict_multi flag to control how aggressive multi-select detection is
- Optional explain flag to return (var_type, reason) instead of just var_type
- Removed ALLOWED_EXTRA_MULTI_CODES filtering - actual data values are checked as-is
"""

import narwhals as nw
from narwhals.typing import FrameT
import polars as pl
import pandas as pd
from typing import Any
import re

# ---------------------------------------------------------------------------
# Configurable "magic" lists and patterns
# ---------------------------------------------------------------------------

SELECTION_PAIRS = [
    ("not selected", "selected"),
    ("unchecked", "checked"),
    ("no", "yes"),
    ("0", "1"),
    ("not mentioned", "mentioned"),
    ("not chosen", "chosen"),
    ("exclude", "include"),
]

GENERIC_BINARY_LABELS = [
    ("no", "yes"),
    ("false", "true"),
    ("disagree", "agree"),
    ("male", "female"),
    ("off", "on"),
    ("absent", "present"),
]

MULTI_SELECT_NAME_PATTERNS = [
    r"[_\-]?\d+$",        # ends with number
    r"Q\d+[A-Z]$",        # Q1A pattern
    r"r\d+$",             # r1 pattern
    r"_[A-Z]$",           # _A pattern
    r"[A-Z]\d+[A-Z]\d+$", # A1B1 pattern
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_mr_set_lookup(meta) -> set[str]:
    """
    Create a set of all variables that belong to multi-response sets.
    
    Parameters
    ----------
    meta : pyreadstat metadata object
    
    Returns
    -------
    set[str]
        Set of variable names that are part of multi-response sets.
    """
    mr_set_variables: set[str] = set()
    
    if hasattr(meta, "mr_sets") and meta.mr_sets:
        for mr_set_name, mr_set_info in meta.mr_sets.items():
            if "variable_list" in mr_set_info:
                mr_set_variables.update(mr_set_info["variable_list"])
    
    return mr_set_variables


def _normalize_value_keys(keys: set[Any]) -> set[Any]:
    """
    Normalize value label keys so that 0/1, 0.0/1.0, and "0"/"1" all map to ints.
    Other keys are left as-is.
    """
    normalized: set[Any] = set()
    for k in keys:
        if isinstance(k, (int, float)) and k in [0, 1, 0.0, 1.0]:
            normalized.add(int(k))
        elif isinstance(k, str) and k in {"0", "1"}:
            normalized.add(int(k))
        else:
            normalized.add(k)
    return normalized


def _is_binary_value_dict(value_dict: dict[Any, str]) -> bool:
    """
    Check if a value label dict represents a 0/1 binary variable.
    """
    if len(value_dict) != 2:
        return False
    keys = set(value_dict.keys())
    normalized = _normalize_value_keys(keys)
    return normalized <= {0, 1}


def _labels_lower_pair(value_dict: dict[Any, str]) -> tuple[str, str]:
    """
    Get labels for 0 and 1 (or their float/string equivalents), lowercased and stripped.
    """
    label_0 = str(
        value_dict.get(0, value_dict.get(0.0, value_dict.get("0", "")))
    ).lower().strip()
    label_1 = str(
        value_dict.get(1, value_dict.get(1.0, value_dict.get("1", "")))
    ).lower().strip()
    return label_0, label_1


def _is_generic_binary_labels(label_0: str, label_1: str) -> bool:
    """
    Check if a (label_0, label_1) pair matches generic binary patterns
    like (no, yes), (false, true), (male, female), etc.
    """
    labels_set_lower = {label_0.lower(), label_1.lower()}
    for pair in GENERIC_BINARY_LABELS:
        if labels_set_lower == {p.lower() for p in pair}:
            return True
    return False


def _get_sibling_vars(meta, var_name: str) -> list[str]:
    """
    Find variables that share the same base as var_name (e.g. Q4A, Q4B...).
    """
    base_match = re.match(r"(.+?)([A-Z]|\d+)$", var_name, re.IGNORECASE)
    if not base_match:
        return []
    base = base_match.group(1)
    return [
        v for v in getattr(meta, "column_names", [])
        if v.startswith(base) and v != var_name
    ]


def _match_multi_name_pattern(var_name: str) -> bool:
    """
    Check if variable name matches any multi-select-like naming patterns.
    """
    for pattern in MULTI_SELECT_NAME_PATTERNS:
        if re.search(pattern, var_name, re.IGNORECASE):
            return True
    return False


def _get_unique_values_for_var(
    df: FrameT,
    var_name: str,
    unique_value_map: dict[str, set[Any]] | None = None,
) -> set[Any]:
    """
    Get unique values for a variable, using an optional precomputed map
    to avoid recomputing on every call.
    """
    if unique_value_map is not None and var_name in unique_value_map:
        return unique_value_map[var_name]

    df_nw = nw.from_native(df)
    unique_vals_df = df_nw.select(nw.col(var_name)).unique()
    unique_vals_native = nw.to_native(unique_vals_df)

    if isinstance(unique_vals_native, pl.DataFrame):
        unique_set = set(unique_vals_native[var_name].to_list())
    else:  # pandas
        unique_set = set(unique_vals_native[var_name].tolist())

    if unique_value_map is not None:
        unique_value_map[var_name] = unique_set

    return unique_set


# ---------------------------------------------------------------------------
# Main detection function
# ---------------------------------------------------------------------------

def detect_variable_type(
    var_name: str,
    meta,
    mr_set_variables: set[str] | None = None,
    df: FrameT | None = None,
    *,
    unique_value_map: dict[str, set[Any]] | None = None,
    strict_multi: bool = True,
    explain: bool = False,
):
    """
    Detect the type of a variable: single-select, multi-select, numeric, text, or date.

    Parameters
    ----------
    var_name : str
        The variable name to classify.
    meta : pyreadstat metadata object
        The metadata object from pyreadstat.
    mr_set_variables : set[str] | None
        Pre-computed set of all variables that are part of multi-response sets.
        If None, it will be computed via create_mr_set_lookup(meta).
    df : FrameT | None
        Optional dataframe for data-based type detection.
    unique_value_map : dict[str, set[Any]] | None, keyword-only
        Optional precomputed map of column -> unique values set, for performance.
    strict_multi : bool, keyword-only
        If True (default), require metadata evidence, series evidence, OR 
        unlabeled variable status before using data patterns to classify as multi-select.
        If False, any variable with matching 0/1 data pattern can be classified as multi-select.
    explain : bool, keyword-only
        If False (default), return only the type string.
        If True, return a tuple: (type_str, reason_str).

    Returns
    -------
    str or (str, str)
        If explain=False: one of 'multi-select', 'single-select', 'numeric', 'text', 'date'.
        If explain=True: (type_str, reason_str).
    """

    def _ret(type_str: str, reason: str):
        return (type_str, reason) if explain else type_str

    # Build the mr_set_variables if not provided
    if mr_set_variables is None:
        mr_set_variables = create_mr_set_lookup(meta)

    # Get variable value labels if available
    variable_value_labels: dict[str, dict[Any, str]] = (
        meta.variable_value_labels if hasattr(meta, "variable_value_labels") else {}
    )

    # Get readstat variable types
    readstat_types: dict[str, str] = (
        meta.readstat_variable_types if hasattr(meta, "readstat_variable_types") else {}
    )
    var_type: str | None = readstat_types.get(var_name, None)

    # Get original variable types (SPSS format types)
    original_types: dict[str, str] = (
        meta.original_variable_types if hasattr(meta, "original_variable_types") else {}
    )
    original_type: str = original_types.get(var_name, "")

    # Get variable measure (SPSS measurement level)
    variable_measure: dict[str, str] = (
        meta.variable_measure if hasattr(meta, "variable_measure") else {}
    )
    measure: str = variable_measure.get(var_name, "unknown")

    # ------------------------------------------------------------------------
    # STEP 1: String/Text Check (highest priority)
    # ------------------------------------------------------------------------
    if var_type == "string":
        return _ret("text", "STEP 1: readstat type is 'string'")

    # ------------------------------------------------------------------------
    # STEP 2: SPSS Multi-Response Set Check
    # ------------------------------------------------------------------------
    if var_name in mr_set_variables:
        return _ret("multi-select", "STEP 2: variable is in meta.mr_sets")

    # ------------------------------------------------------------------------
    # STEP 3: DataFrame-based Detection with Metadata Gating
    # ------------------------------------------------------------------------
    if df is not None:
        try:
            metadata_confirms_01_coding = False
            series_confirms_01_coding = False

            if var_name in variable_value_labels:
                keys = set(variable_value_labels[var_name].keys())
                normalized_keys = _normalize_value_keys(keys)
                if normalized_keys <= {0, 1}:
                    metadata_confirms_01_coding = True

            if not metadata_confirms_01_coding:
                # Check series context
                sibling_vars = _get_sibling_vars(meta, var_name)
                if len(sibling_vars) >= 2:
                    siblings_with_01_coding = 0
                    for sibling_var in sibling_vars[:5]:
                        if sibling_var in variable_value_labels:
                            sibling_keys = set(variable_value_labels[sibling_var].keys())
                            sibling_norm = _normalize_value_keys(sibling_keys)
                            if sibling_norm <= {0, 1}:
                                siblings_with_01_coding += 1
                    if siblings_with_01_coding >= 2:
                        series_confirms_01_coding = True

            df_nw = nw.from_native(df)
            schema = df_nw.schema

            # Only attempt df-based pattern check on non-string columns
            if schema.get(var_name) != nw.String:
                unique_set = _get_unique_values_for_var(
                    df=df,
                    var_name=var_name,
                    unique_value_map=unique_value_map,
                )
                # Remove nulls
                unique_set_no_null = {
                    v
                    for v in unique_set
                    if v is not None and not (isinstance(v, float) and pd.isna(v))
                }

                # Multi-select patterns (with both int and float variants)
                multi_select_patterns = [
                    {0, 1},
                    {0.0, 1.0},
                    {1},
                    {1.0},
                    {0},
                    {0.0},
                ]

                # Check actual data values as-is (no filtering)
                pattern_match = unique_set_no_null in multi_select_patterns

                # Gating logic:
                # - metadata_confirms_01_coding: variable's own labels use 0/1 coding
                # - series_confirms_01_coding: sibling variables use 0/1 coding
                # - var_name not in variable_value_labels: unlabeled variables always proceed
                #   (unlabeled 0/1 binary indicators are likely multi-select)
                # - strict_multi=False: allows labeled variables without 0/1 evidence to proceed
                gated_ok = (
                    metadata_confirms_01_coding
                    or series_confirms_01_coding
                    or var_name not in variable_value_labels
                    or not strict_multi
                )

                if gated_ok and pattern_match:
                    reason_parts = []
                    if metadata_confirms_01_coding:
                        reason_parts.append("metadata confirms 0/1 coding")
                    if series_confirms_01_coding:
                        reason_parts.append("series context confirms 0/1 coding")
                    if var_name not in variable_value_labels:
                        reason_parts.append("unlabeled variable")
                    if not strict_multi:
                        reason_parts.append("strict_multi=False")
                    
                    return _ret(
                        "multi-select",
                        f"STEP 3: df values match 0/1 multi-select pattern ({', '.join(reason_parts)})",
                    )
        except Exception:
            # Any error in df logic -> fall back to meta-based detection
            pass

    # ------------------------------------------------------------------------
    # STEP 4: Date/DateTime Check
    # ------------------------------------------------------------------------
    if isinstance(original_type, str) and (
        "DATETIME" in original_type.upper()
        or "DATE" in original_type.upper()
        or "TIME" in original_type.upper()
    ):
        return _ret("date", "STEP 4: original SPSS type is date/time/datetime")

    # ------------------------------------------------------------------------
    # STEP 5: Value Label Analysis (for categorical variables)
    # ------------------------------------------------------------------------
    has_value_labels: bool = (
        var_name in variable_value_labels and bool(variable_value_labels[var_name])
    )

    if has_value_labels:
        value_dict: dict[Any, str] = variable_value_labels[var_name]

        is_binary: bool = _is_binary_value_dict(value_dict)

        if is_binary:
            # TIER 2: Label analysis
            label_0, label_1 = _labels_lower_pair(value_dict)

            if (not label_0 or label_0 in ["null", "none", "not selected", ""]):
                # The "1" label is the actual option text
                if label_1 and label_1 not in ["yes", "selected", "true", "1"]:
                    return _ret(
                        "multi-select",
                        "STEP 5 TIER 2: 0 label empty/null, 1 label descriptive",
                    )

            # TIER 3: Selection pair labels + variable naming patterns
            labels_set_lower = {label_0, label_1}
            for pair in SELECTION_PAIRS:
                if labels_set_lower == {p.lower() for p in pair}:
                    if _match_multi_name_pattern(var_name):
                        return _ret(
                            "multi-select",
                            "STEP 5 TIER 3: selection pair labels + multi-select name pattern",
                        )

            # TIER 3b: series context (all binary siblings)
            sibling_vars = _get_sibling_vars(meta, var_name)
            if len(sibling_vars) >= 2:
                all_binary = True
                for similar_var in sibling_vars[:3]:
                    if similar_var in variable_value_labels:
                        similar_dict = variable_value_labels[similar_var]
                        if not _is_binary_value_dict(similar_dict):
                            all_binary = False
                            break
                if all_binary:
                    return _ret(
                        "multi-select",
                        "STEP 5 TIER 3b: part of binary-coded series",
                    )

            # TIER 4: generic binary (yes/no, male/female, etc.) -> single-select
            if _is_generic_binary_labels(label_0, label_1):
                return _ret(
                    "single-select",
                    "STEP 5 TIER 4: generic binary labels (yes/no, etc.)",
                )

        # Non-binary categorical -> single-select
        return _ret("single-select", "STEP 5: non-binary categorical with value labels")

    # ------------------------------------------------------------------------
    # STEP 6: Numeric Type Fallback
    # ------------------------------------------------------------------------
    if var_type in ["double", "numeric", "integer", "long"]:
        return _ret("numeric", "STEP 6: numeric readstat type without value labels")

    # ------------------------------------------------------------------------
    # STEP 7: Measurement Level Fallback
    # ------------------------------------------------------------------------
    if measure == "scale":
        return _ret("numeric", "STEP 7: measurement level 'scale'")
    elif measure in ["nominal", "ordinal"]:
        return _ret("single-select", "STEP 7: measurement level nominal/ordinal")

    # ------------------------------------------------------------------------
    # STEP 8: Final Fallback
    # ------------------------------------------------------------------------
    return _ret("numeric", "STEP 8: final fallback to numeric")
