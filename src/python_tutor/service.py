from __future__ import annotations

from .config import Settings
from .graph import TutorGraph
from .knowledge import load_chunks
from .llm import LLMClient
from .memory import TutorMemory
from .rag import TutorRetriever
from .schemas import Source, TutorResponse


class TutorService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        chunks = load_chunks(self.settings.knowledge_path)
        if not chunks:
            raise RuntimeError(f"No knowledge chunks found in {self.settings.knowledge_path}")
        self.memory = TutorMemory(self.settings.db_path)
        self.retriever = TutorRetriever(chunks)
        self.llm = LLMClient(self.settings)
        self.graph = TutorGraph(self.llm, self.retriever, self.memory)

    def ask(self, student_id: str, session_id: str, message: str) -> TutorResponse:
        result = self.graph.app.invoke(
            {
                "student_id": student_id,
                "session_id": session_id,
                "message": message,
            }
        )
        sources = [
            Source(
                source_id=item["source_id"],
                title=item["title"],
                section=item["section"],
                score=item["score"],
            )
            for item in result.get("retrieved_contexts", [])
        ]
        return TutorResponse(
            response=result["final_response"],
            intent=result.get("intent", "learn"),
            sources=sources,
            guardrails_triggered=result.get("guardrail_flags", []),
            next_action=result.get("next_action", ""),
            confidence=result.get("confidence", 0.0),
        )
