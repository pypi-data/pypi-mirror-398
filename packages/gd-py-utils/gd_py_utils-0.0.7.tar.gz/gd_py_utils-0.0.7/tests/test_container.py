from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gdutils.datacontainer.container import Container, ContainerInfosError


def test_creates_root_and_infos(tmp_path: Path):
    root = tmp_path / "exp"
    ct = Container(root)
    assert ct.path == root.resolve()
    assert ct.path.exists()
    # infos is written only on save()/context exit
    assert not (ct.path / ct.infos_name).exists()


def test_container_behaves_like_path(tmp_path: Path):
    root = tmp_path / "exp"
    ct = Container(root, clean=True)

    # PathLike
    assert os.fspath(ct) == str(root.resolve())
    assert Path(ct) == root.resolve()

    # Delegated Path methods/properties
    assert ct.exists()
    assert ct.name == "exp"


def test_clean_removes_existing_dir(tmp_path: Path):
    root = tmp_path / "exp"
    root.mkdir()
    (root / "old.txt").write_text("x", encoding="utf-8")

    ct = Container(root, clean=True)
    assert not (ct.path / "old.txt").exists()


def test_mkdir_creates_directory(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True)
    p = ct.mkdir("a/b/c")
    assert p.is_dir()
    assert p == ct.path / "a/b/c"


def test_slash_requires_file_path(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True)
    with pytest.raises(RuntimeError):
        _ = ct / "just_a_dir"


def test_slash_creates_parents_and_autoregisters(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True)
    f = ct / "results/output.npy"

    assert f.parent.is_dir()
    assert f == ct.path / "results/output.npy"
    assert ct.output == f


def test_save_writes_infos_and_reload_restores_mapping(tmp_path: Path):
    root = tmp_path / "exp"

    with Container(root, clean=True) as ct:
        infos_name = ct.infos_name
        _ = ct / "inputs/data.npy"
        _ = ct / "results/output.npy"
        ct.save()

    infos = root / infos_name
    assert infos.is_file()

    data = json.loads(infos.read_text(encoding="utf-8"))
    assert data["files"]["data"] == "inputs/data.npy"
    assert data["files"]["output"] == "results/output.npy"

    ct2 = Container(root)
    assert ct2.data == root / "inputs/data.npy"
    assert ct2.output == root / "results/output.npy"


def test_collision_raises_keyerror(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True)

    _ = ct / "a/output.npy"
    with pytest.raises(KeyError):
        _ = ct / "b/output.npy"


def test_getattr_missing_key_raises_attribute_error(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True)
    with pytest.raises(AttributeError):
        _ = ct.does_not_exist


def test_absolute_paths_are_returned_but_not_registered(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True)

    absf = (tmp_path / "outside.txt").resolve()
    p = ct / absf
    assert p == absf

    # must not auto-register absolute paths
    with pytest.raises(AttributeError):
        _ = ct.outside


def test_auto_register_can_be_disabled(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True, auto_register=False)

    f = ct / "results/output.npy"
    assert f == ct.path / "results/output.npy"
    assert f.exists() is False  # path only, we did not write the file

    with pytest.raises(AttributeError):
        _ = ct.output


def test_context_manager_always_persists_infos(tmp_path: Path):
    root = tmp_path / "exp"

    with Container(root, clean=True) as ct:
        infos_name = ct.infos_name
        _ = ct / "a/data.npy"
        _ = ct / "b/output.npy"
        # no explicit save()

    infos = root / infos_name
    assert infos.is_file()

    data = json.loads(infos.read_text(encoding="utf-8"))
    assert data["files"]["data"] == "a/data.npy"
    assert data["files"]["output"] == "b/output.npy"


def test_free_releases_key_and_allows_reuse(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True)

    f1 = ct / "a/output.npy"
    assert ct.output == f1

    ct.free("output")
    with pytest.raises(AttributeError):
        _ = ct.output

    f2 = ct / "b/output.npy"
    assert ct.output == f2


def test_free_unknown_key_is_noop(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True)
    ct.free("missing")  # should not raise


def test_infos_json_invalid_json_raises(tmp_path: Path):
    root = tmp_path / "exp"
    root.mkdir()

    infos_name = Container(root).infos_name
    (root / infos_name).write_text("{not: valid json", encoding="utf-8")

    with pytest.raises(ContainerInfosError):
        _ = Container(root)


def test_infos_json_wrong_schema_raises(tmp_path: Path):
    root = tmp_path / "exp"
    root.mkdir()

    infos_name = Container(root).infos_name
    (root / infos_name).write_text(json.dumps({"files": ["nope"]}), encoding="utf-8")

    with pytest.raises(ContainerInfosError):
        _ = Container(root)


def test_infos_json_wrong_entry_types_raises(tmp_path: Path):
    root = tmp_path / "exp"
    root.mkdir()

    infos_name = Container(root).infos_name
    (root / infos_name).write_text(json.dumps({"files": {"ok": 123}}), encoding="utf-8")

    with pytest.raises(ContainerInfosError):
        _ = Container(root)


def test_register_same_key_same_path_is_idempotent(tmp_path: Path):
    ct = Container(tmp_path / "exp", clean=True)

    f = ct / "a/output.npy"
    ct.register("output", "a/output.npy")
    assert ct.output == f


def test_relative_paths_in_infos_are_resolved_under_root(tmp_path: Path):
    root = tmp_path / "exp"
    root.mkdir()

    infos_name = Container(root).infos_name
    (root / infos_name).write_text(
        json.dumps({"files": {"x": "sub/dir/file.txt"}}), encoding="utf-8"
    )

    ct = Container(root)
    assert ct.x == root / "sub/dir/file.txt"


def test_save_is_deterministic_sorted_keys(tmp_path: Path):
    root = tmp_path / "exp"

    ct = Container(root, clean=True)
    _ = ct / "b/output.npy"
    _ = ct / "a/data.npy"
    ct.save()

    raw = (root / ct.infos_name).read_text(encoding="utf-8")
    assert raw.find('"data"') < raw.find('"output"')


# def test_tree_view_contains_all_registered_keys(tmp_path: Path):
#     root = tmp_path / "exp_tree"
#     ct = Container(root, clean=True)

#     _ = ct / "metrics/loss.csv"
#     _ = ct / "models/run_01/weights.pth"

#     tree_str = ct.tree(show_keys=True)

#     assert "Container: exp_tree" in tree_str
#     assert "metrics" in tree_str
#     assert "models" in tree_str
#     assert "run_01" in tree_str
#     assert "loss -> loss.csv" in tree_str
#     assert "weights -> weights.pth" in tree_str


# def test_tree_view_show_keys_toggle(tmp_path: Path):
#     ct = Container(tmp_path / "exp_toggle", clean=True)
#     _ = ct / "data/input.json"

#     tree_with_keys = ct.tree(show_keys=True)
#     assert "input -> input.json" in tree_with_keys

#     tree_no_keys = ct.tree(show_keys=False)
#     assert "input.json" in tree_no_keys
#     assert "input ->" not in tree_no_keys
