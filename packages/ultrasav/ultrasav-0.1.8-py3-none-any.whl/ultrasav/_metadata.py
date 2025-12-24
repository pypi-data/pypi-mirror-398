#_v5_fix_metadata_double_wrap
import warnings
from typing import Any
from dataclasses import dataclass, field
from copy import deepcopy

@dataclass
class Metadata:
    """
    A class to handle SPSS metadata updates for writing SAV files.
    
    This class takes the original pyreadstat metadata and allows explicit updates.
    It does NOT track dataframe changes - users must explicitly update metadata
    to match their dataframe transformations.
    
    All metadata updates MERGE with original metadata - they don't replace it.
    
    Parameters
    ----------
    meta_obj : pyreadstat metadata object, Metadata, dict, or None
        Can be:
        - pyreadstat metadata object from read_sav()
        - Another Metadata instance (creates a deep copy)
        - dict with metadata parameters to set
        - None for empty metadata
    
    Examples
    --------
    >>> # From pyreadstat
    >>> df, meta_raw = pyreadstat.read_sav("file.sav")
    >>> meta = Metadata(meta_raw)
    
    >>> # Copy from another Metadata object
    >>> meta_copy = Metadata(meta)
    
    >>> # Empty metadata
    >>> meta = Metadata()
    
    >>> # With initial values
    >>> meta = Metadata({"column_labels": {"Q1": "Question 1"}})
    """
    
    # Store the original metadata object
    _original_meta: Any | None = field(default=None, init=False)
    
    # User updates - these will override original metadata when provided
    _user_column_labels: dict[str, str] | None = field(default=None, init=False)
    _user_variable_value_labels: dict[str, dict[int | float | str, str]] | None = field(default=None, init=False)
    _user_variable_format: dict[str, str] | None = field(default=None, init=False)
    _user_variable_measure: dict[str, str] | None = field(default=None, init=False)
    _user_variable_display_width: dict[str, int] | None = field(default=None, init=False)
    _user_missing_ranges: dict[str, list] | None = field(default=None, init=False)
    _user_note: str | list[str] | None = field(default=None, init=False)
    _user_file_label: str | None = field(default=None, init=False)
    _user_compress: bool | None = field(default=None, init=False)
    _user_row_compress: bool | None = field(default=None, init=False)
    
    def __init__(self, meta_obj=None):
        """
        Initialize Metadata instance.
        
        Parameters
        ----------
        meta_obj : pyreadstat metadata object, Metadata, dict, or None
            Can be pyreadstat metadata, another Metadata instance, 
            a dict of parameters, or None for empty
        """
        # Initialize all fields
        self._original_meta = None
        self._user_column_labels = None
        self._user_variable_value_labels = None
        self._user_variable_format = None
        self._user_variable_measure = None
        self._user_variable_display_width = None
        self._user_missing_ranges = None
        self._user_note = None
        self._user_file_label = None
        self._user_compress = None
        self._user_row_compress = None
        
        if meta_obj is not None:
            # Check if it's already a Metadata instance - copy its internals
            if isinstance(meta_obj, Metadata):
                self._original_meta = meta_obj._original_meta
                self._user_column_labels = deepcopy(meta_obj._user_column_labels)
                self._user_variable_value_labels = deepcopy(meta_obj._user_variable_value_labels)
                self._user_variable_format = deepcopy(meta_obj._user_variable_format)
                self._user_variable_measure = deepcopy(meta_obj._user_variable_measure)
                self._user_variable_display_width = deepcopy(meta_obj._user_variable_display_width)
                self._user_missing_ranges = deepcopy(meta_obj._user_missing_ranges)
                self._user_note = deepcopy(meta_obj._user_note)
                self._user_file_label = meta_obj._user_file_label
                self._user_compress = meta_obj._user_compress
                self._user_row_compress = meta_obj._user_row_compress
            # Check if it's pyreadstat metadata (has specific attributes)
            elif hasattr(meta_obj, 'column_names') and hasattr(meta_obj, 'column_labels'):
                # It's pyreadstat metadata
                self._original_meta = meta_obj
            elif isinstance(meta_obj, dict):
                # It's user-provided dict of updates
                self.update(**meta_obj)
            else:
                # Try to detect if it's pyreadstat metadata by other attributes
                if hasattr(meta_obj, 'number_columns') or hasattr(meta_obj, 'file_label'):
                    self._original_meta = meta_obj
                else:
                    raise TypeError(
                        f"Unsupported metadata type: {type(meta_obj)}. "
                        "Expected pyreadstat metadata object, Metadata, dict, or None."
                    )
    
    @classmethod
    def from_pyreadstat(cls, meta_obj):
        """
        Create a Metadata instance from a pyreadstat metadata object.
        
        DEPRECATED: Use Metadata(meta_obj) instead.
        
        Parameters
        ----------
        meta_obj : pyreadstat metadata object or None
            The metadata object returned by pyreadstat.read_sav()
        
        Returns
        -------
        Metadata
            A new Metadata instance
        """
        warnings.warn(
            "Metadata.from_pyreadstat() is deprecated. Use Metadata(meta_obj) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return cls(meta_obj)
    
    def _merge_with_original(self, user_dict: dict | None, 
                           original_attr: str, 
                           process_values: bool = False) -> dict:
        """
        Generic method to merge user updates with original metadata.
        
        Parameters
        ----------
        user_dict : dict or None
            User-provided updates
        original_attr : str
            Name of the attribute in original metadata
        process_values : bool
            If True, process value labels (convert keys to numbers)
        
        Returns
        -------
        dict
            Merged dictionary (original + updates)
        """
        # If no user updates, return original
        if not user_dict:
            if not self._original_meta or not hasattr(self._original_meta, original_attr):
                return {}
            original = getattr(self._original_meta, original_attr)
            return original.copy() if original else {}
        
        # If no original metadata, return user updates
        if not self._original_meta or not hasattr(self._original_meta, original_attr):
            if process_values:
                # Convert keys to numbers if possible for value labels
                converted = {}
                for var, lbls in user_dict.items():
                    converted[var] = self._convert_keys_to_numbers_if_possible(lbls)
                return converted
            return user_dict.copy()
        
        # Merge: start with original, then apply user updates
        original = getattr(self._original_meta, original_attr)
        existing = original.copy() if original else {}
        
        # Apply user updates
        for key, value in user_dict.items():
            if process_values:
                existing[key] = self._convert_keys_to_numbers_if_possible(value)
            else:
                existing[key] = value
        
        return existing
    
    # ===================================================================
    # WRITABLE PROPERTIES (can be updated by user)
    # ===================================================================
    
    @property
    def column_labels(self) -> dict[str, str]:
        """Get current column labels (original + updates)."""
        if not self._user_column_labels:
            if not self._original_meta:
                return {}
            # Special handling for column_labels as it's stored differently
            if hasattr(self._original_meta, 'column_names') and hasattr(self._original_meta, 'column_labels'):
                return dict(zip(self._original_meta.column_names, 
                              self._original_meta.column_labels))
            return {}
        
        if self._original_meta is None:
            return self._user_column_labels
        
        # Start with existing labels
        existing = {}
        if hasattr(self._original_meta, 'column_names') and hasattr(self._original_meta, 'column_labels'):
            existing = dict(zip(self._original_meta.column_names, 
                              self._original_meta.column_labels))
        
        # Override with user updates
        return {**existing, **self._user_column_labels}
    
    @column_labels.setter
    def column_labels(self, value: dict[str, str]):
        """Set user column labels updates (merges with original)."""
        self._user_column_labels = value
    
    @property
    def variable_value_labels(self) -> dict[str, dict[int | float | str, str]]:
        """Get current variable value labels (original + updates)."""
        return self._merge_with_original(
            self._user_variable_value_labels,
            'variable_value_labels',
            process_values=True
        )
    
    @variable_value_labels.setter
    def variable_value_labels(self, value: dict[str, dict[int | float | str, str]]):
        """Set user variable value labels updates (merges with original)."""
        self._user_variable_value_labels = value
    
    @property
    def variable_format(self) -> dict[str, str]:
        """Get current variable formats (original + updates)."""
        # First try variable_format, then fall back to original_variable_types
        if hasattr(self._original_meta, 'variable_format') and self._original_meta.variable_format:
            return self._merge_with_original(
                self._user_variable_format,
                'variable_format'
            )
        elif hasattr(self._original_meta, 'original_variable_types') and not self._user_variable_format:
            # Use original_variable_types as fallback if no variable_format exists
            return self._original_meta.original_variable_types.copy()
        else:
            # Merge user updates with original_variable_types if available
            if self._user_variable_format:
                if hasattr(self._original_meta, 'original_variable_types'):
                    existing = self._original_meta.original_variable_types.copy()
                    for key, value in self._user_variable_format.items():
                        existing[key] = value
                    return existing
                return self._user_variable_format.copy()
            return {}
    
    @variable_format.setter
    def variable_format(self, value: dict[str, str]):
        """Set user variable format updates (merges with original)."""
        self._user_variable_format = value
    
    @property
    def variable_measure(self) -> dict[str, str]:
        """Get current variable measures (original + updates)."""
        return self._merge_with_original(
            self._user_variable_measure,
            'variable_measure'
        )
    
    @variable_measure.setter
    def variable_measure(self, value: dict[str, str]):
        """Set user variable measure updates (merges with original)."""
        self._user_variable_measure = value
    
    @property
    def variable_display_width(self) -> dict[str, int]:
        """Get current variable display widths (original + updates)."""
        return self._merge_with_original(
            self._user_variable_display_width,
            'variable_display_width'
        )
    
    @variable_display_width.setter
    def variable_display_width(self, value: dict[str, int]):
        """Set user variable display width updates (merges with original)."""
        self._user_variable_display_width = value
    
    @property
    def missing_ranges(self) -> dict[str, list] | None:
        """Get current missing ranges (original + updates)."""
        # missing_ranges follows same merge pattern
        if not self._user_missing_ranges:
            return getattr(self._original_meta, "missing_ranges", None) if self._original_meta else None
        
        if not self._original_meta or not hasattr(self._original_meta, "missing_ranges"):
            return self._user_missing_ranges
        
        # Merge: start with original, apply user updates
        original = getattr(self._original_meta, "missing_ranges", {})
        if original:
            merged = original.copy()
            for key, value in self._user_missing_ranges.items():
                merged[key] = value
            return merged
        return self._user_missing_ranges
    
    @missing_ranges.setter
    def missing_ranges(self, value: dict[str, list]):
        """Set user missing ranges (merges with original)."""
        self._user_missing_ranges = value
    
    @property
    def note(self) -> str | list[str] | None:
        """Get current note (user or original)."""
        if self._user_note is not None:
            return self._user_note
        if self._original_meta and hasattr(self._original_meta, "notes") and self._original_meta.notes:
            return self._original_meta.notes
        return None
    
    @note.setter
    def note(self, value: str | list[str]):
        """Set user note (replaces original)."""
        self._user_note = value
    
    @property
    def file_label(self) -> str:
        """Get current file label (user or original)."""
        if self._user_file_label is not None:
            return self._user_file_label
        return getattr(self._original_meta, "file_label", "") if self._original_meta else ""
    
    @file_label.setter
    def file_label(self, value: str):
        """Set user file label (replaces original)."""
        self._user_file_label = value
    
    @property
    def compress(self) -> bool:
        """Get compress setting."""
        return self._user_compress if self._user_compress is not None else False
    
    @compress.setter
    def compress(self, value: bool):
        """Set compress setting."""
        self._user_compress = value
    
    @property
    def row_compress(self) -> bool:
        """Get row_compress setting."""
        return self._user_row_compress if self._user_row_compress is not None else False
    
    @row_compress.setter
    def row_compress(self, value: bool):
        """Set row_compress setting."""
        self._user_row_compress = value
    
    # ===================================================================
    # READ-ONLY PROPERTIES (from original metadata)
    # ===================================================================
    
    # Basic file information
    @property
    def notes(self) -> str | list[str] | None:
        """Get notes from original metadata (same as note property)."""
        return self.note
    
    @property
    def creation_time(self) -> str | None:
        """Get creation time from original metadata."""
        return getattr(self._original_meta, "creation_time", None) if self._original_meta else None
    
    @property
    def modification_time(self) -> str | None:
        """Get modification time from original metadata."""
        return getattr(self._original_meta, "modification_time", None) if self._original_meta else None
    
    @property
    def file_encoding(self) -> str | None:
        """Get file encoding from original metadata."""
        return getattr(self._original_meta, "file_encoding", None) if self._original_meta else None
    
    @property
    def table_name(self) -> str | None:
        """Get table name from original metadata."""
        return getattr(self._original_meta, "table_name", None) if self._original_meta else None
    
    # Column/variable information
    @property
    def column_names(self) -> list[str]:
        """Get column names from original metadata."""
        if self._original_meta and hasattr(self._original_meta, 'column_names'):
            return list(self._original_meta.column_names)
        return []
    
    @property
    def column_names_to_labels(self) -> dict[str, str]:
        """Get column names to labels mapping (same as column_labels property)."""
        return self.column_labels
    
    @property
    def number_columns(self) -> int | None:
        """Get number of columns from original metadata."""
        return getattr(self._original_meta, "number_columns", None) if self._original_meta else None
    
    @property
    def number_rows(self) -> int | None:
        """Get number of rows from original metadata."""
        return getattr(self._original_meta, "number_rows", None) if self._original_meta else None
    
    # Variable types and formats
    @property
    def original_variable_types(self) -> dict[str, str]:
        """Get original variable types from metadata."""
        if self._original_meta and hasattr(self._original_meta, 'original_variable_types'):
            return self._original_meta.original_variable_types.copy()
        return {}
    
    @property
    def readstat_variable_types(self) -> dict[str, str]:
        """Get readstat variable types from metadata."""
        if self._original_meta and hasattr(self._original_meta, 'readstat_variable_types'):
            return self._original_meta.readstat_variable_types.copy()
        return {}
    
    # Value labels and mappings
    @property
    def value_labels(self) -> dict:
        """Get value labels from original metadata."""
        if self._original_meta and hasattr(self._original_meta, 'value_labels'):
            return self._original_meta.value_labels.copy() if self._original_meta.value_labels else {}
        return {}
    
    @property
    def variable_to_label(self) -> dict[str, str]:
        """Get variable to label mapping from original metadata."""
        if self._original_meta and hasattr(self._original_meta, 'variable_to_label'):
            return self._original_meta.variable_to_label.copy() if self._original_meta.variable_to_label else {}
        return {}
    
    # Missing value information
    @property
    def missing_user_values(self) -> dict | None:
        """Get missing user values from original metadata."""
        return getattr(self._original_meta, "missing_user_values", None) if self._original_meta else None
    
    # Display properties
    @property
    def variable_alignment(self) -> dict[str, str]:
        """Get variable alignment from original metadata."""
        if self._original_meta and hasattr(self._original_meta, 'variable_alignment'):
            return self._original_meta.variable_alignment.copy() if self._original_meta.variable_alignment else {}
        return {}
    
    @property
    def variable_storage_width(self) -> dict[str, int]:
        """Get variable storage width from original metadata."""
        if self._original_meta and hasattr(self._original_meta, 'variable_storage_width'):
            return self._original_meta.variable_storage_width.copy() if self._original_meta.variable_storage_width else {}
        return {}
    
    # Multiple response sets
    @property
    def mr_sets(self) -> dict | None:
        """Get multiple response sets from original metadata."""
        return getattr(self._original_meta, "mr_sets", None) if self._original_meta else None
    
    # ===================================================================
    # METHODS
    # ===================================================================
    
    def update(self, **kwargs) -> 'Metadata':
        """
        Update metadata with user-provided values.
        
        Parameters
        ----------
        **kwargs : dict
            Any of the writable metadata attributes (column_labels, variable_value_labels, etc.)
        
        Returns
        -------
        self
            Returns self for method chaining
        
        Examples
        --------
        >>> meta.update(
        ...     column_labels={"Q1": "Question 1"},
        ...     file_label="My Survey"
        ... )
        """
        for key, value in kwargs.items():
            if hasattr(self, key) and not key.startswith('_'):
                setattr(self, key, value)
            else:
                warnings.warn(f"Unknown metadata attribute: {key}", UserWarning, stacklevel=2)
        
        return self
    
    def _convert_keys_to_numbers_if_possible(self, value_labels_dict):
        """Convert string keys to numbers where possible (from v1.0 logic)."""
        updated = {}
        for k, v in value_labels_dict.items():
            try:
                temp = float(k)
                if temp.is_integer():
                    temp = int(temp)
                updated[temp] = v
            except (ValueError, TypeError):
                updated[k] = v
        return updated
    
    def _force_string_labels(self, labels_dict):
        """Ensure all labels are strings (from v1.0 logic)."""
        if not labels_dict:
            return {}
        fixed = {}
        for col_name, lbl_val in labels_dict.items():
            col_name_str = str(col_name)
            label_str = str(lbl_val) if lbl_val is not None else ""
            fixed[col_name_str] = label_str
        return fixed
    
    def _resolve_compress_settings(self):
        """Resolve compression settings."""
        final_compress = self.compress
        final_row_compress = self.row_compress
        
        if final_compress and final_row_compress:
            warnings.warn(
                "Both 'compress' and 'row_compress' are True; prioritizing 'compress' over 'row_compress'.",
                UserWarning,
                stacklevel=2
            )
            final_row_compress = False
        
        return final_compress, final_row_compress
    
    def get_write_params(self) -> dict[str, Any]:
        """
        Get parameters formatted for pyreadstat.write_sav().
        
        Returns
        -------
        dict
            Dictionary of parameters ready to pass to write_sav
        """
        # Ensure column labels are all strings
        column_labels = self._force_string_labels(self.column_labels)
        
        # Resolve note formatting
        final_note = self.note
        if isinstance(final_note, list):
            final_note = "\n".join(final_note)
        
        # Resolve compression settings
        final_compress, final_row_compress = self._resolve_compress_settings()
        
        params = {
            'file_label': self.file_label,
            'column_labels': column_labels if column_labels else None,
            'compress': final_compress,
            'row_compress': final_row_compress,
            'note': final_note,
            'variable_value_labels': self.variable_value_labels if self.variable_value_labels else None,
            'missing_ranges': self.missing_ranges,
            'variable_display_width': self.variable_display_width if self.variable_display_width else None,
            'variable_measure': self.variable_measure if self.variable_measure else None,
            'variable_format': self.variable_format if self.variable_format else None,
        }
        
        # Remove None values for cleaner params
        return {k: v for k, v in params.items() if v is not None}
    
    def copy(self) -> 'Metadata':
        """Create a deep copy of the metadata."""
        return deepcopy(self)
    
    def __repr__(self) -> str:
        info = []
        if self._original_meta:
            info.append(f"columns={self.number_columns}")
        if self.column_labels:
            info.append(f"labels={len(self.column_labels)}")
        if self.variable_value_labels:
            info.append(f"value_labels={len(self.variable_value_labels)}")
        
        return f"Metadata({', '.join(info)})"