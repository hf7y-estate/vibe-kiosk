import cv2
import numpy as np
from analysis.omr.preprocess import preprocess_fiducials


def main(path: str):
    binary = preprocess_fiducials(path)
    inv = cv2.bitwise_not(binary)

    contours, _ = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = binary.shape[:2]
    img_area = float(h * w)

    print("image size:", (w, h), "img_area:", int(img_area))
    print("num contours:", len(contours))
    print()

    # Sort contours by area descending
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Prepare debug overlay
    vis = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    print(
        " idx |    area |   bbox(w,h) | aspect |  fill | concav | notes"
    )
    print(
        "-----+---------+-------------+--------+-------+--------+----------------"
    )

    for i, cnt in enumerate(contours[:25]):
        area = float(cv2.contourArea(cnt))
        x, y, cw, ch = cv2.boundingRect(cnt)
        rect_area = float(cw * ch) if cw and ch else 0.0

        aspect = (cw / ch) if ch else 0.0
        fill = (area / rect_area) if rect_area else 0.0

        hull = cv2.convexHull(cnt)
        hull_area = float(cv2.contourArea(hull)) if hull is not None else 0.0
        concavity = ((hull_area - area) / rect_area) if rect_area else 0.0

        notes = []

        # Heuristics for "notched square"
        if 0.75 <= aspect <= 1.25:
            notes.append("square-ish")
        if 0.55 <= fill <= 0.85:
            notes.append("notched-fill")
        if concavity >= 0.05:
            notes.append("concave")

        is_candidate = (
            x < w * 0.35
            and y < h * 0.35
            and area > img_area * 0.00005
            and 0.75 <= aspect <= 1.25
            and 0.55 <= fill <= 0.85
            and concavity >= 0.05
        )

        if is_candidate:
            notes.append("<<< NOTCHED TL CANDIDATE")

            # Draw bounding box
            cv2.rectangle(vis, (x, y), (x + cw, y + ch), (0, 0, 255), 2)

            # Draw anchor point (NW quadrant center)
            ax = int(x + cw * 0.25)
            ay = int(y + ch * 0.25)
            cv2.circle(vis, (ax, ay), 6, (0, 0, 255), -1)

        print(
            f"{i:4d} | {area:7.0f} | ({cw:3d},{ch:3d})     "
            f"| {aspect:6.2f} | {fill:5.2f} | {concavity:6.2f} | "
            + ", ".join(notes)
        )

    cv2.imwrite("debug_contours_notched_overlay.png", vis)
    print()
    print("Wrote debug_contours_notched_overlay.png")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m tools.debug_fiducial_contours path/to/scan.png")
        raise SystemExit(2)
    main(sys.argv[1])

