"""
write_functions.py
v0.1.0
"""

import logging
from pathlib import Path
import pyreadstat

logger = logging.getLogger(__name__)


def write_sav(data,
              meta,
              dst_path: str | Path,
              **overrides) -> None:
    """
    Write data and metadata to a SPSS SAV file.
    
    This is the convergence point where independent data and metadata objects
    reunite. Only columns that exist in the data will have their metadata
    written, regardless of what metadata exists for other columns.
    
    Parameters
    ----------
    data : The data to write, pandas.DataFrame, or polars.DataFrame
    meta : Metadata, metadata_container, or None
        Metadata object containing labels, formats, etc. Can be:
        - A Metadata object (from this package)
        - A pyreadstat metadata_container (will be auto-wrapped)
        - None for minimal metadata (no labels, formats, etc.)
    dst_path : str or Path
        Path where the SAV file will be written.
    **overrides : keyword arguments
        Optional overrides for metadata settings. Common overrides:
        - compress (bool): If True, creates a compressed ZSAV file
        - row_compress (bool): If True, uses row compression
        Note: compress and row_compress cannot both be True.
        Any override temporarily replaces the meta object's setting during write.
    
    Notes
    -----
    The function follows the tidyspss two-track architecture where data and 
    metadata work independently and only converge at write time. Metadata for
    columns that don't exist in the data will be silently ignored by pyreadstat.
    
    Examples
    --------
    >>> # Basic write with data and metadata
    >>> write_sav(data, meta, "output.sav")
    
    >>> # Write without metadata (minimal SPSS file)
    >>> write_sav(df, dst_path="minimal.sav")
    
    >>> # Write with compression override
    >>> write_sav(data, meta, dst_path="output.zsav", compress=True)
    """
    # Convert to native dataframe if needed
    if hasattr(data, 'to_native'):
        df = data.to_native()
    else:
        df = data
    
    # Handle metadata
    if meta is not None:
        # Check if it's already a Metadata object or needs wrapping
        if not hasattr(meta, 'get_write_params'):
            # It's likely a pyreadstat metadata_container, wrap it
            from .class_metadata import Metadata
            meta = Metadata(meta)
        
        # Apply temporary overrides to metadata object
        originals = {}
        for key, value in overrides.items():
            if value is not None and hasattr(meta, key):
                originals[key] = getattr(meta, key)
                setattr(meta, key, value)
        
        # Get write parameters from metadata
        write_params = meta.get_write_params()
        
        # Restore original metadata settings
        for key, value in originals.items():
            setattr(meta, key, value)
        
        # Extract compression settings from write params
        final_compress = write_params.pop('compress', False)
        final_row_compress = write_params.pop('row_compress', False)
    else:
        # No metadata - use minimal parameters with overrides
        write_params = {}
        final_compress = overrides.get('compress', False)
        final_row_compress = overrides.get('row_compress', False)
    
    # Validate compression settings
    if final_compress and final_row_compress:
        raise ValueError("Both 'compress' and 'row_compress' cannot be True at the same time")
    
    # Convert path to string
    dst_path = str(dst_path)
    
    # Write the file
    pyreadstat.write_sav(
        df=df,
        dst_path=dst_path,
        compress=final_compress,
        row_compress=final_row_compress,
        **write_params
    )
    
    logger.info(f"SPSS file saved successfully to {dst_path}")
