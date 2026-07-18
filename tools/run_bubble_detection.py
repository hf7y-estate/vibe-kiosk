from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2

from analysis.omr.bubbles import detect_bubbles, draw_bubbles, load_bubbles
from analysis.omr.fiducials import detect_fiducials, draw_fiducials, load_fiducial_targets
from analysis.omr.preprocess import preprocess
from analysis.omr.warp import warp_image


def _write_debug(path: Path, image: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)


def run_bubble_detection(
    image_path: Path,
    fiducials_path: Path,
    bubbles_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
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

    gray = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    fid_overlay = draw_fiducials(gray, fiducials)
    _write_debug(output_dir / "fiducials.png", fid_overlay)
    _write_debug(output_dir / "warped.png", warped)

    warped_color = cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR)
    filledness = {b["id"]: b["filledness"] for b in bubble_results}
    bubble_overlay = draw_bubbles(warped_color, bubbles, filledness)
    _write_debug(output_dir / "bubbles.png", bubble_overlay)

    results_path = output_dir / "bubble_results.json"
    results_path.write_text(json.dumps(bubble_results, indent=2))

    return {
        "fiducials": fiducials,
        "bubbles": bubble_results,
        "outputs": {
            "fiducials": str(output_dir / "fiducials.png"),
            "warped": str(output_dir / "warped.png"),
            "bubbles": str(output_dir / "bubbles.png"),
            "results": str(results_path),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bubble detection on a scanned form.")
    parser.add_argument(
        "image",
        type=Path,
        nargs="?",
        default=Path("forms/samples/filled.png"),
        help="Path to the scanned form image (default: forms/samples/filled.png)",
    )
    parser.add_argument(
        "--fiducials",
        type=Path,
        default=Path("forms/calibration/fiducials.json"),
        help="Path to fiducials calibration JSON",
    )
    parser.add_argument(
        "--bubbles",
        type=Path,
        default=Path("forms/calibration/bubbles.json"),
        help="Path to bubbles calibration JSON",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/bubble_debug"),
        help="Directory to write debug images and results JSON",
    )
    args = parser.parse_args()

    results = run_bubble_detection(args.image, args.fiducials, args.bubbles, args.output_dir)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

