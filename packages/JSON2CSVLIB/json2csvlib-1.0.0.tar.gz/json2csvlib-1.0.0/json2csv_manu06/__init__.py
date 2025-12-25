"""
json2csv-pro: A professional JSON to CSV conversion library.

This library provides comprehensive tools for converting JSON data to CSV format
with advanced features like nested JSON handling, data validation, and customizable output.
"""

from .converter import JSONConverter
from .validator import DataValidator
from .utils import flatten_json, detect_delimiter
from .exceptions import (
    JSON2CSVError,
    ValidationError,
    ConversionError,
    FileNotFoundError as CustomFileNotFoundError
)

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__all__ = [
    "JSONConverter",
    "DataValidator",
    "flatten_json",
    "detect_delimiter",
    "JSON2CSVError",
    "ValidationError",
    "ConversionError",
    "CustomFileNotFoundError"
]
