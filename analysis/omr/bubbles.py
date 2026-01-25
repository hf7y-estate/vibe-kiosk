from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class Bubble:
    id: str
    x: float
    y: float
    r: float
    metadata: dict[str, Any]


def load_bubbles(path: str | Path) -> list[Bubble]:
    data = json.loads(Path(path).read_text())
    bubbles_data = data.get("bubbles", data)
    bubbles: list[Bubble] = []
    for idx, entry in enumerate(bubbles_data):
        bubble_id = entry.get("id") or entry.get("label") or f"bubble_{idx}"
        bubbles.append(
            Bubble(
                id=bubble_id,
                x=float(entry["x"]),
                y=float(entry["y"]),
                r=float(entry.get("r", entry.get("radius", 12))),
                metadata={k: v for k, v in entry.items() if k not in {"x", "y", "r", "radius"}},
            )
        )
    return bubbles


def _bubble_mask(shape: tuple[int, int], center: tuple[float, float], radius: float) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    cv2.circle(mask, (int(center[0]), int(center[1])), int(radius), 255, -1)
    return mask


def measure_filledness(binary: np.ndarray, bubble: Bubble, shrink: float = 0.8) -> float:
    radius = bubble.r * shrink
    mask = _bubble_mask(binary.shape[:2], (bubble.x, bubble.y), radius)
    roi = binary[mask == 255]
    if roi.size == 0:
        return 0.0
    return float(np.mean(roi == 0))


def detect_bubbles(binary: np.ndarray, bubbles: list[Bubble]) -> list[dict[str, Any]]:
    results = []
    for bubble in bubbles:
        filledness = measure_filledness(binary, bubble)
        results.append(
            {
                "id": bubble.id,
                "x": bubble.x,
                "y": bubble.y,
                "filledness": filledness,
                **bubble.metadata,
            }
        )
    return results


def draw_bubbles(image: np.ndarray, bubbles: list[Bubble], filledness: dict[str, float]) -> np.ndarray:
    overlay = image.copy()
    for bubble in bubbles:
        value = filledness.get(bubble.id, 0.0)
        color = (0, 255, 0) if value > 0.5 else (0, 165, 255)
        cv2.circle(overlay, (int(bubble.x), int(bubble.y)), int(bubble.r), color, 2)
        cv2.putText(
            overlay,
            f"{value:.2f}",
            (int(bubble.x + bubble.r), int(bubble.y)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            color,
            1,
        )
    return overlay
