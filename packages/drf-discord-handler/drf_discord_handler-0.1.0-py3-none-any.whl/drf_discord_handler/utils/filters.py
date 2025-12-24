"""Utility functions for filtering sensitive data."""

import re
from typing import Any, List

from drf_discord_handler.settings.config import DiscordHandlerConfig


def filter_sensitive_data(data: Any, sensitive_keys: List[str]) -> Any:
    """
    Filter sensitive data in a dictionary or string.

    Args:
        data: Data to filter (dict, list, str, etc.)
        sensitive_keys: List of sensitive keywords

    Returns:
        Filtered data
    """
    if isinstance(data, dict):
        filtered = {}
        for key, value in data.items():
            if _is_sensitive_key(key, sensitive_keys):
                filtered[key] = DiscordHandlerConfig.get_filtered_value()
            else:
                filtered[key] = filter_sensitive_data(value, sensitive_keys)
        return filtered
    elif isinstance(data, list):
        return [filter_sensitive_data(item, sensitive_keys) for item in data]
    elif isinstance(data, str):
        return _filter_sensitive_string(data, sensitive_keys)
    else:
        return data


def _is_sensitive_key(key: str, sensitive_keys: List[str]) -> bool:
    """
    Check if the key contains a sensitive keyword.

    Args:
        key: Key to check
        sensitive_keys: List of sensitive keywords

    Returns:
        Whether the key is sensitive
    """
    key_lower = key.lower()
    return any(sensitive_key in key_lower for sensitive_key in sensitive_keys)


def _filter_sensitive_string(text: str, sensitive_keys: List[str]) -> str:
    """
    Filter sensitive information in a string.

    Args:
        text: String to filter
        sensitive_keys: List of sensitive keywords

    Returns:
        Filtered string
    """
    pattern = r"([?&])([^=]+)=([^&]*)"
    
    def replace_param(match):
        prefix = match.group(1)
        param_name = match.group(2)
        param_value = match.group(3)
        
        if _is_sensitive_key(param_name, sensitive_keys):
            return f"{prefix}{param_name}={DiscordHandlerConfig.get_filtered_value()}"
        return match.group(0)
    
    filtered_text = re.sub(pattern, replace_param, text)
    return filtered_text


def should_exclude_exception(
    exception: Exception,
    exclude_exceptions: List[type],
) -> bool:
    """
    Check if the exception is in the exclude list.

    Args:
        exception: Exception object to check
        exclude_exceptions: List of exception classes to exclude

    Returns:
        Whether to exclude
    """
    return any(isinstance(exception, exc_type) for exc_type in exclude_exceptions)
