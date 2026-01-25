from __future__ import annotations

import binascii
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont

import barcode
from barcode.writer import ImageWriter


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
        return f"EA{self.EA} EB{self.EB} AA{self.AA} AB{self.AB}"

    def id_string(self) -> str:
        return f"EA{self.EA}-EB{self.EB}-AA{self.AA}-AB{self.AB}"


def crc8_hex(data: str) -> str:
    c = binascii.crc32(data.encode("utf-8")) & 0xFF
    return f"{c:02X}"


def make_payload(vec: Vector, version: str = "v1") -> Tuple[str, str]:
    vec.validate()
    base = f"{vec.id_string()}|{version}"
    chk = crc8_hex(base)
    payload = f"{base}|{chk}"
    return payload, chk


def pack_vector(vec: Vector) -> str:
    vec.validate()
    return f"{vec.EA}{vec.EB}{vec.AA}{vec.AB}"


def make_payload_short(vec: Vector, version_digit: str = "1") -> tuple[str, str]:
    packed = pack_vector(vec)
    base = f"{version_digit}{packed}"
    chk = f"{(binascii.crc32(base.encode('utf-8')) & 0xFF):02X}"
    payload = f"{base}{chk}"
    return payload, chk


def make_code128_barcode_png(payload: str, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    code128 = barcode.get_barcode_class("code128")
    code = code128(payload, writer=ImageWriter())
    writer_opts = {
        "module_width": 0.4,
        "module_height": 18.0,
        "quiet_zone": 3.0,
        "font_size": 10,
        "text_distance": 1.0,
        "write_text": False,
        "dpi": 300,
    }
    stem = str(out_path.with_suffix(""))
    final_path = Path(code.save(stem, options=writer_opts)).with_suffix(".png")
    return final_path


def load_font(size: int) -> ImageFont.ImageFont:
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
    out_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = label_px
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    font_title = load_font(32)
    font_body = load_font(28)
    font_small = load_font(18)

    draw.text((30, 20), "VIBE KIOSK v1", font=font_title, fill="black")
    draw.text((30, 70), human_text, font=font_body, fill="black")

    bc = Image.open(barcode_png).convert("RGB")
    target_w = width - 60
    target_h = 220
    bc = bc.resize((target_w, target_h))
    img.paste(bc, (30, 130))

    draw.text((30, height - 28), payload, font=font_small, fill="black")

    img.save(out_path)
    return out_path


def print_via_cups(label_png: Path, cups_queue: str) -> None:
    import subprocess

    subprocess.run(
        ["lp", "-d", cups_queue, str(label_png)],
        check=True,
    )
