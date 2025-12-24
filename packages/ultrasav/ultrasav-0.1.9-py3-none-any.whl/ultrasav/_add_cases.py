"""
add_cases.py
Top-level function for merging SAV files or dataframes with metadata
Following tidyspss 2.0's two-track architecture
"""

import logging
from pathlib import Path
from typing import Any
from narwhals.typing import IntoFrame

from ._merge_data import merge_data
from ._merge_meta import merge_meta
from ._read_files import read_sav, read_csv, read_excel
from ._metadata import Metadata
    

logger = logging.getLogger(__name__)


def add_cases(
    # inputs: list[str | Path | IntoFrame | tuple[IntoFrame, Any]],
    inputs: list[str | Path | Any],
    meta: list[Any | None] | None = None,
    output_format: str = "polars",
    source_col: str = "mrgsrc",
    meta_strategy: str = "first"
) -> tuple[Any, Any | None]:
    """
    Merge multiple SAV/CSV/Excel files or dataframes with their metadata.
    
    This is the main entry point for merging that combines both data and metadata
    merging following tidyspss's two-track architecture. Data and metadata are
    merged independently and returned as a tuple.
    
    Parameters
    ----------
    inputs : list[str | Path | DataFrame | tuple[DataFrame, Metadata]]
        List of inputs to merge. Each element can be:
        - File path (str or Path) to:
            * SAV/ZSAV files (metadata extracted automatically)
            * CSV files (no metadata)
            * Excel files (.xlsx, .xls, .xlsm, .xlsb, .ods) (no metadata)
        - A dataframe (pandas, polars, or any narwhals-supported format) without metadata
        - A combination of file paths (str/Path) and dataframes (pandas/polars/narwhals)
        - A tuple of (dataframe, metadata) for explicit data-metadata pairs
    meta : list[Metadata | None] | None, optional
        Optional list of metadata objects to use for merging.
        - If None (default): metadata is automatically extracted from SAV files
        - If provided: uses these metadata objects for merging, ignoring any
          metadata from SAV files. The list does NOT need to match input length.
        Common usage: provide 1-2 metadata objects to merge, regardless of number of inputs
    source_col : str, default "mrgsrc"
        Name of the provenance column to add to track data sources.
        This column will contain:
        - For file paths: the base filename (e.g., "survey_2024.sav", "data.csv", "report.xlsx")
        - For dataframes: "source_1", "source_2", etc.
    output_format : str, default "polars"
        Output dataframe format: "pandas", "polars", or "narwhals"
    meta_strategy : str, default "first"
        Strategy for merging metadata:
        - "first": Use first non-None meta as base, add new columns from others
        - "last": Use last non-None meta as base, add new columns from others
        
    Returns
    -------
    tuple[DataFrame, Metadata | None]
        - Merged dataframe in the specified format with provenance column
        - Merged metadata (Metadata object) or None if no metadata available
        
    Notes
    -----
    - Data and metadata are merged independently (two-track architecture)
    - If meta is None: uses metadata from SAV files (if any)
    - If meta is provided: uses ONLY those metadata objects, ignoring SAV metadata
    - The source column appears as the last column in the merged dataframe
    - Metadata merge follows column-level preservation (base wins for existing columns)
    - CSV and Excel files don't have metadata, but can still be merged for data
    
    File Format Support
    -------------------
    - SAV/ZSAV: Full support with automatic metadata extraction
    - CSV: Data only, no metadata
    - Excel: Data only (reads first sheet), no metadata
        * Supported extensions: .xlsx, .xls, .xlsm, .xlsb, .ods
    
    Examples
    --------
    >>> # Merge SAV files with automatic metadata extraction
    >>> data, meta = add_cases(["survey1.sav", "survey2.sav", "survey3.sav"])
    
    >>> # Mix different file types (SAV with metadata, CSV/Excel without)
    >>> data, meta = add_cases(["survey.sav", "additional_data.csv", "report.xlsx"])
    
    >>> # Provide specific metadata objects (ignores SAV metadata)
    >>> data, meta = add_cases(
    ...     inputs=["data1.sav", "data2.csv", "data3.xlsx"],
    ...     meta=[meta1, meta2]  # Only these two will be merged
    ... )
    
    >>> # Mix different input types
    >>> df1 = pd.DataFrame({'Q1': [1, 2]})
    >>> data, meta = add_cases([df1, "survey.sav", "data.csv", (df2, meta2)])
    
    >>> # Single metadata for multiple files of any type
    >>> data, meta = add_cases(
    ...     inputs=["file1.sav", "file2.csv", "file3.xlsx"],  # Mixed file types
    ...     meta=[base_meta],  # Just one metadata to use
    ...     meta_strategy="first"
    ... )
    
    >>> # Write merged result
    >>> from tidyspss import write_sav
    >>> write_sav(data, meta, "merged_output.sav")
    """
    
    if not inputs:
        raise ValueError("inputs list cannot be empty")
    
    # Separate data and metadata handling
    dfs = []
    metas_to_merge = []
    
    # If meta parameter is provided, use ONLY those metadata objects
    if meta is not None:
        # User provided specific metadata - use only these
        metas_to_merge = [Metadata(m) if m is not None and not isinstance(m, Metadata) else m 
                         for m in meta]
        logger.info(f"Using {len(meta)} provided metadata objects (ignoring any SAV metadata)")
    
    # Process inputs for data extraction
    for i, item in enumerate(inputs):
        if isinstance(item, tuple) and len(item) == 2:
            # It's a (dataframe, metadata) tuple
            df, tuple_meta = item
            dfs.append(df)
            
            # Only use tuple metadata if meta parameter wasn't provided
            if meta is None and tuple_meta is not None:
                metas_to_merge.append(Metadata(tuple_meta) if not isinstance(tuple_meta, Metadata) else tuple_meta)
                logger.debug(f"Using tuple metadata for input {i}")
            
        elif isinstance(item, (str, Path)):
            # It's a file path
            file_path = Path(item)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            ext = file_path.suffix.lower()
            
            # Always pass file path to merge_data to preserve filename in source_col
            dfs.append(str(file_path))
            
            if ext in ['.sav', '.zsav']:
                # SAV files - extract metadata separately if needed
                # Only use SAV metadata if meta parameter wasn't provided
                if meta is None:
                    _, meta_raw = read_sav(file_path, output_format="polars")
                    if meta_raw is not None:
                        metas_to_merge.append(Metadata(meta_raw))
                        logger.debug(f"Using SAV file metadata: {file_path.name}")
            elif ext == '.csv':
                # CSV files - no metadata available
                logger.debug(f"Added CSV file: {file_path.name} (no metadata)")
            elif ext in ['.xlsx', '.xls', '.xlsm', '.xlsb', '.ods']:
                # Excel files - no metadata available
                logger.debug(f"Added Excel file: {file_path.name} (no metadata)")
            else:
                # Other file types - log warning but try to process
                logger.warning(f"Unknown file type: {ext} - will attempt to process: {file_path.name}")
                
        else:
            # It's a dataframe without metadata
            dfs.append(item)
            logger.debug(f"Added dataframe {i}")
    
    # Log summary of inputs
    logger.info(f"Processing {len(inputs)} inputs for data")
    if meta is None:
        logger.info(f"Found {len(metas_to_merge)} metadata objects from SAV files/tuples")
    else:
        logger.info(f"Using {len(metas_to_merge)} provided metadata objects")
    
    # Count file types for logging
    file_type_counts = {}
    for item in inputs:
        if isinstance(item, (str, Path)):
            ext = Path(item).suffix.lower()
            file_type_counts[ext] = file_type_counts.get(ext, 0) + 1
    
    if file_type_counts:
        types_summary = ", ".join([f"{count} {ext}" for ext, count in file_type_counts.items()])
        logger.info(f"File types: {types_summary}")
    
    # Merge data using merge_data function
    logger.info("Merging data...")
    merged_data = merge_data(dfs, source_col=source_col, output_format=output_format)
    
    # Merge metadata if any exists
    merged_meta = None
    if metas_to_merge and any(m is not None for m in metas_to_merge):
        logger.info(f"Merging metadata with strategy='{meta_strategy}'...")
        merged_meta = merge_meta(metas_to_merge, strategy=meta_strategy)
        
        # Add label for the source column if not present
        if merged_meta and source_col not in merged_meta.column_labels:
            logger.debug(f"Adding label for source column '{source_col}'")
            labels_update = {source_col: "Data Source"}
            # Get existing labels and add new one
            existing_labels = merged_meta.column_labels if merged_meta.column_labels else {}
            merged_meta.column_labels = {**existing_labels, **labels_update}
            
            # Set as nominal measure if not present
            if source_col not in merged_meta.variable_measure:
                measures_update = {source_col: "nominal"}
                existing_measures = merged_meta.variable_measure if merged_meta.variable_measure else {}
                merged_meta.variable_measure = {**existing_measures, **measures_update}
    else:
        logger.info("No metadata to merge (common when merging CSV/Excel files)")
    
    # Log final summary
    data_shape = merged_data.shape if hasattr(merged_data, 'shape') else "unknown"
    meta_cols = len(merged_meta.column_labels) if merged_meta and merged_meta.column_labels else 0
    logger.info(f"Merge complete: data shape {data_shape}, metadata for {meta_cols} columns")
    
    return merged_data, merged_meta
