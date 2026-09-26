# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Atomic local state for the Native compaction-hook adapters.

One small JSON record per (host, session_id); never stores transcripts,
tool inputs, or credentials. Writes are atomic (tmp file + os.replace).
"""

from __future__ import annotations

import json
import os
import re
import sys

VERSION = 1
MAX_VALUE_LEN = 256
HOSTS = ("claude", "codex", "unknown")
_SESSION_RE = re.compile(r"[A-Za-z0-9_-]{1,128}")


def default_root() -> str:
    override = os.environ.get("NATIVE_COMPACTION_STATE_DIR")
    if override:
        if not os.path.isabs(override):
            raise ValueError("NATIVE_COMPACTION_STATE_DIR must be absolute")
        return override
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "Native", "compaction-hooks")
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    return os.path.join(base, "native-compaction-hooks")


def sanitize_host(host: str | None) -> str:
    candidate = (host or os.environ.get("NATIVE_HOOK_HOST") or "unknown").lower()
    return candidate if candidate in HOSTS else "unknown"


def sanitize_session(session_id: object) -> str | None:
    if not isinstance(session_id, str):
        return None
    if _SESSION_RE.fullmatch(session_id) is None:
        return None
    return session_id


def path_for(root: str, host: str, session_id: str) -> str:
    return os.path.join(root, f"{host}.{session_id}.json")


def load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_merge(path: str, update: dict) -> None:
    directory = os.path.dirname(path)
    os.makedirs(directory, mode=0o700, exist_ok=True)
    _harden(directory, 0o700)
    record = load(path)
    record.update({k: v for k, v in update.items() if v is not None})
    record["version"] = VERSION
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(record, handle)
        handle.flush()
        os.fsync(handle.fileno())
    _harden(tmp, 0o600)
    os.replace(tmp, path)


def remove(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    except OSError:
        pass


def bound(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value[:MAX_VALUE_LEN]


def _harden(path: str, mode: int) -> None:
    if os.name == "nt":
        return
    try:
        os.chmod(path, mode)
    except OSError:
        pass
