"""
VALLUM — Continuous Adversarial Validation for Agentic Enterprise Systems

The first security validation framework built specifically for multi-agent AI systems.
Combines real-time defense (SHIELD), automated red teaming (SPEAR), and immutable
audit trails (CHAIN) — all mapped to MITRE ATLAS 2026.

Integrates with Veea Lobster Trap, Google Gemini, and CrewAI.

Version: 0.1.0
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Vallum Team"
__license__ = "MIT"

from vallum.config import settings
from vallum.shield import Shield, GeminiIntentClassifier
from vallum.spear import Spear, MutationEngine
from vallum.chain import Chain

__all__ = [
    "Shield",
    "GeminiIntentClassifier",
    "Spear",
    "MutationEngine",
    "Chain",
    "settings",
    "__version__",
]
