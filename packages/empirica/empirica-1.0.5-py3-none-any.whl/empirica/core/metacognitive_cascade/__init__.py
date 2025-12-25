"""
Metacognitive Cascade Package

Canonical epistemic cascade using genuine LLM-powered self-assessment:
THINK → ENGAGEMENT GATE → UNCERTAINTY → INVESTIGATE (loop) → CHECK → ACT

Key Features:
- LLM-powered assessment (no heuristics)
- ENGAGEMENT gate (≥0.60)
- Reflex Frame logging
- Canonical weights (35/25/25/15)
- Domain-aware investigation
"""

from .metacognitive_cascade import (
    CanonicalEpistemicCascade,
    run_canonical_cascade,
    CascadePhase,
    CanonicalCascadeState
)

__all__ = [
    # Canonical (primary)
    'CanonicalEpistemicCascade',
    'run_canonical_cascade',
    'CascadePhase',
    'CanonicalCascadeState',
]