"""
Type definitions for llm-drift-ctl
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Literal, Union
from dataclasses import dataclass
from datetime import datetime


class UserLLM(ABC):
    """
    User-provided LLM interface
    
    The user supplies their own LLM implementation (OpenAI, Gemini, Claude, or custom)
    llm-drift-ctl never owns LLM keys.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        text: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate a response using the user's LLM
        
        Args:
            prompt: The prompt to send to the LLM
            text: Optional text context
            json: Optional JSON context
            
        Returns:
            String or object response from the LLM
        """
        pass


@dataclass
class DriftGuardConfig:
    """DriftGuard configuration"""
    pipeline_id: str
    llm: Optional[UserLLM] = None
    cloud_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    content_requirements: Optional[str] = None  # Optional: Requirements/conditions for content validation


@dataclass
class CheckInput:
    """Check input parameters"""
    json: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    mode: Literal["FORMAT", "CONTENT", "CALIBRATION", "ALL"] = "FORMAT"


Severity = Literal["LOW", "MEDIUM", "HIGH"]
Decision = Literal["ALLOW", "WARN", "BLOCK"]


@dataclass
class DriftLocation:
    """Drift detection location"""
    path: str
    type: str


@dataclass
class CheckResult:
    """Check result - machine-readable decision"""
    block: bool
    decision: Decision
    severity: Severity
    scores: Dict[str, float]  # format, semantic, calibration
    where: List[DriftLocation]


@dataclass
class Baseline:
    """Baseline storage (normalized output + metadata)"""
    id: str
    pipeline_id: str
    normalized: Union[Dict[str, Any], str]
    semantic_fingerprint: str
    score_profile: Dict[str, Optional[float]]
    created_at: datetime

