from pathlib import Path
import cv2

from analysis.omr.preprocess import preprocess_fiducials
from analysis.omr.fiducials import (
    detect_fiducials,
    draw_fiducials,
    _find_square_candidates,
    draw_candidates,
)


def main(png_path: str, out_path: str = "fiducials_debug.png"):
    png_path = Path(png_path)

    # 1) Preprocess for fiducials
    binary = preprocess_fiducials(png_path)
    cv2.imwrite("debug_fiducials_binary.png", binary)

    # 2) Load original image
    original = cv2.imread(str(png_path), cv2.IMREAD_COLOR)
    if original is None:
        raise FileNotFoundError(png_path)

    # 3) Find ALL square candidates
    candidates = _find_square_candidates(binary)
    print("num square candidates:", len(candidates))

    cand_overlay = draw_candidates(original, candidates)
    cv2.imwrite("debug_candidates.png", cand_overlay)

    # 4) Detect labeled fiducials
    fiducials = detect_fiducials(binary, allow_l_marker=True)
    print("Detected fiducials:")
    for name, (x, y) in fiducials.items():
        print(f"  {name}: ({x:.1f}, {y:.1f})")

    fid_overlay = draw_fiducials(original, fiducials)
    cv2.imwrite("debug_fiducials.png", fid_overlay)

    # Optional: legacy output name
    cv2.imwrite(out_path, fid_overlay)

    print("Wrote:")
    print("  debug_fiducials_binary.png  (thresholded image)")
    print("  debug_candidates.png        (all square candidates)")
    print("  debug_fiducials.png         (final picked fiducials)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m tools.test_fiducials path/to/scan.png")
        raise SystemExit(2)

    main(sys.argv[1])

