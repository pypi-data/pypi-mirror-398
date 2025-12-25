"""
Test for tiktoken cache directory configuration
"""

import os
from pathlib import Path

import pytest

from langchain_llm_config import TIKTOKEN_CACHE_DIR


def test_tiktoken_cache_dir_export() -> None:
    """Test that TIKTOKEN_CACHE_DIR is properly exported"""
    assert TIKTOKEN_CACHE_DIR is not None
    assert isinstance(TIKTOKEN_CACHE_DIR, str)
    assert len(TIKTOKEN_CACHE_DIR) > 0


def test_tiktoken_cache_dir_path() -> None:
    """Test that TIKTOKEN_CACHE_DIR points to the correct location"""
    # Get the package directory from the installed package
    from langchain_llm_config import __file__ as package_file

    package_dir = Path(package_file).parent
    expected_cache_dir = package_dir / ".tiktoken_cache"

    # Convert to string for comparison
    expected_cache_dir_str = str(expected_cache_dir)

    assert TIKTOKEN_CACHE_DIR == expected_cache_dir_str


def test_tiktoken_cache_dir_exists() -> None:
    """Test that the tiktoken cache directory exists"""
    cache_dir_path = Path(TIKTOKEN_CACHE_DIR)
    assert (
        cache_dir_path.exists()
    ), f"Tiktoken cache directory does not exist: {cache_dir_path}"
    assert (
        cache_dir_path.is_dir()
    ), f"Tiktoken cache path is not a directory: {cache_dir_path}"


def test_tiktoken_cache_dir_contents() -> None:
    """Test that the tiktoken cache directory contains expected files"""
    cache_dir_path = Path(TIKTOKEN_CACHE_DIR)

    # Check if there are any files in the cache directory
    cache_files = list(cache_dir_path.iterdir())
    assert (
        len(cache_files) > 0
    ), f"No files found in tiktoken cache directory: {cache_dir_path}"

    # Check that at least one file is a regular file (not a directory)
    has_files = any(f.is_file() for f in cache_files)
    assert (
        has_files
    ), f"No regular files found in tiktoken cache directory: {cache_dir_path}"
