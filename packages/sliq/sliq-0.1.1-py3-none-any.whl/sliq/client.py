"""Main client module for the Sliq library.

This module contains the two public functions that users interact with:
- clean_from_file(): Clean a dataset from a file path
- clean_from_dataframe(): Clean a Pandas or Polars DataFrame

Both functions handle the complete cleaning flow:
1. Upload the dataset to cloud storage
2. Trigger the cleaning job
3. Poll for completion
4. Download and return/save the results
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

from sliq.api import (
    call_presign,
    call_run,
    call_status,
    upload_to_presigned_url,
    download_from_presigned_url,
)
from sliq.config import (
    POLL_INTERVAL_SECONDS,
    MAX_POLL_ATTEMPTS,
    WEBSITE_URL,
)
from sliq.dataframe_utils import (
    detect_dataframe_type,
    validate_dataframe,
    dataframe_to_parquet_bytes,
    file_bytes_to_dataframe,
)
from sliq.exceptions import (
    SliqAPIError,
    SliqValidationError,
    SliqJobFailedError,
    SliqTimeoutError,
)
from sliq.file_utils import (
    validate_file_path,
    validate_output_directory,
    create_zip_from_file,
    create_zip_from_bytes,
    extract_file_from_zip,
    save_file_to_disk,
)
from sliq.column_validation import (
    validate_column_guide_for_file,
    validate_column_guide_for_dataframe,
)

# Configure module logger
logger = logging.getLogger(__name__)

# Type alias for DataFrames
DataFrame = Any  # Union[pd.DataFrame, pl.DataFrame]

# Valid output formats for cleaned datasets
# Users can specify any of these formats for the output file
VALID_OUTPUT_FORMATS = {'.csv', '.json', '.jsonl', '.xlsx', '.parquet'}


def clean_from_file(
    api_key: str,
    dataset_path: str,
    dataset_name: str,
    save_clean_file_path: str = "",
    save_clean_file_name: str = "",
    output_format: Optional[str] = None,
    dataset_description: str = "",
    dataset_purpose: str = "",
    column_guide: Optional[Dict[str, str]] = None,
    data_source: str = "",
    user_instructions: str = "",
    is_feature_engineering: bool = False,
    is_detailed_report: bool = False,
    verbose: bool = False,
) -> None:
    """Clean a dataset from a file and optionally save the result.
    
    This function uploads your dataset to Sliq, cleans it using AI, and
    optionally saves the cleaned result to disk.
    
    Args:
        api_key: Your Sliq API key. Get one at https://sliqdata.com/dashboard/account
        dataset_path: Path to your dataset file (CSV, JSON, JSONL, Excel, or Parquet). Pass a string, not a Path object.
        dataset_name: A name for your dataset (used in reports and tracking).
        save_clean_file_path: Directory path where the cleaned file should be saved.
            If empty, the file is not downloaded and you can access it at https://sliqdata.com/dashboard/jobs.
        save_clean_file_name: Custom filename for the saved file (without extension).
            If empty, uses the original filename from Sliq.
        output_format: The file format for the cleaned dataset output.
            Valid values: '.csv', '.json', '.jsonl', '.xlsx', '.parquet'.
            If None or empty string, the cleaned dataset will be saved in the
            same format as the input file.
        dataset_description: Description of what your data contains.
            Helps the AI understand the context for better cleaning.
        dataset_purpose: What you plan to use the cleaned data for.
            Helps tailor the cleaning process to your needs.
        column_guide: Dictionary mapping column names to descriptions.
            Must include all columns in the dataset. Column names are validated
            against the dataset (case-insensitive, underscore-insensitive).
            Example: {"age": "Person's age in years", "income": "Annual income in USD"}
        data_source: Where the data came from (e.g., "Kaggle", "internal database").
        user_instructions: Special instructions for the cleaning process.
            Example: "Preserve all negative values in the 'balance' column"
        is_feature_engineering: If True, perform feature engineering in addition
            to cleaning. Creates new derived features from existing data.
        is_detailed_report: If True, generate a detailed explanation report.
            Available for download at https://sliqdata.com/dashboard/jobs.
        verbose: If True, print progress messages during cleaning.
    
    Returns:
        None. The cleaned file is saved to disk if save_clean_file_path is provided.
    
    Raises:
        SliqValidationError: If input validation fails (missing API key, unsupported
            format, or column_guide doesn't match dataset columns).
        SliqFileError: If file operations fail (file not found, permission denied).
        SliqAuthenticationError: If the API key is invalid.
        SliqAPIError: If the API returns an error.
        SliqJobFailedError: If the cleaning job fails.
        SliqTimeoutError: If the job doesn't complete within the timeout.
    
    Example:
        >>> import sliq
        >>> sliq.clean_from_file(
        ...     api_key="your-api-key",
        ...     dataset="data/raw_sales.csv",
        ...     dataset_name="Sales Data 2024",
        ...     save_clean_file_path="data/cleaned/",
        ...     dataset_description="Monthly sales records from all regions",
        ...     verbose=True,
        ... )
        Uploading dataset...
        ✓ Upload complete
        Cleaning in progress...
        ✓ Cleaning complete!
        ✓ Saved to: data/cleaned/Sliq clean dataset - Sales Data 2024.csv
    """
    _setup_logging(verbose)
    
    # Validate inputs
    _validate_api_key(api_key)
    
    if not dataset_path:
        raise SliqValidationError("Dataset path is required")
    
    if not dataset_name:
        raise SliqValidationError("Dataset name is required")
    
    # Validate save_clean_file_name requires save_clean_file_path
    if save_clean_file_name and not save_clean_file_path:
        raise SliqValidationError(
            "save_clean_file_name requires save_clean_file_path. "
            "Please provide a path to save the cleaned file."
        )
    
    # Validate and normalize output_format
    # Treat empty string as None (no preference - use input format)
    validated_output_format = _validate_output_format(output_format)
    
    # Validate file exists and has supported format
    file_path = validate_file_path(dataset_path)
    _log_progress(f"Preparing to clean: {file_path.name}", verbose)
    
    # Validate column_guide matches dataset columns (if provided)
    # Uses memory-efficient reading to extract only column names
    validate_column_guide_for_file(column_guide, file_path)
    
    # Validate output directory if provided
    output_dir = None
    if save_clean_file_path:
        output_dir = validate_output_directory(save_clean_file_path)
    
    # Step 1: Get presigned URL
    try:
        presign_response = call_presign(api_key)
    except Exception as e:
        raise SliqAPIError(f"Failed to get presigned URL: {e}")
    
    # Step 2: Create zip and upload
    _log_progress("Uploading dataset to Sliq's servers...", verbose)
    zip_bytes, original_filename = create_zip_from_file(file_path)
    upload_to_presigned_url(presign_response["upload_url"], zip_bytes)
    _log_progress("✓ Upload complete", verbose)
    
    # Step 3: Trigger cleaning job
    _log_progress(f"Starting cleaning your dataset: {dataset_name}", verbose)
    _log_progress("The cleaning process may take between 3 up to 15 minutes. Please wait...", verbose)
    run_response = call_run(
        api_key=api_key,
        user_id=presign_response["user_id"],
        job_id=presign_response["job_id"],
        dataset_key=presign_response["object_key"],
        dataset_name=dataset_name,
        dataset_description=dataset_description,
        dataset_purpose=dataset_purpose,
        column_guide=column_guide,
        data_source=data_source,
        user_instructions=user_instructions,
        is_feature_engineering=is_feature_engineering,
        is_detailed_report=is_detailed_report,
        output_format=validated_output_format,
    )
    
    # Step 4: Poll until complete
    status = _poll_until_complete(
        api_key=api_key,
        execution_name=run_response["execution_name"],
        dataset_key=presign_response["object_key"],
        user_id=presign_response["user_id"],
        job_id=presign_response["job_id"],
        dataset_name=dataset_name,
        verbose=verbose,
    )
    
    # Step 5: Download and save if requested
    if save_clean_file_path and output_dir:
        download_urls = status.get("download_urls")
        if download_urls and "cleaned_dataset_url" in download_urls:
            _log_progress("Downloading cleaned dataset to your machine...", verbose)
            # Download the cleaned dataset zip
            zip_bytes = download_from_presigned_url(download_urls["cleaned_dataset_url"])
            
            # Extract the file from the zip
            file_bytes, filename = extract_file_from_zip(zip_bytes)
            
            # Save to disk
            saved_path = save_file_to_disk(
                file_bytes=file_bytes,
                output_dir=output_dir,
                filename=filename,
                custom_name=save_clean_file_name,
            )
            _log_progress(f"✓ Saved to: {saved_path}", verbose)
        else:
            print(f"Warning: Could not download cleaned file. Access it at {WEBSITE_URL}. Check your Sliq dashboard.")
    else:
        # No save path provided
        print(f"Download your dataset at {WEBSITE_URL}. Check your Sliq dashboard.")
        if verbose:
            print(f"\n  Tip: Use save_clean_file_path to automatically save the cleaned dataset to machine.")


def clean_from_dataframe(
    api_key: str,
    dataframe: DataFrame,
    dataset_name: str,
    output_format: Optional[str] = None,
    dataset_description: str = "",
    dataset_purpose: str = "",
    column_guide: Optional[Dict[str, str]] = None,
    data_source: str = "",
    user_instructions: str = "",
    is_feature_engineering: bool = False,
    is_detailed_report: bool = False,
    is_return_dataframe: bool = True,
    verbose: bool = False,
) -> Optional[DataFrame]:
    """Clean a Pandas or Polars DataFrame and optionally return the result.
    
    This function uploads your DataFrame to Sliq, cleans it using AI, and
    optionally returns the cleaned DataFrame.
    
    Args:
        api_key: Your Sliq API key. Get one at https://sliqdata.com/dashboard/account
        dataframe: A Pandas or Polars DataFrame to clean.
        dataset_name: A name for your dataset (used in reports and tracking).
        output_format: The file format for the cleaned dataset output.
            Valid values: '.csv', '.json', '.jsonl', '.xlsx', '.parquet'.
            If None or empty string, the cleaned dataset will be returned in
            Parquet format (the internal transfer format).
        dataset_description: Description of what your data contains.
            Helps the AI understand the context for better cleaning.
        dataset_purpose: What you plan to use the cleaned data for.
            Helps tailor the cleaning process to your needs.
        column_guide: Dictionary mapping column names to descriptions.
            Must include all columns in the DataFrame. Column names are validated
            against the DataFrame (case-insensitive, underscore-insensitive).
            Example: {"age": "Person's age in years", "income": "Annual income in USD"}
        data_source: Where the data came from (e.g., "Kaggle", "internal database").
        user_instructions: Special instructions for the cleaning process.
            Example: "Preserve all negative values in the 'balance' column"
        is_feature_engineering: If True, perform feature engineering in addition
            to cleaning. Creates new derived features from existing data.
        is_detailed_report: If True, generate a detailed explanation report.
            Available for download at https://sliqdata.com/dashboard/jobs.
        is_return_dataframe: By default, True. If True, download and return the cleaned DataFrame.
            If False, the cleaned data is only available via the dashboard at https://sliqdata.com/dashboard/jobs.
        verbose: If True, print progress messages during cleaning.
    
    Returns:
        If is_return_dataframe is True: The cleaned DataFrame (same type as input).
        If is_return_dataframe is False: None.
    
    Raises:
        SliqValidationError: If input validation fails (missing API key, empty
            DataFrame, or column_guide doesn't match DataFrame columns).
        SliqAuthenticationError: If the API key is invalid.
        SliqAPIError: If the API returns an error.
        SliqJobFailedError: If the cleaning job fails.
        SliqTimeoutError: If the job doesn't complete within the timeout.
    
    Example:
        >>> import sliq
        >>> import pandas as pd
        >>> 
        >>> df = pd.read_csv("raw_data.csv")
        >>> cleaned_df = sliq.clean_from_dataframe(
        ...     api_key="your-api-key",
        ...     dataframe=df,
        ...     dataset_name="Customer Data",
        ...     is_return_dataframe=True,
        ...     verbose=True,
        ... )
        Uploading dataset...
        ✓ Upload complete
        Cleaning in progress...
        ✓ Cleaning complete!
        >>> cleaned_df.head()
        customer_id  age  income_normalized
        0            1   25              0.45
        1            2   34              0.67
    """
    _setup_logging(verbose)
    
    # Validate inputs
    _validate_api_key(api_key)
    
    if dataframe is None:
        raise SliqValidationError("DataFrame is required")
    
    if not dataset_name:
        raise SliqValidationError("Dataset name is required")
    
    # Detect DataFrame type and validate
    df_type = detect_dataframe_type(dataframe)
    validate_dataframe(dataframe)
    _log_progress(f"Preparing to clean {df_type.capitalize()} DataFrame: {dataset_name}", verbose)
    
    # Validate column_guide matches DataFrame columns (if provided)
    validate_column_guide_for_dataframe(column_guide, dataframe)
    
    # Validate and normalize output_format
    # Treat empty string as None (no preference - use input format)
    validated_output_format = _validate_output_format(output_format)
    
    # Step 1: Get presigned URL
    try:
        presign_response = call_presign(api_key)
    except Exception as e:
        raise SliqAPIError(f"Failed to get presigned URL: {e}")
    
    # Step 2: Convert DataFrame to Parquet and create zip
    _log_progress("Uploading DataFrame to Sliq's servers...", verbose)
    parquet_bytes = dataframe_to_parquet_bytes(dataframe)
    zip_bytes = create_zip_from_bytes(parquet_bytes, "dataset.parquet")
    
    # Upload to presigned URL
    upload_to_presigned_url(presign_response["upload_url"], zip_bytes)
    _log_progress("✓ Upload complete", verbose)
    
    _log_progress(f"Starting cleaning your dataset: {dataset_name}", verbose)
    _log_progress("The cleaning process may take between 3 up to 15 minutes. Please wait...", verbose)
    # Step 3: Trigger cleaning job
    run_response = call_run(
        api_key=api_key,
        user_id=presign_response["user_id"],
        job_id=presign_response["job_id"],
        dataset_key=presign_response["object_key"],
        dataset_name=dataset_name,
        dataset_description=dataset_description,
        dataset_purpose=dataset_purpose,
        column_guide=column_guide,
        data_source=data_source,
        user_instructions=user_instructions,
        is_feature_engineering=is_feature_engineering,
        is_detailed_report=is_detailed_report,
        output_format=validated_output_format,
    )
    
    # Step 4: Poll until complete
    status = _poll_until_complete(
        api_key=api_key,
        execution_name=run_response["execution_name"],
        dataset_key=presign_response["object_key"],
        user_id=presign_response["user_id"],
        job_id=presign_response["job_id"],
        dataset_name=dataset_name,
        verbose=verbose,
    )
    
    # Step 5: Download and return if requested
    if is_return_dataframe:
        download_urls = status.get("download_urls")
        if download_urls and "cleaned_dataset_url" in download_urls:
            # Download the cleaned dataset zip
            zip_bytes = download_from_presigned_url(download_urls["cleaned_dataset_url"])
            
            # Extract the file from the zip
            file_bytes, filename = extract_file_from_zip(zip_bytes)
            
            # Convert back to DataFrame (same type as input)
            cleaned_df = file_bytes_to_dataframe(file_bytes, filename, output_type=df_type)
            _log_progress("✓ DataFrame ready and returned", verbose)
            return cleaned_df
        else:
            print(f"Warning: Could not download cleaned data. Access it at {WEBSITE_URL}. Check your Sliq dashboard.")
            return None
    else:
        # Not returning DataFrame
        print(
            f"Download your dataset at {WEBSITE_URL}. Check your Sliq dashboard."
        )
        if verbose:
            print(
                f"\nTip: Set is_return_dataframe=True to get the cleaned "
                f"DataFrame returned directly."
            )
        return None


def _setup_logging(verbose: bool) -> None:
    """Configure logging based on verbose flag.
    
    Args:
        verbose: If True, show progress messages to the user.
    """
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
        )
    else:
        # Suppress all library logging when not verbose
        logging.getLogger("sliq").setLevel(logging.WARNING)


def _log_progress(message: str, verbose: bool) -> None:
    """Log a progress message if verbose is enabled.
    
    Args:
        message: Message to display.
        verbose: If True, print the message.
    """
    if verbose:
        print(message)


def _validate_api_key(api_key: str) -> None:
    """Validate that an API key is provided.
    It does not check if the key is valid with the server.
    It only checks for presence and type.
    
    Args:
        api_key: The API key to validate.
        
    Raises:
        SliqValidationError: If the API key is missing or empty.
    """
    if not api_key:
        raise SliqValidationError(
            "API key is required. Get your API key at https://sliqdata.com/dashboard/jobs"
        )
    
    if not isinstance(api_key, str):
        raise SliqValidationError("API key must be a string")


def _validate_output_format(output_format: Optional[str]) -> Optional[str]:
    """Validate and normalize the output format parameter.
    
    This function performs client-side validation of the output_format before
    sending the request to the API. This catches invalid formats early and
    provides a clear error message to the user.
    
    Args:
        output_format: The user-specified output format. Can be None, empty
            string, or a format string like '.csv' or 'csv'.
    
    Returns:
        The normalized output format (lowercase with leading dot) if valid,
        or None if no format was specified.
    
    Raises:
        SliqValidationError: If the output format is not valid.
    
    Examples:
        >>> _validate_output_format(None)
        None
        
        >>> _validate_output_format("")
        None
        
        >>> _validate_output_format("csv")
        '.csv'
        
        >>> _validate_output_format(".JSON")
        '.json'
        
        >>> _validate_output_format("txt")
        # Raises SliqValidationError
    """
    # Treat None as no preference (use input format on the server side)
    if output_format is None:
        return None
    
    # Treat empty string (after stripping whitespace) as None
    if isinstance(output_format, str) and output_format.strip() == "":
        return None
    
    # Normalize the format: lowercase and ensure leading dot
    normalized_format = output_format.lower().strip()
    if not normalized_format.startswith('.'):
        normalized_format = f'.{normalized_format}'
    
    # Validate against allowed formats
    if normalized_format not in VALID_OUTPUT_FORMATS:
        valid_formats_str = ', '.join(sorted(VALID_OUTPUT_FORMATS))
        raise SliqValidationError(
            f"Invalid output format: '{output_format}'. "
            f"Valid formats are: {valid_formats_str}. "
            f"Leave output_format empty or set to None to save the cleaned "
            f"dataset in the same format as the input file."
        )
    
    return normalized_format


def _poll_until_complete(
    api_key: str,
    execution_name: str,
    dataset_key: str,
    user_id: str,
    job_id: str,
    dataset_name: str,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Poll the status endpoint until the job is complete.
    
    Args:
        api_key: The user's API key.
        execution_name: The execution name from the run response.
        dataset_key: The dataset key for cleanup.
        user_id: The user ID (for generating download URLs).
        job_id: The job ID (for generating download URLs).
        dataset_name: The dataset name (for generating download URLs).
        verbose: If True, show progress updates.
        
    Returns:
        The final status response with download URLs.
        
    Raises:
        SliqTimeoutError: If the job doesn't complete within the timeout.
        SliqJobFailedError: If the job fails.
    """
    _log_progress("Cleaning in progress...", verbose)
    
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        status = call_status(
            api_key,
            execution_name,
            dataset_key,
            user_id=user_id,
            job_id=job_id,
            dataset_name=dataset_name,
        )
        
        if status["is_complete"]:
            # Consider a job successful if either the explicit succeeded flag is truthy
            # or the status string indicates success. This makes the client robust to
            # backends that may return inconsistent 'succeeded' flags.
            succeeded_flag = bool(status.get("succeeded", False)) or (
                str(status.get("status", "")).lower() == "succeeded"
            )
            if succeeded_flag:
                _log_progress("\n✓ Cleaning complete! Your cleaned dataset is ready.\n", verbose)
                return status
            else:
                raise SliqJobFailedError(
                    status.get("message", "Job failed"),
                    status=status.get("status"),
                )
        
        # Show progress update
        if verbose and attempt % 3 == 0:  # Every 30 seconds
            elapsed = attempt * POLL_INTERVAL_SECONDS
            print(f"  Still cleaning... ({elapsed}s elapsed)")
        
        if attempt < MAX_POLL_ATTEMPTS:
            time.sleep(POLL_INTERVAL_SECONDS)
    
    # Timed out
    raise SliqTimeoutError(
        f"Job did not complete within {MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS} seconds. "
        f"The job may still be running. Check status at {WEBSITE_URL}"
    )
