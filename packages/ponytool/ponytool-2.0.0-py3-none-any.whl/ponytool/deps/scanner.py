from ponytool.deps.scan.env import get_active_venv, get_active_python
from ponytool.deps.scan.site_packages import get_site_packages
from ponytool.deps.scan.collector import collect_installed_packages
from ponytool.utils.ui import error


def scan() -> dict:
    try:
        venv = get_active_venv()
        python = get_active_python()
    except RuntimeError as e:
        error(str(e))
        raise SystemExit(1)

    site_packages = get_site_packages(python)
    if not site_packages:
        error("site-packages not found")
        raise SystemExit(1)

    packages = collect_installed_packages(site_packages)

    return {
        "python": python,
        "venv": venv,
        "site_packages": site_packages,
        "packages": packages,
    }
