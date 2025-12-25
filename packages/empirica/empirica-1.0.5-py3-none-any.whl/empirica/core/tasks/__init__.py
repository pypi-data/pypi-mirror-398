#!/usr/bin/env python3
"""
Task Decomposition Module

Provides task breakdown and management for goal achievement.
MVP implementation focuses on explicit task creation (AI creates tasks via MCP).
"""

from .types import (
    SubTask,
    TaskDecomposition,
    EpistemicImportance,
    TaskStatus
)
from .repository import TaskRepository

__all__ = [
    'SubTask',
    'TaskDecomposition',
    'EpistemicImportance',
    'TaskStatus',
    'TaskRepository'
]
