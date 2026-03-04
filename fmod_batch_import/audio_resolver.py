"""Audio resolver module for strict filename matching."""

from __future__ import annotations

import logging
from pathlib import Path


class AudioResolver:
    """Resolves audio filenames to absolute paths within a base directory."""

    allowed_extensions = (".wav", ".mp3", ".ogg", ".aif", ".aiff", ".wma", ".flac")

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self._logger = logging.getLogger(__name__)

    def resolve(self, filename: str) -> Path:
        """Resolve a filename against the base directory.

        Args:
            filename: Filename from CSV (no subpath)

        Returns:
            Absolute path to the matched audio file

        Raises:
            FileNotFoundError: If no matching file is found
        """
        if not self.base_dir.exists():
            raise FileNotFoundError(f"Audio base directory not found: {self.base_dir}")

        target_has_extension = Path(filename).suffix != ""
        matches: list[Path] = []

        if target_has_extension:
            for path in self.base_dir.rglob("*"):
                if path.is_file() and path.name == filename:
                    matches.append(path)
        else:
            for path in self.base_dir.rglob("*"):
                if (
                    path.is_file()
                    and path.stem == filename
                    and path.suffix in self.allowed_extensions
                ):
                    matches.append(path)

        if not matches:
            raise FileNotFoundError(f"Audio file not found: {filename}")

        matches_sorted = sorted(matches, key=lambda match: str(match))
        if len(matches_sorted) > 1:
            self._logger.warning(
                "Multiple audio files matched '%s'. Using '%s'.",
                filename,
                matches_sorted[0],
            )

        return matches_sorted[0].resolve()
