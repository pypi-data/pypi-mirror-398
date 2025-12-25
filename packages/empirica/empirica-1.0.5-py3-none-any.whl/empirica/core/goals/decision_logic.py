#!/usr/bin/env python3
"""
Goal Creation Decision Logic - Simple Comprehension/Foundation Check

Philosophy:
- AI self-assesses clarity, signal, know, context
- Simple thresholds guide decision (not micromanage)
- AI decides based on honest self-assessment
- No complex routing tables

Decision:
- High clarity + signal + know + context → Create goal and act
- High clarity but low know/context → Investigate then create goal
- Low clarity/signal → Ask for clarification
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class GoalDecision:
    """
    Result of goal creation decision logic
    
    This is GUIDANCE, not prescription. AI can override.
    """
    should_create_goal_now: bool
    reasoning: str
    suggested_action: str  # 'create_goal', 'investigate_first', 'ask_clarification'
    confidence: float
    
    # Breakdown for transparency
    clarity_score: float
    signal_score: float
    know_score: float
    context_score: float


def decide_goal_creation(
    clarity: float,
    signal: float,
    know: float,
    context: float,
    clarity_threshold: float = 0.6,
    signal_threshold: float = 0.5,
    know_threshold: float = 0.5,
    context_threshold: float = 0.5
) -> GoalDecision:
    """
    Simple decision logic: Should we create a goal now?
    
    Logic:
    1. Check COMPREHENSION (clarity + signal)
    2. Check FOUNDATION (know + context)
    3. Decide based on both
    
    Args:
        clarity: How clear is the request? (0-1)
        signal: How good is the information quality? (0-1)
        know: Do I know the domain/codebase? (0-1)
        context: Do I know the environment? (0-1)
        *_threshold: Decision thresholds (configurable)
    
    Returns:
        GoalDecision with recommendation
        
    Decision Matrix:
        clarity ≥ threshold AND signal ≥ threshold → "I understand the request"
        know ≥ threshold AND context ≥ threshold → "I can operate"
        
        understand + can_operate → create_goal
        understand + can't_operate → investigate_first
        don't_understand → ask_clarification
    """
    
    # Step 1: Do I understand the request?
    understands_request = (clarity >= clarity_threshold and signal >= signal_threshold)
    
    # Step 2: Can I operate?
    can_operate = (know >= know_threshold and context >= context_threshold)
    
    # Step 3: Decide
    if understands_request and can_operate:
        # "I understand what to do AND I have the foundation"
        return GoalDecision(
            should_create_goal_now=True,
            reasoning=(
                f"Clear request (clarity={clarity:.2f}, signal={signal:.2f}) "
                f"and sufficient foundation (know={know:.2f}, context={context:.2f}). "
                f"Ready to create goal and act."
            ),
            suggested_action='create_goal',
            confidence=min(clarity, signal, know, context),  # Most conservative
            clarity_score=clarity,
            signal_score=signal,
            know_score=know,
            context_score=context
        )
    
    elif understands_request and not can_operate:
        # "I understand what to do BUT lack foundation"
        # Check which foundation component is low
        if context < context_threshold:
            focus = "environment/workspace"
            investigate_what = "context"
        elif know < know_threshold:
            focus = "domain knowledge/codebase"
            investigate_what = "know"
        else:
            focus = "foundation"
            investigate_what = "foundation"
        
        return GoalDecision(
            should_create_goal_now=False,
            reasoning=(
                f"Clear request (clarity={clarity:.2f}, signal={signal:.2f}) "
                f"but low {investigate_what} ({know if investigate_what == 'know' else context:.2f}). "
                f"Should investigate {focus} before creating goal."
            ),
            suggested_action='investigate_first',
            confidence=min(clarity, signal),  # Confident in understanding, not in ability
            clarity_score=clarity,
            signal_score=signal,
            know_score=know,
            context_score=context
        )
    
    else:
        # "I don't understand the request"
        # Check which comprehension component is low
        if clarity < clarity_threshold and signal >= signal_threshold:
            problem = "request is ambiguous (low clarity)"
        elif signal < signal_threshold and clarity >= clarity_threshold:
            problem = "information quality is poor (low signal)"
        else:
            problem = "request is unclear (low clarity and signal)"
        
        return GoalDecision(
            should_create_goal_now=False,
            reasoning=(
                f"Cannot create goal: {problem}. "
                f"Clarity={clarity:.2f}, signal={signal:.2f}. "
                f"Should ask for clarification."
            ),
            suggested_action='ask_clarification',
            confidence=0.3,  # Low confidence when unclear
            clarity_score=clarity,
            signal_score=signal,
            know_score=know,
            context_score=context
        )


def get_investigation_focus(decision: GoalDecision) -> Optional[str]:
    """
    Helper: What should investigation focus on?
    
    Returns:
        String describing investigation focus, or None if not investigating
    """
    if decision.suggested_action != 'investigate_first':
        return None
    
    # Identify weakest foundation component
    if decision.context_score < decision.know_score:
        return "Explore workspace and understand environment"
    else:
        return "Learn domain knowledge and understand codebase/concepts"


def format_decision_for_ai(decision: GoalDecision) -> str:
    """
    Format decision as natural language for AI reasoning
    
    This is GUIDANCE for AI, not a command.
    """
    output = [
        f"📊 Goal Creation Decision:",
        f"",
        f"Assessment:",
        f"  • Clarity: {decision.clarity_score:.2f}",
        f"  • Signal: {decision.signal_score:.2f}",
        f"  • Know: {decision.know_score:.2f}",
        f"  • Context: {decision.context_score:.2f}",
        f"",
        f"Reasoning: {decision.reasoning}",
        f"",
        f"Suggested Action: {decision.suggested_action.upper()}",
    ]
    
    if decision.suggested_action == 'investigate_first':
        focus = get_investigation_focus(decision)
        if focus:
            output.append(f"  → Investigation Focus: {focus}")
    
    output.append(f"")
    output.append(f"Confidence in Decision: {decision.confidence:.2f}")
    output.append(f"")
    output.append(f"Note: This is guidance. AI can override based on context.")
    
    return "\n".join(output)


# Default thresholds (can be overridden)
DEFAULT_THRESHOLDS = {
    'clarity': 0.6,
    'signal': 0.5,
    'know': 0.5,
    'context': 0.5
}
