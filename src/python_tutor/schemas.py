from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel, Field


Ability = Literal["beginner", "intermediate", "advanced"]
Intent = Literal["learn", "quiz", "quiz_answer", "answer", "progress", "out_of_scope"]


class Source(BaseModel):
    source_id: str
    title: str
    section: str
    score: float = 0.0


class QuizQuestion(BaseModel):
    question: str
    topic: str
    expected_concepts: list[str]
    difficulty: Ability
    hint: str


class TutorResponse(BaseModel):
    response: str
    intent: Intent
    sources: list[Source] = Field(default_factory=list)
    guardrails_triggered: list[str] = Field(default_factory=list)
    next_action: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class TutorState(TypedDict, total=False):
    student_id: str
    session_id: str
    message: str
    intent: Intent
    topic: str
    student_profile: dict
    session_history: list[dict]
    retrieved_contexts: list[dict]
    guardrail_flags: list[str]
    draft_response: str
    final_response: str
    confidence: float
    context_sufficient: bool
    next_action: str
    quiz_payload: dict
    pending_quiz: bool
    pending_quiz_topic: str
    pending_quiz_question: str
