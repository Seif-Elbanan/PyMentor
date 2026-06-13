from __future__ import annotations

import json
import math
import os
from pathlib import Path

from langchain_ollama import ChatOllama
from ragas.dataset_schema import SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness

from python_tutor.knowledge import load_chunks
from python_tutor.rag import TutorRetriever


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "evaluation/results/ragas_faithfulness.json"


def main() -> None:
    evaluation = json.loads(
        (ROOT / "evaluation/results/latest.json").read_text(encoding="utf-8")
    )
    test_cases = {
        item["id"]: item
        for item in json.loads(
            (ROOT / "evaluation/test_cases.json").read_text(encoding="utf-8")
        )
    }
    retriever = TutorRetriever(load_chunks(ROOT / "data/knowledge"))
    llm = LangchainLLMWrapper(
        ChatOllama(
            model="qwen3:4b",
            base_url="http://127.0.0.1:11434",
            temperature=0,
            reasoning=False,
            format="json",
            num_predict=1000,
        )
    )
    metric = Faithfulness(llm=llm, max_retries=2)

    saved = {"provider": "ollama/qwen3:4b", "format_version": 2, "cases": []}
    if RESULT_PATH.exists():
        previous = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        if previous.get("format_version") == 2:
            saved = previous
    completed = {
        item["id"]
        for item in saved["cases"]
        if isinstance(item.get("score"), (int, float))
        and not math.isnan(item["score"])
    }

    # Faithfulness applies to generated explanations backed by retrieved course material.
    targets = [
        item
        for item in evaluation["system"]["cases"]
        if item["category"] in {"learn", "edge", "withholding"}
        and item["grounded"]
        and item["id"] in test_cases
    ]
    limit = int(os.getenv("RAGAS_LIMIT", "0"))
    if limit:
        targets = targets[:limit]
    for result in targets:
        if result["id"] in completed:
            continue
        case = test_cases[result["id"]]
        contexts = retriever.advanced(
            case["message"],
            topic=case.get("expected_topic", ""),
            difficulty=case["persona"],
            top_k=4,
        )
        sample = SingleTurnSample(
            user_input=case["message"],
            response=result["response"],
            retrieved_contexts=[item["text"] for item in contexts],
        )
        try:
            score = float(metric.single_turn_score(sample))
            error = ""
        except Exception as exc:
            score = math.nan
            error = str(exc)
        saved["cases"] = [
            item for item in saved["cases"] if item["id"] != result["id"]
        ]
        saved["cases"].append({"id": result["id"], "score": score, "error": error})
        valid = [
            item["score"]
            for item in saved["cases"]
            if isinstance(item["score"], (int, float))
            and not math.isnan(item["score"])
        ]
        saved["faithfulness"] = sum(valid) / len(valid) if valid else None
        saved["scored_cases"] = len(valid)
        saved["attempted_cases"] = len(saved["cases"])
        RESULT_PATH.write_text(json.dumps(saved, indent=2), encoding="utf-8")
        print(result["id"], score, error[:120], flush=True)

    print(json.dumps(saved, indent=2))


if __name__ == "__main__":
    main()
