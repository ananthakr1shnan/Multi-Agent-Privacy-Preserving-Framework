"""
Groq API client for LLM inference.
Provides async interface to Llama 3 with retry logic and error handling.
"""
import httpx
import asyncio
from typing import Optional, Dict, Any
from app.core.config import settings


class GroqClient:
    """Async client for Groq API"""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.api_base = settings.groq_api_base
        self.model = settings.groq_model
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt to define agent persona
            temperature: Sampling temperature (default from settings)
            max_tokens: Max tokens to generate (default from settings)
            
        Returns:
            Dict with 'content', 'tokens_used', and 'finish_reason'
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or settings.temperature,
            "max_tokens": max_tokens or settings.max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.api_base}/chat/completions",
                        json=payload,
                        headers=headers
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    return {
                        "content": data["choices"][0]["message"]["content"],
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                        "finish_reason": data["choices"][0].get("finish_reason", "stop")
                    }
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                raise Exception(f"Groq API error: {e.response.text}")
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise Exception(f"LLM generation failed: {str(e)}")
        
        raise Exception("Max retries exceeded for LLM API")


# Global client instance
groq_client = GroqClient()
