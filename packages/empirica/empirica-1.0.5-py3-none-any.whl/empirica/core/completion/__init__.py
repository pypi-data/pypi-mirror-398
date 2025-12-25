#!/usr/bin/env python3
"""
Completion Tracking Module

Provides progress tracking and completion verification for goals and tasks.
Phase 2: Git notes integration for team coordination and lead AI queries.
"""

from .types import (
    CompletionRecord,
    CompletionMetrics
)
from .tracker import CompletionTracker
from .git_query import GitProgressQuery

__all__ = [
    'CompletionRecord',
    'CompletionMetrics',
    'CompletionTracker',
    'GitProgressQuery'
]
