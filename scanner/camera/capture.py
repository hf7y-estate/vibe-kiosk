from __future__ import annotations

from pathlib import Path

import cv2


def capture_with_camera(output_path: Path, camera_index: int = 0) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Unable to open camera device.")
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Unable to capture frame from camera.")
    cv2.imwrite(str(output_path), frame)
    return output_path
