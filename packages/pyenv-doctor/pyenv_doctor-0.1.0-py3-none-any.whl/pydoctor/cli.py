import argparse
from pydoctor.scanner.python_version import check_python_version
from pydoctor.scanner.venv import check_venv
from pydoctor.scanner.dependencies import check_dependencies
from pydoctor.scanner.system_libs import check_system_libs
from pydoctor.reporter import print_report


def main():
    p = argparse.ArgumentParser(prog="pydoctor")
    p.add_argument("command", choices=["scan"])
    args = p.parse_args()

    if args.command == "scan":
        results = [
            check_python_version(),
            check_venv(),
            check_dependencies(),
            check_system_libs(),
        ]
        print_report(results)
