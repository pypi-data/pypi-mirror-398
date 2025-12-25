"""
Abstract interface for reasoning services

Enables different backends: Ollama, OpenAI, Anthropic, custom models
"""

from abc import ABC, abstractmethod
from typing import Dict
from .types import DeprecationJudgment, RelationshipAnalysis, ImplementationGap


class ReasoningService(ABC):
    """Abstract interface for AI reasoning services"""
    
    @abstractmethod
    def analyze_deprecation(
        self,
        feature: str,
        context: Dict
    ) -> DeprecationJudgment:
        """
        Analyze if a feature is deprecated
        
        Args:
            feature: Feature name
            context: Evidence dictionary
            
        Returns:
            DeprecationJudgment with status and reasoning
        """
        pass
    
    @abstractmethod
    def analyze_relationship(
        self,
        doc_section: str,
        code_section: str
    ) -> RelationshipAnalysis:
        """
        Analyze relationship between doc and code
        
        Args:
            doc_section: Documentation text
            code_section: Code text
            
        Returns:
            RelationshipAnalysis
        """
        pass
    
    @abstractmethod
    def analyze_implementation_gap(
        self,
        documented_behavior: str,
        actual_implementation: str
    ) -> ImplementationGap:
        """
        Analyze if implementation matches documented behavior
        
        Args:
            documented_behavior: What docs say
            actual_implementation: What code does
            
        Returns:
            ImplementationGap analysis
        """
        pass
