from __future__ import annotations

import random
import textwrap
from typing import Iterable, Sequence


CONTENT_TYPES = ("python", "java", "markdown", "skill")


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
    sample_id = f"py_{rng.getrandbits(48):012x}"
    parts = [f"# generated sample: {sample_id}", _clean_block(rng.choice(HEADERS))]

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


JAVA_BLOCKS = [
    """
    static String normalize(String value) {
        return value == null ? "" : value.trim().replaceAll("\\\\s+", " ");
    }
""",
    """
    static List<String> filterNonBlank(List<String> values) {
        List<String> result = new ArrayList<>();
        for (String value : values) {
            String normalized = normalize(value);
            if (!normalized.isEmpty()) {
                result.add(normalized);
            }
        }
        return result;
    }
""",
    """
    static Map<String, Integer> countWords(List<String> values) {
        Map<String, Integer> counts = new TreeMap<>();
        for (String value : values) {
            String key = normalize(value).toLowerCase(Locale.ROOT);
            if (key.isEmpty()) {
                continue;
            }
            counts.put(key, counts.getOrDefault(key, 0) + 1);
        }
        return counts;
    }
""",
    """
    static double movingAverage(List<Integer> values, int window) {
        if (window <= 0) {
            throw new IllegalArgumentException("window must be positive");
        }
        if (values.isEmpty()) {
            return 0.0;
        }

        int start = Math.max(0, values.size() - window);
        int total = 0;
        for (int index = start; index < values.size(); index++) {
            total += values.get(index);
        }
        return total / (double) (values.size() - start);
    }
""",
    """
    static List<String> labelsForScores(List<Integer> scores) {
        List<String> labels = new ArrayList<>();
        for (int score : scores) {
            if (score >= 85) {
                labels.add("strong");
            } else if (score >= 60) {
                labels.add("ok");
            } else {
                labels.add("review");
            }
        }
        return labels;
    }
""",
    """
    static String renderSummary(Map<String, Integer> counts) {
        StringBuilder builder = new StringBuilder();
        builder.append("Summary\\n");
        for (Map.Entry<String, Integer> entry : counts.entrySet()) {
            builder.append("- ")
                .append(entry.getKey())
                .append(": ")
                .append(entry.getValue())
                .append("\\n");
        }
        return builder.toString();
    }
""",
]


def make_java_sample(
    rng: random.Random,
    min_lines: int = 60,
    max_lines: int = 120,
) -> str:
    _validate_line_range(min_lines, max_lines)
    target_lines = rng.randint(min_lines, max_lines)
    sample_id = f"{rng.getrandbits(32):08x}"
    class_name = f"WorkSample{sample_id[0].upper()}{sample_id[1:]}"
    parts = [
        "import java.util.ArrayList;",
        "import java.util.Arrays;",
        "import java.util.List;",
        "import java.util.Locale;",
        "import java.util.Map;",
        "import java.util.TreeMap;",
        "",
        f"public class {class_name} {{",
        f"    private static final String SAMPLE_ID = \"java_{sample_id}\";",
        "",
        "    public static void main(String[] args) {",
        "        List<String> words = Arrays.asList(\"alpha\", \"beta\", \"alpha\", \"gamma\");",
        "        List<Integer> scores = Arrays.asList(88, 72, 54, 91);",
        "        Map<String, Integer> counts = countWords(words);",
        "        System.out.println(SAMPLE_ID);",
        "        System.out.println(renderSummary(counts));",
        "        System.out.println(labelsForScores(scores));",
        "        System.out.println(movingAverage(scores, 3));",
        "    }",
    ]

    required_blocks = [JAVA_BLOCKS[index] for index in (0, 2, 3, 4, 5)]
    optional_blocks = [JAVA_BLOCKS[index] for index in (1,)]

    for block in required_blocks:
        parts.extend(["", _clean_block(block)])

    rng.shuffle(optional_blocks)
    for block in optional_blocks:
        if _line_count(parts + ["}"]) >= target_lines:
            break
        parts.extend(["", _clean_block(block)])

    parts.append("}")
    return "\n".join(parts).rstrip() + "\n"


MARKDOWN_TOPICS = [
    "parser edge cases",
    "test data cleanup",
    "local automation checks",
    "release checklist",
    "error handling audit",
    "configuration notes",
]


def make_markdown_sample(
    rng: random.Random,
    min_lines: int = 50,
    max_lines: int = 110,
) -> str:
    _validate_line_range(min_lines, max_lines)
    sample_id = f"md_{rng.getrandbits(48):012x}"
    target_lines = rng.randint(min_lines, max_lines)
    topic = rng.choice(MARKDOWN_TOPICS)
    sections = [
        f"# Notes: {topic.title()}",
        "",
        f"Sample id: `{sample_id}`",
        "",
        "## Context",
        "",
        "The goal is to keep the work small enough to review while still covering the main path and the failure path.",
        "",
        "## Checklist",
        "",
    ]

    tasks = [
        "Confirm the input shape before adding new branches.",
        "Keep the fixture names close to the behavior being tested.",
        "Record the default values near the option parser.",
        "Prefer clear errors over silent fallbacks.",
        "Run the smallest useful verification command first.",
        "Write down any assumption that affects user-facing behavior.",
        "Check that generated files can be deleted and recreated.",
        "Review line endings on Windows before publishing.",
    ]
    rng.shuffle(tasks)
    for task in tasks:
        sections.append(f"- [ ] {task}")

    paragraphs = [
        "A narrow test is useful when it explains exactly which branch changed and why the branch matters.",
        "Generated content should include enough variation to catch accidental assumptions in downstream tooling.",
        "The browser portion of the session should stay on passive pages unless an operator explicitly chooses otherwise.",
        "Long runs need visible controls so the operator can pause, resume, or stop without closing the terminal.",
    ]
    while len(sections) < target_lines:
        heading = rng.choice(["Implementation", "Validation", "Follow-up", "Risk Notes"])
        sections.extend(["", f"## {heading}", "", rng.choice(paragraphs)])
        sections.extend(["", "```text", f"trace={rng.getrandbits(32):08x}", "status=reviewed", "```"])

    return "\n".join(sections[:target_lines]).rstrip() + "\n"


def make_skill_sample(
    rng: random.Random,
    min_lines: int = 50,
    max_lines: int = 110,
) -> str:
    _validate_line_range(min_lines, max_lines)
    sample_id = f"skill_{rng.getrandbits(48):012x}"
    target_lines = rng.randint(min_lines, max_lines)
    skill_name = rng.choice(["local-review", "fixture-builder", "release-notes", "automation-check"])
    lines = [
        "---",
        f"name: {skill_name}-{sample_id[-4:]}",
        "description: Draft skill notes for a local coding workflow.",
        "---",
        "",
        f"# {skill_name.title()} Skill",
        "",
        f"Sample id: `{sample_id}`",
        "",
        "## When To Use",
        "",
        "- Use this when the task has repeated local checks.",
        "- Use this when the expected output needs a consistent shape.",
        "- Skip this when a direct one-off command is clearer.",
        "",
        "## Workflow",
        "",
    ]

    steps = [
        "Inspect the current files and identify the smallest relevant surface.",
        "Run the cheap validation command before editing behavior.",
        "Make the scoped change and avoid unrelated cleanup.",
        "Repeat validation after the edit.",
        "Summarize the result with exact commands and file paths.",
    ]
    for index, step in enumerate(steps, start=1):
        lines.append(f"{index}. {step}")

    notes = [
        "Prefer repository conventions over a new abstraction.",
        "Keep generated examples deterministic only when a seed is provided.",
        "Avoid page actions that submit forms or trigger account changes.",
        "Store reusable commands in the README when they are operator-facing.",
    ]
    while len(lines) < target_lines:
        lines.extend(["", "## Notes", ""])
        for note in rng.sample(notes, k=min(3, len(notes))):
            lines.append(f"- {note}")
        lines.extend(["", "```powershell", f"# check {rng.getrandbits(24):06x}", "python -m compileall human_typing_coder", "```"])

    return "\n".join(lines[:target_lines]).rstrip() + "\n"


def make_content_sample(
    rng: random.Random,
    content_types: Sequence[str],
    min_lines: int = 60,
    max_lines: int = 120,
) -> tuple[str, str]:
    if not content_types:
        raise ValueError("content_types cannot be empty")

    content_type = rng.choice(list(content_types))
    if content_type == "python":
        return content_type, make_python_sample(rng, min_lines=min_lines, max_lines=max_lines)
    if content_type == "java":
        return content_type, make_java_sample(rng, min_lines=min_lines, max_lines=max_lines)
    if content_type == "markdown":
        return content_type, make_markdown_sample(rng, min_lines=min_lines, max_lines=max_lines)
    if content_type == "skill":
        return content_type, make_skill_sample(rng, min_lines=min_lines, max_lines=max_lines)
    raise ValueError(f"unsupported content type: {content_type}")


def _validate_line_range(min_lines: int, max_lines: int) -> None:
    if min_lines < 1:
        raise ValueError("min_lines must be at least 1")
    if max_lines < min_lines:
        raise ValueError("max_lines must be greater than or equal to min_lines")
