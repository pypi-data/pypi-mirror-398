from pathlib import Path

def normalize(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return name.lower().replace("-", "_")

def matches(import_name: str, package_name: str) -> bool:
    imp = normalize(import_name)
    pkg = normalize(package_name)

    return (
        imp == pkg
        or imp == pkg.replace("-", "_")
        or imp.replace("-", "_") == pkg
    )

def match_package(
        imports: dict[str, set[Path]],
        installed: dict[str, str]
) -> dict[str, dict[str, set | str]]:
    """
    Возвращает:
    {
        "aiohttp": {
            "version": "3.13.2",
            "imports": {"aiohttp"},
            "files": {Path(...)},
        }
    }
    """
    result: dict[str, dict[str, set | str]] = {}

    for import_name, files in imports.items():
        for pkg_name, version in installed.items():
            if not matches(import_name, pkg_name):
                continue

            entry = result.setdefault(
                pkg_name,
                {
                    "version": version,
                    "imports": set(),
                    "files": set(),
                }
            )

            entry["imports"].add(import_name)
            entry["files"].update(files)

    return result

def get_unmatched_imports(
        imports: set[str],
        matched_packages: dict[str, str],
) -> set[str]:
    matched_imports = set()

    for pkg in matched_packages:
        matched_imports.add(normalize(pkg))

    return {
        imp for imp in imports
        if normalize(imp) not in matched_imports
    }

def get_unused_packages(
        installed: dict[str, str],
        matched_packages: dict[str, str]
) -> set[str]:
    return set(installed) - set(matched_packages)

