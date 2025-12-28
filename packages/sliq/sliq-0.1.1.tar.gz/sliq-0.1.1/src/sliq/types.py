"""Type definitions for the Sliq library.

This module contains type aliases and TypedDict definitions used
throughout the library for better type safety and documentation.
"""

from typing import TypedDict, Union, Optional
from typing_extensions import NotRequired

# Try to import DataFrame types for type hints
try:
    import pandas as pd
    PandasDataFrame = pd.DataFrame
except ImportError:
    PandasDataFrame = None  # type: ignore

try:
    import polars as pl
    PolarsDataFrame = pl.DataFrame
except ImportError:
    PolarsDataFrame = None  # type: ignore

# Union type for DataFrames - supports both Pandas and Polars
DataFrame = Union["pd.DataFrame", "pl.DataFrame"]


class PresignResponse(TypedDict):
    """Response from the /presign endpoint."""
    
    upload_url: str
    object_key: str
    user_id: str
    job_id: str
    expires_in_seconds: int


class RunResponse(TypedDict):
    """Response from the /run endpoint."""
    
    execution_name: str
    status_url: str


class DownloadUrls(TypedDict, total=False):
    """Download URLs for cleaned outputs."""
    
    cleaned_dataset_url: str
    execution_log_url: str
    explanations_url: str


class StatusResponse(TypedDict):
    """Response from the /status endpoint."""
    
    is_complete: bool
    succeeded: bool
    status: str
    message: str
    dirty_dataset_deleted: bool
    download_urls: NotRequired[Optional[DownloadUrls]]


class CleaningMetadata(TypedDict, total=False):
    """Metadata for a cleaning job request."""
    
    dataset_name: str
    dataset_description: str
    dataset_purpose: str
    column_guide: Optional[str]  # JSON string
    data_source: str
    user_instructions: str
    is_feature_engineering: bool
    is_detailed_report: bool
