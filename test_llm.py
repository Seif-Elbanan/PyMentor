import pytest

from python_tutor.llm import LLMError, clean_ollama_content


def test_qwen_thinking_is_removed():
    raw = "private reasoning here</think>\n\nFinal learner-facing answer."
    assert clean_ollama_content(raw) == "Final learner-facing answer."


def test_truncated_qwen_reasoning_fails_closed():
    with pytest.raises(LLMError):
        clean_ollama_content("We are teaching a learner and need to plan the response.")


@pytest.mark.parametrize(
    "content",
    [
        "We are given a student question and should decide how to respond.",
        "We are creating one beginner question about variables.",
        "The task is to produce a concise tutoring answer.",
        "Student profile: beginner who needs an explanation.",
    ],
)
def test_additional_reasoning_signatures_fail_closed(content):
    with pytest.raises(LLMError):
        clean_ollama_content(content)
