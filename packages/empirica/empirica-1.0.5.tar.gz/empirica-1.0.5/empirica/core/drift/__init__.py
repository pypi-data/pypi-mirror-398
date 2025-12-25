"""
Drift Detection - Mirror Principle Based

Temporal self-validation for detecting epistemic drift.
Compares current epistemic state to historical baselines from Git checkpoints.

No heuristics, no external LLMs - pure temporal comparison.
"""

from .mirror_drift_monitor import MirrorDriftMonitor

__all__ = ['MirrorDriftMonitor']
