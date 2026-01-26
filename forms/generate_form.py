from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def _draw_square(draw: ImageDraw.ImageDraw, center: tuple[float, float], size: float) -> None:
    half = size / 2.0
    x, y = center
    draw.rectangle((x - half, y - half, x + half, y + half), fill="black")


def generate_form(fiducials_path: Path, bubbles_path: Path, output_path: Path) -> Path:
    fiducials_data = json.loads(fiducials_path.read_text())
    bubbles_data = json.loads(bubbles_path.read_text())

    page_size = fiducials_data.get("page_size", {"width": 2480, "height": 3508})
    width = int(page_size["width"])
    height = int(page_size["height"])
    fiducial_size = float(fiducials_data.get("fiducial_size", 32))

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = _load_font(20)

    fiducials = fiducials_data.get("fiducials", fiducials_data)
    for name, point in fiducials.items():
        if not isinstance(point, (list, tuple)):
            continue
        _draw_square(draw, (float(point[0]), float(point[1])), fiducial_size)
        draw.text((point[0] + fiducial_size, point[1] - fiducial_size), name, fill="black", font=font)

    l_marker = fiducials_data.get("l_marker", {})
    if l_marker.get("enabled"):
        origin = l_marker.get("origin")
        if origin is None and "top_left" in fiducials:
            origin = fiducials["top_left"]
        if origin is not None:
            spacing = float(l_marker.get("spacing", fiducial_size * 1.5))
            origin_x, origin_y = float(origin[0]), float(origin[1])
            _draw_square(draw, (origin_x + spacing, origin_y), fiducial_size)
            _draw_square(draw, (origin_x, origin_y + spacing), fiducial_size)

    bubbles_list = bubbles_data.get("bubbles", bubbles_data)
    for bubble in bubbles_list:
        x = float(bubble["x"])
        y = float(bubble["y"])
        r = float(bubble.get("r", bubble.get("radius", 12)))
        draw.ellipse((x - r, y - r, x + r, y + r), outline="black", width=2)
        label = bubble.get("label") or bubble.get("id")
        if label:
            draw.text((x + r + 4, y - r), str(label), fill="black", font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a form template from calibration JSON.")
    parser.add_argument("--fiducials", type=Path, required=True)
    parser.add_argument("--bubbles", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/forms/form.png"))
    args = parser.parse_args()

    path = generate_form(args.fiducials, args.bubbles, args.output)
    print(f"Wrote form template to {path}")


if __name__ == "__main__":
    main()
