"""Utility functions for the Scout CLI."""

import base64
import json
import re
from pathlib import Path


def normalize_snake_case_name(name: str, default: str = "custom_name") -> str:
    """
    Normalize a name to lowercase snake_case format.

    Converts spaces and special characters to underscores, removes consecutive
    underscores, and strips leading/trailing underscores.

    Args:
        name (str): The name to normalize
        default (str): Default value if normalization results in empty string
    """
    # Convert to lowercase and replace spaces and special characters with underscores
    normalized = re.sub(r"[^\w\s]", "_", name.lower())
    normalized = re.sub(r"\s+", "_", normalized)
    # Remove multiple consecutive underscores
    normalized = re.sub(r"_+", "_", normalized)
    # Remove leading/trailing underscores
    normalized = normalized.strip("_")
    return normalized or default


def get_data_path(*parts: str) -> Path:
    """
    Get a path to a file or directory in the data directory.

    Args:
        *parts: Path components relative to the data directory

    Returns:
        Path: Absolute path to the requested file/directory
    """
    from importlib.resources import files
    import scoutsdk.data

    data_files = files(scoutsdk.data)
    result = data_files
    for part in parts:
        result = result / part
    # Convert to Path for consistency with existing code
    return Path(str(result))


def extract_tenant_id_from_token(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        payload_b64 = parts[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)

        return payload.get("tenant_id")
    except Exception:
        return None
