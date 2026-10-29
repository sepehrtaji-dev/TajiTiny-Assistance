"""Thin, synchronous Ollama client wrapper for Taji 1.1."""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

import ollama

from .. import config
from .prompts import CHAT_SYSTEM_PROMPT


class OllamaError(RuntimeError):
    """Raised when the local model cannot be reached or fails to respond."""


class OllamaClient:
    """Wraps the `ollama` package with Taji's defaults (model, temperature)."""

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = "qwen2.5:3b",
    ) -> None:
        self.host = host or config.OLLAMA_HOST
        self.model = model or config.MODEL_NAME
        self._client = ollama.Client(host=self.host)

    def _options(self, temperature: Optional[float] = None) -> Dict[str, Any]:
        return {
            "temperature": config.DEFAULT_TEMPERATURE if temperature is None else temperature,
            "num_ctx": config.DEFAULT_NUM_CTX,
        }

    def _messages_with_system(
        self, messages: List[Dict[str, str]], system: Optional[str]
    ) -> List[Dict[str, str]]:
        """Forcefully inject the system prompt to ensure the model obeys its identity."""
        prompt = system if system is not None else CHAT_SYSTEM_PROMPT
        
        if prompt:
            if not messages or messages[0].get("role") != "system":
                return [{"role": "system", "content": prompt}] + list(messages)
            else:
                messages[0]["content"] = prompt
                
        return list(messages)

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Run a single, non-streaming completion and return the full response."""
        try:
            return self._client.chat(
                model=self.model,
                messages=self._messages_with_system(messages, system),
                options=self._options(temperature),
            )
        except Exception as exc:
            raise OllamaError(f"model request failed: {exc}") from exc

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[str]:
        """Yield text chunks as the model generates (for a live UI)."""
        try:
            stream = self._client.chat(
                model=self.model,
                messages=self._messages_with_system(messages, system),
                options=self._options(temperature),
                stream=True,
            )
        except Exception as exc:
            raise OllamaError(f"model request failed: {exc}") from exc

        for chunk in stream:
            content = (chunk.get("message") or {}).get("content") or ""
            if content:
                yield content

    def ping(self) -> bool:
        """Return True if the Ollama server is reachable and the model is present."""
        try:
            models = self._client.list()
        except Exception:
            return False
        names = {m.get("name") or m.get("model") for m in (models.get("models") or [])}
        return self.model in names