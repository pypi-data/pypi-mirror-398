"""DataFrame handling utilities for the Sliq library.

This module provides utilities for:
- Detecting DataFrame types (Pandas vs Polars)
- Converting DataFrames to Parquet bytes for upload
- Converting downloaded files back to DataFrames
"""

from __future__ import annotations

import io
from typing import Any, Literal, Union

from sliq.exceptions import SliqValidationError

# Type alias for DataFrames
DataFrame = Any  # Union[pd.DataFrame, pl.DataFrame]


def detect_dataframe_type(df: DataFrame) -> Literal["pandas", "polars"]:
    """Detect whether a DataFrame is Pandas or Polars.
    
    Args:
        df: A DataFrame object to check.
        
    Returns:
        "pandas" or "polars" indicating the DataFrame type.
        
    Raises:
        SliqValidationError: If the object is not a recognized DataFrame type.
    """
    # Check class name to avoid requiring both libraries
    class_name = type(df).__name__
    module_name = type(df).__module__
    
    if "pandas" in module_name.lower() and class_name == "DataFrame":
        return "pandas"
    elif "polars" in module_name.lower() and class_name == "DataFrame":
        return "polars"
    else:
        raise SliqValidationError(
            f"Unsupported DataFrame type: {module_name}.{class_name}. "
            "Please provide a Pandas or Polars DataFrame."
        )


def validate_dataframe(df: DataFrame) -> None:
    """Validate that a DataFrame is not empty.
    
    Args:
        df: A DataFrame to validate.
        
    Raises:
        SliqValidationError: If the DataFrame is empty or invalid.
    """
    df_type = detect_dataframe_type(df)
    
    if df_type == "pandas":
        if df.empty:
            raise SliqValidationError("DataFrame is empty. Please provide a DataFrame with data.")
    elif df_type == "polars":
        if df.height == 0:
            raise SliqValidationError("DataFrame is empty. Please provide a DataFrame with data.")


def dataframe_to_parquet_bytes(df: DataFrame) -> bytes:
    """Convert a DataFrame to Parquet format bytes.
    
    Args:
        df: A Pandas or Polars DataFrame.
        
    Returns:
        The DataFrame serialized as Parquet bytes.
        
    Raises:
        SliqValidationError: If conversion fails.
    """
    df_type = detect_dataframe_type(df)
    buffer = io.BytesIO()
    
    try:
        if df_type == "pandas":
            df.to_parquet(buffer, engine="pyarrow", index=False)
        elif df_type == "polars":
            df.write_parquet(buffer)
        
        return buffer.getvalue()
    except Exception as e:
        raise SliqValidationError(f"Failed to convert DataFrame to Parquet: {e}")


def parquet_bytes_to_dataframe(
    data: bytes,
    output_type: Literal["pandas", "polars"] = "pandas",
) -> DataFrame:
    """Convert Parquet bytes back to a DataFrame.
    
    Args:
        data: Parquet file content as bytes.
        output_type: Type of DataFrame to return ("pandas" or "polars").
        
    Returns:
        A Pandas or Polars DataFrame.
        
    Raises:
        SliqValidationError: If conversion fails or required library not installed.
    """
    buffer = io.BytesIO(data)
    
    try:
        if output_type == "pandas":
            try:
                import pandas as pd
            except ImportError:
                raise SliqValidationError(
                    "Pandas is required but not installed. "
                    "Install it with: pip install pandas"
                )
            return pd.read_parquet(buffer)
        
        elif output_type == "polars":
            try:
                import polars as pl
            except ImportError:
                raise SliqValidationError(
                    "Polars is required but not installed. "
                    "Install it with: pip install polars"
                )
            return pl.read_parquet(buffer)
        
        else:
            raise SliqValidationError(
                f"Invalid output_type: {output_type}. Must be 'pandas' or 'polars'."
            )
    except SliqValidationError:
        raise
    except Exception as e:
        raise SliqValidationError(f"Failed to read Parquet data: {e}")


def file_bytes_to_dataframe(
    data: bytes,
    filename: str,
    output_type: Literal["pandas", "polars"] = "pandas",
) -> DataFrame:
    """Convert file bytes to a DataFrame based on file extension.
    
    Args:
        data: File content as bytes.
        filename: Filename (used to determine format from extension).
        output_type: Type of DataFrame to return ("pandas" or "polars").
        
    Returns:
        A Pandas or Polars DataFrame.
        
    Raises:
        SliqValidationError: If conversion fails or format is unsupported.
    """
    import os
    ext = os.path.splitext(filename.lower())[1]
    buffer = io.BytesIO(data)
    
    try:
        if output_type == "pandas":
            try:
                import pandas as pd
            except ImportError:
                raise SliqValidationError(
                    "Pandas is required but not installed. "
                    "Install it with: pip install pandas"
                )
            
            if ext == ".csv":
                return pd.read_csv(buffer)
            elif ext == ".json":
                return pd.read_json(buffer)
            elif ext == ".jsonl":
                return pd.read_json(buffer, lines=True)
            elif ext in (".xlsx", ".xls"):
                return pd.read_excel(buffer)
            elif ext == ".parquet":
                return pd.read_parquet(buffer)
            else:
                raise SliqValidationError(f"Unsupported file format: {ext}")
        
        elif output_type == "polars":
            try:
                import polars as pl
            except ImportError:
                raise SliqValidationError(
                    "Polars is required but not installed. "
                    "Install it with: pip install polars"
                )
            
            if ext == ".csv":
                return pl.read_csv(buffer)
            elif ext == ".json":
                return pl.read_json(buffer)
            elif ext == ".jsonl":
                return pl.read_ndjson(buffer)
            elif ext in (".xlsx", ".xls"):
                return pl.read_excel(buffer)
            elif ext == ".parquet":
                return pl.read_parquet(buffer)
            else:
                raise SliqValidationError(f"Unsupported file format: {ext}")
        
        else:
            raise SliqValidationError(
                f"Invalid output_type: {output_type}. Must be 'pandas' or 'polars'."
            )
    except SliqValidationError:
        raise
    except Exception as e:
        raise SliqValidationError(f"Failed to read {ext} data: {e}")
