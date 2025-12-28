import sys
import os


def check_venv():
    in_venv = sys.prefix != sys.base_prefix

    if not in_venv:
        return {
            "title": "Virtual Environment",
            "ok": False,
            "reason": "No active virtual environment",
            "fix": [
                "python -m venv .venv",
                "source .venv/bin/activate (Linux/macOS)",
                ".venv\\Scripts\\activate (Windows)"
            ]
        }

    return {
        "title": "Virtual Environment",
        "ok": True,
        "reason": "",
        "fix": []
    }
