from importlib.metadata import version, PackageNotFoundError
from pydoctor.parsers.requirements_parser import get_requirements


def check_dependencies():
    reqs = get_requirements()
    missing = []

    for r in reqs:
        name = r.split("==")[0].strip()
        try:
            version(name)
        except PackageNotFoundError:
            missing.append(name)

    if missing:
        return {
            "title": "Dependencies",
            "ok": False,
            "reason": f"Missing packages: {', '.join(missing)}",
            "fix": [f"pip install {' '.join(missing)}"],
        }

    return {
        "title": "Dependencies",
        "ok": True,
        "reason": "",
        "fix": [],
    }
