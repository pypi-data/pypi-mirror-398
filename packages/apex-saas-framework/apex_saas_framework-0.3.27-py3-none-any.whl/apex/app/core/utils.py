"""
Common utilities used across the new architecture.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def utc_now() -> datetime:
    """Return timezone-aware utcnow."""
    return datetime.now(tz=timezone.utc)


def merge_jsonb(base: Dict[str, Any] | None, override: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Merge JSONB structures recursively.

    Args:
        base: Default dictionary.
        override: User provided values.

    Returns:
        Merged dictionary without mutating inputs.
    """
    result: Dict[str, Any] = dict(base or {})
    for key, value in (override or {}).items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_jsonb(result[key], value)
        else:
            result[key] = value
    return result


__all__ = ["utc_now", "merge_jsonb"]

