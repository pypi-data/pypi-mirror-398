"""
Git Integration for Empirica

Provides cryptographic signing of epistemic states and CASCADE tracking.
"""

# Note: Do not import SignedGitOperations here to avoid circular imports
# Import directly: from empirica.core.git.signed_operations import SignedGitOperations

__all__ = ["SignedGitOperations"]
