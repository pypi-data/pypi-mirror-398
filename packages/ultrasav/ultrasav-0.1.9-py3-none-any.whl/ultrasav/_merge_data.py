"""
merge_data.py
Data merging function for ultrasav
Following the dataframe-agnostic architecture using narwhals
"""

import os
import logging
from pathlib import Path
from typing import Any
import narwhals as nw
from narwhals.typing import IntoFrame

# Import read functions
from ._read_files import read_sav, read_csv, read_excel

logger = logging.getLogger(__name__)


def _get_narwhals_dtype(dtype_str: str):
    """
    Map dtype string representation to narwhals dtype object.
    
    Parameters
    ----------
    dtype_str : str
        String representation of the dtype
        
    Returns
    -------
    narwhals dtype or None if unknown
    """
    dtype_map = {
        "String": nw.String,
        "Int64": nw.Int64,
        "Int32": nw.Int32,
        "Int16": nw.Int16,
        "Int8": nw.Int8,
        "Float64": nw.Float64,
        "Float32": nw.Float32,
        "Boolean": nw.Boolean,
        "Datetime": nw.Datetime,
        "Date": nw.Date,
        "Object": nw.Object,
        "Unknown": nw.Unknown,
        # Add more mappings as needed
    }
    
    # Try exact match first
    if dtype_str in dtype_map:
        return dtype_map[dtype_str]
    
    # Handle variations
    if "Utf8" in dtype_str or "str" in dtype_str.lower():
        return nw.String
    if "float" in dtype_str.lower() and "64" in dtype_str:
        return nw.Float64
    if "float" in dtype_str.lower() and "32" in dtype_str:
        return nw.Float32
    if "int" in dtype_str.lower() and "64" in dtype_str:
        return nw.Int64
    if "int" in dtype_str.lower() and "32" in dtype_str:
        return nw.Int32
    
    # Default to String for Unknown/Null
    if dtype_str == "Unknown":
        return nw.String
    
    logger.warning(f"Unknown dtype mapping for '{dtype_str}', defaulting to String")
    return nw.String


def align_schemas(nw_dfs: list) -> list:
    """
    Align schemas across multiple narwhals DataFrames for successful concatenation.
    
    This function harmonizes column types across all dataframes using these rules:
    1. Use df[0] as the baseline schema
    2. If a later df has a new column, append it to the merged schema
    3. If a column is Unknown/Null in merged schema but later appears with real type,
       upgrade to the non-null dtype
    4. For type conflicts, preserve the existing dtype (df[0] wins)
    
    Parameters
    ----------
    nw_dfs : list[narwhals.DataFrame]
        List of narwhals dataframes to align
        
    Returns
    -------
    list[narwhals.DataFrame]
        List of dataframes with aligned schemas
    """
    if not nw_dfs:
        return nw_dfs
    
    if len(nw_dfs) == 1:
        return nw_dfs
    
    # Build the merged schema starting with first dataframe
    merged_schema = {}
    
    for i, df in enumerate(nw_dfs):
        for col_name, dtype in df.schema.items():
            dtype_str = str(dtype)
            
            if col_name not in merged_schema:
                # New column - add to merged schema
                merged_schema[col_name] = dtype_str
                logger.debug(f"Added new column '{col_name}' with type {dtype_str} from df[{i}]")
            
            elif merged_schema[col_name] == "Unknown" and dtype_str != "Unknown":
                # Upgrade from Unknown/Null to real type
                merged_schema[col_name] = dtype_str
                logger.debug(f"Upgraded column '{col_name}' from Unknown to {dtype_str} from df[{i}]")
            
            elif merged_schema[col_name] != dtype_str and dtype_str != "Unknown":
                # Type conflict - log but keep existing (df[0] wins)
                logger.debug(f"Type conflict for column '{col_name}': keeping {merged_schema[col_name]}, ignoring {dtype_str} from df[{i}]")
    
    logger.info(f"Final merged schema: {merged_schema}")
    
    # Now cast all dataframes to match the merged schema
    aligned_dfs = []
    
    for i, df in enumerate(nw_dfs):
        cast_exprs = []
        
        for col_name, target_type_str in merged_schema.items():
            if col_name in df.columns:
                current_type_str = str(df.schema[col_name])
                
                # Only cast if types don't match
                if current_type_str != target_type_str:
                    # Map string type names to narwhals dtypes
                    target_dtype = _get_narwhals_dtype(target_type_str)
                    if target_dtype:
                        cast_exprs.append(nw.col(col_name).cast(target_dtype).alias(col_name))
                        logger.debug(f"df[{i}]: casting column '{col_name}' from {current_type_str} to {target_type_str}")
        
        # Apply casts if needed
        if cast_exprs:
            try:
                df = df.with_columns(cast_exprs)
            except Exception as e:
                error_msg = str(e)
                
                # Check for common type conversion issues and provide helpful guidance
                if "conversion from `str`" in error_msg:
                    # Extract column name from error message if possible
                    import re
                    col_match = re.search(r"column '(\w+)'", error_msg)
                    col_name = col_match.group(1) if col_match else "unknown"
                    
                    # Check if it's likely a date/time column
                    if any(indicator in col_name.lower() for indicator in ['date', 'time', 'timestamp']):
                        raise ValueError(
                            f"\nType casting failed for column '{col_name}'.\n"
                            f"Cannot convert string dates to numeric/datetime format.\n\n"
                            f"The error suggests column '{col_name}' contains date strings that need parsing.\n"
                            f"Please pre-process your data before merging. For example:\n\n"
                            f"  # For date strings like '12/16/2024 10:14':\n"
                            f"  df = df.with_columns(\n"
                            f"      nw.col('{col_name}').str.to_datetime('%m/%d/%Y %H:%M')\n"
                            f"  )\n\n"
                            f"  # Or for other formats:\n"
                            f"  # '%Y-%m-%d %H:%M:%S' for '2024-12-16 10:14:00'\n"
                            f"  # '%d/%m/%Y' for '16/12/2024'\n\n"
                            f"Original error: {error_msg}"
                        ) from e
                    else:
                        # Generic string conversion error
                        raise ValueError(
                            f"\nType casting failed for column '{col_name}'.\n"
                            f"Cannot convert string values to {target_type_str}.\n\n"
                            f"This often happens when:\n"
                            f"  1. String columns contain non-numeric text\n"
                            f"  2. Date/time values are stored as strings\n"
                            f"  3. Numbers have formatting (e.g., '$1,234.56' or '1.234,56')\n\n"
                            f"Please check your data and pre-process if needed.\n"
                            f"Original error: {error_msg}"
                        ) from e
                else:
                    # Re-raise unexpected errors as-is
                    raise
        
        aligned_dfs.append(df)
    
    return aligned_dfs


def _normalize_to_common_backend(nw_dfs: list) -> list:
    """
    Normalize all narwhals dataframes to a common backend using Arrow interchange.
    
    This ensures all dataframes can be concatenated regardless of their original
    backend (pandas, polars, duckdb, ibis, etc.). Uses Arrow as the universal
    interchange format.
    
    Parameters
    ----------
    nw_dfs : list[narwhals.DataFrame]
        List of narwhals dataframes possibly from different backends
        
    Returns
    -------
    list[narwhals.DataFrame]
        List of narwhals dataframes all using the same backend (polars)
    """
    import polars as pl
    import pyarrow as pa
    
    normalized_dfs = []
    
    for i, nw_df in enumerate(nw_dfs):
        # Get the native dataframe
        native_df = nw_df.to_native()
        
        # Check the backend type and convert to arrow
        if isinstance(native_df, pl.DataFrame):
            # Polars to arrow
            arrow_table = native_df.to_arrow()
        elif hasattr(native_df, 'to_arrow'):
            # If it has to_arrow method, use it
            arrow_table = native_df.to_arrow()
        elif hasattr(native_df, '__arrow_c_stream__'):
            # Use Arrow C stream interface if available
            arrow_table = pa.table(native_df)
        else:
            # Fallback: pandas or other - use pyarrow conversion
            try:
                arrow_table = pa.Table.from_pandas(native_df)
            except:
                # Last resort: convert through dict
                data_dict = {}
                for col in native_df.columns:
                    data_dict[col] = native_df[col].tolist() if hasattr(native_df[col], 'tolist') else list(native_df[col])
                arrow_table = pa.Table.from_pydict(data_dict)
        
        # Convert arrow table back to polars (our common backend)
        pl_df = pl.from_arrow(arrow_table)
        
        # Wrap back in narwhals
        normalized_df = nw.from_native(pl_df)
        normalized_dfs.append(normalized_df)
        
        logger.debug(f"Normalized df[{i}] to common backend via Arrow")
    
    return normalized_dfs


def merge_data(
    dfs: list[str | Path | IntoFrame],
    source_col: str = "mrgsrc",
    output_format: str = "polars"
) -> Any:
    """
    Merge multiple dataframes vertically with provenance tracking.
    
    This function performs vertical concatenation of dataframes while adding a 
    provenance column to track the source of each row. It follows tidyspss's 
    dataframe-agnostic design by using narwhals for all processing, only
    converting to the desired format at the final step.
    
    The function uses Arrow as a universal interchange format to ensure
    compatibility between different dataframe backends (pandas, polars, duckdb,
    ibis, etc.) before concatenation.
    
    Parameters
    ----------
    dfs : list[str | Path | IntoFrame]
        List of inputs to merge. Each element can be:
        - File path (str or Path) to a SAV, CSV, or Excel file
        - A dataframe (pandas, polars, or any narwhals-supported format)
        Mixed lists are supported (e.g., [df1, "file.sav", df2])
    source_col : str, default "mrgsrc"
        Name of the provenance column to add. This column will contain:
        - For file paths: the base filename (e.g., "survey_2024.sav")
        - For dataframes: "source_1", "source_2", etc.
    output_format : str, default "polars"
        Output dataframe format: "pandas", "polars", or "narwhals"
        
    Returns
    -------
    DataFrame
        Merged dataframe in the specified format with the provenance column added.
        Uses narwhals.concat with how="diagonal" for column union behavior.
        
    Notes
    -----
    - The function uses diagonal concatenation, which means dataframes with 
      different columns can be stacked (missing columns filled with nulls)
    - The provenance column is added as the last column in the result
    - All merging happens in narwhals format for consistency, then converts
      to the requested output format at the end
    - The provenance column is always string type
    - Schemas are automatically aligned across all dataframes before merging
    - Mixed backend dataframes are normalized through Arrow interchange protocol
    
    Type Casting Behavior
    ---------------------
    When columns exist in multiple dataframes with different types, the function
    attempts to cast them to a common type (first dataframe's type takes precedence).
    
    **Important**: Type casting assumes compatible formats. The function cannot
    automatically convert between incompatible formats such as:
    - String dates (e.g., "12/16/2024 10:14") to numeric/datetime
    - Formatted numbers (e.g., "$1,234.56") to numeric
    - Text booleans (e.g., "Yes"/"No") to boolean
    
    For these cases, pre-process your data before merging:
    ```python
    # Convert string dates to datetime
    df = df.with_columns(
        nw.col('date').str.to_datetime('%m/%d/%Y %H:%M')
    )
    
    # Clean formatted numbers
    df = df.with_columns(
        nw.col('amount').str.replace('[$,]', '').cast(nw.Float64)
    )
    ```
    
    The function will raise a helpful error message if type casting fails,
    indicating which column failed and suggesting how to fix it.
    
    Examples
    --------
    >>> # Merge multiple SAV files
    >>> merged = merge_data(["file1.sav", "file2.sav", "file3.sav"])
    
    >>> # Mix dataframes from different backends
    >>> import pandas as pd
    >>> import polars as pl
    >>> df_pd = pd.DataFrame({'Q1': [1, 2, 3]})
    >>> df_pl = pl.DataFrame({'Q2': [4, 5, 6]})
    >>> merged = merge_data([df_pd, df_pl])
    
    >>> # Handle date format issues
    >>> # If you get a type casting error for date columns:
    >>> df = df.with_columns(
    ...     nw.col('date').str.to_datetime('%m/%d/%Y %H:%M')
    ... )
    >>> merged = merge_data([df, other_df])
    
    >>> # Custom provenance column name and output format
    >>> merged = merge_data(dfs_list, source_col="file_source", output_format="pandas")
    """
    if not dfs:
        raise ValueError("dfs list cannot be empty")
    
    if output_format not in ["pandas", "polars", "narwhals"]:
        raise ValueError(f"output_format must be 'pandas', 'polars', or 'narwhals', got {output_format}")
    
    
    # Prepare list of narwhals dataframes WITHOUT provenance column first
    nw_dfs = []
    source_names = []  # Keep track of source names for each df
    df_counter = 0
    
    for item in dfs:
        # Determine if item is a file path or dataframe
        if isinstance(item, (str, Path)):
            # It's a file path
            file_path = Path(item)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine file type and read appropriately
            ext = file_path.suffix.lower()
            source_name = file_path.name  # Use base filename for provenance
            
            # Read file based on extension (use narwhals format for consistency)
            if ext in ['.sav', '.zsav']:
                df, _ = read_sav(file_path, output_format="narwhals")
                nw_df = df  # Already in narwhals format
            elif ext == '.csv':
                nw_df = read_csv(file_path, output_format="narwhals")
            elif ext in ['.xlsx', '.xls', '.xlsm', '.xlsb', '.ods']:
                nw_df = read_excel(file_path, output_format="narwhals")
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            
        else:
            # It's a dataframe - convert to narwhals
            nw_df = nw.from_native(item)
            df_counter += 1
            source_name = f"source_{df_counter}"
        
        # Store the dataframe and its source name
        nw_dfs.append(nw_df)
        source_names.append(source_name)
        
        logger.info(f"Added dataframe from {source_name} with shape {nw_df.shape}")
    
    # Normalize all dataframes to common backend through Arrow
    logger.info("Normalizing dataframes to common backend via Arrow interchange...")
    normalized_dfs = _normalize_to_common_backend(nw_dfs)
    
    # Align schemas across all dataframes before concatenation
    logger.info("Aligning schemas across all dataframes...")
    aligned_dfs = align_schemas(normalized_dfs)
    
    # Add source column to each aligned dataframe
    dfs_with_source = []
    for df, source_name in zip(aligned_dfs, source_names):
        df_with_source = df.with_columns(
            nw.lit(source_name).alias(source_col)
        )
        dfs_with_source.append(df_with_source)
    
    # Now all dataframes have the same backend and aligned schemas
    # Concatenate all dataframes with diagonal union in narwhals
    merged_nw = nw.concat(dfs_with_source, how="diagonal")
    
    # Move source column to the end if it's not already there
    cols = list(merged_nw.columns)
    if source_col in cols and cols[-1] != source_col:
        cols.remove(source_col)
        cols.append(source_col)
        merged_nw = merged_nw.select(cols)
    
    logger.info(f"Merged {len(dfs)} dataframes into shape {merged_nw.shape}")
    
    # Convert to requested output format using narwhals built-in methods
    if output_format == "narwhals":
        return merged_nw
    elif output_format == "polars":
        return merged_nw.to_polars()
    elif output_format == "pandas":
        return merged_nw.to_pandas()
    
    # Should not reach here due to earlier validation
    return merged_nw
