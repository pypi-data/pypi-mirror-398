"""
File and path validation utilities for PyHelios.

Provides secure file path validation with consistent error handling,
extending the patterns from Context._validate_file_path.
"""

import os
from pathlib import Path
from typing import List, Optional

from .exceptions import ValidationError, create_validation_error


def validate_file_path(filename: str, expected_extensions: List[str] = None, 
                      must_exist: bool = True, param_name: str = "filename", 
                      function_name: str = None) -> str:
    """
    Validate and normalize file path with security checks.
    
    Based on Context._validate_file_path but enhanced with ValidationError
    and standardized error messaging.
    
    Args:
        filename: File path to validate
        expected_extensions: List of allowed file extensions (e.g., ['.ply', '.obj'])
        must_exist: Whether file must already exist
        param_name: Parameter name for error messages
        function_name: Function name for error messages
        
    Returns:
        Normalized absolute path
        
    Raises:
        ValidationError: If path is invalid, doesn't exist, or has wrong extension
    """
    if not isinstance(filename, (str, Path)):
        raise create_validation_error(
            f"Parameter must be a string or Path",
            param_name=param_name,
            function_name=function_name,
            expected_type="string or Path",
            actual_value=filename,
            suggestion="Provide file path as a string or pathlib.Path object."
        )
    
    if not filename:
        raise create_validation_error(
            f"Parameter cannot be empty",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-empty string",
            actual_value=filename,
            suggestion="Provide a valid file path."
        )
    
    # Convert to Path for consistent handling
    try:
        path = Path(filename)
        normalized = path.resolve()
    except (OSError, ValueError) as e:
        raise create_validation_error(
            f"Parameter contains invalid characters or path: {filename} ({e})",
            param_name=param_name,
            function_name=function_name,
            expected_type="valid file path",
            actual_value=filename,
            suggestion="Ensure the path contains valid characters and no illegal sequences."
        )
    
    # Security check - prevent path traversal (following Context pattern)
    abs_path = os.path.abspath(str(path))
    normalized_path = os.path.normpath(abs_path)
    if abs_path != normalized_path:
        raise create_validation_error(
            f"Invalid file path (potential path traversal): {filename}",
            param_name=param_name,
            function_name=function_name,
            expected_type="safe file path",
            actual_value=filename,
            suggestion="Avoid path traversal sequences like '../' in file paths."
        )
    
    # Extension validation
    if expected_extensions:
        if path.suffix.lower() not in [ext.lower() for ext in expected_extensions]:
            extensions_str = ", ".join(expected_extensions)
            raise create_validation_error(
                f"Parameter must have one of these extensions: {extensions_str}, got '{path.suffix}'",
                param_name=param_name,
                function_name=function_name,
                expected_type=f"file with extension {extensions_str}",
                actual_value=filename,
                suggestion=f"Use a file with one of these extensions: {extensions_str}"
            )
    
    # Existence check
    if must_exist and not normalized.exists():
        raise create_validation_error(
            f"File does not exist: {normalized}",
            param_name=param_name,
            function_name=function_name,
            expected_type="existing file",
            actual_value=filename,
            suggestion=f"Ensure the file exists at: {normalized}"
        )
    
    return str(normalized)


def validate_directory_path(directory: str, must_exist: bool = True, 
                          create_if_missing: bool = False, 
                          param_name: str = "directory",
                          function_name: str = None) -> str:
    """
    Validate and normalize directory path.
    
    Args:
        directory: Directory path to validate
        must_exist: Whether directory must already exist
        create_if_missing: Create directory if it doesn't exist
        param_name: Parameter name for error messages
        function_name: Function name for error messages
        
    Returns:
        Normalized absolute path
        
    Raises:
        ValidationError: If path is invalid or doesn't exist
    """
    if not isinstance(directory, (str, Path)):
        raise create_validation_error(
            f"Parameter must be a string or Path",
            param_name=param_name,
            function_name=function_name,
            expected_type="string or Path",
            actual_value=directory,
            suggestion="Provide directory path as a string or pathlib.Path object."
        )
    
    if not directory:
        raise create_validation_error(
            f"Parameter cannot be empty",
            param_name=param_name,
            function_name=function_name,
            expected_type="non-empty string",
            actual_value=directory,
            suggestion="Provide a valid directory path."
        )
    
    try:
        path = Path(directory)
        normalized = path.resolve()
    except (OSError, ValueError) as e:
        raise create_validation_error(
            f"Parameter contains invalid characters or path: {directory} ({e})",
            param_name=param_name,
            function_name=function_name,
            expected_type="valid directory path",
            actual_value=directory,
            suggestion="Ensure the path contains valid characters and no illegal sequences."
        )
    
    if must_exist and not normalized.exists():
        if create_if_missing:
            try:
                normalized.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise create_validation_error(
                    f"Cannot create directory: {normalized} ({e})",
                    param_name=param_name,
                    function_name=function_name,
                    expected_type="creatable directory path",
                    actual_value=directory,
                    suggestion=f"Ensure you have write permissions to create: {normalized}"
                )
        else:
            raise create_validation_error(
                f"Directory does not exist: {normalized}",
                param_name=param_name,
                function_name=function_name,
                expected_type="existing directory",
                actual_value=directory,
                suggestion=f"Ensure the directory exists at: {normalized}"
            )
    
    if normalized.exists() and not normalized.is_dir():
        raise create_validation_error(
            f"Path exists but is not a directory: {normalized}",
            param_name=param_name,
            function_name=function_name,
            expected_type="directory path",
            actual_value=directory,
            suggestion=f"The path {normalized} exists but is a file, not a directory."
        )
    
    return str(normalized)