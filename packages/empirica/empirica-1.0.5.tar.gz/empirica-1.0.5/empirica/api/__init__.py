"""
Empirica Dashboard API

REST API for querying epistemic state, learning deltas, and git-epistemic correlations.
Foundation for Forgejo plugin and standalone dashboards.
"""

from .app import create_app

__all__ = ["create_app"]
