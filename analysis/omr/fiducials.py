from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


@dataclass(frozen=True)
class FiducialTargets:
    points: dict[str, tuple[float, float]]
    page_size: tuple[int, int] | None = None


def load_fiducial_targets(path: str | Path) -> FiducialTargets:
    data = json.loads(Path(path).read_text())
    if "fiducials" in data:
        points = {k: tuple(v) for k, v in data["fiducials"].items()}
    else:
        points = {k: tuple(v) for k, v in data.items() if isinstance(v, (list, tuple))}

    page_size = None
    if "page_size" in data:
        page = data["page_size"]
        page_size = (int(page["width"]), int(page["height"]))

    return FiducialTargets(points=points, page_size=page_size)


@dataclass
class FiducialCandidate:
    center: tuple[float, float]
    area: float
    bbox: tuple[int, int, int, int]


def _find_square_candidates(binary: np.ndarray) -> list[FiducialCandidate]:
    inverted = cv2.bitwise_not(binary)
    contours, _ = cv2.findContours(inverted, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[FiducialCandidate] = []
    img_area = float(binary.shape[0] * binary.shape[1])

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < img_area * 0.0002 or area > img_area * 0.05:
            continue

        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        if len(approx) != 4:
            continue

        x, y, w, h = cv2.boundingRect(approx)
        if w == 0 or h == 0:
            continue

        aspect = w / float(h)
        if not (0.75 <= aspect <= 1.25):
            continue

        rect_area = w * h
        if rect_area == 0 or area / rect_area < 0.7:
            continue

        center = (x + w / 2.0, y + h / 2.0)
        candidates.append(FiducialCandidate(center=center, area=area, bbox=(x, y, w, h)))

    return candidates


def _find_l_corner(candidates: Iterable[FiducialCandidate]) -> FiducialCandidate | None:
    candidates = list(candidates)
    if len(candidates) < 3:
        return None

    sizes = [np.sqrt(c.area) for c in candidates]
    median_size = float(np.median(sizes))
    tol = median_size * 0.8

    for cand in candidates:
        cx, cy = cand.center
        right = None
        down = None
        for other in candidates:
            if other is cand:
                continue
            ox, oy = other.center
            if ox > cx and abs(oy - cy) < tol and abs(ox - cx) < median_size * 3:
                right = other
            if oy > cy and abs(ox - cx) < tol and abs(oy - cy) < median_size * 3:
                down = other
        if right and down:
            return cand

    return None


def _pick_by_corner(candidates: list[FiducialCandidate], corner: tuple[int, int]) -> FiducialCandidate | None:
    if not candidates:
        return None
    cx, cy = corner
    return min(candidates, key=lambda c: (c.center[0] - cx) ** 2 + (c.center[1] - cy) ** 2)


def detect_fiducials(binary: np.ndarray, allow_l_marker: bool = True) -> dict[str, tuple[float, float]]:
    candidates = _find_square_candidates(binary)
    if not candidates:
        raise ValueError("No fiducial candidates detected.")

    h, w = binary.shape[:2]
    corners = {
        "top_left": (0, 0),
        "top_right": (w, 0),
        "bottom_left": (0, h),
        "bottom_right": (w, h),
    }

    detected: dict[str, tuple[float, float]] = {}
    remaining = candidates[:]

    if allow_l_marker:
        l_corner = _find_l_corner(remaining)
        if l_corner:
            detected["top_left"] = l_corner.center
            remaining = [c for c in remaining if c is not l_corner]

    for name, corner in corners.items():
        if name in detected:
            continue
        picked = _pick_by_corner(remaining, corner)
        if picked:
            detected[name] = picked.center
            remaining.remove(picked)

    if len(detected) < 4:
        raise ValueError(f"Expected 4 fiducials, detected {len(detected)}: {list(detected.keys())}")

    return detected


def draw_fiducials(image: np.ndarray, fiducials: dict[str, tuple[float, float]]) -> np.ndarray:
    overlay = image.copy()
    for name, (x, y) in fiducials.items():
        cv2.circle(overlay, (int(x), int(y)), 12, (0, 0, 255), 2)
        cv2.putText(
            overlay,
            name,
            (int(x) + 12, int(y) - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )
    return overlay
