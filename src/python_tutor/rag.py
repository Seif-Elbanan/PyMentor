from __future__ import annotations

import math
import re
from collections import Counter

from .knowledge import Chunk


TOKEN_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class TutorRetriever:
    """Baseline lexical retrieval plus hybrid retrieval and deterministic reranking."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.doc_tokens = [Counter(tokenize(chunk.text)) for chunk in chunks]
        self.document_frequency = Counter()
        for tokens in self.doc_tokens:
            self.document_frequency.update(tokens.keys())

    def baseline(self, query: str, top_k: int = 4) -> list[dict]:
        query_tokens = set(tokenize(query))
        scored = []
        for chunk, tokens in zip(self.chunks, self.doc_tokens):
            score = len(query_tokens.intersection(tokens))
            scored.append((float(score), chunk))
        return self._format(sorted(scored, reverse=True, key=lambda x: x[0])[:top_k])

    def advanced(
        self,
        query: str,
        *,
        topic: str = "",
        difficulty: str = "",
        top_k: int = 4,
    ) -> list[dict]:
        query_terms = tokenize(query)
        query_counts = Counter(query_terms)
        n_docs = max(1, len(self.chunks))
        candidates: list[tuple[float, Chunk]] = []

        for chunk, doc_counts in zip(self.chunks, self.doc_tokens):
            bm25_like = 0.0
            for term, qtf in query_counts.items():
                df = self.document_frequency.get(term, 0)
                idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
                tf = doc_counts.get(term, 0)
                bm25_like += qtf * idf * (tf / (tf + 1.2) if tf else 0)

            phrase_bonus = 0.8 if query.lower() in chunk.text.lower() else 0.0
            topic_bonus = 1.5 if topic and topic.lower() in chunk.topic.lower() else 0.0
            level_bonus = 0.4 if difficulty and difficulty == chunk.difficulty else 0.0
            title_bonus = sum(
                0.35 for term in set(query_terms) if term in tokenize(chunk.section)
            )
            candidates.append(
                (bm25_like + phrase_bonus + topic_bonus + level_bonus + title_bonus, chunk)
            )

        # Reranking rewards concept coverage and concise chunks.
        candidates.sort(reverse=True, key=lambda item: item[0])
        reranked = []
        query_set = set(query_terms)
        for score, chunk in candidates[: max(top_k * 3, 8)]:
            coverage = len(query_set.intersection(tokenize(chunk.text))) / max(1, len(query_set))
            length_penalty = max(0.0, (len(chunk.text.split()) - 150) / 500)
            reranked.append((score + coverage - length_penalty, chunk))
        reranked.sort(reverse=True, key=lambda item: item[0])
        return self._format(reranked[:top_k])

    @staticmethod
    def _format(items: list[tuple[float, Chunk]]) -> list[dict]:
        return [
            {
                "source_id": chunk.chunk_id,
                "title": chunk.title,
                "section": chunk.section,
                "topic": chunk.topic,
                "difficulty": chunk.difficulty,
                "text": chunk.text,
                "score": round(score, 4),
            }
            for score, chunk in items
            if score > 0
        ]
