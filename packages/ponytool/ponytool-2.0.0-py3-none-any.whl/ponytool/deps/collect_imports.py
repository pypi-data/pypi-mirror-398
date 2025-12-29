import ast
import sys
from pathlib import Path

EXCLUDE_DIRS = {"venv", ".venv"}

STDLIB = set(sys.stdlib_module_names)


def scan_imports(project_root: Path) -> dict[str, set[Path]]:
    """
    Возвращает:
    {
        "aiohttp": {Path("src/api/client.py")},
        "pytest": {Path("tests/test_api.py")},
    }
    """

    imports: dict[str, set[Path]] = {}

    for py_file in iter_python_files(project_root):
        found = extract_imports_from_file(py_file)

        for name in found:
            if name in STDLIB: # Потому что os sys и json в зависимостях нет места
                continue
            imports.setdefault(name, set()).add(py_file)

    return imports

def iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if is_excluded(path):
            continue
        yield path

def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)

def extract_imports_from_file(path: Path) -> set[str]:
    imports = set()

    try:
        src = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return imports

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return imports

    collect_imports_from_ast(imports, tree)

    return imports

def collect_imports_from_ast(imports: set[str], tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
