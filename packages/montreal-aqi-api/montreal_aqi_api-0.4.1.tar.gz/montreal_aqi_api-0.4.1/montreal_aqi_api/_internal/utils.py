from __future__ import annotations

import importlib.metadata
import logging
import tomllib
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)


def _read_version_from_pyproject(pyproject: Path) -> str | None:
    try:
        with pyproject.open("rb") as f:
            data: Mapping[str, Any] = tomllib.load(f)

        project = data.get("project")
        if not isinstance(project, Mapping):
            return None

        version = project.get("version")
        if isinstance(version, str):
            return version

    except Exception as exc:  # defensive: malformed toml, permissions, etc.
        logger.debug("Failed to read version from %s: %s", pyproject, exc)

    return None


def get_version() -> str:
    logger.debug("Resolving package version")

    current = Path(__file__).resolve()

    for parent in current.parents:
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            logger.debug("Found pyproject.toml at %s", pyproject)
            version = _read_version_from_pyproject(pyproject)
            if version is not None:
                return version

    try:
        version = importlib.metadata.version("montreal-aqi-api")
        logger.debug("Resolved version from package metadata")
        return version
    except importlib.metadata.PackageNotFoundError:
        logger.warning("Package metadata not found, using fallback version")
        return "0.0.0"
