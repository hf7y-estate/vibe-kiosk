from __future__ import annotations

import numpy as np
import cv2


def _order_points(points: dict[str, tuple[float, float]]) -> np.ndarray:
    ordered = np.array(
        [
            points["top_left"],
            points["top_right"],
            points["bottom_right"],
            points["bottom_left"],
        ],
        dtype=np.float32,
    )
    return ordered


def warp_image(
    image: np.ndarray,
    source_points: dict[str, tuple[float, float]],
    target_points: dict[str, tuple[float, float]],
    output_size: tuple[int, int] | None = None,
) -> np.ndarray:
    src = _order_points(source_points)
    dst = _order_points(target_points)

    if output_size is None:
        width = int(max(dst[:, 0]) - min(dst[:, 0]))
        height = int(max(dst[:, 1]) - min(dst[:, 1]))
        output_size = (width, height)

    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(image, matrix, output_size)
    return warped
