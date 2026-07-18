import cv2
import numpy as np
from pathlib import Path

def main(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(path)

    # Expect black bubbles on white
    _, bw = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY_INV)

    # Clean up
    bw = cv2.medianBlur(bw, 5)

    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []

    for c in contours:
        area = cv2.contourArea(c)
        if area < 50 or area > 5000:
            continue

        (x, y), r = cv2.minEnclosingCircle(c)
        if r < 6 or r > 20:
            continue

        circularity = area / (np.pi * r * r)
        if circularity < 0.6:
            continue

        candidates.append((int(x), int(y), int(r)))

    print(f"found {len(candidates)} candidates")

    vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for x, y, r in candidates:
        cv2.circle(vis, (x, y), r, (0, 0, 255), 1)

    cv2.imwrite("bubble_candidates.png", vis)

    for i, (x, y, r) in enumerate(candidates):
        print(f"{i:3d}: x={x:4d}, y={y:4d}, r={r}")

if __name__ == "__main__":
    import sys
    main(sys.argv[1])

