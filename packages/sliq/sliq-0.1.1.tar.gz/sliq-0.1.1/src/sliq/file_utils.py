"""File handling utilities for the Sliq library.

This module provides utilities for:
- Validating file formats
- Creating zip archives for upload
- Extracting files from downloaded zips
- Saving cleaned datasets to disk
"""

from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path
from typing import Tuple

from sliq.config import SUPPORTED_EXTENSIONS
from sliq.exceptions import SliqFileError, SliqValidationError


def validate_file_path(file_path: str) -> Path:
    """Validate that a file path exists and has a supported format.
    
    Args:
        file_path: Path to the file to validate.
        
    Returns:
        Resolved Path object for the file.
        
    Raises:
        SliqFileError: If the file does not exist.
        SliqValidationError: If the file format is not supported.
    """
    path = Path(file_path).resolve()
    
    if not path.exists():
        raise SliqFileError(f"File not found: {file_path}", file_path=str(path))
    
    if not path.is_file():
        raise SliqFileError(f"Path is not a file: {file_path}", file_path=str(path))
    
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise SliqValidationError(
            f"Unsupported file format: '{ext}'. Supported formats: {supported_list}. If you believe this is an error, or want to request support for a new format, contact support@sliqdata.com",
        )
    
    return path


def validate_output_directory(output_path: str) -> Path:
    """Validate and create output directory if needed.
    
    Args:
        output_path: Path to the output directory.
        
    Returns:
        Resolved Path object for the directory.
        
    Raises:
        SliqFileError: If the directory cannot be created or accessed.
    """
    path = Path(output_path).resolve()
    
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise SliqFileError(
            f"Permission denied: Cannot create directory at {output_path}",
            file_path=str(path),
        )
    except OSError as e:
        raise SliqFileError(
            f"Cannot create directory: {e}",
            file_path=str(path),
        )
    
    if not os.access(path, os.W_OK):
        raise SliqFileError(
            f"Permission denied: Cannot write to directory {output_path}",
            file_path=str(path),
        )
    
    return path


def create_zip_from_file(file_path: Path) -> Tuple[bytes, str]:
    """Create a zip archive containing a single file.
    
    Args:
        file_path: Path to the file to zip.
        
    Returns:
        Tuple of (zip_bytes, original_filename).
        
    Raises:
        SliqFileError: If the file cannot be read.
    """
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
    except PermissionError:
        raise SliqFileError(
            f"Permission denied: Cannot read file",
            file_path=str(file_path),
        )
    except OSError as e:
        raise SliqFileError(
            f"Cannot read file: {e}",
            file_path=str(file_path),
        )
    
    # Create zip in memory
    zip_buffer = io.BytesIO()
    filename = file_path.name
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, file_content)
    
    return zip_buffer.getvalue(), filename


def create_zip_from_bytes(data: bytes, filename: str) -> bytes:
    """Create a zip archive from raw bytes.
    
    Args:
        data: The file content as bytes.
        filename: Name to give the file inside the zip.
        
    Returns:
        The zip archive as bytes.
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, data)
    
    return zip_buffer.getvalue()


def extract_file_from_zip(zip_bytes: bytes) -> Tuple[bytes, str]:
    """Extract the first supported file from a zip archive.
    
    Args:
        zip_bytes: The zip archive as bytes.
        
    Returns:
        Tuple of (file_bytes, filename).
        
    Raises:
        SliqFileError: If the zip is invalid or contains no supported files.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            # Find the first file with a supported extension
            for filename in zf.namelist():
                ext = os.path.splitext(filename.lower())[1]
                if ext in SUPPORTED_EXTENSIONS:
                    return zf.read(filename), filename
            
            # No supported file found
            supported_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise SliqFileError(
                f"No supported dataset file found in zip. Supported: {supported_list}"
            )
    except zipfile.BadZipFile:
        raise SliqFileError("Invalid or corrupted zip file received")


def save_file_to_disk(
    file_bytes: bytes,
    output_dir: Path,
    filename: str,
    custom_name: str = "",
) -> Path:
    """Save file bytes to disk.
    
    Args:
        file_bytes: The file content as bytes.
        output_dir: Directory to save the file in.
        filename: Original filename (used for extension if custom_name provided).
        custom_name: Optional custom filename (without extension).
        
    Returns:
        Path to the saved file.
        
    Raises:
        SliqFileError: If the file cannot be written.
    """
    # Determine the output filename
    if custom_name:
        # Use custom name with original extension
        ext = os.path.splitext(filename)[1]
        output_filename = f"{custom_name}{ext}"
    else:
        output_filename = filename
    
    output_path = output_dir / output_filename
    
    try:
        with open(output_path, "wb") as f:
            f.write(file_bytes)
    except PermissionError:
        raise SliqFileError(
            f"Permission denied: Cannot write to {output_path}",
            file_path=str(output_path),
        )
    except OSError as e:
        raise SliqFileError(
            f"Cannot write file: {e}",
            file_path=str(output_path),
        )
    
    return output_path
