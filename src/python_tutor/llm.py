from __future__ import annotations

import json
import re
from typing import Any

import requests

from .config import Settings


class LLMError(RuntimeError):
    pass


class LLMClient:
    """Small provider adapter so the graph is not coupled to a vendor SDK."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def provider(self) -> str:
        if self.settings.provider != "auto":
            return self.settings.provider
        return "groq" if self.settings.groq_api_key else "ollama"

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.1,
        json_mode: bool = False,
        timeout: int = 120,
    ) -> str:
        if self.provider == "groq":
            return self._groq(messages, temperature, json_mode, timeout)
        if self.provider == "ollama":
            return self._ollama(messages, temperature, json_mode, timeout)
        raise LLMError(f"Unsupported LLM provider: {self.provider}")

    def json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        raw = self.chat(messages, temperature=temperature, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if not match:
                raise LLMError("Model did not return a JSON object.")
            return json.loads(match.group(0))

    def _groq(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        json_mode: bool,
        timeout: int,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.settings.groq_model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise LLMError(f"Groq request failed: {exc}") from exc
        if not response.ok:
            raise LLMError(f"Groq error {response.status_code}: {response.text[:300]}")
        return response.json()["choices"][0]["message"]["content"]

    def _ollama(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        json_mode: bool,
        timeout: int,
    ) -> str:
        ollama_messages = [dict(message) for message in messages]
        if ollama_messages and ollama_messages[0].get("role") == "system":
            ollama_messages[0]["content"] = (
                "/no_think\n"
                + ollama_messages[0]["content"]
                + "\nReturn only the final answer. Do not expose analysis, planning, or hidden reasoning."
            )
        payload: dict[str, Any] = {
            "model": self.settings.ollama_model,
            "messages": ollama_messages,
            "stream": False,
            "think": False,
            # Qwen 3 can spend most of a local request on hidden reasoning. Keep the
            # budget bounded; graph nodes fall back to grounded deterministic output.
            "options": {
                "temperature": temperature,
                "num_predict": 350 if json_mode else 220,
            },
        }
        if json_mode:
            payload["format"] = "json"
        try:
            response = requests.post(
                f"{self.settings.ollama_base_url.rstrip('/')}/api/chat",
                json=payload,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc
        if not response.ok:
            raise LLMError(f"Ollama error {response.status_code}: {response.text[:300]}")
        return clean_ollama_content(response.json()["message"]["content"])


def clean_ollama_content(content: str) -> str:
    content = content.strip()
    if "</think>" in content:
        content = content.rsplit("</think>", 1)[1].strip()
    lowered = content.lower()
    reasoning_markers = (
        "we are to ",
        "we need to ",
        "we are teaching ",
        "we are given ",
        "we are creating ",
        "we have a ",
        "the task is ",
        "okay, let's ",
        "student profile:",
    )
    if (
        len(content.split()) > 160
        or content.startswith("<think>")
        or lowered.startswith(reasoning_markers)
        or ("\nsteps:" in lowered and len(content.split()) > 80)
    ):
        raise LLMError("Ollama exhausted its output budget before the final answer.")
    return content
