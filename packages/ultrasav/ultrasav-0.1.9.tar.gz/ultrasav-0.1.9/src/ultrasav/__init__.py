"""
ultrasav - Ultra-powerful Python package for SPSS/SAV file processing.

⚡ultrasav separates data and metadata operations into independent tracks that only
converge at read/write time. This design provides explicit control, clean separation
of concerns, and flexibility when working with SPSS data files.

 

Basic usage:
    >>> import ultrasav as ul
    >>> # Read SPSS file - splits into two tracks
    >>> data, meta = ul.read_sav("survey.sav")
    >>> 
    >>> # Track 1: Process data independently
    >>> data = ul.Data(data)
    >>> data = data.move(first=["ID"]).rename({"Q1": "Question1"})
    >>> 
    >>> # Track 2: Process metadata independently  
    >>> meta.column_labels = {"Question1": "Customer Satisfaction"}
    >>> 
    >>> # Convergence: Write both tracks to SPSS
    >>> ul.write_sav(data.to_native(), meta, "output.sav")

Main components:
    - Data: Handle dataframe operations (move, rename, replace, drop, select)
    - Metadata: Handle SPSS metadata (labels, formats, measures, missing values)
    - read_sav/write_sav: File I/O for SPSS format
    - add_cases: High-level function for merging files with metadata
    - merge_data/merge_meta: Lower-level merge operations
    
Metadata tools (via metaman submodule):
    - get_meta: Extract metadata to Python files
    - make_labels: Create label dictionaries from Excel
    - make_datamap: Build validation datamaps
    - map_to_excel: Export formatted Excel reports
    - detect_variable_type: Detect variable types (single/multi-select, etc.)
"""

# __version__ = "0.1.0"
from importlib.metadata import version
__version__ = version("ultrasav")
__author__ = "Albert Li"

# =============================================================================
# Core classes
# =============================================================================
from ._data import Data
from ._metadata import Metadata

# =============================================================================
# I/O functions
# =============================================================================
from ._read_files import read_sav, read_csv, read_excel
from ._write_files import write_sav

# =============================================================================
# Merge functions
# =============================================================================
from ._merge_data import merge_data
from ._merge_meta import merge_meta, get_meta_summary

# =============================================================================
# High-level functions
# =============================================================================
from ._add_cases import add_cases
from ._make_dummy import make_dummies

# =============================================================================
# Metaman submodule - The Metadata Superhero 🦸
# =============================================================================
# 1.Submodule namespace access
from . import metaman 
# ultrasav.metaman.get_meta(...)
# from ultrasav import metaman


# 2.Top-level function access
# Re-export metaman's public API at top level for convenience
from .metaman import (
    # Metadata extraction
    get_meta,
    
    # Label creation
    make_labels,
    
    # Variable type detection
    detect_variable_type,
    # create_mr_set_lookup,
    
    # Datamap creation
    make_datamap,
    # map_engine,
    
    # Excel export
    map_to_excel,
    # write_excel_engine,

    # Describe variable summary
    describe,
    
    # Color schemes
    get_color_scheme,
    COLOR_SCHEMES,
)

# =============================================================================
# Public API
# =============================================================================
__all__ = [
    # Version
    "__version__",
    
    # Core classes
    "Data",
    "Metadata",
    
    # Read functions
    "read_sav",
    "read_csv",
    "read_excel",
    
    # Write function
    "write_sav",
    
    # Merge functions
    "merge_data",
    "merge_meta",
    "get_meta_summary",
    
    # High-level functions
    "add_cases",
    "make_dummies",
    
    # Metaman submodule
    "metaman",
    
    # Metaman re-exports (top-level access)
    "get_meta",
    "make_labels",
    "detect_variable_type",

    # "create_mr_set_lookup",
    "make_datamap",
    # "map_engine",
    "map_to_excel",
    # "write_excel_engine",
    "describe",

    "get_color_scheme",
    "COLOR_SCHEMES",
]


# =============================================================================
# Utility functions
# =============================================================================

def _show_architecture():
    """Display the ultrasav two-track architecture diagram."""
    architecture = """
    ⚡ ULTRASAV ARCHITECTURE ⚡
    ==========================
    
    The Two-Track System:
    
    ┌─────────────┐         ┌─────────────┐
    │   DATA      │         │  METADATA   │
    │             │         │             │
    │  DataFrame  │         │   Labels    │
    │  Columns    │         │   Formats   │
    │  Values     │         │   Measures  │
    └─────────────┘         └─────────────┘
          │                         │
          │    Independent Work     │
          │                         │
          └────────┬────────────────┘
                   │
                   ▼
             ┌─────────────┐
             │  WRITE SAV  │
             └─────────────┘
    
    Key Principle:
    --------------
    Data and Metadata are two independent layers that only come together at read/write time.
    
    Workflow:
    ---------
    1. READING (Splitting): read_sav() → (data, metadata)
    2. PROCESSING (Parallel): 
       - Data operations via Data class
       - Metadata operations via Metadata class
    3. WRITING (Reunification): write_sav(data, metadata)
    
Benefits:
    ---------
    • Clean Separation - Each class has single responsibility  
    • Flexibility - Mix and match data/metadata from different sources
    • Explicit Control - No hidden magic or automatic transfers for metadata updates
    • Metadata Utilities - Metaman tools to inspect, extract, and report metadata fast
    
    
    Metaman Submodule:
    ------------------
    🦸 The metadata superhero for inspection & reporting:
    • get_meta() - Extract metadata to Python files
    • make_labels() - Create labels from Excel templates
    • make_datamap() - Build validation datamaps
    • map_to_excel() - Export formatted Excel reports
    """
    print(architecture)


def show_arch():
    """Display the ultrasav two-track architecture diagram."""
    return _show_architecture()


def _quick_merge(files, output_file=None, source_col="mrgsrc", **kwargs):
    """
    Convenience function for quick file merging.
    
    Parameters
    ----------
    files : list
        List of file paths to merge
    output_file : str, optional
        If provided, writes merged data to this file
    source_col : str, default "mrgsrc"
        Name of column tracking data sources
    **kwargs
        Additional arguments passed to add_cases
        
    Returns
    -------
    DataFrame, Metadata or None
        Merged data and metadata if output_file not specified
        
    Examples
    --------
    >>> import ultrasav as ul
    >>> # Quick merge and save
    >>> ul._quick_merge(["file1.sav", "file2.sav"], "merged.sav")
    
    >>> # Quick merge and return
    >>> data, meta = ul._quick_merge(["file1.sav", "file2.sav"])
    """
    data, meta = add_cases(files, source_col=source_col, **kwargs)
    
    if output_file:
        write_sav(data, meta, output_file)
        print(f"⚡ Successful! Merged {len(files)} files → {output_file}")
    else:
        return data, meta


# Add utility functions to __all__
__all__.extend(["show_arch"])
# __all__.extend(["_show_architecture", "show_arch", "_quick_merge"])


# =============================================================================
# Package metadata
# =============================================================================

def about():
    """Display package information."""
    info = f"""
    ⚡ ultrasav v{__version__} ⚡
    ========================
    Ultra-powerful Python package for SPSS/SAV file processing.
    
    Author: {__author__}
    
    
    Core components: Data, Metadata, read_sav, write_sav, add_cases, merge_data, merge_meta
    Metadata tools: get_meta, make_labels, make_datamap, map_to_excel
    
    Use ul.show_arch() to see the two-track design.
    """
    print(info)

__all__.append("about")
