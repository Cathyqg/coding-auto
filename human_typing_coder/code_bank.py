from __future__ import annotations

import random
import textwrap
from typing import Iterable


BLOCKS = [
    """
def normalize_whitespace(value: str) -> str:
    parts = value.strip().split()
    return " ".join(parts)
""",
    """
def chunked(items: list[str], size: int) -> list[list[str]]:
    if size <= 0:
        raise ValueError("size must be positive")

    chunks: list[list[str]] = []
    for index in range(0, len(items), size):
        chunks.append(items[index:index + size])
    return chunks
""",
    """
def moving_average(values: list[float], window: int) -> list[float]:
    if window <= 0:
        raise ValueError("window must be positive")
    if not values:
        return []

    averages: list[float] = []
    running_total = 0.0
    for index, value in enumerate(values):
        running_total += value
        if index >= window:
            running_total -= values[index - window]
        count = min(index + 1, window)
        averages.append(running_total / count)
    return averages
""",
    """
def parse_key_value_lines(lines: Iterable[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result
""",
    """
def top_counts(values: Iterable[str], limit: int = 5) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for value in values:
        key = normalize_whitespace(value).lower()
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1

    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ordered[:limit]
""",
    """
def clamp(value: float, low: float, high: float) -> float:
    if low > high:
        raise ValueError("low cannot be greater than high")
    return max(low, min(value, high))
""",
    """
def score_labels(scores: Iterable[float]) -> list[str]:
    labels: list[str] = []
    for score in scores:
        safe_score = clamp(score, 0.0, 100.0)
        if safe_score >= 85:
            labels.append("strong")
        elif safe_score >= 60:
            labels.append("ok")
        else:
            labels.append("review")
    return labels
""",
    """
def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid json on line {line_number}") from error
    return rows
""",
    """
def write_report(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    lines = ["name,score,label"]
    for row in rows:
        name = str(row.get("name", "unknown")).replace(",", " ")
        score = float(row.get("score", 0))
        label = score_labels([score])[0]
        lines.append(f"{name},{score:.1f},{label}")
    path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
""",
    """
class Timer:
    def __init__(self) -> None:
        self.started_at: float | None = None
        self.finished_at: float | None = None

    def start(self) -> None:
        self.started_at = time.perf_counter()
        self.finished_at = None

    def stop(self) -> float:
        if self.started_at is None:
            raise RuntimeError("timer was not started")
        self.finished_at = time.perf_counter()
        return self.finished_at - self.started_at
""",
    """
@dataclass
class TaskResult:
    name: str
    score: float
    label: str
    notes: list[str]

    def as_row(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "label": self.label,
            "notes": "; ".join(self.notes),
        }
""",
    """
def build_results(raw_rows: Iterable[dict[str, Any]]) -> list[TaskResult]:
    results: list[TaskResult] = []
    for row in raw_rows:
        name = normalize_whitespace(str(row.get("name", "untitled")))
        score = float(row.get("score", 0.0))
        label = score_labels([score])[0]
        notes = [str(item) for item in row.get("notes", [])]
        results.append(TaskResult(name=name, score=score, label=label, notes=notes))
    return results
""",
    """
def summarize_results(results: Iterable[TaskResult]) -> dict[str, Any]:
    items = list(results)
    if not items:
        return {"count": 0, "average": 0.0, "labels": {}}

    labels: dict[str, int] = {}
    for item in items:
        labels[item.label] = labels.get(item.label, 0) + 1

    average = sum(item.score for item in items) / len(items)
    return {"count": len(items), "average": round(average, 2), "labels": labels}
""",
    """
def demo_rows() -> list[dict[str, Any]]:
    return [
        {"name": "import checks", "score": 88.5, "notes": ["stable"]},
        {"name": "parser tests", "score": 72.0, "notes": ["needs fixtures"]},
        {"name": "edge case audit", "score": 54.5, "notes": ["add coverage"]},
    ]
""",
]


HEADERS = [
    """
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
""",
    """
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
""",
]


FOOTERS = [
    """
def main() -> None:
    rows = demo_rows()
    results = build_results(rows)
    summary = summarize_results(results)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
""",
    """
def main() -> None:
    sample = ["alpha", "beta", "alpha", "gamma", "beta", "alpha"]
    print(top_counts(sample, limit=3))
    print(moving_average([82, 91, 76, 88, 95], window=3))


if __name__ == "__main__":
    main()
""",
]


def _clean_block(block: str) -> str:
    return textwrap.dedent(block).strip("\n")


def _line_count(parts: Iterable[str]) -> int:
    return "\n\n".join(parts).count("\n") + 1


def _has_definition(parts: Iterable[str], marker: str) -> bool:
    return any(marker in part for part in parts)


def _ensure_block(parts: list[str], marker: str, block: str) -> bool:
    if _has_definition(parts, marker):
        return False
    parts.append(_clean_block(block))
    return True


def _ensure_dependencies(parts: list[str], footer: str) -> None:
    while True:
        changed = False
        text = "\n".join(parts + [footer])

        if "demo_rows(" in text:
            changed |= _ensure_block(parts, "def demo_rows", BLOCKS[13])
        if "summarize_results(" in text:
            changed |= _ensure_block(parts, "def summarize_results", BLOCKS[12])
        if "build_results(" in text or "TaskResult(" in text:
            changed |= _ensure_block(parts, "def normalize_whitespace", BLOCKS[0])
            changed |= _ensure_block(parts, "def clamp", BLOCKS[5])
            changed |= _ensure_block(parts, "def score_labels", BLOCKS[6])
            changed |= _ensure_block(parts, "class TaskResult", BLOCKS[10])
            changed |= _ensure_block(parts, "def build_results", BLOCKS[11])
        if "score_labels(" in text:
            changed |= _ensure_block(parts, "def clamp", BLOCKS[5])
            changed |= _ensure_block(parts, "def score_labels", BLOCKS[6])
        if "top_counts(" in text:
            changed |= _ensure_block(parts, "def normalize_whitespace", BLOCKS[0])
            changed |= _ensure_block(parts, "def top_counts", BLOCKS[4])
        if "moving_average(" in text:
            changed |= _ensure_block(parts, "def moving_average", BLOCKS[2])

        if not changed:
            return


def make_python_sample(
    rng: random.Random,
    min_lines: int = 60,
    max_lines: int = 120,
) -> str:
    if min_lines < 1:
        raise ValueError("min_lines must be at least 1")
    if max_lines < min_lines:
        raise ValueError("max_lines must be greater than or equal to min_lines")

    target_lines = rng.randint(min_lines, max_lines)
    parts = [_clean_block(rng.choice(HEADERS))]

    footer = _clean_block(rng.choice(FOOTERS))
    _ensure_dependencies(parts, footer)

    candidates = [
        block
        for block in BLOCKS
        if not _has_definition(parts, _definition_marker(block))
    ]
    rng.shuffle(candidates)

    while candidates and _line_count(parts + [footer]) < target_lines:
        block = candidates.pop()
        marker = _definition_marker(block)
        if _has_definition(parts, marker):
            continue
        parts.append(_clean_block(block))
        _ensure_dependencies(parts, footer)

    parts.append(footer)
    return "\n\n".join(parts).rstrip() + "\n"


def _definition_marker(block: str) -> str:
    cleaned = _clean_block(block)
    for line in cleaned.splitlines():
        if line.startswith("def "):
            return line.split("(", 1)[0]
        if line.startswith("class "):
            return line.split(":", 1)[0]
    if "@dataclass" in cleaned:
        return "class TaskResult"
    return cleaned.splitlines()[0]
