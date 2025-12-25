"""
Epistemic Cascade: Uncertainty-Driven Model Delegation

Uses Empirica's epistemic principles for intelligent model routing:
- Fast models for high-confidence cases
- Powerful models for uncertain cases
- Human escalation for impossible cases

This IS meta-metacognition: The reasoning service uses Empirica's
epistemic framework to assess its OWN uncertainty!
"""

import logging
from typing import Dict, List, Optional, Tuple
from .service import ReasoningService
from .ollama_adapter import OllamaReasoningModel
from .types import DeprecationJudgment

logger = logging.getLogger(__name__)


class EpistemicCascade:
    """
    Uncertainty-driven cascade through model tiers
    
    Tiers:
    1. Fast (7B): 2-5s per analysis, handles 70-80% of cases
    2. Powerful (32B): 30s per analysis, handles uncertain cases
    3. Human: Final escalation for impossible decisions
    
    Philosophy: Use Empirica's uncertainty vector to decide when to escalate
    """
    
    def __init__(
        self,
        tier1_model: str = "qwen2.5:7b",
        tier2_model: str = "qwen2.5:32b",
        endpoint: str = "http://localhost:11434",
        tier1_threshold: float = 0.85,
        tier2_threshold: float = 0.75
    ):
        """
        Initialize epistemic cascade
        
        Args:
            tier1_model: Fast model for initial analysis
            tier2_model: Powerful model for uncertain cases
            endpoint: Ollama endpoint
            tier1_threshold: Confidence threshold for tier 1 (higher = more conservative)
            tier2_threshold: Confidence threshold for tier 2
        """
        self.tier1 = OllamaReasoningModel(tier1_model, endpoint)
        self.tier2 = OllamaReasoningModel(tier2_model, endpoint)
        
        self.tier1_threshold = tier1_threshold
        self.tier2_threshold = tier2_threshold
        
        logger.info(f"Initialized cascade: {tier1_model} -> {tier2_model}")
    
    def analyze_with_cascade(
        self,
        feature: str,
        context: Dict
    ) -> Dict:
        """
        Analyze with uncertainty-driven escalation
        
        Returns dict with:
        - judgment: Final DeprecationJudgment
        - tier_used: 1, 2, or "human"
        - tier1_result: Always present
        - tier2_result: Present if escalated
        """
        result = {
            "feature": feature,
            "tier1_result": None,
            "tier2_result": None,
            "tier_used": None,
            "judgment": None
        }
        
        # Tier 1: Fast model
        logger.info(f"Tier 1 analyzing: {feature}")
        tier1_judgment = self.tier1.analyze_deprecation(feature, context)
        result["tier1_result"] = tier1_judgment
        
        # Check if confident enough
        if tier1_judgment.confidence >= self.tier1_threshold:
            logger.info(f"Tier 1 confident ({tier1_judgment.confidence:.2f}), done!")
            result["tier_used"] = 1
            result["judgment"] = tier1_judgment
            return result
        
        # Uncertain, escalate to Tier 2
        logger.info(f"Tier 1 uncertain ({tier1_judgment.confidence:.2f}), escalating...")
        tier2_judgment = self.tier2.analyze_deprecation(feature, context)
        result["tier2_result"] = tier2_judgment
        
        # Check if tier 2 is confident
        if tier2_judgment.confidence >= self.tier2_threshold:
            logger.info(f"Tier 2 confident ({tier2_judgment.confidence:.2f}), done!")
            result["tier_used"] = 2
            result["judgment"] = tier2_judgment
            return result
        
        # Both tiers uncertain, flag for human
        logger.warning(f"Both tiers uncertain about {feature}, needs human review")
        result["tier_used"] = "human"
        result["judgment"] = self._create_human_review_judgment(
            feature,
            tier1_judgment,
            tier2_judgment
        )
        
        return result
    
    def _create_human_review_judgment(
        self,
        feature: str,
        tier1: DeprecationJudgment,
        tier2: DeprecationJudgment
    ) -> DeprecationJudgment:
        """Create judgment indicating human review needed"""
        
        # Check if models agree on status
        agree_on_status = tier1.status == tier2.status
        
        reasoning = f"""Both AI models are uncertain:
        
Tier 1 ({self.tier1.model_name}): {tier1.status} (confidence: {tier1.confidence:.2f})
Reasoning: {tier1.reasoning[:100]}...

Tier 2 ({self.tier2.model_name}): {tier2.status} (confidence: {tier2.confidence:.2f})
Reasoning: {tier2.reasoning[:100]}...

Models {"AGREE on status" if agree_on_status else "DISAGREE on status"}.
Confidence too low for automatic decision.
Human review required."""
        
        return DeprecationJudgment(
            feature=feature,
            status="needs_review",
            confidence=max(tier1.confidence, tier2.confidence),
            reasoning=reasoning,
            evidence=[
                f"Tier 1: {tier1.status}",
                f"Tier 2: {tier2.status}"
            ],
            recommendation="Human review required - models uncertain or disagree",
            metadata={
                "tier1": {
                    "status": tier1.status,
                    "confidence": tier1.confidence
                },
                "tier2": {
                    "status": tier2.status,
                    "confidence": tier2.confidence
                },
                "agreement": agree_on_status
            }
        )
    
    def analyze_batch_with_cascade(
        self,
        candidates: List[Tuple[str, Dict]]
    ) -> Dict:
        """
        Analyze batch with cascade, tracking efficiency
        
        Args:
            candidates: List of (feature, context) tuples
            
        Returns:
            Dict with results and statistics
        """
        results = []
        stats = {
            "total": len(candidates),
            "tier1_solved": 0,
            "tier2_solved": 0,
            "human_review": 0,
            "tier1_time": 0.0,
            "tier2_time": 0.0
        }
        
        import time
        
        for feature, context in candidates:
            start = time.time()
            result = self.analyze_with_cascade(feature, context)
            elapsed = time.time() - start
            
            # Update stats
            if result["tier_used"] == 1:
                stats["tier1_solved"] += 1
                stats["tier1_time"] += elapsed
            elif result["tier_used"] == 2:
                stats["tier2_solved"] += 1
                stats["tier2_time"] += elapsed
            else:
                stats["human_review"] += 1
            
            results.append(result)
        
        # Calculate efficiency
        total_analyzed = stats["tier1_solved"] + stats["tier2_solved"]
        if total_analyzed > 0:
            stats["tier1_efficiency"] = stats["tier1_solved"] / total_analyzed
            stats["avg_tier1_time"] = stats["tier1_time"] / stats["tier1_solved"] if stats["tier1_solved"] > 0 else 0
            stats["avg_tier2_time"] = stats["tier2_time"] / stats["tier2_solved"] if stats["tier2_solved"] > 0 else 0
        
        return {
            "results": results,
            "stats": stats
        }


def create_default_cascade(
    endpoint: str = "http://localhost:11434"
) -> EpistemicCascade:
    """
    Create cascade with default configuration
    
    Returns:
        EpistemicCascade configured for deprecation analysis
    """
    return EpistemicCascade(
        tier1_model="qwen2.5:7b",      # Fast (2-5s)
        tier2_model="qwen2.5:32b",     # Powerful (30s)
        endpoint=endpoint,
        tier1_threshold=0.85,          # High confidence required
        tier2_threshold=0.75           # Medium-high confidence
    )
