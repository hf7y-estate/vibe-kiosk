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

