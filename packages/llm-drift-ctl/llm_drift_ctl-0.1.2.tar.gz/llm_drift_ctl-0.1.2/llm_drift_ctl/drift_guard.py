"""
DriftGuard - Main class for LLM output validation

This class validates LLM outputs after they are produced.
It never generates content, modifies prompts, or fixes outputs.
It only returns: ALLOW, WARN, or BLOCK decisions.
"""

from typing import Optional, Dict, Any, List, Literal
from .types import (
    DriftGuardConfig,
    CheckInput,
    CheckResult,
    UserLLM,
    Baseline,
    Decision,
    Severity,
    DriftLocation
)
from .format import check_json_format, parse_and_validate_json, FormatCheckResult
from .baseline import baseline_store, normalize_output, generate_semantic_fingerprint
from .cloud import verify_license
from .content import check_content_drift
from datetime import datetime
import time


class DriftGuard:
    """Main class for LLM output validation"""
    
    def __init__(self, config: DriftGuardConfig):
        if not config.pipeline_id:
            raise ValueError("pipeline_id is required")
        self.config = config
        self._license_cache: Optional[Dict[str, Any]] = None
    
    async def check(
        self,
        input_data: Optional[CheckInput] = None,
        json: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        mode: Literal["FORMAT", "CONTENT", "CALIBRATION", "ALL"] = "FORMAT"
    ) -> CheckResult:
        """
        Run validation check on output
        
        Can be called with CheckInput object or keyword arguments:
        - check(CheckInput(...))
        - check(json={...}, mode="FORMAT")
        
        Returns machine-readable decision (ALLOW, WARN, BLOCK)
        """
        # Support both CheckInput object and keyword arguments
        if input_data is not None:
            json_data = input_data.json
            text = input_data.text
            mode = input_data.mode or "FORMAT"
        else:
            json_data = json
            # text and mode are already set from parameters
        
        # Determine what to check
        if mode == "ALL":
            modes: List[str] = ["FORMAT", "CONTENT", "CALIBRATION"]
        else:
            modes = [mode]
        
        result = CheckResult(
            block=False,
            decision="ALLOW",
            severity="LOW",
            scores={},
            where=[]
        )
        
        # FORMAT mode checks (always available, offline)
        if "FORMAT" in modes:
            format_result = await self._check_format(json_data, text)
            result.scores["format"] = format_result.score
            result.where.extend(format_result.errors)
            
            if not format_result.valid:
                result.block = True
                result.decision = "BLOCK"
                result.severity = "HIGH"
        
        # CONTENT/CALIBRATION mode checks (require LLM)
        if "CONTENT" in modes or "CALIBRATION" in modes:
            if not self.config.llm:
                raise ValueError("CONTENT/CALIBRATION mode requires UserLLM to be provided")
            
            # If user provides their own LLM, no license check needed
            # License is only for cloud services, not for user's own LLM usage
            
            content_result = await self._check_content(json_data, text)
            if "CONTENT" in modes:
                result.scores["semantic"] = content_result["semantic"]
            if "CALIBRATION" in modes or "CONTENT" in modes:
                result.scores["calibration"] = content_result["calibration"]
            
            # Update decision based on content checks
            if content_result["block"]:
                result.block = True
                result.decision = "BLOCK"
                result.severity = "HIGH"
            elif content_result["warn"]:
                if result.decision == "ALLOW":
                    result.decision = "WARN"
                    result.severity = "MEDIUM"
        
        return result
    
    async def accept_baseline(
        self,
        json: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> None:
        """Accept output as baseline (approved behavior)"""
        if not json and not text:
            raise ValueError("Either json or text must be provided")
        
        normalized = normalize_output(json or text)
        fingerprint = generate_semantic_fingerprint(normalized)
        
        baseline = Baseline(
            id=f"{self.config.pipeline_id}-{int(time.time() * 1000)}",
            pipeline_id=self.config.pipeline_id,
            normalized=normalized,
            semantic_fingerprint=fingerprint,
            score_profile={"format": 1.0 if json else None},
            created_at=datetime.now()
        )
        
        baseline_store.store(baseline)
    
    async def _check_format(
        self,
        json_data: Optional[Dict[str, Any]],
        text: Optional[str]
    ) -> FormatCheckResult:
        """FORMAT mode checks (offline, LLM-free)"""
        if json_data is not None:
            return check_json_format(json_data)
        elif text:
            return parse_and_validate_json(text)
        else:
            return FormatCheckResult(
                valid=False,
                score=0.0,
                errors=[DriftLocation(path="root", type="no_input")]
            )
    
    async def _check_content(
        self,
        json_data: Optional[Dict[str, Any]],
        text: Optional[str]
    ) -> Dict[str, Any]:
        """CONTENT/CALIBRATION mode checks (require LLM)"""
        llm = self.config.llm
        
        # Get latest baseline for comparison
        baseline = baseline_store.get_latest(self.config.pipeline_id)
        
        if not baseline:
            # No baseline yet - allow but warn
            return {
                "semantic": 1.0,
                "calibration": 1.0,
                "block": False,
                "warn": True
            }
        
        # Use LLM to check content drift
        current_output = json_data or text or ""
        result = await check_content_drift(
            llm,
            baseline,
            current_output,
            self.config.content_requirements  # Optional requirements/conditions
        )
        
        return {
            "semantic": result.semantic,
            "calibration": result.calibration,
            "block": result.block,
            "warn": result.warn
        }
    
    async def _ensure_license(self) -> Dict[str, Any]:
        """Ensure license is valid (with caching)"""
        if self._license_cache:
            return self._license_cache
        
        license_resp = await verify_license(self.config)
        
        self._license_cache = {
            "valid": license_resp.valid,
            "features": license_resp.features or ["FORMAT"]
        }
        
        return self._license_cache

