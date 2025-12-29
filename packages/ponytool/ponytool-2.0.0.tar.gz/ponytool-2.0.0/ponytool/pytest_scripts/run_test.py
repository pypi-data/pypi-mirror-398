import sys

from ponytool.utils.shell import run, check
from ponytool.utils.ui import info, error

def run_test(coverage=False, html=False):
    info("Running tests")
    cmd = ['pytest']

    if coverage:
        cmd.append("--cov")

    if html:
        cmd.append("--cov-report=html")

    python = find_venv_python()
    ensure_pytest(python)
    run([python, "-m", *cmd])

def find_venv_python() -> str:
    if sys.prefix == sys.base_prefix:
        error(
            "Virtual environment not detected.\n"
            "Activate venv before running tests."
        )
        raise SystemExit(1)

    return sys.executable

def ensure_pytest(python: str):
    ok = check([python, "-m", "pytest", "--version"])

    if not ok:
        error(
            "pytest is not installed in this virtual environment.\n"
            "Install it with: pip install pytest"
        )
        raise SystemExit(1)