"""
Utility functions for datetime handling in the Overwatch system.
"""

from datetime import datetime
from typing import Any


def parse_datetime_string(value: Any) -> datetime | None:
    """
    Parse a datetime string into a datetime object.

    Args:
        value: The value to parse (string, datetime, or None)

    Returns:
        datetime object if parsing succeeds, None otherwise
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        # Handle ISO 8601 format with 'Z' timezone (convert to +00:00 for fromisoformat)
        if value.endswith("Z"):
            try:
                # Replace 'Z' with '+00:00' for Python's fromisoformat
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Try standard ISO 8601 format
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass

        # Try common formats as fallback
        common_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]

        for fmt in common_formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

    return None


def convert_datetimes_in_data(
    data: dict[str, Any], datetime_fields: list[str]
) -> dict[str, Any]:
    """
    Convert datetime strings to datetime objects in the provided data.

    Args:
        data: Dictionary containing field values
        datetime_fields: List of field names that should be treated as datetime fields

    Returns:
        Modified dictionary with datetime strings converted to datetime objects
    """
    if not data or not datetime_fields:
        return data

    converted_data = {}
    for field_name, value in data.items():
        if field_name in datetime_fields:
            converted_data[field_name] = parse_datetime_string(value)
        else:
            converted_data[field_name] = value

    return converted_data
