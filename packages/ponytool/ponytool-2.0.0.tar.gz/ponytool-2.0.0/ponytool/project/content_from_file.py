import sys
from pathlib import Path

from ponytool.project.content_helper import parse_structure
from ponytool.utils.ui import warning, info, success

from ponytool.project.content_cfg import FILE_NAME, DEFAULT_PATHS


def _read_file(file_path):
    content = file_path.read_text(encoding="utf-8")  # PyCharm и ему подобные очень криво читают файлы без энкода
    if not content.strip():
        warning(".ponyinit is empty")
        sys.exit(1)
    return parse_structure(content)

def _run_script(
        dirs: list[str],
        files: list[str],
        dry_run: bool = False,
):
    base = Path.cwd()

    for d in dirs:
        path = base / d
        if dry_run:
            info(f"[DRY-RUN] Create Folder: {path}")
        else:
            create_dir(path)

    for f in files:
        path = base / f
        if dry_run:
            info(f"[DRY-RUN] Create File: {path}")
        else:
            create_file(path)

def _check_duplicates(
        dirs: list[str],
        files: list[str],
        base: Path | None = None
) -> tuple[list[str], list[str], list[str]]:

    base = base or Path.cwd()

    valid_dirs, existing_dirs = _check_assistance(dirs, base)
    valid_files, existing_files = _check_assistance(files, base)

    existing = existing_dirs + existing_files

    return valid_dirs, valid_files, existing

def _check_assistance(
        items: list[str],
        base: Path,
) -> tuple[list[str], list[str]]:
    existing: list[str] = []
    valid: list[str] = []

    for item in items:
        if (base / item).exists():
            existing.append(item)
        else:
            valid.append(item)

    return valid, existing

def create_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def create_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)

def ensure_data_from_content(file_path: Path | None = None) -> tuple[list[str], list[str]]:
    dirs, files = _read_file(file_path)

    if not dirs and not files:
        warning("No directories or files defined in .ponyinit")
        sys.exit(1)

    dirs, files, existing = _check_duplicates(dirs, files)

    if existing:
        warning("Обнаружены уже существующие элементы:")
        for obj in existing:
            warning(f"  - {obj}")

    return dirs, files


def run(dry_run=False):
    cfg_path = Path.cwd() / FILE_NAME

    if not cfg_path.exists():
        cfg_path.write_text("\n".join(DEFAULT_PATHS) + "\n", encoding="utf-8")
        info("Created default .ponyinit")

    dirs, files = ensure_data_from_content(cfg_path)

    _run_script(dirs, files, dry_run=dry_run)

    success("Project structure created")
