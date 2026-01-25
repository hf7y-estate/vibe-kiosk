from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from omr.bubbles import detect_bubbles, draw_bubbles, load_bubbles
from omr.fiducials import detect_fiducials, draw_fiducials, load_fiducial_targets
from omr.preprocess import preprocess
from omr.warp import warp_image


def _write_debug(path: Path, image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)


def run_omr(image_path: Path, fiducials_path: Path, bubbles_path: Path, debug_dir: Path | None) -> dict:
    binary = preprocess(image_path)

    fiducials = detect_fiducials(binary, allow_l_marker=True)
    targets = load_fiducial_targets(fiducials_path)

    warped = warp_image(
        binary,
        fiducials,
        targets.points,
        output_size=targets.page_size,
    )

    bubbles = load_bubbles(bubbles_path)
    bubble_results = detect_bubbles(warped, bubbles)

    if debug_dir:
        gray = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        fid_overlay = draw_fiducials(gray, fiducials)
        _write_debug(debug_dir / "fiducials.png", fid_overlay)
        _write_debug(debug_dir / "warped.png", warped)

        warped_color = cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR)
        filledness = {b["id"]: b["filledness"] for b in bubble_results}
        bubble_overlay = draw_bubbles(warped_color, bubbles, filledness)
        _write_debug(debug_dir / "bubbles.png", bubble_overlay)

    return {
        "fiducials": fiducials,
        "bubbles": bubble_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OMR on a scanned form.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--fiducials", type=Path, required=True)
    parser.add_argument("--bubbles", type=Path, required=True)
    parser.add_argument("--debug-dir", type=Path)
    args = parser.parse_args()

    result = run_omr(args.image, args.fiducials, args.bubbles, args.debug_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
