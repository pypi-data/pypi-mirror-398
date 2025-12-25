import shutil
import json
import os
import glob
from typing import Any, Iterable
from pathlib import Path
from datetime import datetime

# import yaml




def fPath(filepath: str | Path, *path_parts: str, mkdir: bool = False) -> Path:
    """
    Construct a path relative to the parent directory of a given file path.

    Args:
        filepath: The reference file path (e.g. `__file__`).
        *path_parts: Additional path components to join.
        mkdir: If True, create the resulting directory (including parents) if it doesn't exist.

    Returns:
        The resolved Path object.
    """
    full_path = Path(filepath).parent.joinpath(*path_parts)
    if mkdir:
        full_path.mkdir(exist_ok=True, parents=True)
    return full_path


def clean_dir(path: str | Path):
    """
    Recursively delete a directory if it exists.

    Args:
        path: The directory path to remove.
    """
    if Path(path).exists():
        shutil.rmtree(str(path))


# ---------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------


def dump_json(filename: str | Path, data: dict, **kwargs: Any):
    """
    Write data to a JSON file.

    Args:
        filename: The output file path.
        data: The serializable data to write.
        **kwargs: Additional arguments passed to `json.dump`. Defaults to `indent=4`.
    """
    kwargs.setdefault("indent", 4)
    with open(str(filename), "w") as f:
        json.dump(data, f, **kwargs)


def load_json(filename: str | Path, **kwargs: Any) -> dict:
    """
    Read data from a JSON file.

    Args:
        filename: The input file path.
        **kwargs: Additional arguments passed to `json.load`.

    Returns:
        The parsed JSON data.
    """
    with open(str(filename), "r") as f:
        return json.load(f, **kwargs)


# # ---------------------------------------------------------------------
# # YAML helpers
# # ---------------------------------------------------------------------

# def dump_yaml(filename: str | Path, data, **kwargs) -> None:
#     """
#     Dump data to YAML using PyYAML safe_dump.
#
#     Defaults:
#     - block style
#     - human-readable
#     """
#     kwargs.setdefault("default_flow_style", False)
#     kwargs.setdefault("sort_keys", False)
#
#     with open(str(filename), "w") as f:
#         yaml.safe_dump(data, f, **kwargs)
#
#
# def load_yaml(filename: str | Path) -> dict:
#     """
#     Load YAML using PyYAML safe_load.
#     """
#     with open(str(filename), "r") as f:
#         return yaml.safe_load(f)


# ---------------------------------------------------------------------
# File/Path helpers
# ---------------------------------------------------------------------


def remove_if_exists(fname: str | Path) -> None:
    """
    Remove a file if it exists.

    Args:
        fname: Path to the file to remove.
    """
    if os.path.exists(fname):
        os.remove(fname)


def remove_files(*patterns: str) -> None:
    """
    Remove files matching the given glob patterns if they exist.

    Args:
        *patterns: Glob patterns of files to remove.
    """
    for pattern in patterns:
        for f in glob.glob(str(pattern)):
            remove_if_exists(f)


def move_files(pattern: str, dest: str | Path) -> None:
    """
    Move files matching a glob pattern to a destination directory.
    Overwrites existing files at the destination.

    Args:
        pattern: Glob pattern for source files.
        dest: Destination directory.
    """
    for f in glob.glob(str(pattern)):
        dest_file = Path(dest) / os.path.basename(f)
        remove_if_exists(dest_file)
        shutil.move(f, str(dest))


def copy_files(pattern: str, dest: str | Path) -> None:
    """
    Copy files matching a glob pattern to a destination directory.

    Args:
        pattern: Glob pattern for source files.
        dest: Destination directory.
    """
    dest_path = Path(dest).absolute()
    for f in glob.glob(str(pattern)):
        shutil.copyfile(f, dest_path / os.path.basename(f))


def copy_file(src: str | Path, dst: str | Path) -> None:
    """
    Copy a single file to a destination path.

    Args:
        src: Source file path.
        dst: Destination file path.
    """
    shutil.copyfile(str(src), str(dst))


def load_str(filename: str | Path, method: str = "read") -> str:
    """
    Load a file content to string.

    Args:
        filename: Path to the file.
        method: Method to call on the file object (default: "read").

    Returns:
        The content of the file.
    """
    with open(str(filename), "r") as f:
        return getattr(f, method)()


def dump_str(filename: str | Path, data: Any) -> None:
    """
    Dump string representation of data to a file.

    Args:
        filename: Output file path.
        data: Data to write (converted to string).
    """
    with open(str(filename), "w") as f:
        f.write(str(data))


def greedy_download(*fnames: str | Path, force: bool = False) -> bool:
    """
    Check if any of the given files are missing.

    Args:
        *fnames: Paths to check.
        force: If True, always returns True.

    Returns:
        True if `force` is set or if any file is missing, False otherwise.
    """
    if force:
        return True
    for x in fnames:
        if not os.path.isfile(x):
            return True
    return False


def get_timestamp(fmt: str = "%d%m%Y_%H%M%S") -> str:
    """
    Return the current timestamp formatted as a string.

    Args:
        fmt: Format string (default: "%d%m%Y_%H%M%S").

    Returns:
        Formatted timestamp string.
    """
    return datetime.now().strftime(fmt)


def get_iterable(x: Any) -> Iterable:
    """
    Ensure x is iterable (and treat string as non-iterable single item).

    Args:
        x: The item to check.

    Returns:
        An iterable containing x, or x itself if it is already an iterable (but not a str).
    """
    if isinstance(x, str):
        return (x,)
    elif isinstance(x, Iterable):
        return x
    else:
        return (x,)
