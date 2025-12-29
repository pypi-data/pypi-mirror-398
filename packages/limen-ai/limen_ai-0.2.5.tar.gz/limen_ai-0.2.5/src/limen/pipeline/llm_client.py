"""Lightweight wrappers for invoking large language models."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, List


CompletionFn = Callable[[str], str]


@dataclass
class LLMClient:
    """Minimal client that delegates completions to a callable."""

    completion_fn: CompletionFn

    def complete(self, prompt: str) -> str:
        return self.completion_fn(prompt)

    @classmethod
    def from_hf_pipeline(
        cls,
        text_generator: Callable[..., list[dict[str, Any]]],
        tokenizer: Any | None = None,
        *,
        generation_kwargs: Optional[Dict[str, Any]] = None,
        strip_prompt: bool = True,
    ) -> "LLMClient":
        """Builds a client around a HuggingFace text-generation pipeline."""

        if generation_kwargs is None:
            generation_kwargs = {}
        else:
            generation_kwargs = dict(generation_kwargs)

        if (
            tokenizer is not None
            and getattr(tokenizer, "eos_token_id", None) is not None
            and "eos_token_id" not in generation_kwargs
        ):
            generation_kwargs["eos_token_id"] = tokenizer.eos_token_id

        def _completion(prompt: str) -> str:
            outputs = text_generator(prompt, **generation_kwargs)
            if not outputs:
                return ""
            generated = outputs[0].get("generated_text", "")
            if strip_prompt and generated.startswith(prompt):
                generated = generated[len(prompt) :]
            return generated.strip()

        return cls(_completion)


class MockLLMClient(LLMClient):
    """Deterministic mock useful for tests and notebooks."""

    def __init__(self, responses: Optional[dict[str, str]] = None):
        self.responses = responses or {}
        super().__init__(self._default_completion)

    def _default_completion(self, prompt: str) -> str:
        for key, value in self.responses.items():
            if key in prompt:
                return value
        # fallback: echo empty JSON structure to avoid crashes
        return self.responses.get("__default__", "[]")


class OpenAIClient(LLMClient):
    """Client for OpenAI-compatible APIs (OpenAI, DeepSeek, Ollama, vLLM)."""

    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        **generation_kwargs,
    ):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self.generation_kwargs = generation_kwargs
        super().__init__(self._openai_completion)

    def _openai_completion(self, prompt: str) -> str:
        try:
            import requests
        except ImportError:
            raise ImportError("Please install 'requests' to use OpenAIClient.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.generation_kwargs.get("temperature", 0.0),
            "max_tokens": self.generation_kwargs.get("max_new_tokens", 512),
        }
        
        response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


class GeminiClient(LLMClient):
    """Client for Google Gemini API."""

    def __init__(self, model_name: str, api_key: Optional[str] = None, **generation_kwargs):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.generation_kwargs = generation_kwargs
        super().__init__(self._gemini_completion)

    def _gemini_completion(self, prompt: str) -> str:
        try:
            import requests
        except ImportError:
            raise ImportError("Please install 'requests' to use GeminiClient.")

        url = f"https://generativelanguage.googleapis.com/v1/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        # Ensure we have a reasonable max_tokens
        max_tokens = self.generation_kwargs.get("max_new_tokens")
        if max_tokens is None:
            max_tokens = 2048
            
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.generation_kwargs.get("temperature", 0.0),
                "maxOutputTokens": int(max_tokens),
                "topP": 0.95,
                "topK": 40,
                "candidateCount": 1,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
        }
        
        # DEBUG: Print payload to verify tokens
        # print(f"[DEBUG] Gemini Payload GenerationConfig: {payload['generationConfig']}")
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 429:
            raise RuntimeError(f"Gemini API Quota Exceeded (429). The model '{self.model_name}' has very low limits. "
                               "Please wait or use 'gemini-1.5-flash'. Details: " + response.text)
        if response.status_code != 200:
            raise RuntimeError(f"Gemini API error ({response.status_code}): {response.text}")
        
        data = response.json()
        if "candidates" not in data or not data["candidates"]:
            if "error" in data:
                raise RuntimeError(f"Gemini API returned error: {data['error']['message']}")
            return ""
        
        candidate = data["candidates"][0]
        
        # Check for finish reason (e.g. SAFETY, RECITATION, etc.)
        if "finishReason" in candidate and candidate["finishReason"] != "STOP":
            print(f"\n[WARNING] Gemini stopped early. Reason: {candidate.get('finishReason')}")
            if candidate.get("finishReason") == "MAX_TOKENS":
                print(f"[DEBUG] Sent maxOutputTokens: {payload['generationConfig'].get('maxOutputTokens')}")
            if "safetyRatings" in candidate:
                print(f"[DEBUG] Safety Ratings: {candidate['safetyRatings']}")
            
        if "content" not in candidate or "parts" not in candidate["content"]:
            return ""
            
        return candidate["content"]["parts"][0]["text"].strip()
