from pathlib import Path

from ponytool.deps.scan.metadata import read_metadata


def normalize_name(name: str) -> str:
    return name.lower().replace("-", "_")

EXCLUDE_PACKAGES = {"pip", "setuptools", "wheel"}

def collect_from_site_dir(site_dir: Path, packages: dict[str, str]) -> None:
    for dist_info in site_dir.glob("*.dist-info"):
        meta = read_metadata(dist_info)
        if not meta:
            continue

        name = normalize_name(meta['name'])

        if name in EXCLUDE_PACKAGES:
            continue

        packages[name] = meta['version']


def collect_installed_packages(site_pkg_dirs: list[Path]) -> dict[str, str]:
    packages: dict[str, str] = {}

    for site_dir in site_pkg_dirs:
        collect_from_site_dir(site_dir, packages)

    return dict(sorted(packages.items()))
