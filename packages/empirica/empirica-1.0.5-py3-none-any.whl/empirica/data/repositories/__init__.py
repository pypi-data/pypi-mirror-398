"""
Repository pattern implementation for session database domains.

Each repository encapsulates database operations for a specific domain,
sharing a single SQLite connection for transactional consistency.
"""

from .base import BaseRepository
from .goals import GoalRepository
from .branches import BranchRepository
from .breadcrumbs import BreadcrumbRepository
from .projects import ProjectRepository

__all__ = [
    'BaseRepository',
    'GoalRepository',
    'BranchRepository',
    'BreadcrumbRepository',
    'ProjectRepository',
]
