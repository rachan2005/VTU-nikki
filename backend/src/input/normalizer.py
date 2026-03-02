"""Normalizes input data from various sources into unified format"""
from typing import Union, List, Dict, Any


def normalize_input_data(
    input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Normalize input data into consistent format.

    Ensures all data is a list of entries with standard fields:
    - raw_text: str
    - metadata: dict

    Args:
        input_data: Single dict or list of dicts from processors

    Returns:
        List of normalized entry dicts
    """
    # Convert single entry to list
    if isinstance(input_data, dict):
        input_data = [input_data]

    normalized = []

    for entry in input_data:
        if not entry:  # Skip None/empty entries
            continue

        # Ensure required fields
        if "raw_text" not in entry:
            continue

        if "metadata" not in entry:
            entry["metadata"] = {}

        # Ensure metadata has source
        if "source" not in entry["metadata"]:
            entry["metadata"]["source"] = "unknown"

        normalized.append(entry)

    return normalized
