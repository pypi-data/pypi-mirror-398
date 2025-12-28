"""Sliq - AI-powered data cleaning made effortless.

Sliq provides a simple interface to clean your datasets using AI.
With just a few lines of code, you can clean messy data, handle missing values,
fix inconsistencies, and prepare your data for analysis or machine learning.

Example usage:

    # Clean a file
    import sliq
    sliq.clean_from_file(
        api_key="your-api-key",
        dataset="path/to/data.csv",
        dataset_name="My Dataset",
        save_clean_file_path="path/to/output/",
    )

    # Clean a DataFrame
    import sliq
    import pandas as pd
    df = pd.read_csv("data.csv")
    cleaned_df = sliq.clean_from_dataframe(
        api_key="your-api-key",
        dataframe=df,
        dataset_name="My Dataset",
        is_return_dataframe=True,
    )

For more information, visit https://sliqdata.com/docs
"""

__version__ = "0.1.1"
__author__ = "Sliq Team"
__email__ = "support@sliqdata.com"

# Public API - expose the two main functions at package level
from sliq.client import clean_from_file, clean_from_dataframe

# Also expose exceptions for advanced error handling
from sliq.exceptions import (
    SliqError,
    SliqAPIError,
    SliqAuthenticationError,
    SliqValidationError,
    SliqFileError,
    SliqJobFailedError,
    SliqTimeoutError,
    SliqRateLimitError,
)

# Define what gets exported with "from sliq import *"
__all__ = [
    # Main functions
    "clean_from_file",
    "clean_from_dataframe",
    # Exceptions for error handling
    "SliqError",
    "SliqAPIError",
    "SliqAuthenticationError",
    "SliqValidationError",
    "SliqFileError",
    "SliqJobFailedError",
    "SliqTimeoutError",
    "SliqRateLimitError",
    # Metadata
    "__version__",
]
