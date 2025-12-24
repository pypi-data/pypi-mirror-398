"""
metaman - The Metadata Superhero 🦸
===================================
Metadata inspection, extraction, and reporting tools for ultrasav.

This submodule handles all metadata-related operations including:
- Extracting metadata to Python files (get_meta)
- Creating label dictionaries from Excel (make_labels)
- Building validation datamaps (make_datamap)
- Exporting formatted Excel reports (map_to_excel)
- Detecting variable types (detect_variable_type)

All public functions are also available at the top-level ultrasav namespace.

Examples
--------
>>> import ultrasav as ul
>>> 
>>> # Extract metadata to a Python file
>>> meta_dict = ul.get_meta(meta, output_path="labels.py")
>>> 
>>> # Create labels from Excel template
>>> ul.make_labels("template.xlsx", "labels.py")
>>> 
>>> # Build a validation datamap
>>> datamap = ul.make_datamap(df, meta)
>>> 
>>> # Export to formatted Excel
>>> ul.map_to_excel(datamap, "validation.xlsx")

Or access via submodule:
>>> from ultrasav.metaman import make_datamap, get_color_scheme
"""

# Metadata extraction
from ._get_meta import get_meta

# Label creation from Excel
from ._make_labels import make_labels

# Variable type detection
from ._detect_variable_type import detect_variable_type, create_mr_set_lookup

# Datamap creation
from ._map_engine import map_engine, precompute_value_maps
from ._make_datamap import make_datamap

# Excel export
from ._write_excel_engine import write_excel_engine
from ._map_to_excel import map_to_excel

# Print variable summary
from ._describe import describe

# Color schemes for Excel formatting
from ._color_schemes import (
    get_color_scheme,
    COLOR_SCHEMES,
    CLASSIC_GREY,
    PASTEL_GREEN_MUTED,
    PASTEL_BLUE_COOL,
    PASTEL_PURPLE_WARM,
    PASTEL_INDIGO,
)

__all__ = [
    # Metadata extraction
    "get_meta",
    
    # Label creation
    "make_labels",
    
    # Variable type detection
    "detect_variable_type",
    # "create_mr_set_lookup",
    
    # Datamap creation
    "make_datamap",
    # "map_engine",
    # "precompute_value_maps",
    
    # Excel export
    "map_to_excel",
    # "write_excel_engine",

    # Print variable summary
    "describe",
    
    # Color schemes
    "get_color_scheme",
    "COLOR_SCHEMES",
    "CLASSIC_GREY",
    "PASTEL_GREEN_MUTED",
    "PASTEL_BLUE_COOL",
    "PASTEL_PURPLE_WARM",
    "PASTEL_INDIGO",
]
