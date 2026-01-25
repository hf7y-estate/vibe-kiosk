Prototype pipeline:
scan form -> extract Likert marks -> compute 4D vector -> render barcode/QR -> print label.

Folder map:
- forms/: form templates, calibration data, sample scans
- scanner/: scan acquisition code (SANE or camera)
- analysis/: OMR + scoring
- printing/: label templates + printer drivers
- pi/: Raspberry Pi autorun/service + scripts
- data/: runtime outputs (ignored by git)

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

## Python Dependencies

```bash
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
