"""
CONTENT mode drift detection

Uses LLM to compare new output against baseline
and detect content drift
"""

from typing import Dict, Any, Optional, Union, List
from .types import UserLLM, Baseline


class ContentCheckResult:
    """Result of content drift check"""
    def __init__(
        self,
        semantic: float,
        calibration: float,
        block: bool,
        warn: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        self.semantic = semantic
        self.calibration = calibration
        self.block = block
        self.warn = warn
        self.details = details or {}


async def check_content_drift(
    llm: UserLLM,
    baseline: Baseline,
    current_output: Union[Dict[str, Any], str],
    requirements: Optional[str] = None
) -> ContentCheckResult:
    """Check content drift using LLM comparison"""
    
    baseline_str = baseline.normalized if isinstance(baseline.normalized, str) else str(baseline.normalized)
    if not isinstance(baseline_str, str):
        import json
        baseline_str = json.dumps(baseline_str, indent=2)
    
    current_str = current_output if isinstance(current_output, str) else str(current_output)
    if not isinstance(current_str, str):
        import json
        current_str = json.dumps(current_str, indent=2)
    
    # Build comparison prompt
    prompt = f"""You are a quality control system that detects drift in LLM outputs.

BASELINE (approved output):
```
{baseline_str}
```

CURRENT OUTPUT (to check):
```
{current_str}
```
"""
    
    if requirements:
        prompt += f"\n\nREQUIREMENTS/CONDITIONS:\n{requirements}\n"
    
    prompt += """
Analyze the current output compared to the baseline and determine:
1. Semantic similarity (0.0-1.0): How similar is the meaning/content?
2. Structural consistency (0.0-1.0): How similar is the structure/format?
3. Drift severity: Are there significant deviations from the baseline?

Respond ONLY with a valid JSON object in this exact format:
{
  "semantic": 0.95,
  "structural": 0.90,
  "driftSeverity": "low|medium|high",
  "driftPoints": ["specific issue 1", "specific issue 2"],
  "shouldBlock": false,
  "shouldWarn": false
}"""
    
    try:
        llm_response = await llm.generate(
            prompt=prompt,
            json={
                "semantic": 0.0,
                "structural": 0.0,
                "driftSeverity": "low",
                "driftPoints": [],
                "shouldBlock": False,
                "shouldWarn": False
            }
        )
        
        # Parse LLM response
        import json
        import re
        
        if isinstance(llm_response, str):
            # Extract JSON from response if it's wrapped in text
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                analysis = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse LLM response as JSON")
        else:
            analysis = llm_response
        
        semantic = max(0, min(1, analysis.get("semantic", 0.5)))
        structural = max(0, min(1, analysis.get("structural", 0.5)))
        calibration = (semantic + structural) / 2
        
        drift_severity = analysis.get("driftSeverity", "low")
        should_block = analysis.get("shouldBlock", False) is True
        should_warn = analysis.get("shouldWarn", False) is True or drift_severity == "medium"
        
        # Determine block/warn based on scores
        block = should_block or semantic < 0.3 or calibration < 0.3
        warn = should_warn or (semantic < 0.7 and semantic >= 0.3) or (calibration < 0.7 and calibration >= 0.3)
        
        return ContentCheckResult(
            semantic=semantic,
            calibration=calibration,
            block=block,
            warn=warn,
            details={
                "driftPoints": analysis.get("driftPoints", []),
                "differences": analysis.get("differences", [])
            }
        )
    except Exception as error:
        # Fallback to basic comparison on error
        print(f"Warning: LLM content check failed, using fallback: {error}")
        
        # Simple string comparison fallback
        baseline_str = baseline.normalized if isinstance(baseline.normalized, str) else str(baseline.normalized)
        current_str = current_output if isinstance(current_output, str) else str(current_output)
        
        semantic = 1.0 if baseline_str == current_str else 0.5
        
        return ContentCheckResult(
            semantic=semantic,
            calibration=semantic,
            block=semantic < 0.3,
            warn=semantic < 0.7 and semantic >= 0.3
        )

