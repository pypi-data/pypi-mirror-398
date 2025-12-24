#v2
from typing import Any
import narwhals as nw
from narwhals.typing import IntoFrame


class Data:
    """
    DataFrame handler for tidyspss 2.0 - manages all data transformations.
    
    The Data class is part of tidyspss's two-track architecture where Data and 
    Metadata are completely independent until write time. This class handles all 
    dataframe operations (renaming, selecting, filtering, transforming) while 
    remaining completely agnostic to either pandas or polars dataframes. 
    
    Key Design Principles
    ---------------------
    - **DataFrame Agnostic**: Works with any narwhals-supported dataframe 
      (pandas, Polars, cuDF, Modin, PyArrow, DuckDB, etc.)
    - **No Metadata Awareness**: Never reads or modifies metadata - that's 
      handled by the separate Metadata class
    - **Chainable Operations**: All methods return self for fluent API usage
    - **Explicit Control**: No automatic transfers or hidden magic - you control 
      exactly what happens to your data
    
    Workflow
    --------
    1. Create from a dataframe: `data = Data(df)`
    2. Transform as needed: `data.rename(...).select(...).replace(...)`
    3. Combine with metadata only at write: `write_sav(data, meta, "output.sav")`
    
    Examples
    --------
    >>> import pandas as pd
    >>> from tidyspss import Data
    >>> 
    >>> # Create from any supported dataframe
    >>> df = pd.DataFrame({'Q1': [1, 2, 3], 'Q2': [4, 5, 6]})
    >>> data = Data(df)
    >>> 
    >>> # Chain operations
    >>> data = (data
    ...     .rename({'Q1': 'satisfaction'})
    ...     .select(['satisfaction'])
    ...     .replace({'satisfaction': {1: 10, 2: 20}})
    ... )
    >>> 
    >>> # Convert back to native format when needed
    >>> result_df = data.to_native()
    
    Notes
    -----
    When you rename columns in Data, any associated metadata must be explicitly
    updated in the Metadata object. The two classes do not communicate - this is
    by design for explicit control and clean separation of concerns.
    """
    
    def __init__(self, df: IntoFrame) -> None:
        """
        Initialize with a DataFrame from any narwhals-supported library.
        
        Parameters
        ----------
        df : IntoFrame
            A DataFrame from any narwhals-supported library including:
            pandas, Polars, cuDF, Modin, PyArrow, DuckDB, and others.
        """
        self._nw_df = nw.from_native(df)
    
    def rename(self, mapping: dict[str, str]) -> 'Data':
        """
        Rename columns and return self for chaining.
        
        Parameters
        ----------
        mapping : dict[str, str]
            Mapping of old column names to new column names.
        
        Returns
        -------
        Data
            Self for method chaining.
            
        Notes
        -----
        Remember to update metadata for renamed columns in the Metadata object.
        Old column metadata does not automatically transfer to new names.
        """
        self._nw_df = self._nw_df.rename(mapping)
        return self
    
    def select(self, columns: str | list[str]) -> 'Data':
        """
        Select specified columns and return self for chaining.
        
        Parameters
        ----------
        columns : str or list[str]
            Column name(s) to select.
        
        Returns
        -------
        Data
            Self for method chaining.
        """
        self._nw_df = self._nw_df.select(columns)
        return self
    
    def drop(self, columns: str | list[str]) -> 'Data':
        """
        Drop columns and return self for chaining.
        
        Parameters
        ----------
        columns : str or list[str]
            Column name(s) to drop.
        
        Returns
        -------
        Data
            Self for method chaining.
        """
        self._nw_df = self._nw_df.drop(columns)
        return self
    
    def replace(self, replacements: dict[str, dict[Any, Any]]) -> 'Data':
        """
        Replace values in specified columns.
        
        Parameters
        ----------
        replacements : dict[str, dict[Any, Any]]
            Nested dictionary where keys are column names and values are
            dictionaries mapping old values to new values.
            Use None as a key to replace null values.
        
        Returns
        -------
        Data
            Self for method chaining.
        
        Examples
        --------
        >>> data.replace({
        ...     'column1': {1: 'one', 2: 'two', None: 'missing'},
        ...     'column2': {'old': 'new'}
        ... })
        """
        columns_to_update = []

        for col, mapping in replacements.items():
            col_expr = nw.col(col)

            # Handle null replacements separately
            if None in mapping:
                null_replacement = mapping[None]
                col_expr = col_expr.fill_null(null_replacement)
                # Create new mapping without None
                mapping = {k: v for k, v in mapping.items() if k is not None}

            # Handle regular value replacements
            for old_val, new_val in mapping.items():
                col_expr = nw.when(col_expr == old_val).then(new_val).otherwise(col_expr)

            columns_to_update.append(col_expr.alias(col))

        self._nw_df = self._nw_df.with_columns(columns_to_update)
        return self
    
    def move(
        self,
        config: dict[str, Any] | None = None,
        first: list[str | list[str]] | None = None,
        last: list[str | list[str]] | None = None,
        before: dict[str, str | list[str]] | None = None,
        after: dict[str, str | list[str]] | None = None
    ) -> 'Data':
        """
        Move columns in the DataFrame using various positioning strategies.
        
        This method allows flexible column reordering using four positioning strategies
        that can be combined. Columns can be specified individually, as lists, or using
        slice notation (e.g., 'Q1_1:Q1_25' to select a range of columns).
        
        Parameters
        ----------
        config : dict[str, Any], optional
            Dictionary containing any of the positioning parameters below.
            If provided, overrides individual parameters.
        first : list[str | list[str]], optional
            Columns to position at the beginning of the DataFrame.
            Supports slice notation like 'Q1_1:Q1_5'.
        last : list[str | list[str]], optional  
            Columns to position at the end of the DataFrame.
            Supports slice notation.
        before : dict[str, str | list[str]], optional
            Dictionary mapping anchor columns to columns that should be
            positioned before them. Keys are anchor column names, values
            are columns to insert before the anchor.
        after : dict[str, str | list[str]], optional
            Dictionary mapping anchor columns to columns that should be
            positioned after them. Keys are anchor column names, values
            are columns to insert after the anchor.
        
        Returns
        -------
        Data
            Self for method chaining.
        
        Examples
        --------
        >>> # Move columns to the beginning
        >>> data.move(first=['id', 'name'])
        
        >>> # Move columns to the end
        >>> data.move(last=['created_at', 'updated_at'])
        
        >>> # Move specific columns before/after anchors
        >>> data.move(
        ...     before={'age': ['birth_date', 'birth_year']},
        ...     after={'name': ['first_name', 'last_name']}
        ... )
        
        >>> # Use slice notation for sequential columns
        >>> data.move(first=['Q1_1:Q1_5'], last=['Q10_1:Q10_20'])
        
        >>> # Complex combination
        >>> data.move(
        ...     first=['respondent_id'],
        ...     last=['timestamp'],
        ...     before={'Q2_1': 'Q1_1:Q1_10'},
        ...     after={'demographics': ['age', 'gender', 'income']}
        ... )
        
        Notes
        -----
        - Operations are applied in order: first → before/after → last
        - Columns can only appear in one positioning directive
        - Non-existent columns will raise a ValueError
        - Slice notation 'start:end' includes both endpoints
        """
        # Use config if provided, otherwise use individual parameters
        if config:
            first = config.get('first', first)
            last = config.get('last', last)
            before = config.get('before', before)
            after = config.get('after', after)
        
        # Get current column order
        current_cols = list(self._nw_df.columns)
        
        # Reorder columns based on specifications
        new_order = self._calculate_column_order(
            current_cols, first, last, before, after
        )
        
        # Apply the new order
        self._nw_df = self._nw_df.select(new_order)
        return self
    
    def _calculate_column_order(
        self,
        current_cols: list[str],
        first: list[str | list[str]] | None,
        last: list[str | list[str]] | None,
        before: dict[str, str | list[str]] | None,
        after: dict[str, str | list[str]] | None
    ) -> list[str]:
        """
        Calculate new column order based on positioning specifications.
        
        Parameters
        ----------
        current_cols : list[str]
            Current column order.
        first : list[str | list[str]] | None
            Columns to move to beginning.
        last : list[str | list[str]] | None
            Columns to move to end.
        before : dict[str, str | list[str]] | None
            Columns to position before anchors.
        after : dict[str, str | list[str]] | None
            Columns to position after anchors.
        
        Returns
        -------
        list[str]
            New column order.
        
        Raises
        ------
        ValueError
            If any specified columns don't exist or if there are conflicts.
        """
        # First, validate all columns exist and detect conflicts
        errors = []
        current_cols_set = set(current_cols)
        
        # Check 'first' columns exist
        if first:
            expanded_first = []
            for item in first:
                expanded_first.extend(self._expand_column_spec(item, current_cols))
            missing = [col for col in expanded_first if col not in current_cols_set]
            if missing:
                errors.append(f"'first' contains non-existent columns: {missing}")
            # Update first to be the expanded version
            first = expanded_first
        
        # Check 'last' columns exist
        if last:
            expanded_last = []
            for item in last:
                expanded_last.extend(self._expand_column_spec(item, current_cols))
            missing = [col for col in expanded_last if col not in current_cols_set]
            if missing:
                errors.append(f"'last' contains non-existent columns: {missing}")
            # Update last to be the expanded version
            last = expanded_last
        
        # Check 'before' anchor columns and values
        if before:
            # Check anchor columns (keys)
            missing_anchors = [col for col in before.keys() if col not in current_cols_set]
            if missing_anchors:
                errors.append(f"'before' references non-existent anchor columns: {missing_anchors}")
            
            # Check columns to position (values)
            for anchor, cols in before.items():
                expanded_cols = self._expand_column_spec(cols, current_cols)
                missing = [col for col in expanded_cols if col not in current_cols_set]
                if missing:
                    errors.append(f"'before[{anchor}]' contains non-existent columns: {missing}")
        
        # Check 'after' anchor columns and values
        if after:
            # Check anchor columns (keys)
            missing_anchors = [col for col in after.keys() if col not in current_cols_set]
            if missing_anchors:
                errors.append(f"'after' references non-existent anchor columns: {missing_anchors}")
            
            # Check columns to position (values)
            for anchor, cols in after.items():
                expanded_cols = self._expand_column_spec(cols, current_cols)
                missing = [col for col in expanded_cols if col not in current_cols_set]
                if missing:
                    errors.append(f"'after[{anchor}]' contains non-existent columns: {missing}")
        
        # Raise error if any issues found
        if errors:
            raise ValueError("Column positioning errors:\n" + "\n".join(errors))
        
        # Build the new column order
        new_order = []
        
        # Handle 'first' columns (already expanded above)
        first_set = set(first) if first else set()
        if first:
            new_order.extend(first)
        
        # Identify columns that should be positioned relative to anchors
        relatively_positioned = set()
        
        if before:
            for cols in before.values():
                expanded_cols = self._expand_column_spec(cols, current_cols)
                relatively_positioned.update(expanded_cols)
        
        if after:
            for cols in after.values():
                expanded_cols = self._expand_column_spec(cols, current_cols)
                relatively_positioned.update(expanded_cols)
        
        # Handle 'last' columns set (already expanded above)
        last_set = set(last) if last else set()
        
        # Track what we've already added to avoid duplicates
        positioned = set(first) if first else set()
        
        # Process columns in original order, handling before/after relationships
        for col in current_cols:
            # Skip if already positioned (in first)
            if col in positioned:
                continue
            
            # Skip if this column should be positioned relatively
            if col in relatively_positioned:
                continue
            
            # Skip if this column goes in 'last'
            if col in last_set:
                continue
            
            # Handle 'before' - insert columns before current anchor
            if before and col in before:
                cols_to_insert = self._expand_column_spec(before[col], current_cols)
                
                for insert_col in cols_to_insert:
                    if insert_col not in positioned:
                        new_order.append(insert_col)
                        positioned.add(insert_col)
            
            # Add current column (the anchor)
            new_order.append(col)
            positioned.add(col)
            
            # Handle 'after' - insert columns after current anchor
            if after and col in after:
                cols_to_insert = self._expand_column_spec(after[col], current_cols)
                
                for insert_col in cols_to_insert:
                    if insert_col not in positioned:
                        new_order.append(insert_col)
                        positioned.add(insert_col)
        
        # Handle 'last' columns (already expanded above)
        if last:
            new_order.extend(last)
        
        return new_order

    def _expand_column_spec(
        self, 
        spec: str | list[str], 
        current_cols: list[str]
    ) -> list[str]:
        """
        Expand column specifications including slice notation into list of columns.
        
        Parameters
        ----------
        spec : str or list[str]
            Column specification. Can be:
            - Single column name: 'col1'
            - List of column names: ['col1', 'col2']
            - Slice notation: 'col1:col5'
            - List with mixed notation: ['col1', 'col2:col5', 'col6']
        current_cols : list[str]
            Current column order in the DataFrame.
        
        Returns
        -------
        list[str]
            Expanded list of column names.
        
        Raises
        ------
        ValueError
            If any referenced columns don't exist.
        """
        if isinstance(spec, list):
            # If it's a list, expand each element and flatten
            expanded = []
            for item in spec:
                if isinstance(item, str) and ':' in item:
                    # This item is slice notation - split and strip whitespace
                    start_col, end_col = [col.strip() for col in item.split(':')]
                    try:
                        start_idx = current_cols.index(start_col)
                        end_idx = current_cols.index(end_col)
                        expanded.extend(current_cols[start_idx:end_idx + 1])
                    except ValueError:
                        if start_col not in current_cols:
                            raise ValueError(f"Start column '{start_col}' not found in current columns")
                        if end_col not in current_cols:
                            raise ValueError(f"End column '{end_col}' not found in current columns")
                else:
                    # Regular column name
                    expanded.append(item)
            return expanded
        elif isinstance(spec, str) and ':' in spec:
            # Single string with slice notation - split and strip whitespace
            start_col, end_col = [col.strip() for col in spec.split(':')]
            try:
                start_idx = current_cols.index(start_col)
                end_idx = current_cols.index(end_col)
            except ValueError:
                if start_col not in current_cols:
                    raise ValueError(f"Start column '{start_col}' not found in current columns")
                if end_col not in current_cols:
                    raise ValueError(f"End column '{end_col}' not found in current columns")
            return current_cols[start_idx:end_idx + 1]
        elif isinstance(spec, str):
            # Single column name
            return [spec]
        else:
            # Already a list without slice notation or other type
            return spec if isinstance(spec, list) else [spec]
    
    def to_native(self) -> IntoFrame:
        """
        Convert back to original DataFrame type.
        
        Returns
        -------
        IntoFrame
            DataFrame in its original library format (pandas, polars, etc.).
        """
        return self._nw_df.to_native()
    
    @property
    def columns(self) -> list[str]:
        """Get list of column names."""
        return list(self._nw_df.columns)
    
    @property
    def shape(self) -> tuple[int, int]:
        """Get dataframe shape (rows, cols)."""
        return self._nw_df.shape
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Data(shape={self.shape}, columns={len(self.columns)})"
