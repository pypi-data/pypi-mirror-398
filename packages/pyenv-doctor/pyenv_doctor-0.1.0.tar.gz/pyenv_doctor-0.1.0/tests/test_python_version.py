from pydoctor.scanner.python_version import check_python_version


def test_python_version_returns_dict():
    r = check_python_version()
    assert isinstance(r, dict)
    assert "title" in r
    assert "ok" in r
    assert "reason" in r
    assert "fix" in r
