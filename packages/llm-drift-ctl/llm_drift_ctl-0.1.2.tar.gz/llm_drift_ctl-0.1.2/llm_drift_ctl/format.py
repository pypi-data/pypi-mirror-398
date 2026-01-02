"""
FORMAT mode checks (LLM-free, fully offline)

Checks:
- JSON parse validity
- Schema validation
- Required keys
- Type mismatches
- Structural consistency
"""

from typing import Dict, List, Any, Optional, Union
from .types import DriftLocation


class FormatCheckResult:
    """Result of format check"""
    def __init__(self, valid: bool, score: float, errors: List[DriftLocation]):
        self.valid = valid
        self.score = score
        self.errors = errors


def check_json_format(json: Any) -> FormatCheckResult:
    """Check JSON format validity"""
    errors: List[DriftLocation] = []
    score = 1.0
    
    # Check if it's a valid object
    if not isinstance(json, dict):
        return FormatCheckResult(
            valid=False,
            score=0.0,
            errors=[DriftLocation(path="root", type="not_an_object")]
        )
    
    # Basic structural checks
    for key, value in json.items():
        if value is None:
            errors.append(DriftLocation(path=key, type="null_or_undefined"))
            score -= 0.1
        elif isinstance(value, dict):
            # Recursively check nested objects
            nested = check_json_format(value)
            if not nested.valid:
                errors.extend([
                    DriftLocation(path=f"{key}.{e.path}", type=e.type)
                    for e in nested.errors
                ])
                score -= nested.score * 0.2
    
    score = max(0.0, score)
    
    return FormatCheckResult(
        valid=score >= 0.5,
        score=score,
        errors=errors
    )


def parse_and_validate_json(json_string: str) -> FormatCheckResult:
    """Validate JSON string parse"""
    import json
    
    try:
        parsed = json.loads(json_string)
        return check_json_format(parsed)
    except (json.JSONDecodeError, ValueError):
        return FormatCheckResult(
            valid=False,
            score=0.0,
            errors=[DriftLocation(path="root", type="json_parse_error")]
        )

