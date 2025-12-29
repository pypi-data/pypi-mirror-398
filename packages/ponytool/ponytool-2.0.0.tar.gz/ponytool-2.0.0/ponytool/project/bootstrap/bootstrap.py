from pathlib import Path
from datetime import datetime

from ponytool.utils.ui import warning, success, info
from ponytool.project.bootstrap.template.bootstrap_cfg import GITIGNORE_TEMPLATE, README_TEMPLATE, LICENSE_TEMPLATE

CURRENT_YEAR = datetime.now().year

def create_readme(root: Path):
    readme = root / "README.md"
    if readme.exists():
        warning(f"{readme} уже существует — пропускаем")
        return

    readme.write_text(README_TEMPLATE, encoding="utf-8")
    success("Создан README.md")

def create_gitignore(root: Path):
    ignore = root / ".gitignore"
    if ignore.exists():
        warning(f"{ignore} уже существует — пропускаем")
        return

    ignore.write_text(GITIGNORE_TEMPLATE, encoding="utf-8")
    success("Создан .gitignore")

def create_license(root: Path):
    license_file = root / "LICENSE"
    if license_file.exists():
        warning(f"{license_file} уже существует - пропускаем")
        return

    license_text = LICENSE_TEMPLATE.format(year=CURRENT_YEAR)
    license_file.write_text(license_text, encoding="utf-8")
    success("Создан LICENSE")
    info("LICENSE создан (MIT). При необходимости отредактируйте автора и год.")

def run():
    base = Path.cwd()

    info("Генерация .gitignore, README.md, LICENSE...")

    create_readme(base)
    create_gitignore(base)
    create_license(base)

    success("Генерация завершена.")
