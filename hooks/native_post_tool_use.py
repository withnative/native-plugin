# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""PostToolUse hook: capture the Native bootstrap run_key and WorkItem anchor.

Reads the hook JSON payload from stdin. Only inspects session_id,
tool_name and tool_response; never reads transcript_path or credentials.
Always exits 0 without stdout so the agent is never blocked.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import native_hook_state as state

MAX_STDIN = 1_000_000
RUN_KEY_RE = re.compile(r'"run_key"\s*:\s*"([^"\n]{1,256})"')
ANCHOR_KEYS = ("work_item_id", "anchor_record_id", "record_id", "anchor")
INTENT_HINTS = ("set_intent", "start_work", "claim", "get_run_activity", "intent")


def _find_key(node: object, key: str, depth: int = 0) -> str | None:
    if depth > 6:
        return None
    if isinstance(node, dict):
        for name, value in node.items():
            if name == key and isinstance(value, str) and value:
                return value[: state.MAX_VALUE_LEN]
            found = _find_key(value, key, depth + 1)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_key(item, key, depth + 1)
            if found:
                return found
    return None


def _successful(response: object) -> bool:
    if not isinstance(response, dict):
        return response is not None
    if response.get("isError") is True:
        return False
    error = response.get("error")
    return not error


def main() -> int:
    try:
        raw = sys.stdin.read(MAX_STDIN + 1)
        payload = json.loads(raw[:MAX_STDIN])
        session = state.sanitize_session(payload.get("session_id"))
        if session is None:
            return 0
        tool = str(payload.get("tool_name") or "").lower()
        if not tool:
            return 0
        response = payload.get("tool_response")
        host = state.sanitize_host(_flag_host())
        update: dict = {}
        if "bootstrap" in tool and _successful(response):
            run_key = _find_key(response, "run_key")
            if run_key is None and response is not None:
                match = RUN_KEY_RE.search(json.dumps(response)[:8192])
                run_key = match.group(1) if match else None
            if run_key:
                update["run_key"] = run_key
        if any(hint in tool for hint in INTENT_HINTS) and _successful(response):
            for key in ANCHOR_KEYS:
                anchor = _find_key(response, key)
                if anchor:
                    update["anchor"] = anchor
                    break
        if update:
            update["mcp_observed"] = True
            root = state.default_root()
            state.save_merge(state.path_for(root, host, session), update)
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
