# Single-source version: prefer package metadata when installed, otherwise
# fall back to parsing pyproject.toml next to the project root.
# This keeps the version defined in one place (pyproject.toml) while still
# exposing __version__ for runtime inspection.
from pathlib import Path
import re

try:
    # importlib.metadata is the recommended way to get the installed package version
    from importlib.metadata import version as _pkg_version  # type: ignore
    __version__ = _pkg_version("klogg")
except Exception:
    # Fallback: try to read pyproject.toml located at the repository root
    try:
        _pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        ver = "0.0.0"
        if _pyproject.exists():
            txt = _pyproject.read_text(encoding="utf-8")
            m = re.search(r'^\s*version\s*=\s*"([^"]+)"\s*$', txt, re.MULTILINE)
            if m:
                ver = m.group(1)
        __version__ = ver
    except Exception:
        __version__ = "0.0.0"
