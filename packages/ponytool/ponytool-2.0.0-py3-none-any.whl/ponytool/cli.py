import argparse

from ponytool.utils.ui import error, info

from ponytool.project.content_from_file import run
from ponytool.project.bootstrap.bootstrap import run as boot
from ponytool.deps.generate import generate_requirements as gen
from ponytool.pytest_scripts.run_test import run_test

def main():
    parser = argparse.ArgumentParser(
        prog="pony",
        description="PonyTool CLI",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init")
    subparsers.add_parser("deps")
    subparsers.add_parser("bootstrap")
    test_parser = subparsers.add_parser("test")
    test_parser.add_argument('-c', '--coverage', action='store_true')
    test_parser.add_argument('--html', action='store_true')

    args = parser.parse_args()

    try:
        if args.command == "test":
            run_test(
                coverage=args.coverage,
                html=args.html,
            )
            return

        COMMANDS = {
            "init": lambda: run(),
            "deps": lambda: gen(args),
            "bootstrap": lambda: boot(),
        }

        COMMANDS[args.command]()

    except KeyboardInterrupt:
        info("\nОперация отменена")
    except Exception as err:
        error(f"Ошибка выполнения команды '{args.command}'")
        error(str(err))
