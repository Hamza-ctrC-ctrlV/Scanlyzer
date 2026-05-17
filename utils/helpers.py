"""
Utility functions for JSON parsing, error handling, and common operations.

This module provides shared functionality used across multiple modules
to reduce code duplication and enforce consistent patterns.
"""

import json
import re
import logging
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

SEVERITY_SCORE_MAP = {
    "CRITICAL": 25,
    "HIGH": 15,
    "MEDIUM": 8,
    "LOW": 3,
    "INFO": 1,
}

EMPTY_STATS = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

def compute_scan_stats(patches: list) -> tuple:
    """Compute score, stats, and count from a list of patch dicts.
    Returns:
        (score, stats, patches_count)
    """
    stats = dict(EMPTY_STATS)
    total_points = 0
    count = 0

    for p in patches:
        if not isinstance(p, dict):
            continue
        count += 1
        sev = (p.get("severity") or "").upper()
        total_points += SEVERITY_SCORE_MAP.get(sev, 0)
        if sev in stats:
            stats[sev] += 1

    score = max(0, 100 - total_points)
    return score, stats, count


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract a JSON object from text that may contain markdown code blocks or extra content.
    
    Handles both raw JSON and JSON wrapped in markdown code blocks.
    
    Args:
        text (str): Raw text possibly containing JSON with markdown formatting
        
    Returns:
        Optional[Dict[str, Any]]: Parsed JSON object, or None if extraction fails
        
    Side Effects:
        Logs warnings on parse failures
    """
    if not isinstance(text, str) or not text.strip():
        return None
    
    # Remove markdown code block wrappers if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove opening markdown block
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        # Remove closing markdown block
        cleaned = re.sub(r"\s*```$", "", cleaned)
    
    # Try to extract JSON object (handles nested structures)
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not json_match:
        logger.warning("No JSON object found in text")
        return None
    
    try:
        json_text = json_match.group(0)
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return None


def load_json_file(file_path: str | Path) -> Optional[Any]:
    """Load JSON content from a file path.

    Returns None when the file does not exist or cannot be parsed.
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"JSON file not found: {path}")
        return None

    try:
        with path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except Exception as exc:
        logger.warning(f"Failed to load JSON file {path}: {exc}")
        return None


def standardize_error_response(
    success: bool,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized API response object.
    
    Ensures consistent error/success response format across all endpoints.
    
    Args:
        success (bool): Whether operation succeeded
        message (str): Human-readable message
        data (Optional[Dict]): Additional data to include in response
        error_code (Optional[str]): Machine-readable error identifier
        
    Returns:
        Dict: Standardized response object with success, message, data, and optionally error_code
    """
    response = {
        "success": success,
        "message": message,
    }
    
    if data is not None:
        response["data"] = data
    
    if error_code is not None:
        response["error_code"] = error_code
    
    return response


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive values (API keys, tokens) for safe logging.
    
    Shows only first N characters followed by asterisks.
    
    Args:
        value (str): Sensitive value to mask
        visible_chars (int): Number of leading characters to show
        
    Returns:
        str: Masked value (e.g., "sk_t...****")
    """
    if not value or len(value) <= visible_chars:
        return "***"
    return f"{value[:visible_chars]}...****"


def validate_api_key_format(api_key: str) -> Tuple[bool, str]:
    """
    Validate API key format.
    
    Checks basic format requirements (length, character types).
    
    Args:
        api_key (str): API key to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    if not api_key or len(api_key) < 10:
        return False, "API key must be at least 10 characters"
    
    if not all(c.isalnum() or c == "-" or c == "_" for c in api_key):
        return False, "API key contains invalid characters"
    
    return True, "API key format valid"


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is transient and should trigger a retry.
    
    Transient errors: timeouts, connection issues, rate limits.
    Non-retryable: authentication, validation, not-found errors.
    
    Args:
        error (Exception): Exception to evaluate
        
    Returns:
        bool: True if operation should be retried
    """
    error_str = str(error).lower()
    
    # Retryable conditions
    retryable_keywords = [
        "timeout",
        "connection",
        "429",  # Rate limit
        "503",  # Service unavailable
        "504",  # Gateway timeout
        "temporarily",
        "try again",
    ]
    
    # Non-retryable conditions
    non_retryable_keywords = [
        "authentication",
        "permission",
        "401",
        "403",
        "404",
        "invalid",
    ]
    
    if any(keyword in error_str for keyword in non_retryable_keywords):
        return False
    
    if any(keyword in error_str for keyword in retryable_keywords):
        return True
    
    return False


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with override values taking precedence.
    
    Args:
        base (Dict): Base dictionary
        override (Dict): Dictionary with values to override/add
        
    Returns:
        Dict: Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def safe_get(obj: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary values using dot notation.
    
    Args:
        obj (Dict): Dictionary to query
        path (str): Dot-separated path (e.g., "user.profile.name")
        default (Any): Value to return if path not found
        
    Returns:
        Any: Value at path or default value
        
    Example:
        safe_get({"user": {"name": "Alice"}}, "user.name")  # Returns "Alice"
        safe_get({"user": {}}, "user.age", 0)  # Returns 0
    """
    keys = path.split(".")
    current = obj
    
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    
    return current
