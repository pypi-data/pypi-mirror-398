import sys
from packaging.specifiers import SpecifierSet
from pydoctor.parsers.pyproject_parser import get_required_python


def check_python_version():
    req = get_required_python()
    cur = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    if not req:
        return {
            "title": "Python Version",
            "ok": True,
            "reason": "",
            "fix": [],
        }

    spec = SpecifierSet(req)

    if cur not in spec:
        return {
            "title": "Python Version",
            "ok": False,
            "reason": f"Detected Python {cur}, required {req}",
            "fix": [
                "pyenv install 3.10.14",
                "pyenv local 3.10.14",
            ],
        }

    return {
        "title": "Python Version",
        "ok": True,
        "reason": "",
        "fix": [],
    }
