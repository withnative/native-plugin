# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Focused tests for the PostToolUse capture hook (stdlib only)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POST_TOOL_USE = os.path.join(HOOKS, "native_post_tool_use.py")


def run_hook(payload, host="claude", state_dir=None):
    env = dict(os.environ, NATIVE_COMPACTION_STATE_DIR=state_dir or tempfile.mkdtemp())
    proc = subprocess.run(
        [sys.executable, POST_TOOL_USE, "--host", host],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    return proc, env["NATIVE_COMPACTION_STATE_DIR"]


def read_state(state_dir, host="claude", session="sess-1"):
    path = os.path.join(state_dir, f"{host}.{session}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


class PostToolUseTest(unittest.TestCase):
    def test_captures_run_key_keyed_by_session(self):
        proc, state_dir = run_hook({
            "session_id": "sess-1",
            "tool_name": "mcp__native__bootstrap",
            "tool_response": {"structuredContent": {"run_key": "rk-abc",
                                                    "workspace": "demo"}},
        })
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")
        self.assertEqual(read_state(state_dir)["run_key"], "rk-abc")

    def test_captures_run_key_from_continuation_yaml(self):
        text = (
            "# Internal continuation state\n```yaml\n"
            'run_key: &run_key "gibbon-sextant-ydbvnb"\n'
            "workspace: acme\n```"
        )
        proc, state_dir = run_hook({
            "session_id": "sess-1",
            "tool_name": "mcp__native__bootstrap",
            "tool_response": {
                "content": [{"type": "text", "text": text}],
                "structuredContent": {"workspace": "acme"},
            },
        })
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(read_state(state_dir)["run_key"], "gibbon-sextant-ydbvnb")

    def test_captures_run_key_from_run_context(self):
        proc, state_dir = run_hook({
            "session_id": "sess-1",
            "tool_name": "mcp__plugin_native_native__bootstrap",
            "tool_response": {"structuredContent": {"run_context": {"run_key": "rk-ctx"}}},
        })
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(read_state(state_dir)["run_key"], "rk-ctx")

    def test_ignores_quoted_run_key_in_unrelated_text(self):
        text = 'A pasted note says "run_key": "rk-old-leaked" but means nothing.'
        proc, state_dir = run_hook({
            "session_id": "sess-1",
            "tool_name": "mcp__plugin_native_native__bootstrap",
            "tool_response": {
                "content": [{"type": "text", "text": text}],
                "structuredContent": {"workspace": "acme"},
            },
        })
        self.assertEqual(proc.returncode, 0)
        self.assertIsNone(read_state(state_dir))

    def test_rejects_error_response_carrying_run_key(self):
        proc, state_dir = run_hook({
            "session_id": "sess-1",
            "tool_name": "mcp__native__bootstrap",
            "tool_response": {"isError": True,
                              "structuredContent": {"run_key": "rk-err"}},
        })
        self.assertEqual(proc.returncode, 0)
        self.assertIsNone(read_state(state_dir))

    def test_ignores_other_servers_bootstrap(self):
        proc, state_dir = run_hook({
            "session_id": "sess-1",
            "tool_name": "mcp__other__bootstrap",
            "tool_response": {"structuredContent": {"run_key": "rk-foreign"}},
        })
        self.assertEqual(proc.returncode, 0)
        self.assertIsNone(read_state(state_dir))

    def test_ignores_failed_bootstrap(self):
        proc, state_dir = run_hook({
            "session_id": "sess-1",
            "tool_name": "mcp__native__bootstrap",
            "tool_response": {"isError": True, "error": "boom"},
        })
        self.assertEqual(proc.returncode, 0)
        self.assertIsNone(read_state(state_dir))

    def test_captures_anchor_after_claim(self):
        with tempfile.TemporaryDirectory() as state_dir:
            run_hook({
                "session_id": "sess-1", "tool_name": "mcp__native__bootstrap",
                "tool_response": {"structuredContent": {"run_key": "rk-abc"}},
            }, state_dir=state_dir)
            proc, _ = run_hook({
                "session_id": "sess-1",
                "tool_name": "mcp__native__coordination_write",
                "tool_input": {"operation": "start_work.claim",
                               "arguments": {"record_id": "wi-42"}},
                "tool_response": {"structuredContent": {"claimed": True,
                                                        "record_id": "wi-42"}},
            }, state_dir=state_dir)
            self.assertEqual(proc.returncode, 0)
            record = read_state(state_dir)
            self.assertEqual(record["run_key"], "rk-abc")
            self.assertEqual(record["anchor"], "wi-42")

    def test_repeated_delivery_is_idempotent(self):
        payload = {"session_id": "sess-1", "tool_name": "mcp__native__bootstrap",
                   "tool_response": {"structuredContent": {"run_key": "rk-abc"}}}
        with tempfile.TemporaryDirectory() as state_dir:
            run_hook(payload, state_dir=state_dir)
            proc, _ = run_hook(payload, state_dir=state_dir)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(read_state(state_dir)["run_key"], "rk-abc")

    def test_missing_or_bad_session_is_silent(self):
        for payload in ({"tool_name": "bootstrap", "tool_response": {"run_key": "x"}},
                        {"session_id": "../evil", "tool_name": "bootstrap",
                         "tool_response": {"run_key": "x"}}):
            proc, state_dir = run_hook(payload)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")
            self.assertEqual(os.listdir(state_dir), [])

    def test_never_touches_transcript(self):
        proc, _ = run_hook({"session_id": "sess-1", "tool_name": "Read",
                            "transcript_path": "/nonexistent/transcript.jsonl",
                            "tool_response": {"ok": True}})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
