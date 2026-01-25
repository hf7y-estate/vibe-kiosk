import cv2
import numpy as np
from pathlib import Path


def preprocess(path: str | Path) -> np.ndarray:
    """
    Load a scanned form and return a binary image suitable for OMR.

    Output convention:
      - paper: 255 (white)
      - marks: 0 (black)
    """
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(path)

    img = cv2.GaussianBlur(img, (5, 5), 0)

    thr = cv2.adaptiveThreshold(
        img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        35,
        10,
    )

    # Ensure paper is white (dominant)
    if np.mean(thr == 255) < 0.5:
        thr = 255 - thr

    return thr
