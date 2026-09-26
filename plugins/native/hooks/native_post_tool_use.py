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
YAML_RUN_KEY_RE = re.compile(r'(?m)^[ \t]*run_key:[ \t]*&run_key[ \t]*"([^"\n]{1,256})"')
ANCHOR_KEYS = ("record_id", "work_item_id", "anchor_record_id", "anchor")
COORDINATION_TOOL = "coordination_write"
CLAIM_OP = "start_work.claim"
RELEASE_OP = "start_work.release"


def _find_value(node: object, key: str, depth: int = 0) -> object:
    if depth > 6:
        return None
    if isinstance(node, dict):
        for name, value in node.items():
            if name == key:
                return value
            found = _find_value(value, key, depth + 1)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_value(item, key, depth + 1)
            if found is not None:
                return found
    return None


def _find_key(node: object, key: str) -> str | None:
    return state.bound(_find_value(node, key))


def _content_texts(response: object) -> list:
    """Raw text of MCP content blocks, where continuation YAML lives."""
    texts = []
    if isinstance(response, dict):
        content = response.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    texts.append(block["text"][:8192])
                elif isinstance(block, str) and block:
                    texts.append(block[:8192])
    return texts


def _extract_run_key(response: object) -> str | None:
    found = _find_key(response, "run_key")  # structuredContent and plain fields
    if found:
        return found
    for text in _content_texts(response):
        match = YAML_RUN_KEY_RE.search(text) or RUN_KEY_RE.search(text)
        if match:
            return match.group(1)
    if response is not None:  # last resort: serialised form
        match = RUN_KEY_RE.search(json.dumps(response)[:8192])
        if match:
            return match.group(1)
    return None


def _operation(tool_input: object) -> str | None:
    if isinstance(tool_input, dict) and isinstance(tool_input.get("operation"), str):
        return tool_input["operation"]
    return None


def _input_target(tool_input: object) -> str | None:
    if not isinstance(tool_input, dict):
        return None
    args = tool_input.get("arguments")
    if isinstance(args, dict):
        target = state.bound(args.get("record_id"))
        if target:
            return target
    return state.bound(tool_input.get("record_id"))


def _response_anchor(response: object) -> str | None:
    for key in ANCHOR_KEYS:
        anchor = _find_key(response, key)
        if anchor:
            return anchor
    return None


def _clear_anchor_if_released(host: str, session: str, target: str | None) -> None:
    try:
        root = state.default_root()
    except ValueError:
        return
    path = state.path_for(root, host, session)
    record = state.load(path)
    if not record.get("anchor"):
        return
    if target is not None and target != record.get("anchor"):
        return
    state.remove_keys(path, ("anchor",))


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
        tool_input = payload.get("tool_input")
        host = state.sanitize_host(_flag_host())
        update: dict = {}
        if "bootstrap" in tool and _successful(response):
            run_key = _extract_run_key(response)
            if run_key:
                update["run_key"] = run_key
        if COORDINATION_TOOL in tool:
            operation = _operation(tool_input)
            if operation == CLAIM_OP and _successful(response):
                if _find_value(response, "claimed") is True:
                    anchor = _response_anchor(response) or _input_target(tool_input)
                    if anchor:
                        update["anchor"] = anchor
            elif operation == RELEASE_OP and _successful(response):
                _clear_anchor_if_released(host, session, _input_target(tool_input))
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
