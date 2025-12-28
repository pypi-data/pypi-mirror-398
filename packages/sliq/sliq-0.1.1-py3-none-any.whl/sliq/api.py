"""API client for communicating with the Sliq API.

This module handles all HTTP communication with the Sliq API, including:
- Getting presigned URLs for uploads
- Triggering cleaning jobs
- Polling for job status
- Getting download URLs for results

All API communication is done securely via HTTPS with proper authentication.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import requests

from sliq.config import API_BASE_URL, API_TIMEOUT
from sliq.exceptions import (
    SliqAPIError,
    SliqAuthenticationError,
    SliqRateLimitError,
)
from sliq.types import PresignResponse, RunResponse, StatusResponse

# Configure module logger
logger = logging.getLogger(__name__)


# =============================================================================
# MAIN API FUNCTIONS
# =============================================================================

def call_presign(
    api_key: str,
    content_type: str = "application/zip",
    expires_in_seconds: int = 1800, # 30 minutes
) -> PresignResponse:
    """Request a presigned URL for uploading a dataset.
    
    This is the first step in the cleaning flow. The returned presigned URL
    allows direct upload to cloud storage without exposing credentials.
    
    Args:
        api_key: The user's Sliq API key.
        content_type: MIME type of the upload (default: application/zip).
        expires_in_seconds: How long the upload URL is valid (default: 30 minutes).
        
    Returns:
        PresignResponse containing upload_url, object_key, user_id, and job_id.
        
    Raises:
        SliqAuthenticationError: If the API key is invalid.
        SliqRateLimitError: If rate limit is exceeded.
        SliqAPIError: For other API errors.
    """
    url = f"{API_BASE_URL}/presign"
    headers = _get_auth_headers(api_key)
    payload = {
        "content_type": content_type,
        "expires_in_seconds": expires_in_seconds,
    }
    
    logger.debug("Calling /presign endpoint")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=API_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        raise SliqAPIError("Request timed out while connecting to Sliq API")
    except requests.exceptions.ConnectionError:
        raise SliqAPIError("Failed to connect to Sliq API. Please check your internet connection.")
    
    if response.status_code != 200:
        _handle_api_error(response)
    
    data = response.json()
    logger.debug("Received presign response: job_id=%s", data.get("job_id"))
    
    return PresignResponse(
        upload_url=data["upload_url"],
        object_key=data["object_key"],
        user_id=data["user_id"],
        job_id=data["job_id"],
        expires_in_seconds=data["expires_in_seconds"],
    )


def call_run(
    api_key: str,
    user_id: str,
    job_id: str,
    dataset_key: str,
    dataset_name: str,
    dataset_description: str = "",
    dataset_purpose: str = "",
    column_guide: Optional[Dict[str, str]] = None,
    data_source: str = "",
    user_instructions: str = "",
    is_feature_engineering: bool = False,
    is_detailed_report: bool = False,
    output_format: Optional[str] = None,
) -> RunResponse:
    """Trigger a cleaning job for the uploaded dataset.
    
    This is called after the dataset has been uploaded to the presigned URL.
    The job runs asynchronously and status can be checked via call_status().
    
    Args:
        api_key: The user's Sliq API key.
        user_id: User ID from the presign response.
        job_id: Job ID from the presign response.
        dataset_key: Object key from the presign response.
        dataset_name: Human-readable name for the dataset.
        dataset_description: Description of what the data contains.
        dataset_purpose: What the cleaned data will be used for.
        column_guide: Optional mapping of column names to descriptions.
        data_source: Where the data came from (e.g., "Kaggle", "internal DB").
        user_instructions: Special instructions for the cleaning process.
        is_feature_engineering: Whether to perform feature engineering.
        is_detailed_report: Whether to generate a detailed explanation report.
        output_format: Optional file format for the cleaned dataset output.
            Valid values: '.csv', '.json', '.jsonl', '.xlsx', '.parquet'.
            If None, the cleaned dataset will be saved in the same format as
            the input file.
        
    Returns:
        RunResponse containing execution_name for tracking the job.
        
    Raises:
        SliqAuthenticationError: If the API key is invalid.
        SliqRateLimitError: If rate limit is exceeded.
        SliqAPIError: For other API errors.
    """
    url = f"{API_BASE_URL}/run"
    headers = _get_auth_headers(api_key)
    
    # Convert column_guide dict to JSON string if provided
    column_guide_json = json.dumps(column_guide) if column_guide else None
    
    payload = {
        "user_id": user_id,
        "job_id": job_id,
        "dataset_key": dataset_key,
        "dataset_name": dataset_name,
        "dataset_description": dataset_description or None,
        "dataset_purpose": dataset_purpose or None,
        "column_guide": column_guide_json,
        "data_source": data_source or None,
        "user_instructions": user_instructions or None,
        "is_feature_engineering": is_feature_engineering,
        "is_detailed_report": is_detailed_report,
        "output_format": output_format,  # None means use input format
    }
    
    logger.debug("Calling /run endpoint for job_id=%s", job_id)
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=API_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        raise SliqAPIError("Request timed out while triggering cleaning job")
    except requests.exceptions.ConnectionError:
        raise SliqAPIError("Failed to connect to Sliq API. Please check your internet connection.")
    
    if response.status_code != 200:
        _handle_api_error(response)
    
    data = response.json()
    logger.debug("Cleaning job triggered: execution_name=%s", data.get("execution_name"))
    
    return RunResponse(
        execution_name=data["execution_name"],
        status_url=data["status_url"],
    )


def call_status(
    api_key: str,
    execution_name: str,
    dataset_key: str,
    user_id: str,
    job_id: str,
    dataset_name: str,
) -> StatusResponse:
    """Check the status of a cleaning job.
    
    This should be called periodically to check if the job is complete.
    When complete, the response includes download URLs for the results.
    
    Args:
        api_key: The user's Sliq API key.
        execution_name: The execution name from the run response.
        dataset_key: The dataset key (used for cleanup when job completes).
        user_id: The user ID (for generating download URLs).
        job_id: The job ID (for generating download URLs).
        dataset_name: The dataset name (for generating download URLs).
        
    Returns:
        StatusResponse with job status and download URLs (if complete).
        
    Raises:
        SliqAuthenticationError: If the API key is invalid.
        SliqRateLimitError: If rate limit is exceeded.
        SliqAPIError: For other API errors.
    """
    url = f"{API_BASE_URL}/status"
    headers = _get_auth_headers(api_key)
    payload = {
        "execution_name": execution_name,
        "dataset_key": dataset_key,
        "user_id": user_id,
        "job_id": job_id,
        "dataset_name": dataset_name,
    }
    
    logger.debug("Checking status for execution=%s", execution_name)
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=API_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        raise SliqAPIError("Request timed out while checking job status")
    except requests.exceptions.ConnectionError:
        raise SliqAPIError("Failed to connect to Sliq API. Please check your internet connection.")
    
    if response.status_code != 200:
        _handle_api_error(response)
    
    data = response.json()
    logger.debug("Status response: is_complete=%s, status=%s", data.get("is_complete"), data.get("status"))
    
    # Normalize 'succeeded' to a boolean for robust behavior. Some servers may
    # return strings like 'succeeded' or 'true'. We also fallback to the status
    # string to determine success when the flag is missing or ambiguous.
    raw_succeeded = data.get("succeeded")
    status_str = str(data.get("status", "")).lower()
    if isinstance(raw_succeeded, str):
        succeeded_bool = raw_succeeded.strip().lower() in ("true", "1", "succeeded")
    elif raw_succeeded is not None:
        # If the server returned an explicit boolean, respect it, but also
        # consider the status string (some servers may be inconsistent and set
        # the succeeded flag incorrectly). If either indicates success, treat
        # as success.
        succeeded_bool = bool(raw_succeeded) or (status_str == "succeeded")
    else:
        # No 'succeeded' flag provided - infer from status string.
        succeeded_bool = status_str == "succeeded"

    return StatusResponse(
        is_complete=bool(data["is_complete"]),
        succeeded=succeeded_bool,
        status=status_str,
        message=data.get("message"),
        dirty_dataset_deleted=bool(data.get("dirty_dataset_deleted", False)),
        download_urls=data.get("download_urls"),
    )


def upload_to_presigned_url(
    upload_url: str,
    data: bytes,
    content_type: str = "application/zip",
) -> None:
    """Upload data directly to cloud storage using a presigned URL.
    
    This uploads the dataset directly to R2 storage, bypassing the API server.
    The presigned URL provides temporary, secure access for the upload.
    
    Args:
        upload_url: The presigned URL from the presign response.
        data: The raw bytes to upload (should be a zip file).
        content_type: MIME type of the upload.
        
    Raises:
        SliqAPIError: If the upload fails.
    """
    headers = {"Content-Type": content_type}
    
    logger.debug("Uploading %d bytes to presigned URL", len(data))
    
    try:
        response = requests.put(
            upload_url,
            data=data,
            headers=headers,
            timeout=300,  # 5 minute timeout for large uploads
        )
    except requests.exceptions.Timeout:
        raise SliqAPIError("Upload timed out. The file may be too large.")
    except requests.exceptions.ConnectionError:
        raise SliqAPIError("Upload failed. Please check your internet connection.")
    
    if response.status_code not in (200, 201):
        raise SliqAPIError(
            f"Failed to upload dataset: {response.text}",
            status_code=response.status_code,
        )
    
    logger.debug("Upload successful")


def download_from_presigned_url(download_url: str) -> bytes:
    """Download data from cloud storage using a presigned URL.
    
    This downloads the cleaned dataset directly from R2 storage.
    The presigned URL provides temporary, secure access for the download.
    
    Args:
        download_url: The presigned URL for downloading.
        
    Returns:
        The raw bytes of the downloaded file.
        
    Raises:
        SliqAPIError: If the download fails.
    """
    logger.debug("Downloading from presigned URL")
    
    try:
        response = requests.get(
            download_url,
            timeout=300,  # 5 minute timeout for large downloads
        )
    except requests.exceptions.Timeout:
        raise SliqAPIError("Download timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise SliqAPIError("Download failed. Please check your internet connection.")
    
    if response.status_code != 200:
        raise SliqAPIError(
            f"Failed to download file: {response.text}",
            status_code=response.status_code,
        )
    
    logger.debug("Downloaded %d bytes", len(response.content))
    return response.content


# =============================================================================
# HELPER FUNCTIONS (Internal use only)
# =============================================================================

def _get_auth_headers(api_key: str) -> Dict[str, str]:
    """Create authorization headers for API requests.
    
    Args:
        api_key: The user's Sliq API key.
        
    Returns:
        Dictionary containing the Authorization header.
    """
    return {"Authorization": f"Bearer {api_key}"}


def _handle_api_error(response: requests.Response) -> None:
    """Handle error responses from the API.
    
    Args:
        response: The HTTP response from the API.
        
    Raises:
        SliqAuthenticationError: If the API key is invalid (401).
        SliqRateLimitError: If rate limit is exceeded (429).
        SliqAPIError: For other API errors.
    """
    status_code = response.status_code
    
    # Try to extract error message from response
    try:
        error_data = response.json()
        message = error_data.get("detail", response.text)
    except (json.JSONDecodeError, ValueError):
        message = response.text or f"HTTP {status_code}"
    
    # Raise specific exceptions for known error codes
    if status_code == 401:
        raise SliqAuthenticationError(message)
    elif status_code == 429:
        raise SliqRateLimitError(message)
    else:
        raise SliqAPIError(message, status_code)
