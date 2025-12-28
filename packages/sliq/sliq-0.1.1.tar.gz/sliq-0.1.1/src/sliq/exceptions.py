"""Custom exceptions for the Sliq library.

This module defines all custom exceptions that can be raised by the Sliq library.
These exceptions provide clear error messages to help users understand and fix issues.
"""


class SliqError(Exception):
    """Base exception for all Sliq-related errors.
    
    All Sliq exceptions inherit from this class, allowing users to catch
    all Sliq errors with a single except clause if desired.
    """
    pass


class SliqAPIError(SliqError):
    """Raised when the Sliq API returns an error response.
    
    This can occur due to:
    - Invalid API key
    - Rate limiting
    - Server errors
    - Invalid request parameters
    
    Attributes:
        status_code: HTTP status code from the API response.
        message: Error message from the API or a descriptive message.
    """
    
    def __init__(self, message: str, status_code: int | None = None):
        """Initialize the API error.
        
        Args:
            message: Human-readable error description.
            status_code: HTTP status code from the API (if available).
        """
        self.status_code = status_code
        self.message = message
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format the error message with status code if available."""
        if self.status_code:
            return f"API Error ({self.status_code}): {self.message}"
        return f"API Error: {self.message}"


class SliqAuthenticationError(SliqAPIError):
    """Raised when API key authentication fails.
    
    This occurs when:
    - API key is missing
    - API key is invalid or expired
    - API key does not have permission for the requested operation
    """
    
    def __init__(self, message: str = "Invalid or missing API key"):
        """Initialize the authentication error."""
        super().__init__(message, status_code=401)


class SliqRateLimitError(SliqAPIError):
    """Raised when API rate limit is exceeded.
    
    The Sliq API enforces rate limits to ensure fair usage.
    If you encounter this error, wait before making more requests.
    """
    
    def __init__(self, message: str = "Rate limit exceeded. Please wait before retrying."):
        """Initialize the rate limit error."""
        super().__init__(message, status_code=429)


class SliqValidationError(SliqError):
    """Raised when input validation fails.
    
    This occurs when:
    - Required parameters are missing
    - File format is not supported
    - File path is invalid
    - DataFrame is empty or invalid
    """
    
    def __init__(self, message: str):
        """Initialize the validation error.
        
        Args:
            message: Description of what validation failed.
        """
        self.message = message
        super().__init__(f"Validation Error: {message}")


class SliqFileError(SliqError):
    """Raised when file operations fail.
    
    This occurs when:
    - File does not exist
    - File cannot be read
    - File cannot be written
    - File format is unsupported
    """
    
    def __init__(self, message: str, file_path: str | None = None):
        """Initialize the file error.
        
        Args:
            message: Description of the file error.
            file_path: Path to the file that caused the error (if applicable).
        """
        self.message = message
        self.file_path = file_path
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format the error message with file path if available."""
        if self.file_path:
            return f"File Error ({self.file_path}): {self.message}"
        return f"File Error: {self.message}"


class SliqTimeoutError(SliqError):
    """Raised when a cleaning job times out.
    
    This occurs when the cleaning job takes longer than the maximum
    allowed time. The job may still be running in the background.
    """
    
    def __init__(self, message: str = "Cleaning job timed out"):
        """Initialize the timeout error."""
        self.message = message
        super().__init__(f"Timeout Error: {message}")


class SliqJobFailedError(SliqError):
    """Raised when a cleaning job fails to complete successfully.
    
    This occurs when the cleaning job encounters an error during
    processing. Check the error message for details.
    """
    
    def __init__(self, message: str, status: str | None = None):
        """Initialize the job failed error.
        
        Args:
            message: Description of why the job failed.
            status: Job status string from the API (if available).
        """
        self.message = message
        self.status = status
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format the error message with status if available."""
        if self.status:
            return f"Job Failed ({self.status}): {self.message}"
        return f"Job Failed: {self.message}"
