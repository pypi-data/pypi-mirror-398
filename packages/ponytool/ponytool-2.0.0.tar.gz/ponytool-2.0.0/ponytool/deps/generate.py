from pathlib import Path

from ponytool.utils.ui import (info, warning)
from ponytool.deps.scanner import scan
from ponytool.deps.collect_imports import scan_imports
from ponytool.deps.writer import write
from ponytool.deps.analyzer import analyze_usage

REQ_PATH = Path("requirements.txt")

def generate_requirements(args):
    info("Generating requirements.txt")

    scan_result = scan()

    imports = scan_imports(Path.cwd())
    if not imports:
        warning("No Python imports found in project")

    analysis = analyze_usage(
        imports=imports,
        installed=scan_result["packages"],
    )

    if analysis["unmatched_imports"]:
        warning("Imports without matching packages:")
        for imp in sorted(analysis["unmatched_imports"]):
            info(f"  - {imp}")

    if analysis["unused_packages"]:
        warning("Installed but unused packages:")
        for pkg in sorted(analysis["unused_packages"]):
            info(f"  - {pkg}")

    write(
        packages=analysis["matched"],
        path=REQ_PATH,
        dry_run=getattr(args, "dry_run", False),
        force=getattr(args, "force", False),
        meta={
            "python": str(scan_result["python"]),
            "venv": str(scan_result["venv"]),
        },
    )
