"""
In-memory baseline storage (MVP)

In production, this would be replaced with persistent storage
"""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json
from .types import Baseline


class BaselineStore:
    """In-memory baseline store"""
    
    def __init__(self):
        self._baselines: Dict[str, List[Baseline]] = {}
    
    def store(self, baseline: Baseline) -> None:
        """Store a baseline for a pipeline"""
        if baseline.pipeline_id not in self._baselines:
            self._baselines[baseline.pipeline_id] = []
        self._baselines[baseline.pipeline_id].append(baseline)
    
    def get(self, pipeline_id: str) -> List[Baseline]:
        """Get all baselines for a pipeline"""
        return self._baselines.get(pipeline_id, [])
    
    def get_latest(self, pipeline_id: str) -> Optional[Baseline]:
        """Get the most recent baseline for a pipeline"""
        baselines = self.get(pipeline_id)
        if not baselines:
            return None
        
        # Sort by createdAt descending
        return sorted(baselines, key=lambda b: b.created_at, reverse=True)[0]
    
    def clear(self, pipeline_id: str) -> None:
        """Clear all baselines for a pipeline"""
        if pipeline_id in self._baselines:
            del self._baselines[pipeline_id]


def generate_semantic_fingerprint(data: Union[Dict[str, Any], str]) -> str:
    """
    Generate a simple semantic fingerprint (hash-like)
    For MVP, we use a basic hash. In production, this would use proper semantic embedding.
    """
    if isinstance(data, str):
        s = data
    else:
        s = json.dumps(data, sort_keys=True)
    
    # Simple hash for MVP
    hash_value = 0
    for char in s:
        hash_value = ((hash_value << 5) - hash_value) + ord(char)
        hash_value = hash_value & hash_value  # Convert to 32bit integer
    
    return hex(hash_value & 0xFFFFFFFF)[2:]


def normalize_output(data: Union[Dict[str, Any], str]) -> Union[Dict[str, Any], str]:
    """Normalize output for baseline storage"""
    if isinstance(data, str):
        return data.strip()
    
    # Deep clone and sort keys for consistency
    return json.loads(json.dumps(data, sort_keys=True))


# Global baseline store instance
baseline_store = BaselineStore()

