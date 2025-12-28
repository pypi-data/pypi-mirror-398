# Sliq Python Library

**Data cleaning, made effortless.**

Sliq is a Python library that provides a simple interface to clean your datasets using AI. With just a few lines of code, you can clean messy data, handle missing values, fix inconsistencies, and prepare your data for analysis or machine learning.

## Installation

```bash
pip install sliq
```

## Quick Start

### Clean a file

```python
import sliq

# Clean a CSV file and save the result
sliq.clean_from_file(
    api_key="your-api-key",
    dataset_path="path/to/your/data.csv",
    dataset_name="My Dataset",
    save_clean_file_path="path/to/output/",
)
```

### Clean a DataFrame

```python
import sliq
import pandas as pd

# Load your data
df = pd.read_csv("path/to/your/data.csv")

# Clean and get the result as a DataFrame
cleaned_df = sliq.clean_from_dataframe(
    api_key="your-api-key",
    dataframe=df,
    dataset_name="My Dataset",
    is_return_dataframe=True,
)
```

## Features

- **Simple API**: Just two functions to clean any dataset
- **Multiple formats**: Supports CSV, JSON, JSONL, Excel, and Parquet files
- **DataFrame support**: Works with both Pandas and Polars DataFrames
- **AI-powered**: Uses advanced AI to understand and clean your data
- **Customizable**: Provide context about your data for better cleaning
- **Secure**: Your data is processed securely and deleted after cleaning

## Supported File Formats

| Format | Extension |
|--------|-----------|
| CSV | `.csv` |
| JSON | `.json` |
| JSONL | `.jsonl` |
| Excel | `.xlsx`, `.xls` |
| Parquet | `.parquet` |

## API Reference

### `clean_from_file()`

Clean a dataset from a file path.

```python
sliq.clean_from_file(
    api_key: str,                          # Required: Your Sliq API key
    dataset_path: str,                     # Required: Path to your dataset file
    dataset_name: str,                     # Required: Name for your dataset
    save_clean_file_path: str = "",        # Path to save the cleaned file
    save_clean_file_name: str = "",        # Custom name for the saved file
    output_format: str | None = None,      # Output file format (see below)
    dataset_description: str = "",         # Description of your data
    dataset_purpose: str = "",             # What the data will be used for
    column_guide: dict[str, str] = None,   # Column name to description mapping (see below)
    data_source: str = "",                 # Where the data came from
    user_instructions: str = "",           # Special cleaning instructions
    is_feature_engineering: bool = False,  # Enable feature engineering
    is_detailed_report: bool = False,      # Generate detailed report
    verbose: bool = False,                 # Show progress messages
)
```

### `clean_from_dataframe()`

Clean a Pandas or Polars DataFrame.

```python
cleaned_df = sliq.clean_from_dataframe(
    api_key: str,                          # Required: Your Sliq API key
    dataframe: pd.DataFrame | pl.DataFrame,# Required: Your DataFrame
    dataset_name: str,                     # Required: Name for your dataset
    output_format: str | None = None,      # Output file format (see below)
    dataset_description: str = "",         # Description of your data
    dataset_purpose: str = "",             # What the data will be used for
    column_guide: dict[str, str] = None,   # Column name to description mapping (see below)
    data_source: str = "",                 # Where the data came from
    user_instructions: str = "",           # Special cleaning instructions
    is_feature_engineering: bool = False,  # Enable feature engineering
    is_detailed_report: bool = False,      # Generate detailed report
    is_return_dataframe: bool = True,      # Return cleaned DataFrame
    verbose: bool = False,                 # Show progress messages
)
```

### Output Format

The `output_format` parameter controls the file format of the cleaned dataset:

- **Valid formats**: `.csv`, `.json`, `.jsonl`, `.xlsx`, `.parquet`
- **Default behavior**: If `output_format` is `None` or an empty string, the cleaned dataset is saved in the same format as the input file
- The format string can be specified with or without the leading dot (e.g., both `"csv"` and `".csv"` are valid)

**Example:**

```python
# Save cleaned dataset as Parquet regardless of input format
sliq.clean_from_file(
    api_key="your-api-key",
    dataset_path="data/raw.csv",
    dataset_name="My Dataset",
    output_format=".parquet",
    save_clean_file_path="data/cleaned/",
)
```

### Column Guide Validation

When providing a `column_guide`, the following rules apply:

1. **All columns required**: You must provide descriptions for **all** columns in your dataset
2. **Column count must match**: The number of keys in `column_guide` must equal the number of columns in your dataset
3. **Names must match**: Column names are validated against the dataset (case-insensitive, underscore-insensitive)

**Example:**

```python
# For a dataset with columns: "first_name", "last_name", "Age"
column_guide = {
    "first_name": "Customer's first name",
    "last_name": "Customer's last name", 
    "age": "Customer's age in years",  # Case-insensitive: "age" matches "Age"
}
```

If column names don't match, you'll get a helpful error message listing the mismatched columns and the actual dataset columns.

## Getting an API Key

To use Sliq, you need an API key. Visit [sliqdata.com](https://sliqdata.com/dashboard/account) to get your API key.

## Documentation

For full documentation, visit [sliqdata.com/docs](https://sliqdata.com/docs).

## License

MIT License - see [LICENSE](LICENSE) for details.


# For developers of the library
---

## To install Sliq locally for development
```bash
pip install -e "Sliq-python-lib"
```

## Publishing to PyPI

To upload a new version of Sliq-python-lib to PyPI:

1. **Check your files:**
    - Ensure `pyproject.toml` and `README.md` are present and correct.
    - Source code should be in `src/sliq/`.
    - License and metadata should be set.

2. **Build the distribution:**
    In your project root (`Sliq-python-lib`), run:
    ```powershell
    python -m build
    ```
    (If you don’t have `build`, install it: `pip install build`)

3. **Check the distribution:**
    Optionally, check for errors:
    ```powershell
    twine check dist/*
    ```

4. **Upload to PyPI:**
    Make sure you have a PyPI account and `twine` installed (`pip install twine`).
    Then run:
    ```powershell
    twine upload dist/*
    ```

If you get an error, check the message and resolve it, or ask for help.