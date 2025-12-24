"""
ultrasav: read functions
v_0.1.0
"""


import os
from collections.abc import Sequence
import logging
from typing import Any
import narwhals as nw
import pyreadstat

# Shared encoding list
COMMON_ENCODINGS = [
    None,  # Default
    "utf-8",
    "utf-8-sig",
    "latin1",
    "cp1252",  # Windows Western European
    "iso-8859-1",
    "cp1251",  # Windows Cyrillic
    "cp1250",  # Windows Central European
    "gbk",  # Chinese Simplified
    "big5",  # Chinese Traditional
    "shift_jis",  # Japanese
    "euc-kr",  # Korean
]

def read_sav(
    file_path: str | os.PathLike,
    output_format: str = "polars",
    encoding: str | None = None,
    apply_value_formats: bool = False,
    formats_as_category: bool = True,
    formats_as_ordered_category: bool = False,
    auto_detect_encoding: bool = True,
    **kwargs
) -> tuple[Any, Any]:
    """
    Read SPSS SAV/ZSAV files with automatic encoding detection.

    Parameters
    ----------
    file_path : str or Path
        Path to the SAV/ZSAV file
    output_format : str, default "polars"
        Output format: "pandas", "polars", "narwhals", or "dict"
        - "pandas": returns pandas DataFrame
        - "polars": returns polars DataFrame
        - "narwhals": returns narwhals DataFrame (converted from polars)
        - "dict": returns dictionary
    encoding : str, optional
        File encoding. If None and auto_detect_encoding=True, will try multiple encodings
    auto_detect_encoding : bool, default True
        If True and encoding is None, automatically tries multiple encodings
    apply_value_formats : bool, default False
        Apply value labels to the data
    formats_as_category : bool, default True
        Convert formatted variables to categories
    formats_as_ordered_category : bool, default False
        Convert formatted variables to ordered categories
    **kwargs : additional arguments passed to pyreadstat.read_sav()

    Returns
    -------
    df : DataFrame or dict
        Data in the specified output format
    meta : metadata object
        Metadata from the SPSS file

    Examples
    --------
    >>> df, meta = read_sav("survey.sav")  # Returns polars DataFrame by default
    >>> df, meta = read_sav("survey.sav", output_format="pandas")  # Returns pandas DataFrame
    >>> df, meta = read_sav("survey.sav", output_format="narwhals")  # Returns narwhals DataFrame
    """
    if output_format not in ["pandas", "polars", "narwhals", "dict"]:
        raise ValueError(f"output_format must be 'pandas', 'polars', 'narwhals', or 'dict', got {output_format}")

    # For narwhals output, read as polars first
    read_format = "polars" if output_format == "narwhals" else output_format

    read_kwargs = {
        "apply_value_formats": apply_value_formats,
        "formats_as_category": formats_as_category,
        "formats_as_ordered_category": formats_as_ordered_category,
        "output_format": read_format,
        **kwargs
    }

    if encoding is not None or not auto_detect_encoding:
        if encoding:
            read_kwargs["encoding"] = encoding
        df, meta = pyreadstat.read_sav(file_path, **read_kwargs)
        if output_format == "narwhals":
            df = nw.from_native(df)
        return df, meta

    # Auto-detect encoding
    last_error = None
    for enc in COMMON_ENCODINGS:
        try:
            if enc is not None:
                read_kwargs["encoding"] = enc
            elif "encoding" in read_kwargs:
                del read_kwargs["encoding"]

            df, meta = pyreadstat.read_sav(file_path, **read_kwargs)

            enc_name = enc or "default"
            logging.info(f"Successfully read SAV file with encoding: {enc_name}")

            if output_format == "narwhals":
                df = nw.from_native(df)
            return df, meta

        except (UnicodeDecodeError, UnicodeError) as e:
            last_error = e
            continue
        except Exception as e:
            if any(term in str(e).lower() for term in ["decode", "encode", "codec", "utf", "unicode"]):
                last_error = e
                continue
            raise e

    raise ValueError(
        f"Failed to read SAV file '{file_path}' with any attempted encoding.\n"
        f"Last error: {last_error}"
    )


# Helper: non-string sequence check
def _is_non_str_seq(obj: Any) -> bool:
    return isinstance(obj, Sequence) and not isinstance(obj, (str, bytes))

# Helper: choose a pandas fallback engine from file extension
def _pandas_engine_from_ext(ext: str) -> str | None:
    # Best-effort guesser. Users can always override via `engine=...`.
    if ext in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return "openpyxl"
    if ext == ".xls":
        return "xlrd"
    if ext == ".xlsb":
        return "pyxlsb"
    if ext == ".ods":
        return "odf"
    return None

def read_excel(
    file_path: str | os.PathLike,
    output_format: str = "polars",
    sheet_name: str | int | Sequence[str | int] | None = 0,
    engine: str | None = None,
    **kwargs
) -> Any:
    """
    Read Excel files into the requested DataFrame format.

    Parameters
    ----------
    file_path : str or Path
        Path to the Excel file.
    output_format : {"pandas","polars","narwhals"}, default "polars"
        - "pandas": returns pandas DataFrame or dict[str, DataFrame]
        - "polars": returns polars DataFrame or dict[str, DataFrame]
        - "narwhals": reads via Polars with the same defaults, then converts
    sheet_name : str | int | list[str|int] | None, default 0
        Sheet selector(s).
        - str or list[str]: sheet names.
        - int or list[int]: **0-based indices** (we map to Polars's 1-based sheet_id).
        - None: **read all sheets** (dict is returned).
    engine : str | None, default None
        Backend engine to use.
        - Polars: defaults to "calamine" with "openpyxl" fallback. Options: "calamine", "openpyxl", "xlsx2csv"
        - Pandas: auto-detects based on file extension. Options: "openpyxl" (.xlsx), "xlrd" (.xls), "pyxlsb" (.xlsb), "odf" (.ods)
        If the specified engine fails, we try sensible fallbacks.

    **kwargs :
        Additional keyword args forwarded to the underlying read function.
        Note that available parameters differ between pandas and polars:
        - pandas supports: header, nrows, usecols, dtype, etc.
        - polars supports: has_header, columns, schema_overrides, etc.
        Excel readers do not take an 'encoding' parameter.

    Returns
    -------
    DataFrame or dict[str, DataFrame]
        Depending on `output_format` and whether multiple sheets were requested.

    Notes
    -----
    - Integer sheet indices are **0-based** in this API, even though Polars uses 1-based
      `sheet_id`. We adjust automatically.
    - Passing a mixed list of integers and strings for `sheet_name` is not supported and
      will raise a ValueError.
    """
    if output_format not in {"pandas", "polars", "narwhals"}:
        raise ValueError("output_format must be 'pandas', 'polars', or 'narwhals'.")

    # Determine how to read (narwhals reads via Polars first)
    backend = "polars" if output_format == "narwhals" else output_format

    # Normalize sheet selection
    sheet_is_seq = _is_non_str_seq(sheet_name)
    if sheet_is_seq:
        items = list(sheet_name)  # type: ignore[arg-type]
    else:
        items = [] if sheet_name is None else [sheet_name]  # None handled below

    # Check for mixed types in sheet_name
    if sheet_is_seq and items:
        first_type = type(items[0])
        if not all(isinstance(item, first_type) for item in items):
            raise ValueError(
                f"Mixed sheet types are not supported. Got: {[type(item).__name__ for item in items]}"
            )

    # Read based on backend
    file_str = str(file_path)

    if backend == "polars":
        import polars as pl

        # Polars-specific kwargs
        polars_kwargs = dict(kwargs)

        # Note: Polars doesn't have nrows parameter, it uses other mechanisms
        # Remove nrows if present since polars doesn't support it
        if "nrows" in polars_kwargs:
            polars_kwargs.pop("nrows")
            # Could warn user that nrows is not supported in polars

        # Map sheet selection
        if sheet_name is None:
            # Read all sheets
            polars_kwargs["sheet_name"] = None
        elif sheet_is_seq:
            # Multiple sheets
            if all(isinstance(item, int) for item in items):
                # 0-based to 1-based conversion for sheet indices
                polars_kwargs["sheet_id"] = [i + 1 for i in items]
            else:
                # Sheet names
                polars_kwargs["sheet_name"] = items
        else:
            # Single sheet
            if isinstance(sheet_name, int):
                polars_kwargs["sheet_id"] = sheet_name + 1
            else:
                polars_kwargs["sheet_name"] = sheet_name

        # Engine handling for Polars
        # Default to calamine if no engine specified
        if engine is None:
            engine = "calamine"
        else:
            # Validate user-provided engine
            valid_polars_engines = {"calamine", "openpyxl", "xlsx2csv"}
            if engine not in valid_polars_engines:
                import warnings
                warnings.warn(
                    f"Invalid engine '{engine}' for polars. "
                    f"Valid options are: {valid_polars_engines}. "
                    f"Defaulting to 'calamine'.",
                    UserWarning
                )
                engine = "calamine"
        
        polars_kwargs["engine"] = engine

        try:
            result = pl.read_excel(file_str, **polars_kwargs)
        except Exception as e:
            # If calamine fails, try openpyxl as fallback
            if engine == "calamine" and "calamine" in str(e).lower():
                logging.info("Calamine engine failed, falling back to openpyxl")
                polars_kwargs["engine"] = "openpyxl"
                try:
                    result = pl.read_excel(file_str, **polars_kwargs)
                except Exception as e2:
                    # If openpyxl also fails, try xlsx2csv as last resort
                    logging.info("Openpyxl engine failed, falling back to xlsx2csv")
                    polars_kwargs["engine"] = "xlsx2csv"
                    result = pl.read_excel(file_str, **polars_kwargs)
            else:
                raise

    else:  # backend == "pandas"
        import pandas as pd

        # Pandas-specific kwargs
        pandas_kwargs = dict(kwargs)

        # Sheet selection
        if sheet_name is None:
            pandas_kwargs["sheet_name"] = None
        elif sheet_is_seq:
            # Convert 0-based indices to sheet names if possible
            if all(isinstance(item, int) for item in items):
                # Keep as 0-based for pandas
                pandas_kwargs["sheet_name"] = items
            else:
                pandas_kwargs["sheet_name"] = items
        else:
            pandas_kwargs["sheet_name"] = sheet_name

        # Engine selection for pandas
        if engine:
            pandas_kwargs["engine"] = engine
        else:
            # Auto-detect engine based on file extension
            ext = os.path.splitext(file_str)[1].lower()
            pandas_engine = _pandas_engine_from_ext(ext)
            if pandas_engine:
                pandas_kwargs["engine"] = pandas_engine

        try:
            result = pd.read_excel(file_str, **pandas_kwargs)
        except Exception as e:
            # Fallback for engine issues
            if "engine" in pandas_kwargs and "engine" in str(e).lower():
                ext = os.path.splitext(file_str)[1].lower()
                fallback_engine = _pandas_engine_from_ext(ext)
                if fallback_engine and fallback_engine != pandas_kwargs.get("engine"):
                    pandas_kwargs["engine"] = fallback_engine
                    result = pd.read_excel(file_str, **pandas_kwargs)
                else:
                    raise
            else:
                raise

    # Convert to narwhals if requested
    if output_format == "narwhals":
        if isinstance(result, dict):
            return {name: nw.from_native(df) for name, df in result.items()}
        else:
            return nw.from_native(result)

    return result

def _is_encoding_error(e: Exception) -> bool:
    """Check if an exception is encoding-related."""
    error_str = str(e).lower()
    error_type = type(e).__name__.lower()
    
    encoding_indicators = [
        "encode", "decode", "codec", "utf", "unicode",
        "charmap", "ascii", "latin", "gbk", "big5"
    ]
    
    return any(ind in error_str or ind in error_type for ind in encoding_indicators)

def _normalize_sep_kwargs(kwargs: dict[str, Any], backend: str) -> dict[str, Any]:
    """
    Normalize delimiter-related kwargs for different backends.
    - pandas: uses `sep`
    - polars: uses `separator`
    """
    out = dict(kwargs)

    if backend == "polars":
        # Prefer explicit 'separator' if provided, else map common pandas spellings
        if "separator" not in out:
            if "sep" in out:
                out["separator"] = out.pop("sep")
            elif "delimiter" in out:
                out["separator"] = out.pop("delimiter")
    else:  # backend == "pandas"
        # Prefer explicit 'sep' if provided, else map 'separator'/'delimiter'
        if "sep" not in out:
            if "separator" in out:
                out["sep"] = out.pop("separator")
            elif "delimiter" in out:
                out["sep"] = out.pop("delimiter")

    return out

def _pick_backend_for_narwhals_preference(prefer: str = "polars") -> str:
    """
    Choose a backend module name for Narwhals ('polars' or 'pandas').
    If the preferred backend isn't importable, fall back to the other.
    """
    if prefer == "polars":
        try:
            import polars  # noqa: F401
            return "polars"
        except Exception:
            pass
        try:
            import pandas  # noqa: F401
            return "pandas"
        except Exception:
            raise RuntimeError(
                "Neither Polars nor pandas is installed. Please install one of them."
            )
    else:  # prefer pandas
        try:
            import pandas  # noqa: F401
            return "pandas"
        except Exception:
            pass
        try:
            import polars  # noqa: F401
            return "polars"
        except Exception:
            raise RuntimeError(
                "Neither pandas nor Polars is installed. Please install one of them."
            )

def read_csv(
    file_path: str | os.PathLike,
    output_format: str = "polars",
    encoding: str | None = None,
    auto_detect_encoding: bool = True,
    **kwargs
) -> Any:
    """
    Read CSV files into the requested DataFrame format using Narwhals under the hood.

    Parameters
    ----------
    file_path : str or Path
        Path to the CSV file.
    output_format : {"polars","pandas","narwhals"}, default "polars"
        - "polars": returns a polars.DataFrame
        - "pandas": returns a pandas.DataFrame
        - "narwhals": returns a narwhals.DataFrame (backed by a native df)
    encoding : str, optional
        Encoding hint passed to the native reader. If None and
        auto_detect_encoding=True, we'll try several encodings.
    auto_detect_encoding : bool, default True
        If True and `encoding` is None, attempt multiple encodings.
    **kwargs :
        Extra keywords forwarded to the native CSV reader (through Narwhals).
        These may be backend-specific (e.g., pandas uses `sep`, Polars uses
        `separator`). We normalize only delimiter args (`sep`/`delimiter`↔`separator`)
        to reduce friction.

    Returns
    -------
    DataFrame
        pandas.DataFrame, polars.DataFrame, or narwhals.DataFrame according to
        `output_format`.

    Notes
    -----
    - Narwhals API: `nw.read_csv(source, backend=..., **kwargs)` then
      `nw.to_native(df)` if you want the native object. Kwargs pass through to
      the backend reader.
    - Polars CSV reader is UTF‑8‑first; for non‑UTF encodings, pandas tends to
      be more permissive, so we use a pandas fallback during autodetection.
    """
    if output_format not in {"polars", "pandas", "narwhals"}:
        raise ValueError("output_format must be 'polars', 'pandas', or 'narwhals'.")

    # Decide the first backend to try based on the requested output.
    if output_format == "polars":
        preferred_backend = "polars"
    elif output_format == "pandas":
        preferred_backend = "pandas"
    else:  # "narwhals"
        # Prefer polars for performance; fall back to pandas if not installed
        preferred_backend = _pick_backend_for_narwhals_preference("polars")

    def _read_once(backend: str, enc: str | None, passthrough_kwargs: dict[str, Any]):
        # Normalize delimiter kwargs for this backend
        k = _normalize_sep_kwargs(passthrough_kwargs, backend=backend)
        if enc:
            k = {**k, "encoding": enc}
        # Use Narwhals to create a Narwhals DataFrame backed by the chosen backend
        return nw.read_csv(str(file_path), backend=backend, **k)  # narwhals DF

    last_err: Exception | None = None

    # Fast path: if encoding is provided or autodetect is off, do a single attempt
    if (encoding is not None) or (not auto_detect_encoding):
        try:
            df_nw = _read_once(preferred_backend, encoding, kwargs)
        except Exception as e:
            # If it's encoding-related and the preferred backend is Polars,
            # try pandas as a one-shot fallback with the same encoding.
            if _is_encoding_error(e) and preferred_backend == "polars":
                try:
                    df_nw = _read_once("pandas", encoding, kwargs)
                except Exception as e2:
                    raise e2
            else:
                raise
        # Return in the requested format
        if output_format == "narwhals":
            return df_nw
        native = nw.to_native(df_nw)  # pandas or polars depending on backend
        if output_format == "polars" and not (type(native).__module__.startswith("polars")):
            # Convert pandas->polars if fallback used
            import polars as pl
            return pl.from_pandas(native)
        return native

    # Autodetect encoding: try preferred backend with default (utf-8), then iterate COMMON_ENCODINGS
    # Strategy:
    #   1) Try preferred backend with no 'encoding' kwarg (native default).
    #   2) For each enc in COMMON_ENCODINGS (skipping None), try preferred backend.
    #      If that fails due to encoding, try pandas (broad support).
    #   3) On success, convert to requested output.
    try:
        df_nw = _read_once(preferred_backend, None, kwargs)
        # Success with default encoding
        if output_format == "narwhals":
            return df_nw
        native = nw.to_native(df_nw)
        if output_format == "polars" and not (type(native).__module__.startswith("polars")):
            import polars as pl
            return pl.from_pandas(native)
        return native
    except Exception as e:
        last_err = e
        if not _is_encoding_error(e):
            # Not encoding-related -> propagate immediately
            raise

    # Try a list of encodings
    for enc in (e for e in COMMON_ENCODINGS if e is not None):
        try:
            df_nw = _read_once(preferred_backend, enc, kwargs)
            logging.info(f"read_csv succeeded with backend={preferred_backend}, encoding={enc}")
            if output_format == "narwhals":
                return df_nw
            native = nw.to_native(df_nw)
            if output_format == "polars" and not (type(native).__module__.startswith("polars")):
                import polars as pl
                return pl.from_pandas(native)
            return native
        except Exception as e:
            last_err = e
            # If encoding-related and we haven't tried pandas yet (or preferred is polars), try pandas
            if _is_encoding_error(e) and preferred_backend == "polars":
                try:
                    df_nw = _read_once("pandas", enc, kwargs)
                    logging.info(f"read_csv succeeded with backend=pandas, encoding={enc}")
                    if output_format == "narwhals":
                        return df_nw
                    native = nw.to_native(df_nw)  # pandas DF
                    if output_format == "polars":
                        import polars as pl
                        return pl.from_pandas(native)
                    return native
                except Exception as e2:
                    last_err = e2
                    continue
            # Non-encoding error -> raise early
            if not _is_encoding_error(e):
                raise

    raise ValueError(
        f"Failed to read CSV file '{file_path}' with any attempted encoding. "
        f"Last error: {last_err}"
    )
