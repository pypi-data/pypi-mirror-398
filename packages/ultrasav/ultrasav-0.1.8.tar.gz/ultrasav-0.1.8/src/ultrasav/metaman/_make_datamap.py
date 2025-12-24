import narwhals as nw
from narwhals.typing import FrameT
import polars as pl
import pandas as pd
from ._map_engine import map_engine


def make_datamap(
    df: pl.DataFrame | pd.DataFrame,
    meta,
    output_format: str | None = None
) -> pl.DataFrame | pd.DataFrame:
    """
    Create a validation data map from dataframe and pyreadstat meta object.
    
    This wrapper function internally calls map_engine() to generate the core_map,
    then adds computed columns for missing value labels, missing data flags, 
    and base_n calculations.
    
    Parameters:
    -----------
    df : pl.DataFrame | pd.DataFrame
        The data dataframe (Polars or Pandas)
    meta : pyreadstat metadata object
        The metadata object returned by pyreadstat when reading SPSS files
    output_format : str | None
        Output format - either "polars" or "pandas"
        If None, will match the input dataframe type
    
    Returns:
    --------
    pl.DataFrame | pd.DataFrame
        A data map dataframe with columns:
        - variable: variable name
        - variable_label: variable label text
        - variable_type: variable type (single-select, multi-select, numeric, text, date)
        - value_code: value code (None for missing data row, actual codes for values)
        - value_label: value label ("NULL" for missing data row, labels or None for unlabeled)
        - value_n: count of occurrences
        - base_n: total non-NULL count for the variable
        - base_pct: percentage of value_n over base_n (null if base_n is 0)
        - total_n: total count of value_n per variable
        - total_pct: percentage of value_n over total_n (null if total_n is 0)
        - missing_value_label: "Yes" if value exists in data but not in meta, else "No"
        - missing_data: "Yes" for NULL data rows only, else "No"
    
    Examples:
    ---------
    >>> import pyreadstat
    >>> df, meta = pyreadstat.read_sav('data.sav', user_missing=True)
    >>> data_map = make_datamap(df, meta)
    >>> data_map.write_excel('datamap.xlsx')  # For Polars
    >>> # or
    >>> data_map_pd = make_datamap(df, meta, output_format="pandas")
    >>> data_map_pd.to_excel('datamap.xlsx', index=False)  # For Pandas
    """
    
    # First, get the core_map from map_engine
    core_map = map_engine(df, meta, output_format)
    
    # Then apply the data map transformations
    data_map = nw.from_native(core_map).with_columns(
        # missing_label: "Yes" if value exists in data but not in meta for single-select or multi-select variables
        nw.when(
            (~nw.col("value_code").is_null()) &  # Changed from is_not_null()
            (nw.col("value_label").is_null())
        ).then(nw.lit("Yes"))
        .otherwise(nw.lit("No"))
        .alias("missing_value_label"),
        
        # missing_data: "Yes" for NULL data rows only
        nw.when(nw.col("value_label") == "NULL")
        .then(nw.lit("Yes"))
        .otherwise(nw.lit("No"))
        .alias("missing_data"),  # Added missing comma
        
        # Calculate base_n: sum of non-NULL value_n per variable
        nw
        .when(nw.col("value_label") == "NULL")
        .then(nw.col("value_n"))
        .otherwise(
             nw
             .when((nw.col("value_label") != "NULL") | (nw.col("value_label").is_null()))
             .then(nw.col("value_n"))  
             .sum()  
             .over("variable")  
        )
        .alias("base_n")
        
    ).with_columns(
        # Calculate base_pct (might create value 'NaN' if base_n is 0)
        (nw.col("value_n") / nw.col("base_n")).alias("base_pct")
    ).with_columns(
        # Replace NaN with null
        nw.when(nw.col("base_pct").is_nan())
        .then(None)  # Convert NaN to null
        .otherwise(nw.col("base_pct"))
        .alias("base_pct")
    ).with_columns(
        # Calculate total_n per variable for total_pct
        nw.col('value_n').sum().over("variable").alias('total_n')
    ).with_columns(
        # Calculate total_pct
        (nw.col('value_n')/nw.col('total_n')).alias('total_pct')
    ).with_columns(
        # Replace NaN with null
        nw.when(nw.col("total_pct").is_nan())
        .then(None)  # Convert NaN to null
        .otherwise(nw.col("total_pct"))
        .alias("total_pct")
    ).select([
            # Reorder columns: variable info first, then everything else
            'variable',
            'variable_label',
            'variable_type',
            'value_code',
            'value_label',
            'value_n',
            'base_n',
            'base_pct',
            'total_n',
            'total_pct',
            'missing_value_label',
            'missing_data'
        ]).to_native()
    
    return data_map
