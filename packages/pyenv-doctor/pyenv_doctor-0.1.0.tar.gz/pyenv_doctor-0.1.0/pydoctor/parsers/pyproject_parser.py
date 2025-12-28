import os

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def get_required_python():
    if not os.path.exists("pyproject.toml"):
        return None
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data.get("project", {}).get("requires-python")
