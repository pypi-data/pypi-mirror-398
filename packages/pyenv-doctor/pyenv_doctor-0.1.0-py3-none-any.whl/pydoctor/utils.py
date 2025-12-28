import subprocess


def run(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return out.decode().strip()
    except Exception:
        return None
