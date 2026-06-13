from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    provider: str = os.getenv("LLM_PROVIDER", "auto")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    db_path: Path = Path(os.getenv("TUTOR_DB_PATH", "data/tutor_memory.db"))
    knowledge_path: Path = Path("data/knowledge")
