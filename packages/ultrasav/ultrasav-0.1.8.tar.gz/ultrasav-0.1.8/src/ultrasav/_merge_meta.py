"""
merge_meta.py
Metadata merging function for tidyspss 2.0
Following the two-track architecture where metadata is independent from data
"""

import logging
from typing import Any
from copy import deepcopy

# Import Metadata class
from ._metadata import Metadata

logger = logging.getLogger(__name__)


def _merge_dict_field(base_dict: dict, other_dict: dict, field_name: str) -> tuple[dict, list]:
    """
    Merge two dictionary fields at column level - base wins for existing columns.
    
    Parameters
    ----------
    base_dict : dict
        Base dictionary (takes precedence for existing keys)
    other_dict : dict
        Other dictionary (only new keys are added)
    field_name : str
        Name of the field being merged (for logging)
        
    Returns
    -------
    tuple[dict, list]
        Merged dictionary and list of new columns added
    """
    merged = base_dict.copy() if base_dict else {}
    new_columns = []
    
    for col_name, col_value in other_dict.items():
        if col_name not in merged:
            # This is a new column - add entire column:value pair
            merged[col_name] = deepcopy(col_value)
            new_columns.append(col_name)
        # If column exists in base, keep base's value entirely
    
    if new_columns:
        logger.debug(f"  Added {len(new_columns)} new columns to {field_name}: {new_columns[:5]}{'...' if len(new_columns) > 5 else ''}")
    
    return merged, new_columns


def _collect_column_labels(meta) -> dict:
    """
    Extract column_labels from metadata, handling both list and dict formats.
    
    Parameters
    ----------
    meta : Metadata
        Metadata object to extract column labels from
        
    Returns
    -------
    dict
        Column labels in dictionary format
    """
    column_labels = {}
    
    if hasattr(meta, 'column_labels') and meta.column_labels:
        if isinstance(meta.column_labels, dict):
            column_labels = meta.column_labels.copy()
        elif isinstance(meta.column_labels, list) and hasattr(meta, 'column_names'):
            # Convert list format to dict format
            for name, label in zip(meta.column_names, meta.column_labels):
                column_labels[name] = label
    
    return column_labels


def merge_meta(
    metas: list[Any | None],
    strategy: str = "first"
) -> Any:
    """
    Merge multiple metadata objects with column-level preservation.
    
    This function merges metadata from multiple sources following tidyspss's
    principle that metadata is independent from data. The merge operates at
    the column level - for each column, we take ALL metadata from one source,
    never mixing metadata values within a column.
    
    Parameters
    ----------
    metas : list[Metadata | None]
        List of Metadata objects or None values. Can include:
        - Metadata objects from read_sav/pyreadstat
        - None for missing metadata
        - Metadata objects created manually
    strategy : str, default "first"
        Merge strategy for combining metadata:
        - "first": Use first non-None meta as base, add new columns from others
        - "last": Use last non-None meta as base, add new columns from others
        
    Returns
    -------
    Metadata
        Merged Metadata object with combined metadata from all sources
        
    Notes
    -----
    The merge strategy works at the COLUMN level, not value level:
    - If base meta has metadata for column "Q1", it keeps ALL of Q1's metadata
    - Only columns NOT in base are added from subsequent metas
    - No mixing of values within a column's metadata
    
    Only these fields are merged:
    - column_labels
    - variable_value_labels  
    - variable_format
    - variable_measure
    - variable_display_width
    - missing_ranges
    
    File-level metadata (notes, file_label) are taken from base only.
    
    Examples
    --------
    >>> # Merge metadata from multiple SAV files
    >>> _, meta1 = read_sav("file1.sav")
    >>> _, meta2 = read_sav("file2.sav")
    >>> _, meta3 = read_sav("file3.sav")
    >>> merged_meta = merge_meta([meta1, meta2, meta3])
    
    >>> # Handle None values
    >>> merged_meta = merge_meta([None, meta1, None, meta2])
    
    >>> # Use last strategy
    >>> merged_meta = merge_meta([meta1, meta2, meta3], strategy="last")
    """
    
    # Filter out None values
    valid_metas = [m for m in metas if m is not None]
    
    if not valid_metas:
        # Return empty metadata if all are None
        logger.info("All metadata objects are None, returning empty Metadata")
        return Metadata()
    
    if len(valid_metas) == 1:
        # Only one valid metadata, return it wrapped in Metadata class
        logger.info("Only one valid metadata found, returning as Metadata object")
        return Metadata(valid_metas[0])
    
    # Select base metadata based on strategy
    if strategy == "first":
        base_meta = valid_metas[0]
        others = valid_metas[1:]
        logger.info(f"Using first non-None metadata as base")
    elif strategy == "last":
        base_meta = valid_metas[-1]
        others = valid_metas[:-1]
        logger.info(f"Using last non-None metadata as base")
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}. Use 'first' or 'last'")
    
    # Wrap base metadata in Metadata class to ensure we have proper methods
    merged = Metadata(base_meta)
    
    # Fields to merge (dict-based metadata that maps columns to values)
    dict_fields = [
        'variable_value_labels',   # Dict with column keys
        'variable_format',         # Dict with column keys
        'variable_measure',        # Dict with column keys
        'variable_display_width',  # Dict with column keys
        'missing_ranges',          # Dict with column keys
    ]
    
    # Collect all unique column names (for logging)
    column_names_all = []
    if hasattr(merged, 'column_names') and merged.column_names:
        column_names_all.extend(merged.column_names)
    
    # Collect and merge column_labels from all metadata
    column_labels_dict = _collect_column_labels(merged)
    
    # Process each subsequent metadata object
    for i, other_meta in enumerate(others):
        logger.debug(f"Merging metadata {i+1} of {len(others)}")
        
        # Collect column names from this metadata
        if hasattr(other_meta, 'column_names') and other_meta.column_names:
            for col in other_meta.column_names:
                if col not in column_names_all:
                    column_names_all.append(col)
        
        # Merge column_labels
        other_labels = _collect_column_labels(other_meta)
        if other_labels:
            merged_labels, new_cols = _merge_dict_field(column_labels_dict, other_labels, 'column_labels')
            column_labels_dict = merged_labels
        
        # Merge each dict field
        for field_name in dict_fields:
            # Get current and other field values
            merged_field = getattr(merged, field_name, None)
            other_field = getattr(other_meta, field_name, None)
            
            # Skip if either is None or not a dict
            if merged_field is None or other_field is None:
                continue
            if not isinstance(merged_field, dict) or not isinstance(other_field, dict):
                logger.debug(f"  Skipping {field_name} - not dict type")
                continue
            
            # Merge the field
            merged_result, _ = _merge_dict_field(merged_field, other_field, field_name)
            setattr(merged, field_name, merged_result)
    
    # Update column_labels with the merged dictionary
    if column_labels_dict:
        merged.column_labels = column_labels_dict
        logger.debug(f"Updated column_labels with {len(column_labels_dict)} entries")
    
    # Log summary of unique columns found (column_names is read-only)
    if column_names_all:
        unique_count = len(set(column_names_all))
        logger.debug(f"Found {unique_count} unique columns across all metadata")
    
    # Log summary
    total_columns = set()
    for field_name in ['column_labels'] + dict_fields:
        field_value = getattr(merged, field_name, None)
        if field_value and isinstance(field_value, dict):
            total_columns.update(field_value.keys())
    
    logger.info(f"Merge complete: {len(valid_metas)} metadata objects merged, {len(total_columns)} unique columns in result")
    
    return merged


def get_meta_summary(meta: Any) -> dict:
    """
    Get a summary of metadata contents for debugging/logging.
    
    Parameters
    ----------
    meta : Metadata
        Metadata object to summarize
        
    Returns
    -------
    dict
        Summary statistics about the metadata
    """
    if meta is None:
        return {"status": "None"}
    
    summary = {
        "column_names": len(getattr(meta, 'column_names', [])),
        "column_labels": len(getattr(meta, 'column_labels', {})),
        "value_labels": len(getattr(meta, 'variable_value_labels', {})),
        "formats": len(getattr(meta, 'variable_format', {})),
        "measures": len(getattr(meta, 'variable_measure', {})),
        "display_widths": len(getattr(meta, 'variable_display_width', {})),
        "missing_ranges": len(getattr(meta, 'missing_ranges', {})),
        "missing_user_values": len(getattr(meta, 'missing_user_values', {})),
        "original_types": len(getattr(meta, 'original_variable_types', {})),
        "readstat_types": len(getattr(meta, 'readstat_variable_types', {})),
        "alignment": len(getattr(meta, 'variable_alignment', {})),
        "storage_width": len(getattr(meta, 'variable_storage_width', {})),
        "variable_to_label": len(getattr(meta, 'variable_to_label', {})),
        "value_label_defs": len(getattr(meta, 'value_labels', {})),
        "mr_sets": len(getattr(meta, 'mr_sets', {})),
    }
    
    # Add file-level metadata if present
    if hasattr(meta, 'file_label') and meta.file_label:
        summary['file_label'] = meta.file_label
    if hasattr(meta, 'notes') and meta.notes:
        summary['has_notes'] = True
        
    return summary
