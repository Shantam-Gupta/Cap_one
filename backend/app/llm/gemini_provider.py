"""Google Gemini LLM Provider Implementation."""
import json
import os
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.llm.base import BaseLLMProvider, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Integrates Google Gemini API using native REST v1beta."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY or settings.LLM_API_KEY
        if model:
            self.model = model
        elif settings.LLM_MODEL and "gemini" in settings.LLM_MODEL.lower():
            self.model = settings.LLM_MODEL
        else:
            self.model = "gemini-3.6-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_mime_type: Optional[str] = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Provide an API key in .env or environment.")

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        body: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        if response_mime_type:
            body["generationConfig"]["responseMimeType"] = response_mime_type

        if system_prompt:
            body["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            last_err = None
            for attempt in range(3):
                try:
                    resp = await client.post(url, json=body)
                    if resp.status_code in (503, 429):
                        if attempt == 2:
                            raise RuntimeError(f"Rate limited or unavailable after 3 attempts. Status: {resp.status_code}")
                        import asyncio
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise RuntimeError("Gemini API returned no candidates.")
                    # Guard against empty content (e.g. finishReason=MAX_TOKENS returns content: {})
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text_content = parts[0].get("text", "") if parts else ""
                    usage = data.get("usageMetadata", {})
                    total_tokens = usage.get("totalTokenCount", 0)
                    return LLMResponse(content=text_content, model=self.model, tokens_used=total_tokens, raw=data)
                except Exception as e:
                    last_err = e
                    import asyncio
                    await asyncio.sleep(2 * (attempt + 1))
            if last_err:
                raise last_err
            raise RuntimeError("Failed to obtain response from Gemini API.")

    async def complete_structured(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        system = (system_prompt or "") + "\nYou MUST return strictly a valid JSON object."
        res = await self.complete(
            prompt,
            system_prompt=system,
            temperature=temperature,
            response_mime_type="application/json",
        )
        try:
            clean_text = res.content.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("\n", 1)[-1]
                if clean_text.endswith("```"):
                    clean_text = clean_text.rsplit("```", 1)[0]
            res.structured = json.loads(clean_text.strip())
        except Exception:
            res.structured = {"raw_output": res.content}
        return res
