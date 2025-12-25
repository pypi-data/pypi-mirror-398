from __future__ import annotations

from tempfile import TemporaryDirectory
from typing import Any

from .container import Container


class TempContainer(Container):
    """
    A Container that uses a temporary directory as its root.
    The directory is automatically cleaned up when the context manager exits.
    """

    def __init__(
        self,
        clean: bool = False,
        infos_name: str = "tree.json",
        auto_register: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a TempContainer.

        Parameters:
            clean: Passed to Container (default False).
            infos_name: Registry filename (default "tree.json").
            auto_register: Whether to auto-register files (default True).
            **kwargs: Additional arguments passed to TemporaryDirectory
                      (suffix, prefix, dir, ignore_cleanup_errors).
        """
        # Extract TemporaryDirectory args
        temp_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in ["suffix", "prefix", "dir", "ignore_cleanup_errors"]
        }
        self._temp_dir = TemporaryDirectory(**temp_kwargs)

        super().__init__(
            root=self._temp_dir.name,
            clean=clean,
            infos_name=infos_name,
            auto_register=auto_register,
        )

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """
        Exit the context manager.

        Saves the container registry (via super), then cleans up the temporary directory.
        """
        try:
            super().__exit__(exc_type, exc, tb)
        finally:
            self._temp_dir.cleanup()

