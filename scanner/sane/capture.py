from __future__ import annotations

import subprocess
from pathlib import Path


def scan_with_sane(output_path: Path, resolution: int = 300, mode: str = "Color") -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "scanimage",
        "--format=png",
        f"--resolution={resolution}",
        f"--mode={mode}",
        f"--output-file={output_path}",
    ]
    subprocess.run(cmd, check=True)
    return output_path
