Prototype pipeline:
scan form -> extract Likert marks -> compute 4D vector -> render barcode/QR -> print label.

Folder map:
- forms/: form templates, calibration data, sample scans
- scanner/: scan acquisition code (SANE or camera)
- analysis/: OMR + scoring
- printing/: label templates + printer drivers
- pi/: Raspberry Pi autorun/service + scripts
- tools/: ad-hoc dev/debug scripts used while tuning fiducial and bubble
  detection (not part of the pipeline entry points below)
- data/: runtime outputs (ignored by git)

## Sample Inputs

`forms/samples/` holds reference images used to exercise the OMR tools
without a real scanner:
- `multiple_choice_sheet_75q.pdf`: the source form template (a generic
  75-question bubble sheet).
- `og.png`: that template rasterized to a blank page, used as fiducial-only
  test input (e.g. `python -m tools.test_fiducials forms/samples/og.png`).
- `filled.png`: a scanned, filled-in copy of the form used to exercise
  bubble detection (the default input for `tools/run_bubble_detection.py`).

`forms/calibration/fiducials.json` and `forms/calibration/bubbles.json` are
site-specific (they encode exact pixel coordinates for one printed form) and
are intentionally **not** committed — see `forms/calibration/README.md` for
the schema and generate your own from a real printed/scanned form before
running anything below.

## System Dependencies

This project assumes a Linux system with a USB document scanner.

For Epson ES-50 (and similar SANE-compatible scanners), install:

```bash
sudo apt update
sudo apt install sane sane-utils sane-airscan
```

If you plan to print via CUPS:

```bash
sudo apt install cups
```

`opencv-python` (used throughout `analysis/omr/`) links against system
graphics libraries that a minimal/headless Debian or Raspberry Pi OS image
may not have. If `import cv2` fails with a `libGL.so.1` error, install:

```bash
sudo apt install libgl1
```

Label rendering (`printing/label.py`, `forms/generate_form.py`) tries to
load `DejaVuSans.ttf` and silently falls back to PIL's built-in bitmap font
if it isn't found. For proper-looking labels/templates, install:

```bash
sudo apt install fonts-dejavu-core
```

## Python Dependencies

Create and activate a virtualenv first (`.venv/` is gitignored — never
commit it):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Form Template Generation

Keep `fiducials.json` and `bubbles.json` in sync with your printed form by
generating templates directly from those calibration files:

```bash
python forms/generate_form.py \
  --fiducials forms/calibration/fiducials.json \
  --bubbles forms/calibration/bubbles.json \
  --output data/forms/form.png
```

## End-to-end Pipeline

Run the full pipeline (scan → OMR → scoring → barcode/label):

```bash
python run_pipeline.py \
  --fiducials forms/calibration/fiducials.json \
  --bubbles forms/calibration/bubbles.json \
  --output-dir data/run \
  --debug-dir data/run/debug
```

To use an existing scan instead of capturing:

```bash
python run_pipeline.py \
  --image data/scans/scan.png \
  --fiducials forms/calibration/fiducials.json \
  --bubbles forms/calibration/bubbles.json
```

## Testing Approaches

Suggested manual checks:

1. **Scanner capture**: run a SANE capture and confirm the PNG is readable.
   ```bash
   python -c "from pathlib import Path; from scanner.sane.capture import scan_with_sane; scan_with_sane(Path('data/scans/scan.png'))"
   ```
2. **OMR debug overlays**: run OMR on a known scan and inspect the debug
   outputs (`fiducials.png`, `warped.png`, `bubbles.png`).
   ```bash
   python analysis/run_omr.py data/scans/scan.png \
     --fiducials forms/calibration/fiducials.json \
     --bubbles forms/calibration/bubbles.json \
     --debug-dir data/run/debug
   ```
3. **Label rendering**: verify that barcodes and labels render properly.
   ```bash
   python printing/print_test.py --outdir data/prints
   ```
4. **Full pipeline**: confirm the JSON output includes vector, barcode, and
   label paths.
   ```bash
   python run_pipeline.py \
     --image data/scans/scan.png \
     --fiducials forms/calibration/fiducials.json \
     --bubbles forms/calibration/bubbles.json \
     --output-dir data/run
   ```

## Debug Output

The pipeline's own entry points (`run_pipeline.py --debug-dir`,
`analysis/run_omr.py --debug-dir`, `tools/run_bubble_detection.py`) write
debug overlays under `data/`, which is gitignored.

A few one-off scripts in `tools/` (`test_fiducials.py`,
`find_bubble_candidates.py`) instead hardcode debug image filenames
relative to the current directory (e.g. `debug_fiducials.png`,
`bubble_candidates.png`) rather than writing into `data/`. These are
harmless, regenerable byproducts of running those scripts from the repo
root; `.gitignore` has patterns (`/debug_*.png`, `/*_debug.png`,
`/*_candidates.png`) so they never get committed, but don't be surprised to
see them appear at the top level after using those particular tools.
