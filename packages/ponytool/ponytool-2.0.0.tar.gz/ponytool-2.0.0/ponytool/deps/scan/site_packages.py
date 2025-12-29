import subprocess
import json
from pathlib import Path


def get_site_packages(python: Path) -> list[Path]:
    cmd = [
        str(python),
        "-c",
        "import site, json; print(json.dumps(site.getsitepackages()))"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError("Failed to determine site-packages")

    try:
        paths = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        raise RuntimeError("Invalid site-packages output")

    return [Path(p) for p in paths]
