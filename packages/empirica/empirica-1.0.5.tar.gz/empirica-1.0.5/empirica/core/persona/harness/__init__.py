"""
Persona Harness - Runtime container for persona execution

The PersonaHarness wraps the CASCADE workflow with persona-specific:
- Epistemic priors (initial knowledge state)
- Thresholds (when to investigate, when to proceed)
- Weights (how to combine foundation/comprehension/execution)
- Focus domains (what to pay attention to)
- Sentinel communication (progress reporting)
"""

from .persona_harness import PersonaHarness
from .communication import (
    SentinelMessage,
    PersonaMessage,
    MessageType,
    send_message,
    receive_message
)

__all__ = [
    'PersonaHarness',
    'SentinelMessage',
    'PersonaMessage',
    'MessageType',
    'send_message',
    'receive_message'
]
