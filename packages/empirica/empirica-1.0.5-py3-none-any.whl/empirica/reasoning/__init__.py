"""
Empirica Reasoning Layer

AI-powered reasoning for doc-code intelligence.
Converts any local LLM into a specialized reasoning assistant.
"""

from .service import ReasoningService
from .ollama_adapter import OllamaReasoningModel
from .epistemic_cascade import EpistemicCascade, create_default_cascade
from .types import DeprecationJudgment, RelationshipAnalysis, ImplementationGap

__all__ = [
    'ReasoningService',
    'OllamaReasoningModel',
    'EpistemicCascade',
    'create_default_cascade',
    'DeprecationJudgment',
    'RelationshipAnalysis',
    'ImplementationGap'
]
