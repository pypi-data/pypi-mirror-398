import narwhals as nw
from narwhals.typing import FrameT
import polars as pl
import pandas as pd
from typing import Any
from ._detect_variable_type import detect_variable_type, create_mr_set_lookup
# version_9

def precompute_value_maps(
    df: FrameT,
) -> tuple[
    dict[str, dict[Any, int]],
    dict[str, int],
    dict[str, int],
    dict[str, set[Any]],
]:
    """
    Precompute value counts, null counts, non-null counts, and unique values
    for each column in the dataframe.

    Hybrid design:
    - If the underlying native frame is Polars or Pandas, use an optimized
      backend-specific implementation (_precompute_value_maps_native).
    - Otherwise, fall back to a generic Narwhals-based implementation
      (_precompute_value_maps_narwhals), which should still be efficient and
      automatically benefit from fast backends like Polars.

    Parameters
    ----------
    df : FrameT
        Any Narwhals-compatible dataframe (Polars, Pandas, etc).

    Returns
    -------
    value_counts_map : dict[str, dict[Any, int]]
        For each column, a dict of {value -> count} (excluding nulls).
    null_count_map : dict[str, int]
        For each column, the count of null values.
    non_null_count_map : dict[str, int]
        For each column, the count of non-null values.
    unique_value_map : dict[str, set[Any]]
        For each column, the set of unique non-null values.
        This map is what you pass into detect_variable_type to avoid
        recomputing uniques.
    """
    # Normalize to a Narwhals frame
    df_nw = nw.from_native(df)
    native = nw.to_native(df_nw)

    # Fast path for Polars / Pandas
    if isinstance(native, pl.DataFrame) or isinstance(native, pd.DataFrame):
        return _precompute_value_maps_native(native)

    # Generic Narwhals path (for other backends)
    return _precompute_value_maps_narwhals(df_nw)


def _precompute_value_maps_native(
    df_native: pl.DataFrame | pd.DataFrame,
) -> tuple[
    dict[str, dict[Any, int]],
    dict[str, int],
    dict[str, int],
    dict[str, set[Any]],
]:
    """
    Backend-specific fast implementation for Polars and Pandas.

    For string/text columns, empty strings "" are treated as missing (like nulls).
    Whitespace-only strings are treated as valid non-missing data.
    """
    value_counts_map: dict[str, dict[Any, int]] = {}
    null_count_map: dict[str, int] = {}
    non_null_count_map: dict[str, int] = {}
    unique_value_map: dict[str, set[Any]] = {}

    if isinstance(df_native, pl.DataFrame):
        for col in df_native.columns:
            s = df_native[col]

            # Check if column is string type
            is_string_col = s.dtype == pl.Utf8 or s.dtype == pl.String

            if is_string_col:
                # For string columns: treat nulls AND empty strings as missing
                actual_null_count = int(s.null_count())

                # Count empty strings (only exact "", not whitespace)
                empty_string_count = int(
                    s.drop_nulls().eq("").sum()
                )

                # Total "missing" = nulls + empty strings
                null_count_map[col] = actual_null_count + empty_string_count

                # Value counts for non-null, non-empty values
                s_valid = s.filter(s.is_not_null() & (s != ""))

                if s_valid.len() > 0:
                    vc_df = s_valid.value_counts()
                    cols = vc_df.columns
                    value_col = cols[0]
                    count_col = cols[1] if len(cols) > 1 else None

                    values = vc_df[value_col].to_list()
                    counts = vc_df[count_col].to_list() if count_col else [1] * len(values)
                    vc_dict = dict(zip(values, counts))
                else:
                    values = []
                    counts = []
                    vc_dict = {}

                value_counts_map[col] = vc_dict
                unique_value_map[col] = set(values)
                non_null_count_map[col] = int(sum(counts))

            else:
                # Non-string columns: original logic
                null_count = int(s.null_count())
                null_count_map[col] = null_count

                vc_df = s.drop_nulls().value_counts()
                if vc_df.height > 0:
                    cols = vc_df.columns
                    value_col = cols[0]
                    count_col = cols[1] if len(cols) > 1 else None

                    values = vc_df[value_col].to_list()
                    counts = vc_df[count_col].to_list() if count_col else [1] * len(values)
                    vc_dict = dict(zip(values, counts))
                else:
                    values = []
                    counts = []
                    vc_dict = {}

                value_counts_map[col] = vc_dict
                unique_value_map[col] = set(values)
                non_null_count_map[col] = int(sum(counts))

    elif isinstance(df_native, pd.DataFrame):
        for col in df_native.columns:
            s = df_native[col]

            # Check if column is string/object type
            is_string_col = s.dtype == "object" or pd.api.types.is_string_dtype(s)

            if is_string_col:
                # For string columns: treat nulls AND empty strings as missing
                actual_null_count = int(s.isna().sum())

                # Count empty strings (only exact "", not whitespace)
                non_null_mask = s.notna()
                empty_string_count = int((s[non_null_mask] == "").sum())

                null_count_map[col] = actual_null_count + empty_string_count

                # Value counts for non-null, non-empty values
                valid_mask = non_null_mask & (s != "")
                s_valid = s[valid_mask]

                vc = s_valid.value_counts(dropna=True)
                vc_dict = vc.to_dict()
                value_counts_map[col] = vc_dict
                unique_value_map[col] = set(vc.index.tolist())
                non_null_count_map[col] = int(vc.sum())

            else:
                # Non-string columns: original logic
                null_count = int(s.isna().sum())
                null_count_map[col] = null_count

                vc = s.value_counts(dropna=True)
                vc_dict = vc.to_dict()
                value_counts_map[col] = vc_dict
                unique_value_map[col] = set(vc.index.tolist())
                non_null_count_map[col] = int(vc.sum())
    else:
        raise ValueError(f"Unsupported native dataframe type: {type(df_native)}")

    return value_counts_map, null_count_map, non_null_count_map, unique_value_map


def _precompute_value_maps_narwhals(
    df_nw: FrameT,
) -> tuple[
    dict[str, dict[Any, int]],
    dict[str, int],
    dict[str, int],
    dict[str, set[Any]],
]:
    """
    Generic Narwhals implementation.

    For string/text columns, empty strings "" are treated as missing (like nulls).
    Whitespace-only strings are treated as valid non-missing data.
    """
    value_counts_map: dict[str, dict[Any, int]] = {}
    null_count_map: dict[str, int] = {}
    non_null_count_map: dict[str, int] = {}
    unique_value_map: dict[str, set[Any]] = {}

    schema = df_nw.schema  # dict-like: {column_name: dtype}

    for col in schema.keys():
        col_expr = nw.col(col)
        col_dtype = schema[col]

        # Check if column is string type
        is_string_col = col_dtype == nw.String

        if is_string_col:
            # For string columns: treat nulls AND empty strings as missing
            
            # Count actual nulls
            actual_null_count = int(
                df_nw.select(col_expr.is_null().sum().alias("n_null")).item(0, "n_null")
            )

            # Count empty strings (only exact "", not whitespace)
            empty_string_count = int(
                df_nw.filter(~col_expr.is_null())
                .select((col_expr == "").sum().alias("n_empty"))
                .item(0, "n_empty")
            )

            null_count_map[col] = actual_null_count + empty_string_count

            # Value counts for non-null, non-empty values
            vc_nw = (
                df_nw.filter(~col_expr.is_null() & (col_expr != ""))
                .select(col_expr.alias(col))
                .group_by(col)
                .agg(nw.col(col).count().alias("count"))
            )

            vc_native = nw.to_native(vc_nw)

            if isinstance(vc_native, pl.DataFrame):
                values = vc_native[col].to_list()
                counts = vc_native["count"].to_list()
            else:  # assume pandas-like
                values = vc_native[col].tolist()
                counts = vc_native["count"].tolist()

            vc_dict = dict(zip(values, counts))
            value_counts_map[col] = vc_dict
            unique_value_map[col] = set(values)
            non_null_count_map[col] = int(sum(counts))

        else:
            # Non-string columns: original logic
            null_count = int(
                df_nw.select(col_expr.is_null().sum().alias("n_null")).item(0, "n_null")
            )
            null_count_map[col] = null_count

            vc_nw = (
                df_nw.filter(~col_expr.is_null())
                .select(col_expr.alias(col))
                .group_by(col)
                .agg(nw.col(col).count().alias("count"))
            )

            vc_native = nw.to_native(vc_nw)

            if isinstance(vc_native, pl.DataFrame):
                values = vc_native[col].to_list()
                counts = vc_native["count"].to_list()
            else:  # assume pandas-like
                values = vc_native[col].tolist()
                counts = vc_native["count"].tolist()

            vc_dict = dict(zip(values, counts))
            value_counts_map[col] = vc_dict
            unique_value_map[col] = set(values)
            non_null_count_map[col] = int(sum(counts))

    return value_counts_map, null_count_map, non_null_count_map, unique_value_map


def merge_meta_and_actual_values(
    meta_values: dict[Any, str],
    actual_value_counts: dict[Any, int]
) -> list[tuple[Any, Any, int, bool]]:
    """
    Merge meta value labels with actual values found in data.
    Insert unlabeled values in proper numeric/string order.

    Parameters
    ----------
    meta_values : dict[Any, str]
        Value labels from meta (code -> label).
    actual_value_counts : dict[Any, int]
        Actual values and their counts from data.

    Returns
    -------
    list[tuple[Any, Any, int, bool]]
        List of (value_code, value_label, count, is_missing_label),
        sorted by value_code.

    Notes
    -----
    - All values in meta_values are included (even if count=0) for integrity.
    - Values in actual data but not in meta are also included (unlabeled values).
    """
    result: list[tuple[Any, Any, int, bool]] = []

    # All codes from meta + actual data
    all_codes: set[Any] = set(meta_values.keys()) | set(actual_value_counts.keys())

    # Sort codes robustly (mixed types handled via (type_name, str(value)))
    try:
        sorted_codes = sorted(all_codes)
    except TypeError:
        sorted_codes = sorted(all_codes, key=lambda x: (type(x).__name__, str(x)))

    for code in sorted_codes:
        if code in meta_values or code in actual_value_counts:
            label: str | None = meta_values.get(code, None)
            count: int = actual_value_counts.get(code, 0)
            is_missing_label: bool = code not in meta_values
            result.append((code, label, count, is_missing_label))

    return result

def map_engine(
    df: pl.DataFrame | pd.DataFrame,
    meta,
    output_format: str | None = None
) -> pl.DataFrame | pd.DataFrame:
    """
    Create a data validation core map from dataframe and pyreadstat meta object.

    This function serves as the core map engine that analyzes both metadata and
    actual data to produce a comprehensive mapping for data validation and analysis.

    It identifies:
    - Missing data (nulls)
    - Unlabeled values (values in data but not in meta)
    - Value distributions (counts for each value)

    Parameters
    ----------
    df : pl.DataFrame | pd.DataFrame
        The data dataframe (Polars or Pandas).
    meta : pyreadstat metadata object
        The metadata object returned by pyreadstat when reading SPSS files.
    output_format : str | None
        Output format - either "polars" or "pandas".
        If None, will match the input dataframe type.

    Returns
    -------
    pl.DataFrame | pd.DataFrame
        A dataframe with columns:
        - variable: variable name
        - variable_label: variable label text from meta
        - variable_type: variable type (single-select, multi-select, numeric, text, date)
        - value_code: value code (None for missing-data row, codes for categories)
        - value_label: value label ("NULL" for missing-data row, labels or None for unlabeled)
        - value_n: count of occurrences
    """

    # Determine output format
    if output_format is None:
        if isinstance(df, pl.DataFrame):
            output_format = "polars"
        elif isinstance(df, pd.DataFrame):
            output_format = "pandas"
        else:
            raise ValueError(f"Unsupported dataframe type: {type(df)}")

    if output_format not in {"polars", "pandas"}:
        raise ValueError(f"output_format must be 'polars' or 'pandas', got '{output_format}'")

    # Precompute MR set variables for efficiency
    mr_set_variables: set[str] = create_mr_set_lookup(meta)

    # Precompute value counts, null counts, non-null counts, and unique sets
    (
        value_counts_map,
        null_count_map,
        non_null_count_map,
        unique_value_map,
    ) = precompute_value_maps(df)

    # Initialize lists to store final map rows
    variables: list[str] = []
    variable_labels: list[str] = []
    variable_types: list[str] = []
    value_codes: list[Any] = []
    value_labels: list[Any] = []
    value_ns: list[int] = []

    # Meta helpers
    col_names_to_labels: dict[str, str] = meta.column_names_to_labels
    variable_value_labels: dict[str, dict[Any, str]] = (
        meta.variable_value_labels if hasattr(meta, "variable_value_labels") else {}
    )

    # Iterate through variables defined in meta
    for var_name in meta.column_names:
        # Variable label
        variable_label: str = col_names_to_labels.get(var_name, "")

        # Detect variable type using cached uniques
        var_type: str = detect_variable_type(
            var_name,
            meta,
            mr_set_variables=mr_set_variables,
            df=df,
            unique_value_map=unique_value_map,
        )

        # Pull precomputed counts
        value_count_dict: dict[Any, int] = value_counts_map.get(var_name, {})
        null_count: int = null_count_map.get(var_name, 0)
        non_null_count: int = non_null_count_map.get(var_name, 0)

        is_categorical: bool = var_type in ["single-select", "multi-select"]

        # STEP 1: Add missing data row if nulls exist
        if null_count > 0:
            variables.append(var_name)
            variable_labels.append(variable_label)
            variable_types.append(var_type)
            value_codes.append(None)
            value_labels.append("NULL")
            value_ns.append(null_count)

        # STEP 2: Categorical vs non-categorical handling
        if is_categorical:
            # Meta value labels for this variable
            meta_values: dict[Any, str] = variable_value_labels.get(var_name, {})

            # Merge meta and actual values
            merged_values = merge_meta_and_actual_values(meta_values, value_count_dict)

            for code, label, count, _is_missing_label in merged_values:
                variables.append(var_name)
                variable_labels.append(variable_label)
                variable_types.append(var_type)
                value_codes.append(code)
                value_labels.append(label)
                value_ns.append(count)
        else:
            # Non-categorical (numeric, text, date)
            if non_null_count > 0:
                variables.append(var_name)
                variable_labels.append(variable_label)
                variable_types.append(var_type)
                value_codes.append(None)
                value_labels.append(None)
                value_ns.append(non_null_count)

    # Build final core map dataframe
    if output_format == "polars":
        # Decide dtype for value_code column based on non-None codes
        non_none_codes = [v for v in value_codes if v is not None]

        if non_none_codes:
            try:
                numeric_values = [float(v) for v in non_none_codes]
                if all(v.is_integer() for v in numeric_values):
                    value_code_dtype = pl.Int64
                    value_codes_typed = [
                        int(float(v)) if v is not None else None for v in value_codes
                    ]
                else:
                    value_code_dtype = pl.Float64
                    value_codes_typed = [
                        float(v) if v is not None else None for v in value_codes
                    ]
            except (ValueError, TypeError):
                value_code_dtype = pl.Utf8
                value_codes_typed = [
                    str(v) if v is not None else None for v in value_codes
                ]
        else:
            value_code_dtype = pl.Float64
            value_codes_typed = value_codes

        core_map = pl.DataFrame(
            {
                "variable": variables,
                "variable_label": variable_labels,
                "variable_type": variable_types,
                "value_code": pl.Series(value_codes_typed, dtype=value_code_dtype),
                "value_label": value_labels,
                "value_n": value_ns,
            }
        )
    else:  # "pandas"
        core_map = pd.DataFrame(
            {
                "variable": variables,
                "variable_label": variable_labels,
                "variable_type": variable_types,
                "value_code": value_codes,
                "value_label": value_labels,
                "value_n": value_ns,
            }
        )

    return core_map


# Example usage:
if __name__ == "__main__":
    import pyreadstat

    # Read SPSS file as Polars or Pandas (pyreadstat gives Pandas by default)
    df_pd, meta = pyreadstat.read_sav("your_file.sav", user_missing=True)

    # If you prefer Polars:
    df_pl = pl.from_pandas(df_pd)

    # Create core map (Polars)
    core_map_pl = map_engine(df_pl, meta)
    print(core_map_pl.head())

    # Save to files
    core_map_pl.write_excel("data_core_map_polars.xlsx")
    core_map_pl.write_csv("data_core_map_polars.csv")

    # Or explicitly ask for Pandas output
    core_map_pd = map_engine(df_pl, meta, output_format="pandas")
    core_map_pd.to_excel("data_core_map_pandas.xlsx", index=False)
