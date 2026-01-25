from __future__ import annotations

from collections import defaultdict
from typing import Any


def score_likert(
    bubbles: list[dict[str, Any]],
    threshold: float = 0.5,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unscored: list[dict[str, Any]] = []

    for bubble in bubbles:
        question = bubble.get("question")
        if question is None:
            unscored.append(bubble)
            continue
        grouped[str(question)].append(bubble)

    responses: dict[str, int | None] = {}
    issues: dict[str, str] = {}

    for question, entries in grouped.items():
        filled = [b for b in entries if b.get("filledness", 0.0) >= threshold]
        if len(filled) == 1:
            responses[question] = int(filled[0].get("value"))
        elif len(filled) > 1:
            responses[question] = None
            issues[question] = "ambiguous"
        else:
            responses[question] = None
            issues[question] = "empty"

    return {
        "responses": responses,
        "issues": issues,
        "unscored": unscored,
    }
