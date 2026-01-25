from __future__ import annotations

from collections import defaultdict
from typing import Any


def compute_vector(
    bubbles: list[dict[str, Any]],
    threshold: float = 0.5,
) -> dict[str, int | None]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bubble in bubbles:
        dimension = bubble.get("dimension")
        if dimension is None:
            continue
        grouped[str(dimension)].append(bubble)

    vector: dict[str, int | None] = {}
    for dimension, entries in grouped.items():
        best = None
        for bubble in entries:
            if bubble.get("filledness", 0.0) < threshold:
                continue
            if best is None or bubble["filledness"] > best["filledness"]:
                best = bubble
        if best is None:
            vector[dimension] = None
        else:
            vector[dimension] = int(best.get("value"))
    return vector
