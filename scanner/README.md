Scanner capture layer.

- sane/: wrappers around `scanimage` (USB scanner via SANE)
- camera/: capture via libcamera/OpenCV (if using Pi camera)

Scripts:
- `scanner/sane/capture.py`: capture a PNG via SANE (`scanimage`)
- `scanner/camera/capture.py`: capture a single frame via OpenCV
