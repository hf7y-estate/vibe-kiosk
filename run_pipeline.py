from __future__ import annotations

import argparse
import json
from pathlib import Path

from analysis.run_omr import run_omr
from analysis.scoring.likert import score_likert
from analysis.scoring.vector import compute_vector
from printing.label import (
    Vector,
    make_code128_barcode_png,
    make_payload_short,
    print_via_cups,
    render_label,
)
from scanner.camera.capture import capture_with_camera
from scanner.sane.capture import scan_with_sane


def _resolve_vector(vector_data: dict[str, int | None]) -> Vector:
    missing = [k for k in ("EA", "EB", "AA", "AB") if vector_data.get(k) is None]
    if missing:
        raise ValueError(f"Missing vector values for {missing}")
    return Vector(
        EA=int(vector_data["EA"]),
        EB=int(vector_data["EB"]),
        AA=int(vector_data["AA"]),
        AB=int(vector_data["AB"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the end-to-end kiosk pipeline.")
    parser.add_argument("--image", type=Path, help="Use an existing scan instead of capturing.")
    parser.add_argument("--scanner", choices=["sane", "camera"], default="sane")
    parser.add_argument("--fiducials", type=Path, required=True)
    parser.add_argument("--bubbles", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/run"))
    parser.add_argument("--debug-dir", type=Path)
    parser.add_argument("--cups-queue", type=str)
    args = parser.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.image:
        scan_path = args.image
    elif args.scanner == "camera":
        scan_path = capture_with_camera(output_dir / "scan.png")
    else:
        scan_path = scan_with_sane(output_dir / "scan.png")

    omr_result = run_omr(scan_path, args.fiducials, args.bubbles, args.debug_dir)
    scoring = score_likert(omr_result["bubbles"])
    vector_data = compute_vector(omr_result["bubbles"])

    vector = _resolve_vector(vector_data)
    payload, _chk = make_payload_short(vector, version_digit="1")

    barcode_path = make_code128_barcode_png(payload, output_dir / "barcode_code128.png")
    label_path = render_label(
        human_text=vector.human_text(),
        payload=payload,
        barcode_png=barcode_path,
        out_path=output_dir / "label.png",
    )

    if args.cups_queue:
        print_via_cups(label_path, args.cups_queue)

    result = {
        "scan": str(scan_path),
        "omr": omr_result,
        "scoring": scoring,
        "vector": vector.as_dict(),
        "barcode": str(barcode_path),
        "label": str(label_path),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
