"""Configuration constants for the Sliq library.

This module contains configuration values that control the library's behavior.
These values are not secrets and are safe to be public.
"""

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Production API endpoint
API_BASE_URL = "https://sliq-api-716392330170.us-central1.run.app"

# API request timeout in seconds
API_TIMEOUT = 30

# =============================================================================
# FILE FORMAT CONFIGURATION
# =============================================================================

# Supported file extensions for dataset upload
SUPPORTED_EXTENSIONS = frozenset({
    ".csv",
    ".json",
    ".jsonl",
    ".xlsx",
    ".xls",
    ".xlsb",
    ".parquet",
})

# Content type for zip uploads
UPLOAD_CONTENT_TYPE = "application/zip"

# Default presigned URL expiration time in seconds (1 hour)
PRESIGN_EXPIRY_SECONDS = 3600

# =============================================================================
# JOB POLLING CONFIGURATION
# =============================================================================

# How often to check job status (in seconds)
POLL_INTERVAL_SECONDS = 10

# Maximum time to wait for a job to complete (in seconds)
# Default: 30 minutes
MAX_POLL_TIME_SECONDS = 1800

# Maximum number of poll attempts (calculated from above values)
MAX_POLL_ATTEMPTS = MAX_POLL_TIME_SECONDS // POLL_INTERVAL_SECONDS

# =============================================================================
# WEBSITE URLS (for user messages)
# =============================================================================

# Main website
WEBSITE_URL = "https://sliqdata.com"
# Documentation and dashboard URLs
DOCS_URL = "https://sliqdata.com/docs"
DASHBOARD_URL = "https://sliqdata.com/dashboard"
