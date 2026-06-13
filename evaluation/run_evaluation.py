from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from python_tutor.config import Settings
from python_tutor.knowledge import load_chunks
from python_tutor.rag import TutorRetriever, tokenize
from python_tutor.service import TutorService


ROOT = Path(__file__).resolve().parents[1]
PERSONAS = {
    "beginner": "Needs simple language, concrete examples, and frequent checks.",
    "intermediate": "Knows syntax and needs conceptual comparisons and debugging help.",
    "advanced": "Can handle abstractions, design trade-offs, and edge cases.",
}


def retrieval_metrics(results: list[dict], expected_topic: str) -> dict:
    if not results:
        return {"context_precision": 0.0, "context_recall": 0.0}
    expected_forms = {expected_topic.lower(), expected_topic.lower().rstrip("s")}
    matches = []
    for item in results:
        searchable = (
            item["topic"] + " " + item["section"] + " " + item["text"]
        ).lower()
        matches.append(any(form and form in searchable for form in expected_forms))
    return {
        "context_precision": sum(matches) / len(matches),
        "context_recall": float(any(matches)),
    }


def evaluate_retrieval(cases: list[dict]) -> dict:
    retriever = TutorRetriever(load_chunks(ROOT / "data/knowledge"))
    rows = []
    for case in cases:
        if "expected_topic" not in case:
            continue
        baseline = retriever.baseline(case["message"], top_k=4)
        advanced = retriever.advanced(
            case["message"],
            topic=case["expected_topic"],
            difficulty=case["persona"],
            top_k=4,
        )
        rows.append(
            {
                "id": case["id"],
                "baseline": retrieval_metrics(baseline, case["expected_topic"]),
                "advanced": retrieval_metrics(advanced, case["expected_topic"]),
            }
        )
    return {
        "cases": rows,
        "baseline": _average(rows, "baseline"),
        "advanced": _average(rows, "advanced"),
    }


def evaluate_system(
    cases: list[dict], settings: Settings, checkpoint_path: Path | None = None
) -> dict:
    service = TutorService(settings)
    rows = []
    for case in cases:
        start = time.perf_counter()
        response = service.ask(
            student_id=f"eval-{case['persona']}",
            session_id=f"eval-{case['id']}",
            message=case["message"],
        )
        latency = time.perf_counter() - start
        expected_guardrail = case.get("expected_guardrail")
        expected_intent = case.get("expected_intent")
        rows.append(
            {
                "id": case["id"],
                "category": case["category"],
                "latency_seconds": latency,
                "intent": response.intent,
                "guardrails": response.guardrails_triggered,
                "guardrail_pass": (
                    expected_guardrail in response.guardrails_triggered
                    if expected_guardrail
                    else True
                ),
                "intent_pass": response.intent == expected_intent if expected_intent else True,
                "grounded": bool(response.sources) or response.intent in {"out_of_scope", "progress"},
                "response": response.response,
            }
        )
        if checkpoint_path:
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_path.write_text(
                json.dumps(
                    {
                        "provider": service.llm.provider,
                        "completed": len(rows),
                        "cases": rows,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        print(
            f"[{len(rows):02d}/{len(cases):02d}] {case['id']} "
            f"{latency:.2f}s {response.intent}",
            flush=True,
        )
    latencies = sorted(row["latency_seconds"] for row in rows)
    p95_index = min(len(latencies) - 1, int(0.95 * len(latencies)))
    return {
        "provider": service.llm.provider,
        "persona_count": len(PERSONAS),
        "test_count": len(rows),
        "pedagogical_compliance_rate": _rate(rows, "guardrail_pass"),
        "routing_accuracy": _rate(rows, "intent_pass"),
        "grounded_response_rate": _rate(rows, "grounded"),
        "p95_latency_seconds": latencies[p95_index],
        "median_latency_seconds": statistics.median(latencies),
        "cases": rows,
        "note": (
            "Run evaluation/llm_judge.py for model-scored pedagogical compliance and "
            "RAGAS faithfulness after configuring an API provider."
        ),
    }


def _average(rows: list[dict], key: str) -> dict:
    metrics = ("context_precision", "context_recall")
    return {
        metric: sum(row[key][metric] for row in rows) / max(1, len(rows))
        for metric in metrics
    }


def _rate(rows: list[dict], key: str) -> float:
    return sum(bool(row[key]) for row in rows) / max(1, len(rows))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Call Groq/Ollama for all cases.")
    parser.add_argument("--output", default="evaluation/results/latest.json")
    args = parser.parse_args()
    cases = json.loads((ROOT / "evaluation/test_cases.json").read_text())
    report = {"retrieval": evaluate_retrieval(cases)}
    if args.live:
        report["system"] = evaluate_system(
            cases,
            Settings(),
            ROOT / "evaluation/results/live_checkpoint.json",
        )
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
