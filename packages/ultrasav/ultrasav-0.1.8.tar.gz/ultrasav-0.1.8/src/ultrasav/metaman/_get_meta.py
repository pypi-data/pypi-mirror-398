"""
Extract Metadict Module (v2 - Flat Format)
==========================================
A utility module for extracting SPSS metadata from pyreadstat meta objects
and saving as importable Python files with flat, pyreadstat-ready variables.

Output variables are directly usable with pyreadstat.write_sav():
- column_labels: {var: label, ...}
- variable_value_labels: {var: {val: label}, ...}

Dependencies: pathlib, datetime
"""

from datetime import datetime
from pathlib import Path


# =============================================================================
# Type Aliases
# =============================================================================
ColumnLabelsDict = dict[str, str]
ValueLabelsDict = dict[str, dict[int | float | str, str]]
FileInfoDict = dict[str, str | int | None]
MetaDictFlat = dict[str, ColumnLabelsDict | ValueLabelsDict | FileInfoDict]


# =============================================================================
# Value Conversion Helper
# =============================================================================

def _convert_value(value):
    """
    Convert values to serializable types (handles datetime, dict, list).
    
    Uses inner function for recursion to avoid Marimo's function renaming.
    
    Parameters
    ----------
    value : any
        Value to convert
    
    Returns
    -------
    any
        Converted value (datetime -> str, others unchanged)
    """
    def convert_nested(obj):
        """Iteratively convert nested structures."""
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        
        if not isinstance(obj, (dict, list)):
            return obj
        
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                result[k] = convert_nested(v) if isinstance(v, (dict, list, datetime)) else v
            return result
        else:  # list
            result = []
            for item in obj:
                result.append(convert_nested(item) if isinstance(item, (dict, list, datetime)) else item)
            return result
    
    return convert_nested(value)


# =============================================================================
# Metadata Extraction (Pure Functions)
# =============================================================================

def _extract_column_labels(meta) -> ColumnLabelsDict:
    """
    Extract column labels dict directly usable with pyreadstat.write_sav().
    
    Parameters
    ----------
    meta : pyreadstat.metadata_container
        The metadata object from pyreadstat.read_sav()
    
    Returns
    -------
    ColumnLabelsDict
        {variable_name: label, ...}
    """
    return dict(meta.column_names_to_labels)


def _extract_variable_value_labels(meta) -> ValueLabelsDict:
    """
    Extract variable value labels dict directly usable with pyreadstat.write_sav().
    
    Parameters
    ----------
    meta : pyreadstat.metadata_container
        The metadata object from pyreadstat.read_sav()
    
    Returns
    -------
    ValueLabelsDict
        {variable_name: {value: label, ...}, ...}
    """
    return _convert_value(meta.variable_value_labels)


def _extract_file_info(meta) -> FileInfoDict:
    """
    Extract general file information for reference.
    
    Parameters
    ----------
    meta : pyreadstat.metadata_container
        The metadata object from pyreadstat.read_sav()
    
    Returns
    -------
    FileInfoDict
        General file metadata
    """
    return {
        "file_label": meta.file_label,
        "table_name": meta.table_name,
        "file_encoding": meta.file_encoding,
        "number_rows": meta.number_rows,
        "number_columns": meta.number_columns,
        "creation_time": _convert_value(meta.creation_time),
        "modification_time": _convert_value(meta.modification_time),
        "notes": _convert_value(meta.notes),
    }


def _extract_extended_metadata(meta) -> dict:
    """
    Extract extended metadata fields (for include_all=True).
    
    Parameters
    ----------
    meta : pyreadstat.metadata_container
        The metadata object from pyreadstat.read_sav()
    
    Returns
    -------
    dict
        Extended metadata fields
    """
    return {
        "variable_measure": dict(meta.variable_measure),
        "variable_display_width": dict(meta.variable_display_width),
        "variable_storage_width": dict(meta.variable_storage_width),
        "variable_alignment": dict(meta.variable_alignment),
        "original_variable_types": dict(meta.original_variable_types),
        "readstat_variable_types": dict(meta.readstat_variable_types),
        "missing_ranges": _convert_value(meta.missing_ranges),
        "missing_user_values": _convert_value(meta.missing_user_values),
        # Additional fields for metadata integrity (less commonly used)
        "column_names": list(meta.column_names),
        "column_labels": list(meta.column_labels),
        "value_labels": _convert_value(meta.value_labels),
        "variable_to_label": dict(meta.variable_to_label),
    }


# =============================================================================
# Python Code Formatting
# =============================================================================

def _format_value_as_python(value, indent_level: int = 0) -> str:
    """
    Format a Python value as valid Python code string.
    
    Uses inner function for recursion to avoid Marimo's function renaming.
    
    Parameters
    ----------
    value : any
        Value to format
    indent_level : int
        Current indentation level
    
    Returns
    -------
    str
        Python code representation of the value
    """
    def fmt(val, level: int) -> str:
        """Inner recursive formatter."""
        indent = "    " * level
        next_indent = "    " * (level + 1)
        
        if val is None:
            return "None"
        elif isinstance(val, bool):
            return "True" if val else "False"
        elif isinstance(val, (int, float)):
            return repr(val)
        elif isinstance(val, str):
            # Use triple quotes for strings with newlines or quotes
            if '\n' in val or "'" in val or '"' in val:
                escaped = val.replace("'''", "\\'\\'\\'")
                return f"'''{escaped}'''"
            return repr(val)
        elif isinstance(val, list):
            if not val:
                return "[]"
            if len(val) <= 3 and all(isinstance(v, (int, float, str, bool, type(None))) for v in val):
                items = ", ".join(fmt(v, 0) for v in val)
                return f"[{items}]"
            lines = ["["]
            for item in val:
                formatted = fmt(item, level + 1)
                lines.append(f"{next_indent}{formatted},")
            lines.append(f"{indent}]")
            return "\n".join(lines)
        elif isinstance(val, dict):
            if not val:
                return "{}"
            lines = ["{"]
            for k, v in val.items():
                key_repr = repr(k)
                val_repr = fmt(v, level + 1)
                lines.append(f"{next_indent}{key_repr}: {val_repr},")
            lines.append(f"{indent}}}")
            return "\n".join(lines)
        else:
            return repr(val)
    
    return fmt(value, indent_level)


def _format_variable_assignment(var_name: str, data, comment: str | None = None) -> str:
    """
    Format a variable assignment as Python code.
    
    Parameters
    ----------
    var_name : str
        Variable name
    data : any
        Data to assign
    comment : str, optional
        Comment to add above the assignment
    
    Returns
    -------
    str
        Python code for the assignment
    """
    lines: list[str] = []
    if comment:
        lines.append(f"# {comment}")
    formatted = _format_value_as_python(data, 0)
    lines.append(f"{var_name} = {formatted}")
    return "\n".join(lines)


# =============================================================================
# File Generation
# =============================================================================

def _generate_python_file_content(
    column_labels: ColumnLabelsDict,
    variable_value_labels: ValueLabelsDict,
    file_info: FileInfoDict,
    extended_metadata: dict | None = None,
    col_labels_var: str = "column_names_to_labels",
    val_labels_var: str = "variable_value_labels",
    file_info_var: str = "file_info",
) -> str:
    """
    Generate complete Python file content with flat, pyreadstat-ready format.
    
    Parameters
    ----------
    column_labels : ColumnLabelsDict
        Column labels dictionary
    variable_value_labels : ValueLabelsDict
        Variable value labels dictionary
    file_info : FileInfoDict
        File information dictionary
    extended_metadata : dict, optional
        Extended metadata (if include_all=True)
    col_labels_var : str
        Variable name for column labels
    val_labels_var : str
        Variable name for value labels
    file_info_var : str
        Variable name for file info
    
    Returns
    -------
    str
        Complete Python file content
    """
    lines: list[str] = []
    
    # Module docstring
    lines.append('"""')
    lines.append("SPSS Metadata Dictionary")
    lines.append("========================")
    lines.append("Auto-generated metadata extracted from SPSS file.")
    lines.append("")
    # lines.append("Usage with pyreadstat.write_sav():")
    # lines.append(f"    pyreadstat.write_sav(df, 'output.sav',")
    # lines.append(f"        column_labels={col_labels_var},")
    # lines.append(f"        variable_value_labels={val_labels_var}")
    # lines.append(f"    )")
    # lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append('"""')
    lines.append("")
    
    # File info first (high-level overview)
    lines.append(_format_variable_assignment(
        file_info_var,
        file_info,
        "File Information (high-level overview)"
    ))
    lines.append("")
    lines.append("")
    
    # Column labels (primary output)
    lines.append(_format_variable_assignment(
        col_labels_var,
        column_labels,
        f"Column Names to Labels - use with column_labels= in pyreadstat.write_sav()"
    ))
    lines.append("")
    lines.append("")
    
    # Variable value labels (primary output)
    lines.append(_format_variable_assignment(
        val_labels_var,
        variable_value_labels,
        f"Variable Value Labels - use with variable_value_labels= in pyreadstat.write_sav()"
    ))
    lines.append("")
    
    # Extended metadata if included
    if extended_metadata:
        lines.append("")
        lines.append(_format_variable_assignment(
            "extended_metadata",
            extended_metadata,
            "Extended Metadata (variable measures, widths, types, etc.)"
        ))
        lines.append("")
    
    return "\n".join(lines)


def _save_python_file(content: str, output_path: Path, encoding: str = "utf-8") -> Path:
    """
    Save Python content to file.
    
    Parameters
    ----------
    content : str
        Python file content
    output_path : Path
        Output file path
    encoding : str
        File encoding
    
    Returns
    -------
    Path
        Path to saved file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding=encoding) as f:
        f.write(content)
    
    return output_path


def _get_default_output_path() -> Path:
    """
    Get default output path in Downloads folder.
    
    Returns
    -------
    Path
        Default output path
    """
    downloads_dir = Path.home() / "Downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    return downloads_dir / "spss_metadata.py"


# =============================================================================
# Main Function
# =============================================================================

def get_meta(
    meta,
    include_all: bool = False,
    output_path: str | None = None,
    col_labels_var: str = "column_names_to_labels",
    val_labels_var: str = "variable_value_labels",
    file_info_var: str = "file_info",
    encoding: str = "utf-8",
    verbose: bool = False
) -> MetaDictFlat:
    """
    Extract metadata from pyreadstat meta object in flat, pyreadstat-ready format.
    
    Output is directly usable with pyreadstat.write_sav() - no nested digging required.
    
    Parameters
    ----------
    meta : pyreadstat.metadata_container
        The metadata returned by pyreadstat.read_sav()
    include_all : bool, default False
        If True, also extract extended metadata (variable measures, widths, types, etc.)
    output_path : str, optional
        File path to save Python file. Options:
        - None: Don't save, just return the dict (default)
        - "downloads": Save to system Downloads folder as 'spss_metadata.py'
        - "path/to/file.py": Save to specific path (must end with .py)
    col_labels_var : str, default "column_names_to_labels"
        Variable name for column labels in output file
    val_labels_var : str, default "variable_value_labels"
        Variable name for value labels in output file
    file_info_var : str, default "file_info"
        Variable name for file info in output file
    encoding : str, default "utf-8"
        File encoding for output
    verbose : bool, default False
        Whether to print progress messages
    
    Returns
    -------
    MetaDictFlat
        Flat dictionary with keys:
        - "column_names_to_labels": {var: label, ...} - directly usable with pyreadstat
        - "variable_value_labels": {var: {val: label}, ...} - directly usable with pyreadstat
        - "file_info": General file metadata
        - "extended_metadata": (only if include_all=True) Additional metadata fields
    
    Examples
    --------
    >>> import pyreadstat
    >>> df, meta = pyreadstat.read_sav("survey.sav")
    
    >>> # Extract metadata (no file saving)
    >>> meta_dict = get_meta(meta)
    
    >>> # Use directly with pyreadstat.write_sav()
    >>> pyreadstat.write_sav(
    ...     df, "output.sav",
    ...     column_labels=meta_dict["column_names_to_labels"],
    ...     variable_value_labels=meta_dict["variable_value_labels"]
    ... )
    
    >>> # Or save to file and import later
    >>> get_meta(meta, output_path="my_metadata.py")
    >>> # Then in another script:
    >>> from my_metadata import column_names_to_labels, variable_value_labels
    >>> pyreadstat.write_sav(df, "output.sav",
    ...     column_labels=column_names_to_labels,
    ...     variable_value_labels=variable_value_labels
    ... )
    
    >>> # Save to Downloads folder
    >>> get_meta(meta, output_path="downloads")
    
    >>> # Include extended metadata
    >>> meta_dict = get_meta(meta, include_all=True)
    >>> print(meta_dict["extended_metadata"]["variable_measure"])
    """
    
    def _print(msg: str) -> None:
        if verbose:
            print(msg)
    
    try:
        _print("=" * 60)
        _print("GET METADATA SUMMARY")
        _print("=" * 60)
        
        # Extract the three main components
        column_labels = _extract_column_labels(meta)
        variable_value_labels = _extract_variable_value_labels(meta)
        file_info = _extract_file_info(meta)
        
        # Extended metadata if requested
        extended_metadata = _extract_extended_metadata(meta) if include_all else None
        
        # Display info
        _print(f"File: {file_info.get('file_label') or file_info.get('table_name') or 'Unknown'}")
        _print(f"Rows: {file_info.get('number_rows')}, Columns: {file_info.get('number_columns')}")
        _print(f"Variables with labels: {len(column_labels)}")
        _print(f"Variables with value labels: {len(variable_value_labels)}")
        if output_path is not None:
            _print(f"Output: {'Downloads folder' if output_path.lower() == 'downloads' else output_path}")
        
        # Build return dict
        result: MetaDictFlat = {
            "column_names_to_labels": column_labels,
            "variable_value_labels": variable_value_labels,
            "file_info": file_info,
        }
        if extended_metadata:
            result["extended_metadata"] = extended_metadata
        
        # Determine if we should save and where
        save_path: Path | None = None
        
        if output_path is not None:
            if output_path.lower() == "downloads":
                save_path = _get_default_output_path()
            elif not output_path.lower().endswith(".py"):
                raise ValueError("output_path must end with .py or be 'downloads'")
            else:
                save_path = Path(output_path)
        
        # Save if path provided
        saved_path: Path | None = None
        if save_path is not None:
            content = _generate_python_file_content(
                column_labels,
                variable_value_labels,
                file_info,
                extended_metadata,
                col_labels_var,
                val_labels_var,
                file_info_var,
            )
            saved_path = _save_python_file(content, save_path, encoding)
        
        # Summary
        _print("\n" + "=" * 60)
        _print("EXTRACTION COMPLETE")
        _print("=" * 60)
        _print(f"  • column_names_to_labels: {len(column_labels)} variables")
        _print(f"  • variable_value_labels: {len(variable_value_labels)} variables")
        if extended_metadata:
            _print(f"  • extended_metadata:")
            for key, val in extended_metadata.items():
                if isinstance(val, (dict, list)):
                    _print(f"      - {key}: {len(val)} items")
                else:
                    _print(f"      - {key}")
        
        _print("")
        if saved_path:
            _print(f"✅ Saved to: {saved_path}")
        else:
            _print("✅ Extracted (no file saved)")
        _print("=" * 60)
        
        return result
        
    except Exception as e:
        _print(f"\n❌ Error during extraction: {str(e)}")
        raise


__all__ = ["get_meta"]
