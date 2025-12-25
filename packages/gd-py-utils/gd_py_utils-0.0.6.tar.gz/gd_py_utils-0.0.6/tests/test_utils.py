from pathlib import Path

from gdutils.utils.io import fPath


def test_fpath_resolves_relative_to_file_and_creates_dirs(tmp_path: Path):
    fake_file = tmp_path / "script.py"

    p = fPath(fake_file, "out", "results", mkdir=True)

    assert p == tmp_path / "out" / "results"
    assert p.exists()
    assert p.is_dir()


def test_fpath_does_not_create_dirs_by_default(tmp_path: Path):
    fake_file = tmp_path / "script.py"

    p = fPath(fake_file, "out")

    assert p == tmp_path / "out"
    assert not p.exists()
