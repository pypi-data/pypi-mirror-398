#!/usr/bin/env python3
"""
Memory Gap Policy Loader - Configurable Enforcement for Cross-Session Context Tracking

Part of the Empirica Meta-Agent Configuration Object (MCO) architecture.
Loads memory gap enforcement policies from epistemic_conduct.yaml.

Philosophy:
- Detection is always on (transparency)
- Enforcement is configurable (user agency)
- Different modes for different use cases (inform/warn/strict/block)
- Per-category policies (findings, unknowns, file_changes, compaction, confabulation)

Usage:
    from empirica.config.memory_gap_policy_loader import get_memory_gap_policy

    # Get default policy (inform mode)
    policy = get_memory_gap_policy()

    # Get strict policy
    policy = get_memory_gap_policy(mode='strict')

    # Get policy for specific gap type
    policy = get_memory_gap_policy(gap_type='confabulation', mode='strict')

Architecture:
    - Part of MCO: epistemic_conduct.yaml defines enforcement modes
    - Used by MemoryGapDetector for policy enforcement
    - AI can query policy to understand enforcement level
    - User can configure per-project or per-session policies
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MemoryGapPolicyLoader:
    """
    Memory gap policy loader for configurable enforcement.

    Design:
    - Loads policies from epistemic_conduct.yaml
    - Provides enforcement mode configuration
    - Supports per-category policy overrides
    - Includes threshold and severity mapping
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize memory gap policy loader.

        Args:
            config_path: Optional path to epistemic_conduct.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent / 'mco' / 'epistemic_conduct.yaml'

        self.config_path = config_path
        self.enforcement_modes: Dict[str, Dict[str, Any]] = {}
        self.scope_policies: Dict[str, Dict[str, Any]] = {}
        self.default_mode: str = 'inform'

        # Load configurations
        self._load_configurations()

    def _load_configurations(self):
        """Load memory gap policies from YAML"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Epistemic conduct config not found: {self.config_path}")
                self._load_hardcoded_defaults()
                return

            with open(self.config_path) as f:
                data = yaml.safe_load(f)

                if not data or 'workflow_integration' not in data:
                    logger.error("Invalid config: missing 'workflow_integration'")
                    self._load_hardcoded_defaults()
                    return

                memory_gap_config = data.get('workflow_integration', {}).get('memory_gap_enforcement', {})

                if not memory_gap_config:
                    logger.warning("No memory_gap_enforcement config found, using defaults")
                    self._load_hardcoded_defaults()
                    return

                self.enforcement_modes = memory_gap_config.get('enforcement_modes', {})
                self.scope_policies = memory_gap_config.get('scope_policies', {})
                self.default_mode = memory_gap_config.get('default_mode', 'inform')

                logger.info(f"✅ Loaded memory gap policies: {len(self.enforcement_modes)} modes, "
                           f"{len(self.scope_policies)} scope policies")

        except Exception as e:
            logger.error(f"Failed to load memory gap policies: {e}")
            self._load_hardcoded_defaults()

    def _load_hardcoded_defaults(self):
        """Fallback hardcoded policies if YAML loading fails"""
        logger.warning("⚠️  Using hardcoded memory gap policy defaults")

        self.enforcement_modes = {
            'inform': {
                'description': 'Show gaps, no penalty (default)',
                'bypass_allowed': True
            },
            'warn': {
                'description': 'Show gaps + recommendations',
                'bypass_allowed': True
            },
            'strict': {
                'description': 'Show gaps + adjust vectors to realistic',
                'bypass_allowed': False
            },
            'block': {
                'description': 'Show gaps + prevent proceeding',
                'bypass_allowed': False
            }
        }

        self.scope_policies = {
            'findings': {'threshold': 10},
            'unknowns': {'threshold': 5},
            'file_changes': {'threshold': 0},
            'compaction': {'threshold': 0.4},
            'confabulation': {'threshold': 0.3}
        }

        self.default_mode = 'inform'

    def get_policy(
        self,
        mode: Optional[str] = None,
        gap_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get memory gap policy configuration.

        Args:
            mode: Enforcement mode ('inform', 'warn', 'strict', 'block')
            gap_type: Optional specific gap type for per-category policy

        Returns:
            Policy dictionary with enforcement configuration

        Example:
            >>> loader = MemoryGapPolicyLoader()
            >>> policy = loader.get_policy(mode='strict', gap_type='confabulation')
            >>> print(policy)
            {
                'enforcement': 'strict',
                'scope': {...},
                'thresholds': {...}
            }
        """
        # Use default mode if not specified
        if mode is None:
            mode = self.default_mode

        # Validate mode
        if mode not in self.enforcement_modes:
            logger.warning(f"Unknown enforcement mode '{mode}', using default '{self.default_mode}'")
            mode = self.default_mode

        # Build policy dictionary
        policy = {
            'enforcement': mode,
            'description': self.enforcement_modes[mode].get('description', ''),
            'bypass_allowed': self.enforcement_modes[mode].get('bypass_allowed', True),
            'thresholds': {}
        }

        # Add scope-specific policies
        if gap_type and gap_type in self.scope_policies:
            # Single gap type
            scope_config = self.scope_policies[gap_type]
            policy['scope'] = {gap_type: mode}
            policy['thresholds'][gap_type] = scope_config.get('threshold', 0)
        else:
            # All gap types
            policy['scope'] = {
                gap_name: mode for gap_name in self.scope_policies.keys()
            }
            policy['thresholds'] = {
                gap_name: config.get('threshold', 0)
                for gap_name, config in self.scope_policies.items()
            }

        return policy

    def get_enforcement_for_gap(
        self,
        gap_type: str,
        gap_score: float,
        gap_count: Optional[int] = None,
        default_mode: Optional[str] = None
    ) -> str:
        """
        Get recommended enforcement mode for a specific gap.

        Args:
            gap_type: Type of memory gap
            gap_score: Gap score (0.0-1.0) or count
            gap_count: Optional count for count-based gaps
            default_mode: Default enforcement mode if not specified

        Returns:
            Recommended enforcement mode ('inform', 'warn', 'strict', 'block')

        Example:
            >>> loader = MemoryGapPolicyLoader()
            >>> mode = loader.get_enforcement_for_gap('confabulation', 0.5)
            >>> print(mode)  # 'block' (critical confabulation)
        """
        if gap_type not in self.scope_policies:
            return default_mode or self.default_mode

        scope_config = self.scope_policies[gap_type]
        severity_map = scope_config.get('severity_map', {})

        # Determine severity based on score/count
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity not in severity_map:
                continue

            severity_config = severity_map[severity]

            # Check count-based threshold
            if gap_count is not None and 'count_min' in severity_config:
                if gap_count >= severity_config['count_min']:
                    return severity_config.get('enforcement', default_mode or self.default_mode)

            # Check score-based threshold (for confabulation, compaction)
            if 'gap_min' in severity_config:
                if gap_score >= severity_config['gap_min']:
                    return severity_config.get('enforcement', default_mode or self.default_mode)

            if 'compaction_min' in severity_config:
                if gap_score >= severity_config['compaction_min']:
                    return severity_config.get('enforcement', default_mode or self.default_mode)

            if 'files_min' in severity_config:
                if gap_count is not None and gap_count >= severity_config['files_min']:
                    return severity_config.get('enforcement', default_mode or self.default_mode)

        # No threshold met, use default
        return default_mode or self.default_mode

    def list_enforcement_modes(self) -> Dict[str, str]:
        """List all available enforcement modes"""
        return {
            mode: config.get('description', 'No description')
            for mode, config in self.enforcement_modes.items()
        }

    def list_scope_policies(self) -> Dict[str, Dict[str, Any]]:
        """List all scope-specific policies"""
        return {
            gap_type: {
                'description': config.get('description', 'No description'),
                'threshold': config.get('threshold', 0)
            }
            for gap_type, config in self.scope_policies.items()
        }


# Global instance accessor
_POLICY_LOADER_INSTANCE = None


def get_policy_loader() -> MemoryGapPolicyLoader:
    """
    Get global MemoryGapPolicyLoader instance (singleton pattern).

    Returns:
        MemoryGapPolicyLoader instance
    """
    global _POLICY_LOADER_INSTANCE
    if _POLICY_LOADER_INSTANCE is None:
        _POLICY_LOADER_INSTANCE = MemoryGapPolicyLoader()
    return _POLICY_LOADER_INSTANCE


def get_memory_gap_policy(
    mode: Optional[str] = None,
    gap_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get memory gap policy configuration.

    Convenience function that uses global MemoryGapPolicyLoader.

    Args:
        mode: Enforcement mode ('inform', 'warn', 'strict', 'block')
        gap_type: Optional specific gap type

    Returns:
        Policy dictionary

    Example:
        >>> policy = get_memory_gap_policy(mode='strict')
        >>> print(policy['enforcement'])  # 'strict'
    """
    loader = get_policy_loader()
    return loader.get_policy(mode=mode, gap_type=gap_type)


def get_enforcement_for_gap(
    gap_type: str,
    gap_score: float,
    gap_count: Optional[int] = None,
    default_mode: Optional[str] = None
) -> str:
    """
    Get recommended enforcement mode for a specific gap.

    Convenience function.

    Args:
        gap_type: Type of memory gap
        gap_score: Gap score (0.0-1.0)
        gap_count: Optional count for count-based gaps
        default_mode: Default mode if not specified

    Returns:
        Enforcement mode string
    """
    loader = get_policy_loader()
    return loader.get_enforcement_for_gap(gap_type, gap_score, gap_count, default_mode)
