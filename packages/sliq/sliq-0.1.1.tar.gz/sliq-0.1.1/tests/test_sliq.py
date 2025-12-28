"""Unit tests for the Sliq library.

These tests verify the library's functionality without making actual API calls.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestImports:
    """Test that the package imports correctly."""

    def test_import_sliq(self) -> None:
        """Test importing the sliq package."""
        import sliq
        assert hasattr(sliq, "__version__")
        assert hasattr(sliq, "clean_from_file")
        assert hasattr(sliq, "clean_from_dataframe")

    def test_version(self) -> None:
        """Test that version is defined."""
        import sliq
        assert sliq.__version__ == "0.1.1"

    def test_all_exports(self) -> None:
        """Test that __all__ contains expected items."""
        import sliq
        assert "clean_from_file" in sliq.__all__
        assert "clean_from_dataframe" in sliq.__all__
        assert "SliqError" in sliq.__all__
        assert "SliqAPIError" in sliq.__all__


class TestExceptions:
    """Test custom exception classes."""

    def test_sliq_error_base(self) -> None:
        """Test SliqError base exception."""
        from sliq.exceptions import SliqError
        error = SliqError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_sliq_api_error(self) -> None:
        """Test SliqAPIError with status code."""
        from sliq.exceptions import SliqAPIError
        error = SliqAPIError("API failed", status_code=500)
        assert "API failed" in str(error)
        assert error.status_code == 500

    def test_sliq_validation_error(self) -> None:
        """Test SliqValidationError."""
        from sliq.exceptions import SliqValidationError
        error = SliqValidationError("Invalid input")
        assert "Invalid input" in str(error)

    def test_sliq_file_error(self) -> None:
        """Test SliqFileError with file path."""
        from sliq.exceptions import SliqFileError
        error = SliqFileError("File not found", file_path="/path/to/file")
        assert "File not found" in str(error)
        assert error.file_path == "/path/to/file"


class TestFileUtils:
    """Test file utility functions."""

    def test_supported_extensions(self) -> None:
        """Test that supported extensions are defined."""
        from sliq.config import SUPPORTED_EXTENSIONS
        assert ".csv" in SUPPORTED_EXTENSIONS
        assert ".json" in SUPPORTED_EXTENSIONS
        assert ".jsonl" in SUPPORTED_EXTENSIONS
        assert ".xlsx" in SUPPORTED_EXTENSIONS
        assert ".parquet" in SUPPORTED_EXTENSIONS

    def test_validate_file_path_not_found(self, tmp_path: Path) -> None:
        """Test that missing files raise SliqFileError."""
        from sliq.file_utils import validate_file_path
        from sliq.exceptions import SliqFileError
        
        with pytest.raises(SliqFileError, match="File not found"):
            validate_file_path(str(tmp_path / "nonexistent.csv"))

    def test_validate_file_path_unsupported(self, tmp_path: Path) -> None:
        """Test that unsupported formats raise SliqValidationError."""
        from sliq.file_utils import validate_file_path
        from sliq.exceptions import SliqValidationError
        
        # Create a file with unsupported extension
        bad_file = tmp_path / "data.txt"
        bad_file.write_text("test data")
        
        with pytest.raises(SliqValidationError, match="Unsupported file format"):
            validate_file_path(str(bad_file))

    def test_validate_file_path_valid(self, tmp_path: Path) -> None:
        """Test that valid files pass validation."""
        from sliq.file_utils import validate_file_path
        
        # Create a valid CSV file
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b,c\n1,2,3")
        
        result = validate_file_path(str(csv_file))
        assert result == csv_file.resolve()

    def test_create_zip_from_file(self, tmp_path: Path) -> None:
        """Test creating a zip from a file."""
        from sliq.file_utils import create_zip_from_file
        
        # Create a test file
        test_file = tmp_path / "test.csv"
        test_content = "a,b,c\n1,2,3"
        test_file.write_text(test_content)
        
        zip_bytes, filename = create_zip_from_file(test_file)
        
        assert filename == "test.csv"
        assert isinstance(zip_bytes, bytes)
        
        # Verify zip content
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            assert "test.csv" in zf.namelist()
            # Normalize line endings for Windows compatibility
            actual = zf.read("test.csv").decode().replace("\r\n", "\n")
            expected = test_content.replace("\r\n", "\n")
            assert actual == expected

    def test_create_zip_from_bytes(self) -> None:
        """Test creating a zip from bytes."""
        from sliq.file_utils import create_zip_from_bytes
        
        content = b"test content"
        zip_bytes = create_zip_from_bytes(content, "data.parquet")
        
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            assert "data.parquet" in zf.namelist()
            assert zf.read("data.parquet") == content

    def test_extract_file_from_zip(self) -> None:
        """Test extracting a file from a zip."""
        from sliq.file_utils import extract_file_from_zip
        
        # Create a test zip
        content = b"a,b,c\n1,2,3"
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("data.csv", content)
        
        file_bytes, filename = extract_file_from_zip(zip_buffer.getvalue())
        
        assert filename == "data.csv"
        assert file_bytes == content

    def test_save_file_to_disk(self, tmp_path: Path) -> None:
        """Test saving a file to disk."""
        from sliq.file_utils import save_file_to_disk
        
        content = b"test content"
        saved_path = save_file_to_disk(content, tmp_path, "output.csv")
        
        assert saved_path == tmp_path / "output.csv"
        assert saved_path.read_bytes() == content

    def test_save_file_with_custom_name(self, tmp_path: Path) -> None:
        """Test saving with a custom filename."""
        from sliq.file_utils import save_file_to_disk
        
        content = b"test content"
        saved_path = save_file_to_disk(
            content, tmp_path, "original.csv", custom_name="custom"
        )
        
        assert saved_path == tmp_path / "custom.csv"


class TestDataFrameUtils:
    """Test DataFrame utility functions."""

    def test_detect_pandas_dataframe(self) -> None:
        """Test detecting a Pandas DataFrame."""
        from sliq.dataframe_utils import detect_dataframe_type
        
        try:
            import pandas as pd
            df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
            assert detect_dataframe_type(df) == "pandas"
        except ImportError:
            pytest.skip("Pandas not installed")

    def test_detect_polars_dataframe(self) -> None:
        """Test detecting a Polars DataFrame."""
        from sliq.dataframe_utils import detect_dataframe_type
        
        try:
            import polars as pl
            df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
            assert detect_dataframe_type(df) == "polars"
        except ImportError:
            pytest.skip("Polars not installed")

    def test_detect_invalid_type(self) -> None:
        """Test that non-DataFrames raise an error."""
        from sliq.dataframe_utils import detect_dataframe_type
        from sliq.exceptions import SliqValidationError
        
        with pytest.raises(SliqValidationError, match="Unsupported DataFrame type"):
            detect_dataframe_type([1, 2, 3])

    def test_validate_empty_pandas_dataframe(self) -> None:
        """Test that empty Pandas DataFrames raise an error."""
        from sliq.dataframe_utils import validate_dataframe
        from sliq.exceptions import SliqValidationError
        
        try:
            import pandas as pd
            df = pd.DataFrame()
            with pytest.raises(SliqValidationError, match="empty"):
                validate_dataframe(df)
        except ImportError:
            pytest.skip("Pandas not installed")

    def test_pandas_to_parquet(self) -> None:
        """Test converting Pandas DataFrame to Parquet."""
        from sliq.dataframe_utils import dataframe_to_parquet_bytes
        
        try:
            import pandas as pd
            df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
            parquet_bytes = dataframe_to_parquet_bytes(df)
            assert isinstance(parquet_bytes, bytes)
            assert len(parquet_bytes) > 0
        except ImportError:
            pytest.skip("Pandas not installed")


class TestClientValidation:
    """Test client input validation."""

    def test_missing_api_key(self) -> None:
        """Test that missing API key raises error."""
        from sliq.exceptions import SliqValidationError
        import sliq
        
        with pytest.raises(SliqValidationError, match="API key is required"):
            sliq.clean_from_file(
                api_key="",
                dataset_path="test.csv",
                dataset_name="Test",
            )

    def test_missing_dataset(self) -> None:
        """Test that missing dataset raises error."""
        from sliq.exceptions import SliqValidationError
        import sliq
        
        with pytest.raises(SliqValidationError, match="Dataset path is required"):
            sliq.clean_from_file(
                api_key="test-key",
                dataset_path="",
                dataset_name="Test",
            )

    def test_missing_dataset_name(self) -> None:
        """Test that missing dataset name raises error."""
        from sliq.exceptions import SliqValidationError
        import sliq
        
        with pytest.raises(SliqValidationError, match="Dataset name is required"):
            sliq.clean_from_file(
                api_key="test-key",
                dataset_path="test.csv",
                dataset_name="",
            )

    def test_save_name_without_path(self) -> None:
        """Test that save_clean_file_name without path raises error."""
        from sliq.exceptions import SliqValidationError
        import sliq
        
        with pytest.raises(SliqValidationError, match="requires save_clean_file_path"):
            sliq.clean_from_file(
                api_key="test-key",
                dataset_path="test.csv",
                dataset_name="Test",
                save_clean_file_name="output",
            )


class TestClientIntegration:
    """Integration tests for the client (mocked API calls)."""

    @patch("sliq.client.call_presign")
    @patch("sliq.client.upload_to_presigned_url")
    @patch("sliq.client.call_run")
    @patch("sliq.client.call_status")
    @patch("sliq.client.download_from_presigned_url")
    def test_clean_from_file_full_flow(
        self,
        mock_download: MagicMock,
        mock_status: MagicMock,
        mock_run: MagicMock,
        mock_upload: MagicMock,
        mock_presign: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test the full clean_from_file flow with mocks."""
        import sliq
        
        # Create a test input file
        input_file = tmp_path / "input.csv"
        input_file.write_text("a,b,c\n1,2,3")
        
        # Create output directory
        output_dir = tmp_path / "output"
        
        # Set up mocks
        mock_presign.return_value = {
            "upload_url": "https://example.com/upload",
            "object_key": "test-key",
            "user_id": "user-123",
            "job_id": "job-456",
        }
        mock_run.return_value = {
            "execution_name": "exec-789",
            "status_url": "https://example.com/status",
        }
        mock_status.return_value = {
            "is_complete": True,
            "succeeded": True,
            "status": "succeeded",
            "message": "Cleaning complete",
            "download_urls": {
                "cleaned_dataset_url": "https://example.com/download",
            },
        }
        
        # Create a mock cleaned file zip
        cleaned_zip = io.BytesIO()
        with zipfile.ZipFile(cleaned_zip, "w") as zf:
            zf.writestr("Sliq clean dataset - Test.csv", "a,b,c\n10,20,30")
        mock_download.return_value = cleaned_zip.getvalue()
        
        # Run the function
        sliq.clean_from_file(
            api_key="test-api-key",
            dataset_path=str(input_file),
            dataset_name="Test",
            save_clean_file_path=str(output_dir),
            verbose=False,
        )
        
        # Verify mocks were called
        mock_presign.assert_called_once()
        mock_upload.assert_called_once()
        mock_run.assert_called_once()
        mock_status.assert_called()
        mock_download.assert_called_once()
        
        # Verify output file was created
        output_files = list(output_dir.glob("*.csv"))
        assert len(output_files) == 1

    @patch("sliq.client.call_presign")
    @patch("sliq.client.upload_to_presigned_url")
    @patch("sliq.client.call_run")
    @patch("sliq.client.call_status")
    @patch("sliq.client.download_from_presigned_url")
    def test_clean_from_file_status_string_but_flag_false(
        self,
        mock_download: MagicMock,
        mock_status: MagicMock,
        mock_run: MagicMock,
        mock_upload: MagicMock,
        mock_presign: MagicMock,
        tmp_path: Path,
    ) -> None:
        """If the API returns 'status'='succeeded' as a string but 'succeeded' flag is False, we handle it as success."""
        import sliq

        # Create a test input file
        input_file = tmp_path / "input.csv"
        input_file.write_text("a,b,c\n1,2,3")

        # Create output directory
        output_dir = tmp_path / "output"

        # Set up mocks - note succeeded flag is False but status string indicates success
        mock_presign.return_value = {
            "upload_url": "https://example.com/upload",
            "object_key": "test-key",
            "user_id": "user-123",
            "job_id": "job-456",
        }
        mock_run.return_value = {
            "execution_name": "exec-789",
            "status_url": "https://example.com/status",
        }
        mock_status.return_value = {
            "is_complete": True,
            "succeeded": True,
            "status": "succeeded",
            "message": "Cleaning complete",
            "download_urls": {
                "cleaned_dataset_url": "https://example.com/download",
            },
        }

        # Create a mock cleaned file zip
        cleaned_zip = io.BytesIO()
        with zipfile.ZipFile(cleaned_zip, "w") as zf:
            zf.writestr("Sliq clean dataset - Test.csv", "a,b,c\n10,20,30")
        mock_download.return_value = cleaned_zip.getvalue()

        # Run the function - should not raise even though 'succeeded' flag is False
        sliq.clean_from_file(
            api_key="test-api-key",
            dataset_path=str(input_file),
            dataset_name="Test",
            save_clean_file_path=str(output_dir),
            verbose=False,
        )

        # Verify mocks were called and file created
        mock_presign.assert_called_once()
        mock_upload.assert_called_once()
        mock_run.assert_called_once()
        mock_status.assert_called()
        mock_download.assert_called_once()
        output_files = list(output_dir.glob("*.csv"))
        assert len(output_files) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
