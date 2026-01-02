"""
llm-drift-ctl

Production-grade LLM output validation package.
Validates LLM outputs using your own LLM when needed — and no LLM when not.
"""

from .drift_guard import DriftGuard
from .types import UserLLM, DriftGuardConfig, CheckInput, CheckResult, DriftLocation
from .adapters import OpenAIAdapter

__all__ = [
    "DriftGuard",
    "UserLLM",
    "DriftGuardConfig",
    "CheckInput",
    "CheckResult",
    "DriftLocation",
    "OpenAIAdapter",
]

__version__ = "0.1.1"
