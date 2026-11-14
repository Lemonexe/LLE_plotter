"""Versioned, atomic best-effort session persistence."""

import json
import os
import time
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from .data import check_state, defaults


def state_path():
    return (
        Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
        / "session.json"
    )


def load(path):
    if not path.exists():
        return defaults(), ""
    try:
        return check_state(json.loads(path.read_text(encoding="utf-8"))), ""
    except (ValueError, KeyError, TypeError, OSError) as exc:
        backup = path.with_name(f"session-damaged-{time.time_ns()}.json")
        try:
            path.rename(backup)
            detail = f"Preserved as {backup.name}."
        except OSError:
            detail = "The original cache was left in place."
        return defaults(), f"Could not restore session: {exc}. {detail}"


def save(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(state, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
