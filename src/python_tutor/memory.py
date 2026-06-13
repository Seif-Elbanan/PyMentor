from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


PENDING_QUIZ_TTL_SECONDS = 3600  # Stale quiz questions expire after 1 hour.


class TutorMemory:
    """SQLite session, student-profile, quiz, and misconception memory."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    ability TEXT NOT NULL DEFAULT 'beginner',
                    goals TEXT NOT NULL DEFAULT '[]',
                    mastered_topics TEXT NOT NULL DEFAULT '[]',
                    struggling_topics TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    score REAL NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS misconceptions (
                    student_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    misconception TEXT NOT NULL,
                    occurrences INTEGER NOT NULL DEFAULT 1,
                    last_seen TEXT NOT NULL,
                    PRIMARY KEY (student_id, topic, misconception)
                );
                CREATE TABLE IF NOT EXISTS quiz_state (
                    student_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    question TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (student_id, session_id)
                );
                """
            )

    def profile(self, student_id: str) -> dict:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if row is None:
                now = _now()
                db.execute(
                    "INSERT INTO students(student_id, updated_at) VALUES (?, ?)",
                    (student_id, now),
                )
                return {
                    "student_id": student_id,
                    "ability": "beginner",
                    "goals": [],
                    "mastered_topics": [],
                    "struggling_topics": [],
                    "misconceptions": [],
                    "quiz_history": [],
                }
            misconceptions = [
                dict(item)
                for item in db.execute(
                    "SELECT topic, misconception, occurrences FROM misconceptions "
                    "WHERE student_id = ? ORDER BY occurrences DESC",
                    (student_id,),
                ).fetchall()
            ]
            quizzes = [
                dict(item)
                for item in db.execute(
                    "SELECT topic, score, created_at FROM quiz_attempts "
                    "WHERE student_id = ? ORDER BY id DESC LIMIT 10",
                    (student_id,),
                ).fetchall()
            ]
            return {
                "student_id": student_id,
                "ability": row["ability"],
                "goals": json.loads(row["goals"]),
                "mastered_topics": json.loads(row["mastered_topics"]),
                "struggling_topics": json.loads(row["struggling_topics"]),
                "misconceptions": misconceptions,
                "quiz_history": quizzes,
            }

    def history(self, student_id: str, session_id: str, limit: int = 12) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT role, content FROM messages WHERE student_id = ? AND session_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (student_id, session_id, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def add_message(
        self, student_id: str, session_id: str, role: str, content: str
    ) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO messages(session_id, student_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, student_id, role, content, _now()),
            )

    def get_pending_quiz(self, student_id: str, session_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT topic, question, updated_at FROM quiz_state "
                "WHERE student_id = ? AND session_id = ?",
                (student_id, session_id),
            ).fetchone()
            if row is None:
                return None
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(row["updated_at"])).total_seconds()
            if age > PENDING_QUIZ_TTL_SECONDS:
                db.execute(
                    "DELETE FROM quiz_state WHERE student_id = ? AND session_id = ?",
                    (student_id, session_id),
                )
                return None
        return {"topic": row["topic"], "question": row["question"]}

    def set_pending_quiz(self, student_id: str, session_id: str, topic: str, question: str) -> None:
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO quiz_state(student_id, session_id, topic, question, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(student_id, session_id)
                DO UPDATE SET topic = excluded.topic, question = excluded.question,
                    updated_at = excluded.updated_at
                """,
                (student_id, session_id, topic, question, _now()),
            )

    def clear_pending_quiz(self, student_id: str, session_id: str) -> None:
        with self._connect() as db:
            db.execute(
                "DELETE FROM quiz_state WHERE student_id = ? AND session_id = ?",
                (student_id, session_id),
            )

    def update_profile_from_quiz_history(self, student_id: str) -> None:
        """Deterministically recompute mastered/struggling topics from quiz history.

        Rule: per-topic average score >= 0.7 => mastered, < 0.4 => struggling.
        Topics in between are left unclassified (not enough evidence either way).
        No LLM is involved; this keeps ability/progress fully explainable.
        """
        with self._connect() as db:
            rows = db.execute(
                "SELECT topic, AVG(score) as avg_score, COUNT(*) as attempts "
                "FROM quiz_attempts WHERE student_id = ? GROUP BY topic",
                (student_id,),
            ).fetchall()
        mastered, struggling = [], []
        for row in rows:
            if row["avg_score"] >= 0.7:
                mastered.append(row["topic"])
            elif row["avg_score"] < 0.4:
                struggling.append(row["topic"])
        # Ability bump: 3+ mastered topics moves beginner -> intermediate -> advanced.
        current = self.profile(student_id)
        ability = current["ability"]
        if ability == "beginner" and len(mastered) >= 3:
            ability = "intermediate"
        elif ability == "intermediate" and len(mastered) >= 6:
            ability = "advanced"
        self.update_profile(
            student_id,
            ability=ability,
            mastered_topics=mastered,
            struggling_topics=struggling,
        )

    def record_misconception(
        self, student_id: str, topic: str, misconception: str
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO misconceptions(student_id, topic, misconception, last_seen)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(student_id, topic, misconception)
                DO UPDATE SET occurrences = occurrences + 1, last_seen = excluded.last_seen
                """,
                (student_id, topic, misconception, _now()),
            )

    def record_quiz(
        self, student_id: str, topic: str, score: float, details: dict
    ) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO quiz_attempts(student_id, topic, score, details, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (student_id, topic, score, json.dumps(details), _now()),
            )

    def update_profile(
        self,
        student_id: str,
        *,
        ability: str | None = None,
        mastered_topics: list[str] | None = None,
        struggling_topics: list[str] | None = None,
    ) -> None:
        current = self.profile(student_id)
        with self._connect() as db:
            db.execute(
                """
                UPDATE students
                SET ability = ?, mastered_topics = ?, struggling_topics = ?, updated_at = ?
                WHERE student_id = ?
                """,
                (
                    ability or current["ability"],
                    json.dumps(mastered_topics or current["mastered_topics"]),
                    json.dumps(struggling_topics or current["struggling_topics"]),
                    _now(),
                    student_id,
                ),
            )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
