"""Tests for column validation utilities."""

import pytest
import tempfile
import os
from pathlib import Path

from sliq.column_validation import (
    _normalize_column_name,
    validate_column_guide,
    validate_column_guide_for_file,
    validate_column_guide_for_dataframe,
)
from sliq.exceptions import SliqValidationError


class TestNormalizeColumnName:
    """Tests for the _normalize_column_name function."""
    
    def test_lowercase_conversion(self) -> None:
        """Normalizes to lowercase."""
        assert _normalize_column_name("COLUMN") == "column"
        assert _normalize_column_name("Column") == "column"
    
    def test_underscore_removal(self) -> None:
        """Removes underscores."""
        assert _normalize_column_name("column_name") == "columnname"
        assert _normalize_column_name("my_column_name") == "mycolumnname"
    
    def test_combined_normalization(self) -> None:
        """Handles both case and underscores."""
        assert _normalize_column_name("My_Column_Name") == "mycolumnname"
        assert _normalize_column_name("FIRST_NAME") == "firstname"


class TestValidateColumnGuide:
    """Tests for the validate_column_guide function."""
    
    def test_matching_columns(self) -> None:
        """Passes when columns match exactly."""
        column_guide = {"name": "desc1", "age": "desc2"}
        dataset_columns = ["name", "age"]
        # Should not raise
        validate_column_guide(column_guide, dataset_columns)
    
    def test_case_insensitive_match(self) -> None:
        """Passes when columns match case-insensitively."""
        column_guide = {"NAME": "desc1", "AGE": "desc2"}
        dataset_columns = ["name", "age"]
        # Should not raise
        validate_column_guide(column_guide, dataset_columns)
    
    def test_underscore_insensitive_match(self) -> None:
        """Passes when columns differ only by underscores."""
        column_guide = {"first_name": "desc1", "last_name": "desc2"}
        dataset_columns = ["firstname", "lastname"]
        # Should not raise
        validate_column_guide(column_guide, dataset_columns)
    
    def test_combined_case_underscore_match(self) -> None:
        """Passes when columns differ by both case and underscores."""
        column_guide = {"First_Name": "desc1", "LAST_NAME": "desc2"}
        dataset_columns = ["firstname", "LastName"]
        # Should not raise
        validate_column_guide(column_guide, dataset_columns)
    
    def test_column_count_mismatch_too_few(self) -> None:
        """Fails when column_guide has fewer columns than dataset."""
        column_guide = {"name": "desc1"}
        dataset_columns = ["name", "age", "city"]
        
        with pytest.raises(SliqValidationError) as exc_info:
            validate_column_guide(column_guide, dataset_columns)
        
        assert "Column count mismatch" in str(exc_info.value)
        assert "1 columns" in str(exc_info.value)
        assert "3 columns" in str(exc_info.value)
    
    def test_column_count_mismatch_too_many(self) -> None:
        """Fails when column_guide has more columns than dataset."""
        column_guide = {"name": "desc1", "age": "desc2", "city": "desc3"}
        dataset_columns = ["name", "age"]
        
        with pytest.raises(SliqValidationError) as exc_info:
            validate_column_guide(column_guide, dataset_columns)
        
        assert "Column count mismatch" in str(exc_info.value)
    
    def test_column_name_mismatch(self) -> None:
        """Fails when column names don't match."""
        column_guide = {"name": "desc1", "wrong_column": "desc2"}
        dataset_columns = ["name", "age"]
        
        with pytest.raises(SliqValidationError) as exc_info:
            validate_column_guide(column_guide, dataset_columns)
        
        assert "Column name mismatch" in str(exc_info.value)
        assert "'wrong_column'" in str(exc_info.value)
    
    def test_multiple_mismatched_columns(self) -> None:
        """Lists all mismatched columns in error message."""
        column_guide = {"wrong1": "desc1", "wrong2": "desc2"}
        dataset_columns = ["name", "age"]
        
        with pytest.raises(SliqValidationError) as exc_info:
            validate_column_guide(column_guide, dataset_columns)
        
        assert "'wrong1'" in str(exc_info.value)
        assert "'wrong2'" in str(exc_info.value)


class TestValidateColumnGuideForFile:
    """Tests for validate_column_guide_for_file function."""
    
    def test_none_column_guide_skips_validation(self) -> None:
        """Skips validation when column_guide is None."""
        # Should not raise or try to read file
        validate_column_guide_for_file(None, Path("nonexistent.csv"))
    
    def test_empty_column_guide_skips_validation(self) -> None:
        """Skips validation when column_guide is empty dict."""
        validate_column_guide_for_file({}, Path("nonexistent.csv"))
    
    def test_csv_file_validation(self) -> None:
        """Validates column_guide against CSV file columns."""
        # Create a temp CSV file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("name,age,city\n")
            f.write("John,30,NYC\n")
            temp_path = f.name
        
        try:
            # Valid column_guide
            column_guide = {"name": "desc1", "age": "desc2", "city": "desc3"}
            validate_column_guide_for_file(column_guide, Path(temp_path))
            
            # Invalid column_guide - wrong column name
            bad_guide = {"name": "desc1", "age": "desc2", "wrong": "desc3"}
            with pytest.raises(SliqValidationError) as exc_info:
                validate_column_guide_for_file(bad_guide, Path(temp_path))
            assert "'wrong'" in str(exc_info.value)
        finally:
            os.unlink(temp_path)


class TestValidateColumnGuideForDataFrame:
    """Tests for validate_column_guide_for_dataframe function."""
    
    def test_none_column_guide_skips_validation(self) -> None:
        """Skips validation when column_guide is None."""
        import pandas as pd
        df = pd.DataFrame({"a": [1], "b": [2]})
        # Should not raise
        validate_column_guide_for_dataframe(None, df)
    
    def test_pandas_dataframe_validation(self) -> None:
        """Validates column_guide against Pandas DataFrame columns."""
        import pandas as pd
        df = pd.DataFrame({"name": ["John"], "age": [30]})
        
        # Valid column_guide
        column_guide = {"name": "Person name", "age": "Person age"}
        validate_column_guide_for_dataframe(column_guide, df)
        
        # Invalid column_guide
        bad_guide = {"name": "Person name", "wrong": "Bad column"}
        with pytest.raises(SliqValidationError) as exc_info:
            validate_column_guide_for_dataframe(bad_guide, df)
        assert "'wrong'" in str(exc_info.value)
    
    def test_polars_dataframe_validation(self) -> None:
        """Validates column_guide against Polars DataFrame columns."""
        import polars as pl
        df = pl.DataFrame({"name": ["John"], "age": [30]})
        
        # Valid column_guide
        column_guide = {"name": "Person name", "age": "Person age"}
        validate_column_guide_for_dataframe(column_guide, df)
        
        # Invalid column_guide
        bad_guide = {"name": "Person name", "wrong": "Bad column"}
        with pytest.raises(SliqValidationError) as exc_info:
            validate_column_guide_for_dataframe(bad_guide, df)
        assert "'wrong'" in str(exc_info.value)
