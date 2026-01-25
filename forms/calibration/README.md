Put calibration files here:
- fiducials.json (corner marks / alignment info)
- bubbles.json (bubble center coords per question/option)

Suggested fiducials.json schema:
```json
{
  "page_size": { "width": 2480, "height": 3508 },
  "fiducial_size": 32,
  "fiducials": {
    "top_left": [120, 120],
    "top_right": [2360, 120],
    "bottom_left": [120, 3388],
    "bottom_right": [2360, 3388]
  },
  "l_marker": {
    "enabled": true,
    "spacing": 48
  }
}
```

Suggested bubbles.json schema:
```json
{
  "bubbles": [
    { "id": "Q1_A", "question": "Q1", "value": 1, "x": 300, "y": 600, "r": 12 },
    { "id": "Q1_B", "question": "Q1", "value": 2, "x": 360, "y": 600, "r": 12 },
    { "id": "EA_1", "dimension": "EA", "value": 1, "x": 300, "y": 900, "r": 12 }
  ]
}
```

The form generator (`forms/generate_form.py`) consumes these JSON files to
draw fiducials and bubble outlines, keeping template geometry in sync with
OMR expectations.
