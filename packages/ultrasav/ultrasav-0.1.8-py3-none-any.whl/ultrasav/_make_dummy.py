import narwhals as nw
from narwhals.typing import IntoFrameT


def make_dummies(
    df: IntoFrameT, 
    column: str, 
    level: int | list[int | float] = 0,
    *,
    prefix: str | None = None, 
    drop_original: bool = False, 
    detect_special: bool = True
) -> IntoFrameT:
    """
    Create dummy variables for all specified categories.
    Works with both pandas and polars DataFrames via Narwhals.
    Convert single-select question into binary variables.

    Parameters:
    - df: pandas or polars DataFrame
    - column: name of column to create dummies from (must be numeric type)
    - level: Can be either:
             * int: number of categories to create (1 to level) [default: 0]
                    If level=0, only values found in data will get dummy columns
             * list: explicit list of values to create dummies for (e.g., [1,2,3,4,5,99])
                     Creates dummy columns for ALL listed values, even if not present in data
                     This ensures consistent columns across datasets
    - prefix: prefix for dummy column names (default: same as column name)
    - drop_original: if True, drop the original column [default: False]
    - detect_special: if True, automatically create dummies for any values found in data
                      that are outside the specified level range (e.g., 99 for "don't know")
                      [default: True]

    Returns:
    - DataFrame (same type as input) with dummy columns added
    - Missing values: If the original column has null/NaN, all dummy columns for that row will be null
    
    Examples:
    >>> make_dummies(df, "q1", level=5)  
    # Creates dummies for 1-5 + any special values found (like 99, -1)
    
    >>> make_dummies(df, "q1", level=[1,2,3,4,5])  
    # Creates dummies for 1-5 + any special values found
    
    >>> make_dummies(df, "q1", level=[1,2,3,4,5], detect_special=False)  
    # Creates dummies for ONLY 1-5, ignoring any other values
    """
    df_nw = nw.from_native(df)
    
    # Check if column is numeric
    col_dtype = df_nw.schema[column]
    numeric_types = [
        nw.Int8, nw.Int16, nw.Int32, nw.Int64,
        nw.UInt8, nw.UInt16, nw.UInt32, nw.UInt64,
        nw.Float32, nw.Float64
    ]
    
    if col_dtype not in numeric_types:
        raise TypeError(
            f"Column '{column}' must be numeric (int or float). "
            f"Got {col_dtype}. Please convert string columns to numeric first."
        )
    
    if prefix is None:
        prefix = column
    
    is_list: bool = isinstance(level, (list, tuple))
    
    # Collect all expressions to apply at once
    expressions: list = []
    
    # Determine base categories to create
    base_categories: list[int | float]
    if is_list:
        base_categories = sorted(level)  # type: ignore
    elif level > 0:
        base_categories = list(range(1, level + 1))
    else:
        base_categories = []
    
    # Detect special values if requested
    special_vals: list[int | float] = []
    if detect_special:
        unique_vals: list = (
            df_nw.select(nw.col(column))
            .filter(~nw.col(column).is_null())
            .unique()
            .to_native()[column]
            .to_list()
        )
        
        if is_list:
            # For list mode: any value not in the list is special
            special_vals = sorted([v for v in unique_vals if v not in level])
        elif level > 0:
            # For integer mode: any value outside 1-level range is special
            special_vals = sorted([v for v in unique_vals if v < 1 or v > level])
        else:
            # For level=0: all values found are included
            special_vals = sorted(unique_vals)
    
    # Create expressions for base categories
    for val in base_categories:
        if isinstance(val, float) and val == int(val):
            val = int(val)
        col_name: str = f"{prefix}_{val}"
        
        expr = (
            nw.when(nw.col(column).is_null())
            .then(None)
            .otherwise((nw.col(column) == val).cast(nw.Int8))
            .alias(col_name)
        )
        expressions.append(expr)
    
    # Create expressions for special values
    for val in special_vals:
        if isinstance(val, float) and val == int(val):
            val = int(val)
        col_name = f"{prefix}_{val}"
        
        expr = (
            nw.when(nw.col(column).is_null())
            .then(None)
            .otherwise((nw.col(column) == val).cast(nw.Int8))
            .alias(col_name)
        )
        expressions.append(expr)
    
    # Apply all transformations in one go
    if expressions:
        df_nw = df_nw.with_columns(*expressions)
    
    if drop_original:
        df_nw = df_nw.drop(column)
    
    return nw.to_native(df_nw)