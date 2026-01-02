"""
Cloud control plane client

Responsibilities:
- license verification
- feature flags (FORMAT vs CONTENT)
- usage tracking
"""

from typing import Dict, List, Optional
import aiohttp
from .types import DriftGuardConfig


class LicenseResponse:
    """License verification response"""
    def __init__(self, valid: bool, plan: Optional[str] = None, features: Optional[List[str]] = None):
        self.valid = valid
        self.plan = plan
        self.features = features or []


async def verify_license(config: DriftGuardConfig) -> LicenseResponse:
    """Verify license with cloud control plane"""
    endpoint = config.cloud_endpoint or "https://llm-drift-ctl-cloud.fly.dev"
    api_key = config.api_key
    
    if not api_key:
        # FORMAT mode can work offline
        return LicenseResponse(
            valid=True,
            plan="offline",
            features=["FORMAT"]
        )
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/license/verify",
                json={"apiKey": api_key},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    return LicenseResponse(valid=False)
                
                data = await response.json()
                return LicenseResponse(
                    valid=data.get("valid", False),
                    plan=data.get("plan"),
                    features=data.get("features", [])
                )
    except Exception as error:
        # Network error - allow offline mode (FORMAT only)
        print(f"Warning: Cloud license check failed, falling back to offline mode: {error}")
        return LicenseResponse(
            valid=True,
            plan="offline",
            features=["FORMAT"]
        )

