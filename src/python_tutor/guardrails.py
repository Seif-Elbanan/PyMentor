from __future__ import annotations

import re
from dataclasses import dataclass, field


INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior) instructions",
    r"reveal (your|the) (system|developer) prompt",
    r"developer mode",
    r"act as .* without restrictions",
]
DIRECT_ANSWER_PATTERNS = [
    r"(do|solve|finish|write) (my|this) (homework|assignment|lab)",
    r"give me (the )?(full|complete|final) (answer|solution|code)",
    r"just (send|give|write) (the )?(answer|code|solution)",
    r"just (send|give|write) (the )?(full|complete|final) (answer|code|solution)",
]
PYTHON_TERMS = {
    "python", "variable", "loop", "function", "list", "tuple", "dictionary",
    "dict", "set", "class", "object", "exception", "file", "recursion",
    "algorithm", "code", "syntax", "range", "print", "input", "string",
    "integer", "float", "boolean", "module", "import", "comprehension",
    "if", "elif", "else", "return", "none", "keyerror", "valueerror",
    "argument", "parameter", "mutable", "default", "inheritance", "composition",
}


@dataclass
class GuardrailResult:
    safe_text: str
    flags: list[str] = field(default_factory=list)
    blocked: bool = False


def input_guardrail(text: str, max_chars: int = 4000) -> GuardrailResult:
    normalized = text.strip()
    flags: list[str] = []
    if len(normalized) > max_chars:
        normalized = normalized[:max_chars]
        flags.append("input_truncated")
    if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in INJECTION_PATTERNS):
        flags.append("prompt_injection")
        return GuardrailResult(
            safe_text="The learner submitted an instruction-manipulation attempt.",
            flags=flags,
            blocked=True,
        )
    return GuardrailResult(safe_text=normalized, flags=flags)


def asks_for_direct_solution(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in DIRECT_ANSWER_PATTERNS)


def likely_in_scope(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in PYTHON_TERMS)


def output_guardrail(text: str) -> tuple[str, list[str]]:
    flags: list[str] = []
    # Basic secret and prompt leakage protection.
    text = re.sub(r"gsk_[A-Za-z0-9_-]+", "[REDACTED_API_KEY]", text)
    if "[REDACTED_API_KEY]" in text:
        flags.append("secret_redacted")
    if re.search(r"(system prompt|developer message)\s*:", text, re.IGNORECASE):
        flags.append("possible_prompt_leakage")
        return (
            "I cannot expose private instructions. I can still help you learn the Python concept.",
            flags,
        )
    return text, flags
