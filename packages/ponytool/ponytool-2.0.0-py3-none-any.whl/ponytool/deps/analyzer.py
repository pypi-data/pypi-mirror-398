from pathlib import Path
from ponytool.deps.collect_packages import (match_package, get_unused_packages, get_unmatched_imports)


def analyze_usage(
        imports: dict[str, set[Path]],
        installed: dict[str, str]
) -> dict[str, object]:
    matched = match_package(imports, installed)
    matched_names = set(matched)

    unmatched = get_unmatched_imports(
        imports=set(imports),
        matched_packages=matched_names,
    )

    unused = get_unused_packages(
        installed=installed,
        matched_packages=matched_names,
    )

    return {
        "matched": matched,
        "unmatched_imports": unmatched,
        "unused_packages": unused,
    }