from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUBRIC = {
    "range_stop": {
        "accepted": ("3",),
        "misconception": "range includes the stop value",
        "bad_signals": ("4", "includes"),
    },
    "print_return": {
        "accepted": ("return", "caller"),
        "misconception": "print and return have the same purpose",
        "bad_signals": ("print gives", "same"),
    },
    "assignment": {
        "accepted": ("assign", "compare"),
        "misconception": "assignment and equality are interchangeable",
        "bad_signals": ("same", "both compare"),
    },
}


def grade(answer: str, item: dict) -> bool:
    lowered = answer.lower()
    return all(term in lowered for term in item["accepted"])


def detect_misconception(answer: str, item: dict) -> bool:
    lowered = answer.lower()
    return any(signal in lowered for signal in item["bad_signals"])


def evaluate() -> dict:
    personas = json.loads((ROOT / "evaluation/personas.json").read_text())
    rows = []
    detection_true = 0
    detection_total = 0
    for persona in personas:
        pre_correct = 0
        post_correct = 0
        misconceptions = []
        for question_id, item in RUBRIC.items():
            pre_answer = persona["pre_answers"][question_id]
            post_answer = persona["post_answers"][question_id]
            pre_ok = grade(pre_answer, item)
            post_ok = grade(post_answer, item)
            pre_correct += int(pre_ok)
            post_correct += int(post_ok)

            expected_detection = not pre_ok
            detected = detect_misconception(pre_answer, item)
            detection_true += int(detected == expected_detection)
            detection_total += 1
            if detected:
                misconceptions.append(item["misconception"])

        question_count = len(RUBRIC)
        pre_score = pre_correct / question_count
        post_score = post_correct / question_count
        rows.append(
            {
                "persona": persona["id"],
                "pre_score": round(pre_score, 3),
                "post_score": round(post_score, 3),
                "delta": round(post_score - pre_score, 3),
                "detected_misconceptions": misconceptions,
            }
        )
    return {
        "personas": rows,
        "misconception_detection_accuracy": round(
            detection_true / max(1, detection_total), 3
        ),
        "method": (
            "Controlled labeled answers measure whether the assessment layer recognizes "
            "three course misconceptions before and after targeted tutoring."
        ),
    }


if __name__ == "__main__":
    output = evaluate()
    path = ROOT / "evaluation/results/learning_assessment.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
