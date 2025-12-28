"""
move-data: A Python package for moving data between various sources and destinations.

This package provides utilities for:
- Google Sheets data extraction
- SharePoint file operations
- Google Cloud Storage file operations
- Snowflake data loading and extraction
"""

from .move_data import (
    get_googlesheets_data,
    sharepoint,
    snowflake,
    googlestorage
)

__version__ = "0.1.5"
__all__ = [
    "get_googlesheets_data",
    "sharepoint",
    "snowflake",
    "googlestorage"
]

