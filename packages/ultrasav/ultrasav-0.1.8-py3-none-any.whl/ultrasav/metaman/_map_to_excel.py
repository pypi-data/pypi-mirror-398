import polars as pl
import xlsxwriter
from typing import Any
from pathlib import Path
from ._color_schemes import get_color_scheme
from ._write_excel_engine import write_excel_engine
# version_2


def map_to_excel(
    df: pl.DataFrame,
    file_path: str | Path,
    merge_columns: list[str] | None = None,
    column_widths: dict[str, int] | None = None,
    header_format: dict[str, Any] | None = None,
    column_formats: dict[str, dict[str, Any]] | None = None,
    merge_format: dict[str, Any] | None = None,
    group_border_format: dict[str, Any] | None = None,
    alternating_row_colors: tuple[str, str] | None = None,
    alternating_group_formats: tuple[dict[str, Any], dict[str, Any]] | None = None,
    sheet_name: str = "Sheet1",
    freeze_panes: tuple | None = (1, 0),
) -> None:
    """
    Write survey metadata DataFrame to Excel with standardized formatting.
    
    This is a convenience wrapper around write_excel_engine() with pre-configured
    default formatting optimized for survey data maps and metadata. All parameters
    can still be overridden if needed.
    
    Parameters
    ----------
    df : pl.DataFrame
        The DataFrame to write to Excel.
    file_path : str or Path
        Path to the output Excel file. Parent directories will be created if needed.
    merge_columns : list of str, optional
        Column names to merge. Defaults to ['variable', 'variable_label', 'variable_type'].
        Pass an empty list [] to disable merging, or provide custom columns to override.
    column_widths : dict of str to int, optional
        Mapping of column names to widths in pixels. Defaults include optimized widths
        for common survey metadata columns. User values override defaults.
    header_format : dict, optional
        xlsxwriter format properties for header row. Defaults to bold, 12pt font
        with gray bottom border. User values override defaults.
    column_formats : dict of str to dict, optional
        Mapping of column names to xlsxwriter format dictionaries. Defaults include
        centered formatting for value_code and percentage formatting for base_pct.
        User values override defaults.
    merge_format : dict, optional
        xlsxwriter format properties for merged cells. Defaults to left-aligned
        with vertical centering. User values override defaults.
    group_border_format : dict, optional
        Border format for merge group bottoms. Defaults to thick green border.
        User values override defaults.
    alternating_row_colors : tuple of (str, str), optional
        Two colors to alternate between merge groups. Defaults to light and darker grey.
        Pass None to disable alternating colors, or provide custom colors to override.
        Note: If alternating_group_formats is provided, it takes precedence.
    alternating_group_formats : tuple of (dict, dict), optional
        Two complete format dictionaries to alternate between merge groups.
        Provides full control over font color, borders, background, etc.
        Takes precedence over alternating_row_colors. Pass None to use colors only.
    sheet_name : str, default "Sheet1"
        Name of the worksheet.
    freeze_panes : tuple of (row, col), optional
        Position to freeze panes. Default (1, 0) freezes the header row.
    
    Examples
    --------
    Simple usage with all defaults:
    
    >>> df = pl.DataFrame({
    ...     "variable": ["Q1", "Q1", "Q2"],
    ...     "variable_label": ["Age", "Age", "Gender"],
    ...     "variable_type": ["single", "single", "single"],
    ...     "value_code": [1, 2, 1],
    ...     "value_label": ["18-25", "26+", "Male"]
    ... })
    >>> map_to_excel(df, "survey_map.xlsx")
    
    Override with custom alternating formats:
    
    >>> map_to_excel(
    ...     df, 
    ...     "survey_map.xlsx",
    ...     alternating_group_formats=(
    ...         {"bg_color": "#F0F8FF", "font_color": "#00008B", "border": 1},
    ...         {"bg_color": "#FFF0F5", "font_color": "#8B008B", "border": 1}
    ...     )
    ... )
    
    Custom alternating colors only:
    
    >>> map_to_excel(
    ...     df,
    ...     "survey_map.xlsx", 
    ...     alternating_row_colors=("#FFE6E6", "#FFCCCC")  # Light red alternating
    ... )
    
    Disable all alternating:
    
    >>> map_to_excel(
    ...     df, 
    ...     "survey_map.xlsx", 
    ...     alternating_row_colors=None,
    ...     alternating_group_formats=None
    ... )
    
    Notes
    -----
    This function is specifically designed for survey metadata with standard columns
    like variable, variable_label, value_code, etc. It provides sensible defaults
    while maintaining full flexibility to override any formatting parameter.
    
    The default formatting includes:
    - Merging by variable, variable_label, and variable_type
    - Optimized column widths for survey metadata
    - Professional header styling with borders
    - Centered value codes
    - Percentage formatting for base_pct column (0.00%)
    - Green group borders for visual separation
    - Classic Grey Scale alternating formats with borders and professional fonts
    
    See Also
    --------
    write_excel_with_merge : The underlying function with full control
    """
    # Validate input DataFrame type
    if not isinstance(df, pl.DataFrame):
        # Check specifically for pandas DataFrame
        df_type = type(df).__module__ + "." + type(df).__name__
        if "pandas" in df_type.lower():
            raise TypeError(
                f"Expected a Polars DataFrame, but received a pandas DataFrame. "
                f"Convert with: pl.from_pandas(df)"
            )
        else:
            raise TypeError(
                f"Expected a Polars DataFrame, but received {type(df).__name__}. "
                f"Please pass a pl.DataFrame."
            )
    
    # Define default values
    default_merge_columns = [
        'variable',
        'variable_label',
        'variable_type',
    ]
    
    default_column_widths = {
        "variable": 100,
        "variable_label": 400,
        "variable_type": 100,
        "value_code": 80,
        "value_label": 200,
        "value_n": 100,
        "base_n": 100,
        "base_pct": 100,
        "total_n": 100,
        "total_pct": 100,
        "missing_value_label": 130,
        "missing_data": 120
    }
    
    default_header_format = {
        "bold": True,
        "font_size": 12,
        "bottom": 1,
        "bottom_color": "#808080"
    }
    
    default_column_formats = {
        "variable_label": {
            "text_wrap": True
        },
        "value_code": {
            "num_format": "0",
            "align": "center",
            "valign": "vcenter"
        },
        "base_pct": {
            "num_format": "0.0%",
            "align": "right",
            "valign": "vcenter"
        },
        "total_pct": {
            "num_format": "0.0%",
            "align": "right",
            "valign": "vcenter"
        }
    }
    
    default_merge_format = {
        "text_wrap": True, # This is needs to be true for triggering the wrap
        "align": "left",
        "valign": "vcenter",
    }
    
    default_group_border_format = {
        # "bottom": 4,
        # "bottom_color": "#4d6b4a"
        # commented out if default_alternating_formats are provided below
    }
    
    # Classic Grey Scale as default alternating formats
    default_alternating_formats = (
        get_color_scheme("classic_grey")
        # get_color_scheme("pastel_green")
        # get_color_scheme("pastel_blue")
        # get_color_scheme("pastel_purple")
    )
        # {
        #     "bg_color": "#F5F5F5",      # Light grey
        #     "font_color": "#1A1A1A",     # Near black
        #     "border": 1,
        #     "border_color": "#D9D9D9",
        #     "valign": "vcenter"
        # },
        # {
        #     "bg_color": "#FFFFFF",      # Pure white
        #     "font_color": "#2C2C2C",     # Charcoal grey
        #     "border": 1,
        #     "border_color": "#D9D9D9",
        #     "valign": "vcenter"
        # }
    
    # Merge user-provided values with defaults
    # For merge_columns, use default only if None, allow empty list to disable
    if merge_columns is None:
        merge_columns = default_merge_columns
    
    # For column_widths, merge user values with defaults
    if column_widths is None:
        column_widths = default_column_widths
    else:
        column_widths = {**default_column_widths, **column_widths}
    
    # For header_format, merge user values with defaults
    if header_format is None:
        header_format = default_header_format
    else:
        header_format = {**default_header_format, **header_format}
    
    # For column_formats, merge nested dictionaries
    if column_formats is None:
        column_formats = default_column_formats
    else:
        merged_formats = default_column_formats.copy()
        for col, fmt in column_formats.items():
            if col in merged_formats:
                # Merge the format dicts for this column
                merged_formats[col] = {**merged_formats[col], **fmt}
            else:
                merged_formats[col] = fmt
        column_formats = merged_formats
    
    # For merge_format, merge user values with defaults
    if merge_format is None:
        merge_format = default_merge_format
    else:
        merge_format = {**default_merge_format, **merge_format}
    
    # For group_border_format, merge user values with defaults
    if group_border_format is None:
        group_border_format = default_group_border_format
    else:
        group_border_format = {**default_group_border_format, **group_border_format}
    
    # For alternating formats, use the comprehensive defaults if neither is specified
    if alternating_group_formats is None and alternating_row_colors is None:
        # Neither specified, use default comprehensive formats
        alternating_group_formats = default_alternating_formats
    # If either is explicitly set (including to None), use as-is
    
    # Call the main function with merged parameters
    write_excel_engine(
        df=df,
        file_path=file_path,
        merge_columns=merge_columns,
        column_widths=column_widths,
        header_format=header_format,
        column_formats=column_formats,
        merge_format=merge_format,
        group_border_format=group_border_format,
        alternating_row_colors=alternating_row_colors,
        alternating_group_formats=alternating_group_formats,
        sheet_name=sheet_name,
        freeze_panes=freeze_panes
    )
    
    # Success message
    output_path = Path(file_path)
    print(f"✓ Saved: {output_path.name}") #({df.shape[0]:,} rows × {df.shape[1]} cols)"