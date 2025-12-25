"""
Session ID Resolver - Resolve session aliases to UUIDs

Supports magic aliases for easy session resumption:
- "latest" or "last" - Most recent session
- "latest:active" - Most recent active session (not ended)
- "latest:<ai_id>" - Most recent session for specific AI
- "latest:active:<ai_id>" - Most recent active session for specific AI

Examples:
    resolve_session_id("latest")
    resolve_session_id("latest:active")
    resolve_session_id("latest:claude-code")
    resolve_session_id("latest:active:claude-code")
    resolve_session_id("88dbf132")  # Partial UUID still works
"""

import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def resolve_session_id(session_id_or_alias: str, ai_id: Optional[str] = None) -> str:
    """
    Resolve session ID from alias or return original UUID.

    Args:
        session_id_or_alias: UUID (full or partial), "latest", "last", or compound alias
        ai_id: Optional AI identifier for scoped resolution (used as fallback filter)

    Returns:
        Resolved full UUID

    Raises:
        ValueError: If alias doesn't match any session

    Examples:
        >>> resolve_session_id("88dbf132-cc7c-4a4b-9b59-77df3b13dbd2")
        '88dbf132-cc7c-4a4b-9b59-77df3b13dbd2'

        >>> resolve_session_id("88dbf132")  # Partial UUID
        '88dbf132-cc7c-4a4b-9b59-77df3b13dbd2'

        >>> resolve_session_id("latest")
        '88dbf132-cc7c-4a4b-9b59-77df3b13dbd2'  # Most recent session

        >>> resolve_session_id("latest:active")
        'fc87adfc-...'  # Most recent active session

        >>> resolve_session_id("latest:claude-code")
        '20586d3b-...'  # Most recent claude-code session

        >>> resolve_session_id("latest:active:claude-code")
        '88dbf132-...'  # Most recent active claude-code session
    """
    # Check if it's an alias
    if not session_id_or_alias.startswith("latest") and session_id_or_alias != "last":
        # Regular UUID (partial or full) - resolve via database
        return _resolve_partial_uuid(session_id_or_alias)

    # Parse alias
    alias = session_id_or_alias
    if alias == "last":
        alias = "latest"  # Normalize to "latest"

    parts = alias.split(":")

    # Extract filters from alias parts
    filters = {
        'active_only': False,
        'ai_id': None
    }

    for part in parts[1:]:  # Skip first part ("latest")
        if part == "active":
            filters['active_only'] = True
        else:
            # Assume it's an AI identifier
            filters['ai_id'] = part

    # Use provided ai_id as fallback if no AI specified in alias
    if not filters['ai_id'] and ai_id:
        filters['ai_id'] = ai_id
        logger.debug(f"Using provided ai_id as fallback filter: {ai_id}")

    # Query database
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()

        # Build query
        query = "SELECT session_id FROM sessions WHERE 1=1"
        params = []

        if filters['active_only']:
            query += " AND end_time IS NULL"
            logger.debug("Filtering for active sessions only")

        if filters['ai_id']:
            query += " AND ai_id = ?"
            params.append(filters['ai_id'])
            logger.debug(f"Filtering for ai_id: {filters['ai_id']}")

        query += " ORDER BY start_time DESC LIMIT 1"

        logger.debug(f"Executing query: {query} with params: {params}")

        cursor = db.conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()

        db.close()

        if result:
            resolved_id = result[0]
            logger.info(f"Resolved alias '{session_id_or_alias}' to session: {resolved_id[:8]}")
            return resolved_id
        else:
            error_msg = f"No session found for alias: {session_id_or_alias}"
            if filters['ai_id']:
                error_msg += f" (ai_id: {filters['ai_id']})"
            if filters['active_only']:
                error_msg += " (active only)"
            logger.warning(error_msg)
            raise ValueError(error_msg)

    except ImportError as e:
        logger.error(f"Failed to import SessionDatabase: {e}")
        raise ValueError(f"Cannot resolve session alias - database unavailable: {e}")


def _resolve_partial_uuid(partial_or_full_uuid: str) -> str:
    """
    Resolve partial UUID (8 chars) to full UUID, or validate full UUID.

    Args:
        partial_or_full_uuid: Partial (8+ chars) or full UUID string

    Returns:
        Full UUID

    Raises:
        ValueError: If UUID not found or ambiguous
    """
    # If it looks like a full UUID (contains hyphens), return as-is
    if "-" in partial_or_full_uuid:
        logger.debug(f"Full UUID provided: {partial_or_full_uuid}")
        return partial_or_full_uuid

    # Partial UUID - query database
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Match beginning of session_id
        cursor.execute(
            "SELECT session_id FROM sessions WHERE session_id LIKE ? ORDER BY start_time DESC",
            (f"{partial_or_full_uuid}%",)
        )

        results = cursor.fetchall()
        db.close()

        if not results:
            raise ValueError(f"No session found matching: {partial_or_full_uuid}")

        if len(results) > 1:
            logger.warning(f"Multiple sessions match '{partial_or_full_uuid}' - using most recent")

        resolved = results[0][0]
        logger.debug(f"Resolved partial UUID '{partial_or_full_uuid}' to {resolved}")
        return resolved

    except ImportError as e:
        logger.error(f"Failed to import SessionDatabase: {e}")
        # Fallback: assume it's a full UUID if it's 36 chars
        if len(partial_or_full_uuid) == 36:
            logger.debug("Database unavailable, assuming full UUID")
            return partial_or_full_uuid
        raise ValueError(f"Cannot resolve partial UUID - database unavailable: {e}")


def get_latest_session_id(ai_id: Optional[str] = None, active_only: bool = False) -> str:
    """
    Get the most recent session ID.

    Convenience function equivalent to resolve_session_id("latest:...").

    Args:
        ai_id: Optional AI identifier to filter by
        active_only: If True, only return active (not ended) sessions

    Returns:
        Most recent session UUID

    Raises:
        ValueError: If no session found

    Examples:
        >>> get_latest_session_id()
        '88dbf132-cc7c-4a4b-9b59-77df3b13dbd2'

        >>> get_latest_session_id(ai_id="claude-code")
        '20586d3b-...'

        >>> get_latest_session_id(ai_id="claude-code", active_only=True)
        '88dbf132-...'
    """
    # Build alias string
    alias_parts = ["latest"]

    if active_only:
        alias_parts.append("active")

    if ai_id:
        alias_parts.append(ai_id)

    alias = ":".join(alias_parts)

    return resolve_session_id(alias)


def is_session_alias(session_id_or_alias: str) -> bool:
    """
    Check if string is a session alias (not a UUID).

    Args:
        session_id_or_alias: String to check

    Returns:
        True if it's an alias, False if it's a UUID

    Examples:
        >>> is_session_alias("latest")
        True

        >>> is_session_alias("latest:active:claude-code")
        True

        >>> is_session_alias("88dbf132-cc7c-4a4b-9b59-77df3b13dbd2")
        False
    """
    return session_id_or_alias.startswith("latest") or session_id_or_alias == "last"
