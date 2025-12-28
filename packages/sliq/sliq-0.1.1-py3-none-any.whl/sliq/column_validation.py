"""Column validation utilities for the Sliq library.

This module provides utilities for validating column_guide against dataset columns.
It ensures that:
1. The number of columns in column_guide matches the number of columns in the dataset
2. Column names match (case-insensitive, ignoring underscores)

Uses Polars LazyFrame for memory-efficient column name extraction from files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from sliq.exceptions import SliqValidationError

# Type alias for DataFrames
DataFrame = Any  # Union[pd.DataFrame, pl.DataFrame]


def _normalize_column_name(name: str) -> str:
    """Normalize a column name for comparison.
    
    Converts to lowercase and removes underscores for case-insensitive,
    underscore-insensitive comparison.
    
    Args:
        name: The column name to normalize.
        
    Returns:
        Normalized column name (lowercase, no underscores).
    """
    return name.lower().replace("_", "")


def _get_columns_from_file(file_path: Path) -> List[str]:
    """Extract column names from a file using minimal memory.
    
    Uses Polars LazyFrame to read only the schema (column names) without
    loading the entire file into memory. For Excel files, uses Pandas
    with nrows=0 to read only the header.
    
    Args:
        file_path: Path to the dataset file.
        
    Returns:
        List of column names from the file.
        
    Raises:
        SliqValidationError: If column names cannot be extracted.
    """
    ext = file_path.suffix.lower()
    
    try:
        # Import polars for efficient lazy reading
        import polars as pl
        
        if ext == ".csv":
            # Use LazyFrame to scan only schema - minimal memory usage
            lf = pl.scan_csv(file_path)
            columns = lf.collect_schema().names()
        
        elif ext == ".parquet":
            # Parquet files store schema separately - very efficient
            lf = pl.scan_parquet(file_path)
            columns = lf.collect_schema().names()
        
        elif ext == ".json":
            # For JSON, need to infer schema - read lazily
            lf = pl.scan_ndjson(file_path)
            columns = lf.collect_schema().names()
        
        elif ext == ".jsonl":
            # JSONL is newline-delimited JSON
            lf = pl.scan_ndjson(file_path)
            columns = lf.collect_schema().names()
        
        elif ext in (".xlsx", ".xls", ".xlsb"):
            # Excel files: use pandas with nrows=0 for header-only read
            try:
                import pandas as pd
            except ImportError:
                raise SliqValidationError(
                    "Pandas is required to read Excel files. "
                    "Install it with: pip install pandas openpyxl"
                )
            # Read only header row (nrows=0 reads column names only)
            df_header = pd.read_excel(file_path, nrows=0)
            columns = df_header.columns.tolist()
        
        else:
            raise SliqValidationError(
                f"Cannot extract columns from unsupported file type: {ext}"
            )
        
        return columns
        
    except SliqValidationError:
        raise
    except ImportError:
        raise SliqValidationError(
            "Polars is required for column validation. "
            "Install it with: pip install polars"
        )
    except Exception as e:
        raise SliqValidationError(f"Failed to read column names from file: {e}")


def _get_columns_from_dataframe(df: DataFrame) -> List[str]:
    """Extract column names from a Pandas or Polars DataFrame.
    
    Args:
        df: A Pandas or Polars DataFrame.
        
    Returns:
        List of column names.
        
    Raises:
        SliqValidationError: If DataFrame type is not recognized.
    """
    class_name = type(df).__name__
    module_name = type(df).__module__
    
    if "pandas" in module_name.lower() and class_name == "DataFrame":
        return df.columns.tolist()
    elif "polars" in module_name.lower() and class_name == "DataFrame":
        return df.columns
    else:
        raise SliqValidationError(
            f"Unsupported DataFrame type: {module_name}.{class_name}. "
            "Please provide a Pandas or Polars DataFrame."
        )


def validate_column_guide(
    column_guide: Dict[str, str],
    dataset_columns: List[str],
) -> None:
    """Validate that column_guide matches the dataset columns.
    
    Performs two validations:
    1. Column count: Number of keys in column_guide must match number of dataset columns
    2. Column names: Each key in column_guide must match a dataset column (case-insensitive, underscore-insensitive)
    
    Args:
        column_guide: Dictionary mapping column names to descriptions.
        dataset_columns: List of actual column names from the dataset.
        
    Raises:
        SliqValidationError: If validation fails, with specific details about
            which columns don't match.
    """
    guide_columns = list(column_guide.keys())
    
    # Check 1: Column count must match
    if len(guide_columns) != len(dataset_columns):
        raise SliqValidationError(
            f"Column count mismatch: column_guide has {len(guide_columns)} columns, "
            f"but dataset has {len(dataset_columns)} columns. "
            f"Please provide descriptions for all {len(dataset_columns)} columns."
        )
    
    # Check 2: All column names must match (case-insensitive, underscore-insensitive)
    # Build a mapping of normalized dataset column names to original names
    normalized_dataset_cols: Dict[str, str] = {
        _normalize_column_name(col): col for col in dataset_columns
    }
    
    # Find mismatched columns
    mismatched_columns: List[str] = []
    for guide_col in guide_columns:
        normalized_guide_col = _normalize_column_name(guide_col)
        if normalized_guide_col not in normalized_dataset_cols:
            mismatched_columns.append(guide_col)
    
    if mismatched_columns:
        # Format the error message with the mismatched columns and actual dataset columns
        mismatched_list = ", ".join(f"'{col}'" for col in mismatched_columns)
        actual_list = ", ".join(f"'{col}'" for col in dataset_columns)
        raise SliqValidationError(
            f"Column name mismatch in column_guide. "
            f"The following column(s) do not match any dataset column: {mismatched_list}. "
            f"Dataset columns are: {actual_list}. "
            f"Please use the exact column names as they appear in your dataset."
        )


def validate_column_guide_for_file(
    column_guide: Optional[Dict[str, str]],
    file_path: Path,
) -> None:
    """Validate column_guide against columns in a file.
    
    Uses memory-efficient reading to extract only column names.
    Skips validation if column_guide is None or empty.
    
    Args:
        column_guide: Dictionary mapping column names to descriptions, or None.
        file_path: Path to the dataset file.
        
    Raises:
        SliqValidationError: If validation fails.
    """
    # Skip validation if no column_guide provided
    if not column_guide:
        return
    
    # Extract columns from file using minimal memory
    dataset_columns = _get_columns_from_file(file_path)
    
    # Validate
    validate_column_guide(column_guide, dataset_columns)


def validate_column_guide_for_dataframe(
    column_guide: Optional[Dict[str, str]],
    df: DataFrame,
) -> None:
    """Validate column_guide against columns in a DataFrame.
    
    Skips validation if column_guide is None or empty.
    
    Args:
        column_guide: Dictionary mapping column names to descriptions, or None.
        df: A Pandas or Polars DataFrame.
        
    Raises:
        SliqValidationError: If validation fails.
    """
    # Skip validation if no column_guide provided
    if not column_guide:
        return
    
    # Get columns from DataFrame
    dataset_columns = _get_columns_from_dataframe(df)
    
    # Validate
    validate_column_guide(column_guide, dataset_columns)
