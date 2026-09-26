# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""SessionStart hook: emit a small cue after context compaction.

Acts only when the payload source is "compact"; all other sources stay
silent. The cue carries the retained run_key/anchor (when captured) and
directs the agent to re-orient via current Native context and effective
guidance. It never tells the agent to call bootstrap and never pastes
guide bodies (Codex additionalContext lands in developer context).
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import native_hook_state as state

MAX_STDIN = 256_000
MAX_CUE = 800
MAPPING_TTL_SECONDS = 7 * 24 * 3600


def full_cue(run_key: str, anchor: str | None) -> str:
    scope = f" on WorkItem {anchor}" if anchor else ""
    return (
        "Native compaction checkpoint: this conversation already bootstrapped "
        "Native before compaction. Do not call bootstrap again. Reuse run_key "
        f"{run_key}{scope} on subsequent Native calls; call "
        "guidance_read.manage_instructions.resolve "
        "with that run_key and apply guidance only when it reports ready. If "
        "resolve is unavailable or unknown, guidance cannot be refreshed: "
        "continue from visible context or ask; if the Native "
        "MCP tools are unavailable, use the packaged connect skill. Do not "
        "invent workspace state."
    )[:MAX_CUE]


def recoverable_cue() -> str:
    return (
        "Native compaction checkpoint unavailable: no bootstrap run_key "
        "was captured in this host mapping. If the original key is still "
        "visible in the conversation summary, reuse it for the current "
        "guidance and task reads. Otherwise, run continuity is unavailable: "
        "continue from visible evidence or ask for context. Do not invent "
        "Native state or call bootstrap merely because of compaction. If "
        "Native MCP tools are unavailable, use the packaged connect skill."
    )[:MAX_CUE]


def _fresh(record: dict) -> bool:
    try:
        updated = int(record.get("updated_at", 0))
    except (TypeError, ValueError):
        return False
    return (time.time() - updated) <= MAPPING_TTL_SECONDS


def main() -> int:
    try:
        raw = sys.stdin.read(MAX_STDIN + 1)
        payload = json.loads(raw[:MAX_STDIN])
        if payload.get("source") != "compact":
            return 0
        host = state.sanitize_host(_flag_host())
        session = state.sanitize_session(payload.get("session_id"))
        record: dict = {}
        if session is not None:
            try:
                root = state.default_root()
            except ValueError:
                root = ""
            if root:
                record = state.load(state.path_for(root, host, session))
        if not _fresh(record):
            record = {}
        run_key = state.bound(record.get("run_key"))
        cue = full_cue(run_key, state.bound(record.get("anchor"))) if run_key else recoverable_cue()
        print(json.dumps(_envelope(host, cue)))
    except Exception:
        pass
    return 0


def _envelope(host: str, cue: str) -> dict:
    # Both Claude Code and Codex document SessionStart additionalContext
    # under hookSpecificOutput with the hookEventName repeated.
    del host
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": cue}}


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
