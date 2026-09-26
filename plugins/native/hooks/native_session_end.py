# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""SessionEnd hook: best-effort cleanup of this session's hook state.

Removes only this hook's own namespaced record. Missing or stale
mappings are silently ignored. Always exits 0 without stdout.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import native_hook_state as state

MAX_STDIN = 256_000


def main() -> int:
    try:
        raw = sys.stdin.read(MAX_STDIN + 1)
        payload = json.loads(raw[:MAX_STDIN])
        session = state.sanitize_session(payload.get("session_id"))
        if session is None:
            return 0
        host = state.sanitize_host(_flag_host())
        try:
            root = state.default_root()
        except ValueError:
            return 0
        state.remove(state.path_for(root, host, session))
    except Exception:
        pass
    return 0


def _flag_host() -> str | None:
    args = sys.argv[1:]
    for index, arg in enumerate(args):
        if arg == "--host" and index + 1 < len(args):
            return args[index + 1]
        if arg.startswith("--host="):
            return arg.split("=", 1)[1]
    return None


if __name__ == "__main__":
    raise SystemExit(main())
