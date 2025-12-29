from pathlib import Path

def parse_structure(content: str) -> tuple[list[str], list[str]]:
    dirs: list[str] = []
    files: list[str] = []

    for raw in content.splitlines():
        obj = raw.strip()
        if not obj:
            continue

        if Path(obj).suffix:
            files.append(obj)
        else:
            dirs.append(obj)

    return dirs, files

