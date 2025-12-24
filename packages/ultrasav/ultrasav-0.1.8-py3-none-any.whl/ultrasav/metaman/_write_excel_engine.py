import polars as pl
import xlsxwriter
from typing import Any
from pathlib import Path
from ._color_schemes import get_color_scheme
# version_6

def write_excel_engine(
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
    Write a Polars DataFrame to Excel with merged cells for consecutive duplicate values.
    
    This function extends Polars' write_excel functionality by adding support for
    merging cells when consecutive rows have identical values in specified columns.
    This is particularly useful for survey metadata, hierarchical data, or any
    dataset where visual grouping improves readability.
    
    Parameters
    ----------
    df : pl.DataFrame
        The DataFrame to write to Excel.
    file_path : str or Path
        Path to the output Excel file. Parent directories will be created if needed.
    merge_columns : list of str, optional
        Column names to merge. Cells are merged when ALL specified columns have
        consecutive duplicate values. If None, no merging is performed.
        Example: ["variable", "question_label"]
    column_widths : dict of str to int, optional
        Mapping of column names to widths in pixels.
        Example: {"variable": 200, "question_label": 500}
    header_format : dict, optional
        xlsxwriter format properties for header row.
        Example: {"bold": True, "font_color": "#4472C4", "bg_color": "#F0F0F0"}
    column_formats : dict of str to dict, optional
        Mapping of column names to xlsxwriter format dictionaries.
        Example: {"value_code": {"num_format": "0", "align": "center"}}
    merge_format : dict, optional
        xlsxwriter format properties for merged cells. Defaults to left-aligned
        with vertical centering.
        Example: {"align": "left", "valign": "vcenter", "text_wrap": True}
    group_border_format : dict, optional
        Border format to apply to the bottom row of each merge group. When set,
        adds a bottom border to all cells (merged and non-merged) at the same row
        where a merge group ends. Common usage: {"bottom": 1, "bottom_color": "#808080"}
    alternating_row_colors : tuple of (str, str), optional
        Two colors to alternate between merge groups for better visual separation.
        Groups will alternate between these background colors.
        Example: ("#F5F5F5", "#E0E0E0") for light and darker grey.
        Note: If alternating_group_formats is also provided, it takes precedence.
    alternating_group_formats : tuple of (dict, dict), optional
        Two complete format dictionaries to alternate between merge groups.
        This provides full control over all formatting aspects including font color,
        borders, background, etc. Takes precedence over alternating_row_colors.
        Example: (
            {"bg_color": "#F5F5F5", "font_color": "#000000", "border": 1},
            {"bg_color": "#E0E0E0", "font_color": "#333333", "border": 2}
        )
    sheet_name : str, default "Sheet1"
        Name of the worksheet.
    freeze_panes : tuple of (row, col), optional
        Position to freeze panes. Default (1, 0) freezes the header row.
        Set to None to disable. Example: (1, 2) freezes header and first 2 columns.
    
    Raises
    ------
    ValueError
        If merge_columns contains column names not in the DataFrame.
    TypeError
        If df is not a Polars DataFrame.
    
    Examples
    --------
    Basic usage with merged cells:
    
    >>> import polars as pl
    >>> df = pl.DataFrame({
    ...     "variable": ["S0", "S0", "S0", "S1", "S1"],
    ...     "question": ["Age?", "Age?", "Age?", "Gender?", "Gender?"],
    ...     "value_code": [1, 2, 3, 1, 2],
    ...     "value_label": ["18-25", "26-35", "36+", "Male", "Female"]
    ... })
    >>> write_excel_engine(
    ...     df=df,
    ...     file_path="survey.xlsx",
    ...     merge_columns=["variable", "question"],
    ...     column_widths={"variable": 150, "question": 300}
    ... )
    
    Advanced formatting with alternating group formats:
    
    >>> write_excel_engine(
    ...     df=df,
    ...     file_path="survey.xlsx",
    ...     merge_columns=["variable", "question"],
    ...     alternating_group_formats=(
    ...         {"bg_color": "#F0F8FF", "font_color": "#00008B", "border": 1, "border_color": "#4169E1"},
    ...         {"bg_color": "#FFF0F5", "font_color": "#8B008B", "border": 1, "border_color": "#DA70D6"}
    ...     ),
    ...     freeze_panes=(1, 2)
    ... )
    
    Notes
    -----
    - Column widths are converted from pixels to Excel character units (approx. 7 pixels per unit)
    - Merging only occurs for consecutive rows with identical values in ALL merge_columns
    - Non-consecutive duplicates are not merged (maintains data integrity)
    - Alternating formats are applied to entire merge groups, not individual rows
    - alternating_group_formats takes precedence over alternating_row_colors if both are provided
    - The function uses xlsxwriter as the backend (same as Polars' write_excel)
    
    See Also
    --------
    polars.DataFrame.write_excel : Standard Polars Excel writer without merging
    """
    # Input validation
    if not isinstance(df, pl.DataFrame):
        raise TypeError(f"Expected pl.DataFrame, got {type(df).__name__}")
    
    if df.is_empty():
        raise ValueError("Cannot write empty DataFrame to Excel")
    
    # Validate merge_columns
    if merge_columns:
        invalid_cols = set(merge_columns) - set(df.columns)
        if invalid_cols:
            raise ValueError(
                f"merge_columns contains invalid column names: {invalid_cols}. "
                f"Available columns: {df.columns}"
            )
    
    # Convert file_path to Path and ensure parent directory exists
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create workbook and worksheet
    workbook = xlsxwriter.Workbook(str(file_path))
    worksheet = workbook.add_worksheet(sheet_name)
    
    # Apply freeze panes if specified
    if freeze_panes:
        worksheet.freeze_panes(*freeze_panes)
    
    # Create formats
    fmt_header = workbook.add_format(header_format or {})
    
    # Default merge format with vertical centering
    default_merge_format = {"align": "left", "valign": "vcenter"}
    if merge_format:
        default_merge_format.update(merge_format)
    fmt_merge = workbook.add_format(default_merge_format)
    
    # Create column-specific formats
    fmt_columns = {}
    if column_formats:
        for col_name, fmt_dict in column_formats.items():
            if col_name in df.columns:
                fmt_columns[col_name] = workbook.add_format(fmt_dict)
    
    # Get column names and create index mapping
    columns = df.columns
    col_indices = {col: idx for idx, col in enumerate(columns)}
    
    # Set column widths
    if column_widths:
        for col_name, width_px in column_widths.items():
            if col_name in col_indices:
                # Convert pixels to Excel character units (approximate: 1 char ≈ 7 pixels)
                width_chars = width_px / 7
                col_idx = col_indices[col_name]
                worksheet.set_column(col_idx, col_idx, width_chars)
    
    # Write headers
    for col_idx, col_name in enumerate(columns):
        worksheet.write(0, col_idx, col_name, fmt_header)
    
    # Convert dataframe to list of dictionaries for easier processing
    data = df.to_dicts()
    
    if not merge_columns or len(data) == 0:
        # No merging needed - use standard write
        for row_idx, row_data in enumerate(data, start=1):
            for col_idx, col_name in enumerate(columns):
                value = row_data[col_name]
                cell_format = fmt_columns.get(col_name)
                worksheet.write(row_idx, col_idx, value, cell_format)
    else:
        # Write data with merging logic
        row = 1
        i = 0
        group_index = 0  # Track which group we're in for alternating formats
        
        while i < len(data):
            # Get values for merge columns in current row
            merge_values = tuple(data[i][col] for col in merge_columns)
            
            start_row = row
            j = i
            
            # Determine the formatting for this group
            group_format_dict = None
            if alternating_group_formats:
                # Use comprehensive alternating formats
                format_index = group_index % 2
                group_format_dict = alternating_group_formats[format_index]
            elif alternating_row_colors:
                # Use simple color alternation
                color_index = group_index % 2
                group_format_dict = {"bg_color": alternating_row_colors[color_index]}
            
            # Find consecutive rows with same merge column values
            while j < len(data):
                current_merge_values = tuple(data[j][col] for col in merge_columns)
                if current_merge_values != merge_values:
                    break
                
                # Determine if this is the last row in the group
                is_last_row_in_group = (j + 1 >= len(data) or 
                                       tuple(data[j + 1][col] for col in merge_columns) != merge_values)
                
                # Write all non-merge columns for this row
                for col_name in columns:
                    if col_name not in merge_columns:
                        col_idx = col_indices[col_name]
                        value = data[j][col_name]
                        
                        # Prepare format with group formatting and/or border
                        combined_format = {}
                        
                        # Add column-specific format if exists
                        if col_name in column_formats:
                            combined_format.update(column_formats[col_name])
                        
                        # Add group format (colors, borders, font, etc.)
                        if group_format_dict:
                            combined_format.update(group_format_dict)
                        
                        # Add group border if this is the last row
                        if is_last_row_in_group and group_border_format:
                            combined_format.update(group_border_format)
                        
                        # Create and apply the format
                        if combined_format:
                            cell_format = workbook.add_format(combined_format)
                        else:
                            cell_format = fmt_columns.get(col_name)
                        
                        worksheet.write(row, col_idx, value, cell_format)
                
                row += 1
                j += 1
            
            # Write/merge the merge columns
            end_row = row - 1
            for col_name in merge_columns:
                col_idx = col_indices[col_name]
                value = data[i][col_name]
                
                # Prepare format for merged cells
                combined_merge_format = default_merge_format.copy()
                
                # Add group format if specified
                if group_format_dict:
                    combined_merge_format.update(group_format_dict)
                
                # Add border if group_border_format is specified
                if group_border_format:
                    combined_merge_format.update(group_border_format)
                
                current_fmt = workbook.add_format(combined_merge_format)
                
                if end_row > start_row:
                    # Multiple rows - merge cells
                    worksheet.merge_range(start_row, col_idx, end_row, col_idx, 
                                        value, current_fmt)
                else:
                    # Single row - no merge needed
                    worksheet.write(start_row, col_idx, value, current_fmt)
            
            i = j
            group_index += 1  # Move to next group for format alternation
    
    # Close workbook to save file
    try:
        workbook.close()
    except Exception as e:
        raise IOError(f"Failed to write Excel file to {file_path}: {e}") from e
