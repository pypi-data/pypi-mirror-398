import os
import pytest
from pathlib import Path
from gdutils.utils.io import (
    clean_dir,
    remove_if_exists,
    remove_files,
    move_files,
    copy_files,
    copy_file,
    load_str,
    dump_str,
    greedy_download,
    get_timestamp,
    get_iterable,
    dump_json,
    load_json,
    fPath,
)


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


def test_clean_dir(tmp_path: Path):
    d = tmp_path / "to_delete"
    d.mkdir()
    (d / "file.txt").touch()
    clean_dir(d)
    assert not d.exists()
    
    # Should not raise if dir doesn't exist
    clean_dir(d)


def test_remove_if_exists(tmp_path: Path):
    f = tmp_path / "file.txt"
    f.touch()
    remove_if_exists(f)
    assert not f.exists()
    
    # Should not raise if file doesn't exist
    remove_if_exists(f)


def test_remove_files(tmp_path: Path):
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.log"
    f3 = tmp_path / "keep.txt"
    f1.touch()
    f2.touch()
    f3.touch()
    
    # Remove all txt files
    remove_files(tmp_path / "*.txt")
    
    assert not f1.exists()
    assert not f3.exists()
    assert f2.exists()


def test_move_files(tmp_path: Path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    
    f1 = src / "file1.txt"
    f1.write_text("content")
    
    move_files(src / "*.txt", dst)
    
    assert not f1.exists()
    assert (dst / "file1.txt").exists()
    assert (dst / "file1.txt").read_text() == "content"


def test_copy_files(tmp_path: Path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    
    f1 = src / "file1.txt"
    f1.write_text("content")
    
    copy_files(src / "*.txt", dst)
    
    assert f1.exists()
    assert (dst / "file1.txt").exists()
    assert (dst / "file1.txt").read_text() == "content"


def test_copy_file(tmp_path: Path):
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    f1.write_text("content")
    
    copy_file(f1, f2)
    
    assert f1.exists()
    assert f2.exists()
    assert f2.read_text() == "content"


def test_load_dump_str(tmp_path: Path):
    f = tmp_path / "data.txt"
    data = "some data"
    
    dump_str(f, data)
    assert f.read_text() == data
    
    loaded = load_str(f)
    assert loaded == data


def test_greedy_download(tmp_path: Path):
    f1 = tmp_path / "exist.txt"
    f1.touch()
    f2 = tmp_path / "missing.txt"
    
    assert greedy_download(f1) is False
    assert greedy_download(f1, force=True) is True
    assert greedy_download(f2) is True
    assert greedy_download(f1, f2) is True


def test_get_timestamp():
    ts = get_timestamp()
    assert len(ts) == 15 # ddmmyyyy_HHMMSS
    assert "_" in ts


def test_get_iterable():
    assert get_iterable("abc") == ("abc",)
    assert get_iterable(["a", "b"]) == ["a", "b"]
    assert get_iterable(1) == (1,)


def test_json_io(tmp_path: Path):
    f = tmp_path / "data.json"
    data = {"key": "value"}
    
    dump_json(f, data)
    assert f.exists()
    
    loaded = load_json(f)
    assert loaded == data
