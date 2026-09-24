"""Metric helpers that require caller-supplied ground truth."""
from sentinel.schemas.operations import BenchmarkSummary


def benchmark_record(name: str, summary: BenchmarkSummary, duration_seconds: float, coverage_complete: bool) -> dict[str, object]:
    return {"name": name, "duration_seconds": duration_seconds, "coverage_complete": coverage_complete, **summary.model_dump(mode="json")}


def summarize_benchmark(true_positives: int, false_positives: int, false_negatives: int) -> BenchmarkSummary:
    predicted = true_positives + false_positives
    actual = true_positives + false_negatives
    return BenchmarkSummary(evaluated=max(predicted, actual), true_positives=true_positives, false_positives=false_positives, false_negatives=false_negatives, precision=true_positives / predicted if predicted else None, recall=true_positives / actual if actual else None)
