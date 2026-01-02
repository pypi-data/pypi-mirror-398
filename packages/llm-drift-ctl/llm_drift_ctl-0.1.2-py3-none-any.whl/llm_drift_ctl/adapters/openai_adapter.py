"""
OpenAI Adapter for llm-drift-ctl

Uses GPT-4o-mini by default for content validation

⚠️ IMPORTANT: You must provide your own OpenAI API key.
llm-drift-ctl never stores or manages API keys.
"""

from typing import Optional, Dict, Any, Union
import aiohttp
from ..types import UserLLM


class OpenAIAdapter(UserLLM):
    """OpenAI Adapter implementing UserLLM interface"""
    
    def __init__(
        self,
        api_key: str,  # ⚠️ YOUR OpenAI API key (required)
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        if not api_key:
            raise ValueError("OpenAI API key is required - you must provide your own API key")
        
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"
        self.base_url = base_url or "https://api.openai.com/v1"
    
    async def generate(
        self,
        prompt: str,
        text: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Union[str, Dict[str, Any]]:
        """Generate response using OpenAI API"""
        messages = []
        
        # Build the prompt
        system_prompt = prompt
        if json:
            import json as json_lib
            system_prompt += f"\n\nExpected JSON structure:\n{json_lib.dumps(json, indent=2)}"
        
        if text:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            messages.append({
                "role": "user",
                "content": text
            })
        else:
            messages.append({
                "role": "user",
                "content": system_prompt
            })
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.3,  # Lower temperature for consistent validation
                        "max_tokens": 2000
                    }
                ) as response:
                    if response.status != 200:
                        error = await response.json()
                        raise ValueError(f"OpenAI API error: {error}")
                    
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content")
                    
                    if not content:
                        raise ValueError("No content in OpenAI response")
                    
                    # Try to parse as JSON if input.json was provided
                    if json:
                        try:
                            import json as json_lib
                            return json_lib.loads(content)
                        except (json_lib.JSONDecodeError, ValueError):
                            return content
                    
                    return content
        except aiohttp.ClientError as e:
            raise ValueError(f"OpenAI API call failed: {e}")
        except Exception as e:
            raise ValueError(f"OpenAI API error: {e}")

