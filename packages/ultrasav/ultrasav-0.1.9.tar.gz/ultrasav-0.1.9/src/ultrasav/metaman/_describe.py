"""
_describe.py
Variable summary tool for ultrasav

Provides a quick way to inspect variable metadata and value distributions.
Uses dynamic terminal width detection and text wrapping for clean output.

This version uses only standard library modules (textwrap, shutil).
Leverages make_datamap() for pre-calculated statistics (base_pct, total_pct, etc.)
"""

import textwrap
import shutil
from typing import Any

import polars as pl

from ._make_datamap import make_datamap


def describe(
    df,
    meta: Any,
    columns: str | list[str],
    *,
    show_missing: bool = True,
    show_unlabeled: bool = True,
    print_output: bool = True,
    max_width: int | None = None,
) -> dict | list[dict]:
    """
    Print and return a summary of one or more variables including metadata and value distribution.
    
    This function provides a quick way to inspect a variable's:
    - Variable name and label
    - Variable type (single-select, multi-select, numeric, text, date)
    - All value codes (from both metadata and actual data)
    - Value labels and counts
    - Missing data information
    
    Parameters
    ----------
    df : DataFrame (pandas or polars)
        The data dataframe
    meta : Metadata or pyreadstat metadata
        The metadata object containing variable and value labels
    columns : str or list of str
        Single column name (str) or list of column names to describe.
        - If str: returns a single dict
        - If list: returns a list of dicts (optimized to call make_datamap once)
    show_missing : bool, default True
        Whether to include NULL/missing data row in output
    show_unlabeled : bool, default True
        Whether to flag values that exist in data but not in metadata (⚠️)
    print_output : bool, default True
        Whether to print the formatted summary to console
    max_width : int, optional
        Maximum width for output. If None, auto-detects terminal width.
        Useful for consistent output in scripts or notebooks.
        
    Returns
    -------
    dict or list of dict
        If columns is str: single summary dictionary
        If columns is list: list of summary dictionaries
        
        Each summary dictionary contains:
        - variable: column name
        - variable_label: label from metadata (or None)
        - variable_type: detected type (single-select, multi-select, numeric, text, date)
        - values: list of dicts, each containing:
            - value_code: the numeric/string code (None for missing)
            - value_label: the label text (or "(unlabeled)" / "(Missing/NULL)")
            - value_n: count of occurrences
            - valid_pct: percentage of valid responses (None for missing row)
            - total_pct: percentage of total responses
            - in_meta: bool, whether this value has a label in metadata
            - in_data: bool, always True (value exists in data)
        - total_n: total count (valid + missing)
        - base_n: non-missing count
        - missing_n: missing/null count
        
    Raises
    ------
    ValueError
        If a specified column is not found in the dataframe
        
    Examples
    --------
    >>> import ultrasav as ul
    >>> df, meta = ul.read_sav("survey.sav")
    >>> 
    >>> # Single variable - returns dict
    >>> summary = ul.describe(df, meta, "Q1")
    >>> 
    >>> # Multiple variables - returns list of dicts (optimized)
    >>> summaries = ul.describe(df, meta, ["Q1", "Q2", "Q3"])
    >>> 
    >>> # Get dict for programmatic use (no printing)
    >>> summary = ul.describe(df, meta, "Q1", print_output=False)
    >>> print(f"Variable {summary['variable']} has {summary['base_n']} valid responses")
    >>> 
    >>> # Hide missing data row
    >>> ul.describe(df, meta, "Q1", show_missing=False)
    >>> 
    >>> # Fixed width output (useful in notebooks)
    >>> ul.describe(df, meta, "Q1", max_width=100)
    
    Notes
    -----
    - When passing a list of columns, make_datamap() is called only ONCE for efficiency
    - When passing a single column string, make_datamap() is called once for that request
    - Values are sorted by code (numeric order if possible)
    - Unlabeled values (in data but not in metadata) are flagged with ⚠️
    - Long labels are automatically wrapped to fit the terminal width
    - Valid % (base_pct) is calculated excluding missing values (value_n / base_n)
    - Total % (total_pct) is calculated including missing values (value_n / total_n)
    
    See Also
    --------
    make_datamap : Create a full datamap for all variables
    map_to_excel : Export datamap to formatted Excel
    """
    # Determine if single or multiple columns
    is_single = isinstance(columns, str)
    
    if is_single:
        # Single column - call make_datamap and extract
        datamap = make_datamap(df, meta, output_format="polars")
        summary = _describe_from_datamap(
            datamap, columns,
            show_missing=show_missing,
            show_unlabeled=show_unlabeled,
            print_output=print_output,
            max_width=max_width,
        )
        return summary
    else:
        # Multiple columns - call make_datamap ONCE (optimized)
        datamap = make_datamap(df, meta, output_format="polars")
        
        summaries = []
        for col in columns:
            try:
                summary = _describe_from_datamap(
                    datamap, col,
                    show_missing=show_missing,
                    show_unlabeled=show_unlabeled,
                    print_output=print_output,
                    max_width=max_width,
                )
                summaries.append(summary)
            except ValueError as e:
                if print_output:
                    print(f"⚠️ Skipping '{col}': {e}")
        
        return summaries


def _describe_from_datamap(
    datamap: pl.DataFrame,
    column: str,
    *,
    show_missing: bool = True,
    show_unlabeled: bool = True,
    print_output: bool = True,
    max_width: int | None = None,
) -> dict:
    """
    Internal function to extract variable summary from pre-computed datamap.
    
    This avoids re-running make_datamap() for each variable when describing
    multiple variables.
    
    Parameters
    ----------
    datamap : pl.DataFrame
        Pre-computed datamap from make_datamap()
    column : str
        The column/variable name to describe
    show_missing : bool
        Whether to include NULL/missing data row
    show_unlabeled : bool
        Whether to flag unlabeled values
    print_output : bool
        Whether to print the formatted summary
    max_width : int, optional
        Maximum output width
        
    Returns
    -------
    dict
        Summary dictionary
    """
    # Filter to the requested column
    var_map = datamap.filter(pl.col("variable") == column)
    
    if var_map.is_empty():
        available_cols = datamap.get_column("variable").unique().to_list()
        raise ValueError(
            f"Column '{column}' not found in dataframe. "
            f"Available columns: {available_cols[:10]}{'...' if len(available_cols) > 10 else ''}"
        )
    
    # Extract summary info from first row
    first_row = var_map.row(0, named=True)
    variable_label = first_row["variable_label"]
    variable_type = first_row["variable_type"]
    total_n = first_row["total_n"]
    
    # Get base_n (valid count) and missing_n
    missing_n = 0
    base_n = 0
    
    for row in var_map.iter_rows(named=True):
        if row["missing_data"] == "Yes":
            missing_n = row["value_n"]
        else:
            base_n = row["base_n"]
            break
    
    if base_n == 0 and missing_n > 0:
        base_n = total_n - missing_n
    elif base_n == 0:
        base_n = total_n
    
    # Build values list using pre-calculated fields
    values = []
    
    for row in var_map.iter_rows(named=True):
        is_missing_row = row["missing_data"] == "Yes"
        
        if is_missing_row:
            if show_missing:
                total_pct = row["total_pct"]
                total_pct_value = (total_pct * 100) if total_pct is not None else 0
                
                values.append({
                    "value_code": None,
                    "value_label": "(Missing/NULL)",
                    "value_n": row["value_n"],
                    "valid_pct": None,
                    "total_pct": total_pct_value,
                    "in_meta": False,
                    "in_data": True,
                })
        else:
            in_meta = row["missing_value_label"] == "No"
            
            base_pct = row["base_pct"]
            total_pct = row["total_pct"]
            
            valid_pct_value = (base_pct * 100) if base_pct is not None else 0
            total_pct_value = (total_pct * 100) if total_pct is not None else 0
            
            # Determine the display label
            # For text variables, use "Raw verbatims" instead of "(unlabeled)"
            if row["value_label"]:
                display_label = row["value_label"]
            elif variable_type == "text":
                display_label = "Raw verbatims"
            else:
                display_label = "(unlabeled)"
            
            values.append({
                "value_code": row["value_code"],
                "value_label": display_label,
                "value_n": row["value_n"],
                "valid_pct": valid_pct_value,
                "total_pct": total_pct_value,
                "in_meta": in_meta,
                "in_data": True,
            })
    
    summary = {
        "variable": column,
        "variable_label": variable_label,
        "variable_type": variable_type,
        "values": values,
        "total_n": total_n,
        "base_n": base_n,
        "missing_n": missing_n,
    }
    
    if print_output:
        _print_summary(summary, show_unlabeled=show_unlabeled, max_width=max_width)
    
    return summary


def _print_summary(
    summary: dict, 
    show_unlabeled: bool = True, 
    max_width: int | None = None
) -> None:
    """
    Pretty print the variable summary with dynamic width and text wrapping.
    
    Parameters
    ----------
    summary : dict
        The summary dictionary from describe
    show_unlabeled : bool
        Whether to show warning flag for unlabeled values
    max_width : int, optional
        Maximum output width. Auto-detects if None.
    """
    # Get terminal width, default to 100 if can't detect
    if max_width is None:
        terminal_width = shutil.get_terminal_size((100, 20)).columns
        terminal_width = min(terminal_width, 120)  # Cap at 120 for readability
    else:
        terminal_width = max_width
    
    # Ensure minimum width
    terminal_width = max(terminal_width, 80)
    
    # Fixed column widths for the table
    value_width = 10      # "Value" column
    n_width = 12          # "N" column
    valid_pct_width = 10  # "Valid %" column
    total_pct_width = 10  # "Total %" column
    flag_width = 3        # For the ⚠️ flag
    
    # Calculate remaining space for label column
    label_width = terminal_width - value_width - n_width - valid_pct_width - total_pct_width - flag_width - 4
    label_width = max(label_width, 25)  # Minimum label width
    
    # Separators
    separator = "=" * terminal_width
    thin_sep = "-" * terminal_width
    
    # ===== HEADER SECTION =====
    print(f"\n{separator}")
    print(f"Variable: {summary['variable']}")
    
    # Wrap long variable labels
    var_label = summary['variable_label'] or '(no label)'
    label_indent = "Label:    "
    available_width = terminal_width - len(label_indent)
    
    if len(var_label) > available_width:
        wrapped = textwrap.wrap(var_label, width=available_width)
        print(f"{label_indent}{wrapped[0]}")
        for line in wrapped[1:]:
            print(f"{' ' * len(label_indent)}{line}")
    else:
        print(f"{label_indent}{var_label}")
    
    print(f"Type:     {summary['variable_type']}")
    print(separator)
    
    # ===== COUNTS SUMMARY =====
    print(f"Total N: {summary['total_n']:,}  |  Valid: {summary['base_n']:,}  |  Missing: {summary['missing_n']:,}")
    print(thin_sep)
    
    # ===== TABLE HEADER =====
    header = (
        f"{'Value':<{value_width}}"
        f"{'Label':<{label_width}}"
        f"{'N':>{n_width}}"
        f"{'Valid %':>{valid_pct_width}}"
        f"{'Total %':>{total_pct_width}}"
    )
    print(header)
    print(thin_sep)
    
    # ===== VALUE ROWS =====
    for v in summary["values"]:
        value_str = str(v["value_code"]) if v["value_code"] is not None else "NULL"
        label_str = v["value_label"] or ""
        
        # Determine if we need to show unlabeled warning
        flag = ""
        if show_unlabeled and not v["in_meta"] and v["value_code"] is not None:
            flag = " ⚠️"
        
        # Format N
        n_str = f"{v['value_n']:,}"
        
        # Format Valid % (blank for missing row)
        if v["valid_pct"] is not None:
            valid_pct_str = f"{v['valid_pct']:.1f}%"
        else:
            valid_pct_str = ""  # Blank for missing row
        
        # Format Total %
        total_pct_str = f"{v['total_pct']:.1f}%"
        
        # Wrap label if needed
        if len(label_str) > label_width:
            wrapped_label = textwrap.wrap(label_str, width=label_width)
            
            # First line with all columns
            first_line = (
                f"{value_str:<{value_width}}"
                f"{wrapped_label[0]:<{label_width}}"
                f"{n_str:>{n_width}}"
                f"{valid_pct_str:>{valid_pct_width}}"
                f"{total_pct_str:>{total_pct_width}}"
                f"{flag}"
            )
            print(first_line)
            
            # Continuation lines (label only, indented under label column)
            for line in wrapped_label[1:]:
                continuation = f"{'':<{value_width}}{line:<{label_width}}"
                print(continuation)
        else:
            # Single line output
            row_line = (
                f"{value_str:<{value_width}}"
                f"{label_str:<{label_width}}"
                f"{n_str:>{n_width}}"
                f"{valid_pct_str:>{valid_pct_width}}"
                f"{total_pct_str:>{total_pct_width}}"
                f"{flag}"
            )
            print(row_line)
    
    print(f"{separator}\n")
