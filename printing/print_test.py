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
import binascii
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont

# python-barcode
import barcode
from barcode.writer import ImageWriter


# -----------------------------
# 1) Contract helpers
# -----------------------------

@dataclass(frozen=True)
class Vector:
    EA: int
    EB: int
    AA: int
    AB: int

    def validate(self) -> None:
        for k, v in self.as_dict().items():
            if not (1 <= v <= 5):
                raise ValueError(f"{k} must be 1..5, got {v}")

    def as_dict(self) -> Dict[str, int]:
        return {"EA": self.EA, "EB": self.EB, "AA": self.AA, "AB": self.AB}

    def human_text(self) -> str:
        # "EA3 EB2 AA5 AB1"
        return f"EA{self.EA} EB{self.EB} AA{self.AA} AB{self.AB}"

    def id_string(self) -> str:
        # "EA3-EB2-AA5-AB1"
        return f"EA{self.EA}-EB{self.EB}-AA{self.AA}-AB{self.AB}"


def crc8_hex(data: str) -> str:
    """
    Simple checksum. This is NOT cryptographic; it just helps detect typos.
    We'll use a CRC32 and take the low 8 bits as a quick CRC-8 style tag.
    Output: 2 hex chars, e.g. '7F'
    """
    c = binascii.crc32(data.encode("utf-8")) & 0xFF
    return f"{c:02X}"


def make_payload(vec: Vector, version: str = "v1") -> Tuple[str, str]:
    """
    Returns (payload, checksum).
    payload format: "<ID>|<version>|<CHK>"
    """
    vec.validate()
    base = f"{vec.id_string()}|{version}"
    chk = crc8_hex(base)
    payload = f"{base}|{chk}"
    return payload, chk

def pack_vector(vec: Vector) -> str:
    vec.validate()
    # EA,EB,AA,AB are 1..5 so a single digit each is fine
    return f"{vec.EA}{vec.EB}{vec.AA}{vec.AB}"

def make_payload_short(vec: Vector, version_digit: str = "1") -> tuple[str, str]:
    """
    Short payload for minimum barcode width:
      payload = <version><packed><chk>
      example: "1" + "3251" + "A7" => "13251A7"
    """
    packed = pack_vector(vec)
    base = f"{version_digit}{packed}"
    chk = f"{(binascii.crc32(base.encode('utf-8')) & 0xFF):02X}"
    payload = f"{base}{chk}"
    return payload, chk


# -----------------------------
# 2) Barcode generation
# -----------------------------

def make_code128_barcode_png(payload: str, out_path: Path) -> Path:
    """
    Generates a Code128 barcode PNG.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    Code128 = barcode.get_barcode_class("code128")
    code = Code128(payload, writer=ImageWriter())

    # writer options: tune for readability; no human text inside barcode
    writer_opts = {
        "module_width": 0.4,   # thickness of the narrowest bar (mm-ish)
        "module_height": 18.0, # bar height
        "quiet_zone": 3.0,
        "font_size": 10,
        "text_distance": 1.0,
        "write_text": False,
        "dpi": 300,
    }

    # python-barcode will append .png automatically if you pass a stem
    # so pass out_path without suffix.
    stem = str(out_path.with_suffix(""))
    final_path = Path(code.save(stem, options=writer_opts)).with_suffix(".png")
    return final_path

def make_code39_barcode_png(payload: str, out_path: Path) -> Path:
    """
    Generates a Code 39 barcode PNG.
    NOTE: Code 39 supports a limited character set and is less compact than Code 128.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Code39 character set is basically: A-Z 0-9 space - . $ / + %
    # Many implementations also allow lowercase but may encode as uppercase.
    Code39 = barcode.get_barcode_class("code39")
    code = Code39(payload, writer=ImageWriter(), add_checksum=False)

    writer_opts = {
        "module_width": 0.4,
        "module_height": 18.0,
        "quiet_zone": 3.0,
        "write_text": False,
        "dpi": 300,
    }

    stem = str(out_path.with_suffix(""))
    final_path = Path(code.save(stem, options=writer_opts)).with_suffix(".png")
    return final_path

# -----------------------------
# 3) Label rendering
# -----------------------------

def load_font(size: int) -> ImageFont.ImageFont:
    # Use default PIL font if no system font is available.
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def render_label(
    human_text: str,
    payload: str,
    barcode_png: Path,
    out_path: Path,
    label_px: Tuple[int, int] = (800, 400),
) -> Path:
    """
    Renders a simple label PNG: title + human text + barcode image.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    W, H = label_px
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    font_title = load_font(32)
    font_body = load_font(28)
    font_small = load_font(18)

    # Title + human text
    draw.text((30, 20), "VIBE KIOSK v1", font=font_title, fill="black")
    draw.text((30, 70), human_text, font=font_body, fill="black")

    # Barcode image
    bc = Image.open(barcode_png).convert("RGB")
    # Fit barcode area
    target_w = W - 60
    target_h = 220
    bc = bc.resize((target_w, target_h))
    img.paste(bc, (30, 130))

    # Small payload hint (optional; keeps debugging easy)
    # You can remove later.
    draw.text((30, H - 28), payload, font=font_small, fill="black")

    img.save(out_path)
    return out_path


# -----------------------------
# 4) Printing backends
# -----------------------------

def print_via_cups(label_png: Path, cups_queue: str) -> None:
    """
    Minimal CUPS print using the 'lp' command.
    This assumes your printer is installed as a CUPS queue.
    """
    import subprocess

    subprocess.run(
        ["lp", "-d", cups_queue, str(label_png)],
        check=True,
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
    # payload, chk = make_payload(vec, version="v1")
    payload, chk = make_payload_short(vec, version_digit="1")

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    barcode_path = make_code128_barcode_png(payload, outdir / "barcode_code128.png")
    # barcode_path = make_code39_barcode_png(payload, outdir / "barcode_code39.png")
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

