from pydoctor.parsers.requirements_parser import get_requirements

MAP = {
    "psycopg2": ("libpq-dev", "brew install postgresql"),
    "lxml": ("libxml2-dev libxslt-dev", "brew install libxml2"),
    "cryptography": ("libssl-dev", "brew install openssl"),
}


def check_system_libs():
    reqs = get_requirements()
    missing = []

    fixes = []

    for r in reqs:
        pkg = r.split("==")[0]
        if pkg in MAP:
            missing.append(pkg)
            fixes.append(f"Ubuntu: sudo apt install {MAP[pkg][0]}")
            fixes.append(f"macOS: {MAP[pkg][1]}")

    if missing:
        return {
            "title": "System Libraries",
            "ok": False,
            "reason": f"Potential missing system libs for {', '.join(missing)}",
            "fix": fixes
        }

    return {
        "title": "System Libraries",
        "ok": True,
        "reason": "",
        "fix": []
    }
