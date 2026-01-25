#!/usr/bin/env python3
"""
Print-test for vibe-kiosk prototype.

Creates a label with:
- human-readable text: "EA3 EB2 AA5 AB1"
- 1D Code128 barcode encoding: "EA3-EB2-AA5-AB1|v1|CHK"

Always writes output PNG to disk.
Optionally prints via CUPS if --cups-queue is provided.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from printing.label import (
    Vector,
    make_payload_short,
    make_code128_barcode_png,
    render_label,
    print_via_cups,
)


# -----------------------------
# Main (dummy data)
# -----------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--EA", type=int, default=3)
    ap.add_argument("--EB", type=int, default=2)
    ap.add_argument("--AA", type=int, default=5)
    ap.add_argument("--AB", type=int, default=1)
    ap.add_argument("--outdir", type=Path, default=Path("data/prints"))
    ap.add_argument("--cups-queue", type=str, default=None, help="If set, prints via CUPS queue name")
    args = ap.parse_args()

    vec = Vector(EA=args.EA, EB=args.EB, AA=args.AA, AB=args.AB)
    payload, _chk = make_payload_short(vec, version_digit="1")

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    barcode_path = make_code128_barcode_png(payload, outdir / "barcode_code128.png")
    label_path = render_label(
        human_text=vec.human_text(),
        payload=payload,
        barcode_png=barcode_path,
        out_path=outdir / "label.png",
    )

    print(f"Wrote barcode: {barcode_path}")
    print(f"Wrote label:   {label_path}")
    print(f"Payload:       {payload}")

    if args.cups_queue:
        print(f"Printing via CUPS queue '{args.cups_queue}'...")
        print_via_cups(label_path, args.cups_queue)
        print("Done.")


if __name__ == "__main__":
    main()
