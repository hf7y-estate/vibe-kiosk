import cv2
import numpy as np
from pathlib import Path

def preprocess_fiducials(path: str | Path) -> np.ndarray:
    """
    Binary image optimized for detecting filled black fiducial squares.

    Output convention:
      - paper: 255 (white)
      - marks: 0 (black)
    """
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(path)

    # Slight blur helps Otsu
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # Otsu tends to preserve filled blacks as filled
    _, thr = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Ensure paper is white
    if np.mean(thr == 255) < 0.5:
        thr = 255 - thr

    # Optional: close small holes / gaps in the black squares
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    thr = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel, iterations=1)

    return thr

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
