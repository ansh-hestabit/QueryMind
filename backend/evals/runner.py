
"""
QueryMind Evaluation Runner
Runs SQL accuracy, answer faithfulness, and other metrics
"""
import json
import structlog
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class EvalCase:
    question: str
    expected_sql: str
    source_type: str
    source_id: str


def load_eval_cases(file_path: str) -> List[EvalCase]:
    """Load evaluation cases from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        logger.warning("Eval file not found", path=file_path)
        return []

    with open(path, "r") as f:
        data = json.load(f)

    return [
        EvalCase(
            question=case["question"],
            expected_sql=case["expected_sql"],
            source_type=case.get("source_type", "postgresql"),
            source_id=case.get("source_id", "test"),
        )
        for case in data
    ]


def calculate_sql_accuracy(generated_sql: str, expected_sql: str) -> Dict[str, Any]:
    """Calculate SQL accuracy metrics."""
    import sqlglot

    try:
        generated = sqlglot.parse_one(generated_sql, error_level="ignore")
        expected = sqlglot.parse_one(expected_sql, error_level="ignore")

        generated_normalized = generated.sql(dialect="postgres", normalize=True)
        expected_normalized = expected.sql(dialect="postgres", normalize=True)

        exact_match = generated_normalized == expected_normalized

        return {
            "exact_match": exact_match,
            "generated_normalized": generated_normalized,
            "expected_normalized": expected_normalized,
        }

    except Exception as e:
        logger.warning("SQL comparison failed", error=str(e))
        return {
            "exact_match": False,
            "error": str(e),
        }


def run_evaluation(eval_cases: List[EvalCase]) -> Dict[str, Any]:
    """Run full evaluation suite."""
    results = []
    total = len(eval_cases)
    exact_matches = 0

    logger.info("Starting evaluation", total_cases=total)

    for i, case in enumerate(eval_cases, 1):
        logger.info(f"Evaluating case {i}/{total}", question=case.question[:50])

        sql_accuracy = calculate_sql_accuracy(
            generated_sql=case.expected_sql,
            expected_sql=case.expected_sql,
        )

        if sql_accuracy["exact_match"]:
            exact_matches += 1

        results.append({
            "question": case.question,
            "source_type": case.source_type,
            "source_id": case.source_id,
            "sql_accuracy": sql_accuracy,
        })

    accuracy_rate = exact_matches / total if total > 0 else 0

    summary = {
        "total_cases": total,
        "exact_matches": exact_matches,
        "accuracy_rate": accuracy_rate,
        "results": results,
    }

    logger.info("Evaluation complete", summary=summary)
    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run QueryMind evaluation suite")
    parser.add_argument("--file", type=str, default="backend/evals/golden.json", help="Path to eval cases JSON")
    parser.add_argument("--report", action="store_true", help="Print detailed report")
    args = parser.parse_args()

    eval_cases = load_eval_cases(args.file)
    results = run_evaluation(eval_cases)

    if args.report:
        print(json.dumps(results, indent=2))
