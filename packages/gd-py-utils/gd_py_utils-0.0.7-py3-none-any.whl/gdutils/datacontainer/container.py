from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Dict, Union, Any
import os
import json

PathLike = Union[str, Path, os.PathLike[str]]


class ContainerInfosError(RuntimeError):
    """
    Raised when the container registry file cannot be read or does not match the
    expected schema.
    """


@dataclass
class Container(os.PathLike[str]):
    """
    A small filesystem container with an optional key->relative-path registry.

    The container owns a root directory and persists a registry file (default:
    `tree.json`) storing logical keys mapped to relative file paths.

    Design choices / conventions:

    - `container / "file.ext"` is a file-creation helper:
        - It ensures parent directories exist.
        - Optionally auto-registers the file under key = stem ("file").

    - Directories should be created via `mkdir()` (not `/`):
        - Enforced by requiring a suffix when using `/` with a relative path.

    Args:
        root: Root directory path of the container.
        clean: If True, aggressively removes the existing root directory contents
            (files and subdirectories) before recreating it.
        infos_name: Registry filename stored at container root.
        auto_register: If True, `/` on a relative file path auto-registers the
            file under key = stem.
    """

    root: PathLike
    clean: bool = False
    infos_name: str = "tree.json"
    auto_register: bool = True

    _root: Path = field(init=False, repr=False)
    _infos_path: Path = field(init=False, repr=False)
    _files: Dict[str, str] = field(init=False, default_factory=dict, repr=False)
    _extras: Dict[str, Any] = field(init=False, default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """
        Initialize the container root and load the registry.

        If `clean=True`, recursively deletes the root directory contents, then
        recreates the root directory.
        """
        self._root = Path(self.root).expanduser().resolve()
        if self.clean:
            # replace with your clean_dir
            if self._root.exists():
                for p in sorted(self._root.glob("**/*"), reverse=True):
                    if p.is_file() or p.is_symlink():
                        p.unlink(missing_ok=True)
                    elif p.is_dir():
                        p.rmdir()
                self._root.rmdir()
        self._root.mkdir(parents=True, exist_ok=True)
        self._infos_path = self._root / self.infos_name
        self._files, self._extras = self._load_infos()

    # --- Path-like core -------------------------------------------------
    @property
    def path(self) -> Path:
        """Return the container root as a Path."""
        return self._root

    def __fspath__(self) -> str:
        """Allow using `os.fspath(container)` and passing to stdlib path APIs."""
        return os.fspath(self._root)

    def __str__(self) -> str:
        """String representation is the root path."""
        return str(self._root)

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Container({self._root!s})"

    def __truediv__(self, other: PathLike) -> Path:
        """
        Build a path under the container root.

        Behavior:
        
            - If `other` is an absolute path: return it as-is (no registration).
            - If `other` is relative:
            
                * Requires a suffix (file-only policy). Use `mkdir()` for dirs.
                * Ensures parent dirs exist under container root.
                * If `auto_register=True`, registers under key = `other.stem`.

        Raises:
        
            RuntimeError: If a relative path without suffix is provided.
            KeyError: If auto-registration conflicts with an existing key pointing
                to a different path.
        """
        other_p = Path(other)
        if other_p.is_absolute():
            # absolute paths: return as-is, do not register
            target = other_p
        else:
            if other_p.suffix == "":
                raise RuntimeError(
                    "Use mkdir() for directories; '/' is for files only."
                )
            target = self._root / other_p

        target.parent.mkdir(parents=True, exist_ok=True)

        if self.auto_register and not other_p.is_absolute():
            self.register(other_p.stem, target.relative_to(self._root).as_posix())

        return target

    def joinpath(self, *parts: PathLike) -> Path:
        """
        Join path components under the container root.

        This behaves like `Path.joinpath` and does *not* enforce the "/" suffix
        policy nor auto-register.
        """
        # behaves like Path.joinpath, but keeps your '/' policy if you want:
        return self._root.joinpath(*map(Path, parts))

    # Delegate any unknown attribute to the underlying Path
    # IMPORTANT: keys take precedence; else Path methods/properties work.
    def __getattr__(self, name: str) -> Any:
        """
        Provide ergonomic access to registered files via attribute lookup.

        If `name` is a registered key, this returns `self.get(name)`.
        Otherwise, it forwards the attribute access to the underlying root Path.
        """
        if name in self._files:
            return self.get(name)
        return getattr(self._root, name)

    # --- Registry -------------------------------------------------------
    def _load_infos(self) -> tuple[Dict[str, str], Dict[str, Any]]:
        """
        Load the registry file if it exists.

        Expected schema:
            {"files": {"key": "relative/path.ext", ...}}

        Returns:
            A mapping of key -> relative POSIX path.

        Raises:
            ContainerInfosError: If the file cannot be read/parsed or schema invalid.
        """
        if not self._infos_path.is_file():
            return {}, {}
        try:
            data = json.loads(self._infos_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise ContainerInfosError(f"Cannot read {self._infos_path}") from e

        files = data.get("files")
        if not isinstance(files, dict):
            raise ContainerInfosError("Invalid schema: expected {'files': {key: path}}")

        out: Dict[str, str] = {}
        for k, v in files.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ContainerInfosError(
                    "Invalid entry types: keys/values must be strings"
                )
            out[k] = v
        extras = {k: v for k, v in data.items() if k != "files"}
        return out, extras

    def save(self) -> None:
        """
        Persist the current registry to disk.

        Writes JSON to `self._infos_path` with stable ordering of keys.
        """
        payload = {"files": dict(sorted(self._files.items())), **self._extras}
        self._infos_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def __enter__(self) -> "Container":
        """Context manager entry; returns self."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Context manager exit; always saves the registry."""
        self.save()

    def register(self, key: str, relpath: PathLike) -> Path:
        """
        Register a logical key to a relative path.

        Parameters:
            key: Logical name used to retrieve the file later.
            relpath: Path relative to the container root (stored as POSIX).

        Returns:
            The absolute path (under root) corresponding to the registered entry.

        Raises:
            KeyError: If `key` is already registered to a different relative path.
        """
        if "/" in key or "\\" in key:
            raise ValueError(f"Invalid registry key {key!r}: '/' not allowed")
        rel = Path(relpath).as_posix()
        if key in self._files and self._files[key] != rel:
            raise KeyError(f"{key!r} already registered as {self._files[key]!r}")
        self._files[key] = rel
        return self._root / rel

    def free(self, key: str) -> None:
        """Remove a key from the registry (no-op if missing)."""
        self._files.pop(key, None)

    def get(self, key: str) -> Path:
        """
        Resolve a registered key to an absolute path.

        Raises:
            AttributeError: If the key is not registered (to play nicely with __getattr__).
        """
        try:
            return self._root / self._files[key]
        except KeyError as e:
            raise AttributeError(key) from e

    def mkdir(
        self, relpath: PathLike, *, parents: bool = True, exist_ok: bool = True
    ) -> Path:
        """
        Create a directory under the container root.

        This is the preferred way to create directories (instead of using `/`).
        """
        p = self._root / Path(relpath)
        p.mkdir(parents=parents, exist_ok=exist_ok)
        return p

    # def tree(self, show_keys: bool = False) -> str:
    #     """
    #     Generate a visual tree representation of registered files.

    #     Parameters:
    #         show_keys: If True, leaf entries are displayed as 'logical_key -> filename'.
    #             If False, leaf entries show only the filename.

    #     Returns:
    #         A formatted tree string (built using `treelib`).
    #     """
    #     from treelib.tree import Tree

    #     tree = Tree()
    #     tree.create_node(tag=f"Container: {self._root.name}", identifier="root")

    #     # deterministic layout
    #     sorted_items = sorted(self._files.items(), key=lambda kv: kv[1])

    #     for key, relpath in sorted_items:
    #         parts = Path(relpath).parts
    #         current_id = "root"

    #         for i, part in enumerate(parts):
    #             node_id = "/".join(parts[: i + 1])  # unique id by full prefix

    #             if not tree.contains(node_id):
    #                 is_last = i == len(parts) - 1
    #                 label = f"{key} -> {part}" if (is_last and show_keys) else part
    #                 tree.create_node(tag=label, identifier=node_id, parent=current_id)

    #             current_id = node_id

    #     return str(tree.show(stdout=False))

    def get_extra(self, key: str, default: Any = None) -> Any:
        return self._extras.get(key, default)

    def set_extra(self, key: str, value: Any) -> None:
        self._extras[key] = value


log = logging.getLogger(__name__)
