from pydoctor.scanner.dependencies import check_dependencies


def test_dependencies_check_runs():
    r = check_dependencies()
    assert isinstance(r, dict)
    assert "ok" in r
