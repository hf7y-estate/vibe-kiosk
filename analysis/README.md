# Analysis Layer

This directory contains the image analysis and interpretation logic for the
vibe-kiosk pipeline.

Input to this layer is a **single scanned image** (PNG/TIFF) produced by the
scanner layer. Output is **structured data** (marks, values, IDs, confidence).

The analysis layer is intentionally split into two concerns:
1. **What marks are present**
2. **What those marks mean**

---

## Directory Structure

analysis/
├── omr/
│ ├── preprocess.py
│ ├── fiducials.py
│ ├── warp.py
│ ├── bubbles.py
│ └── decode.py
├── scoring/
│ ├── likert.py
│ ├── ids.py
│ └── validate.py
├── run_omr.py
└── README.md

---

## `omr/` — Optical Mark Recognition

Responsibilities:
- Normalize scanned images (grayscale, thresholding)
- Detect fiducials / timing marks
- Warp scans into a canonical coordinate system
- Detect filled vs unfilled bubbles
- Output **raw mark data** with confidence metrics

Fiducials may be simple square marks. The OMR layer also supports an optional
top-left L-marker (three adjacent squares forming an L) to disambiguate page
orientation during early form drafts.

This layer does **not** interpret meaning.  
It answers questions like:
- Where is each bubble?
- How filled is it?
- Is the mark ambiguous?

### Output (example)

```json
{
  "bubbles": [
    { "row": 1, "col": "A", "filledness": 0.62 },
    { "row": 1, "col": "B", "filledness": 0.08 },
    { "row": 1, "col": "C", "filledness": 0.11 }
  ],
  "confidence": {
    "row_1": "high"
  }
}
scoring/ — Interpretation & Encoding
Responsibilities:

Map detected marks to semantic values (e.g. Likert 1–5)

Enforce rules (one bubble per row, required answers, etc.)

Encode IDs from marked regions

Validate and flag errors or ambiguities

This layer is form-specific and policy-driven.

It answers questions like:

Which Likert value was selected?

Is the response valid?

What is the encoded respondent ID?

Output (example)
json
Copy code
{
  "responses": {
    "Q1": 4,
    "Q2": 2,
    "Q3": 5
  },
  "respondent_id": "EA3-AB1",
  "status": "ok"
}
Design Principles
Deterministic: Same image → same result

Debuggable: Intermediate images and overlays should be saved

Separable: OMR does not care about meaning; scoring does

Scanner-agnostic: Assumes only a warped, normalized image

Development Notes
All geometry is defined in canonical page coordinates (post-warp)

Bubble positions are defined by form templates (see /forms/)

PDF is not used for analysis; only PNG/TIFF

Ambiguity is a first-class outcome, not an error

Entry Point
run_omr.py is the primary entry point for this layer during development.
It should:

Load a scanned image

Run OMR

Run scoring

Emit structured output (JSON/CSV) and debug artifacts
