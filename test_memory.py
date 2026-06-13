from pathlib import Path

from python_tutor.memory import TutorMemory


def test_memory_persists_profile_messages_and_misconceptions(tmp_path: Path):
    memory = TutorMemory(tmp_path / "memory.db")
    profile = memory.profile("student-1")
    assert profile["ability"] == "beginner"

    memory.add_message("student-1", "session-1", "user", "Explain loops")
    memory.record_misconception("student-1", "loops", "range includes stop")
    memory.record_misconception("student-1", "loops", "range includes stop")
    memory.record_quiz("student-1", "loops", 0.5, {"correct": False})

    assert memory.history("student-1", "session-1")[0]["content"] == "Explain loops"
    updated = memory.profile("student-1")
    assert updated["misconceptions"][0]["occurrences"] == 2
    assert updated["quiz_history"][0]["score"] == 0.5
