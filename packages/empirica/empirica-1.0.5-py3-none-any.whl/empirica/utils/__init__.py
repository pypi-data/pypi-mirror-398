"""
Empirica Utilities Module

Provides utility functions for session management, data handling, and common operations.
"""

from .session_resolver import (
    resolve_session_id,
    get_latest_session_id,
    is_session_alias
)

__all__ = [
    'resolve_session_id',
    'get_latest_session_id',
    'is_session_alias',
]
