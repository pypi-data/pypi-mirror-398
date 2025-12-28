import os


def get_requirements():
    if not os.path.exists("requirements.txt"):
        return []
    with open("requirements.txt") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]
