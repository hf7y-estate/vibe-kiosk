from pathlib import Path
import json
import cv2

from analysis.omr.preprocess import preprocess
from analysis.omr.fiducials import detect_fiducials
from analysis.omr.warp import warp_to_template  # adjust if needed


def load_bubbles(path: str | Path):
    data = json.loads(Path(path).read_text())
    return data["bubbles"]


def draw_bubbles(image, bubbles):
    overlay = image.copy()
    for b in bubbles:
        x, y, r = int(b["x"]), int(b["y"]), int(b.get("r", 12))
        cv2.circle(overlay, (x, y), r, (0, 0, 255), 2)
        # optional: label tiny
        # cv2.putText(overlay, b["id"], (x+r+2, y-2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,0,255), 1)
    return overlay


def main(scan_path: str, fid_json: str, bubbles_json: str):
    scan_path = Path(scan_path)

    # 1) Preprocess (binary for fiducials/warp)
    binary = preprocess(scan_path)
    cv2.imwrite("debug_bubbles_preprocess.png", binary)

    # 2) Detect fiducials in scan space
    detected = detect_fiducials(binary, allow_l_marker=True)
    print("Detected fiducials:", detected)

    # 3) Load template fiducials (expected positions)
    fid_data = json.loads(Path(fid_json).read_text())
    targets = fid_data["fiducials"]
    targets = {k: tuple(v) for k, v in targets.items()}
    page_w = fid_data["page_size"]["width"]
    page_h = fid_data["page_size"]["height"]

    # 4) Warp scan to template coordinate space
    warped = warp_to_template(binary, detected, targets, (page_w, page_h))
    cv2.imwrite("debug_warped.png", warped)

    # 5) Overlay bubbles on warped image
    bubbles = load_bubbles(bubbles_json)
    warped_color = cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR)
    overlay = draw_bubbles(warped_color, bubbles)
    cv2.imwrite("debug_bubbles_overlay.png", overlay)

    print("Wrote:")
    print("  debug_warped.png")
    print("  debug_bubbles_overlay.png")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python -m tools.test_bubbles_overlay scan.png forms/calibration/fiducials.json forms/calibration/bubbles.json")
        raise SystemExit(2)
    main(sys.argv[1], sys.argv[2], sys.argv[3])

