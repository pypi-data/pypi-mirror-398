from pydoctor.scanner.venv import check_venv


def test_venv_check_structure():
    r = check_venv()
    assert isinstance(r, dict)
    assert r["title"] == "Virtual Environment"
