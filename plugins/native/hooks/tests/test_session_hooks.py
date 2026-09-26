# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Focused tests for SessionStart cue and SessionEnd cleanup (stdlib only)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_START = os.path.join(HOOKS, "native_session_start.py")
SESSION_END = os.path.join(HOOKS, "native_session_end.py")
POST_TOOL_USE = os.path.join(HOOKS, "native_post_tool_use.py")


def run_script(script, payload, host="claude", state_dir=None):
    env = dict(os.environ, NATIVE_COMPACTION_STATE_DIR=state_dir or tempfile.mkdtemp())
    proc = subprocess.run(
        [sys.executable, script, "--host", host],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    return proc, env["NATIVE_COMPACTION_STATE_DIR"]


def seed(state_dir, session="sess-9", run_key="rk-kept", anchor="wi-7", host="claude"):
    proc, _ = run_script(POST_TOOL_USE, {
        "session_id": session, "tool_name": "mcp__native__bootstrap",
        "tool_response": {"structuredContent": {"run_key": run_key}}}, host=host, state_dir=state_dir)
    assert proc.returncode == 0
    proc, _ = run_script(POST_TOOL_USE, {
        "session_id": session, "tool_name": "mcp__native__coordination_write",
        "tool_input": {"operation": "start_work.claim",
                       "arguments": {"record_id": anchor}},
        "tool_response": {"structuredContent": {"claimed": True,
                                                "record_id": anchor}}}, host=host,
                         state_dir=state_dir)
    assert proc.returncode == 0


class SessionStartTest(unittest.TestCase):
    def test_compact_emits_full_cue_never_bootstrap(self):
        with tempfile.TemporaryDirectory() as state_dir:
            seed(state_dir)
            proc, _ = run_script(SESSION_START, {"session_id": "sess-9",
                                                "source": "compact"}, state_dir=state_dir)
            self.assertEqual(proc.returncode, 0)
            cue = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("rk-kept", cue)
            self.assertIn("wi-7", cue)
            self.assertIn("Do not call bootstrap", cue)
            self.assertLessEqual(len(cue), 800)

    def test_max_length_keys_keep_resolve_directive(self):
        with tempfile.TemporaryDirectory() as state_dir:
            seed(state_dir, run_key="r" * 256, anchor="w" * 256)
            proc, _ = run_script(SESSION_START, {"session_id": "sess-9",
                                                "source": "compact"}, state_dir=state_dir)
            self.assertEqual(proc.returncode, 0)
            cue = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertLessEqual(len(cue), 800)
            self.assertIn("resolve", cue)
            self.assertIn("ready", cue)
            self.assertIn("Do not call bootstrap", cue)

    def test_full_cue_states_refresh_unavailable_path(self):
        with tempfile.TemporaryDirectory() as state_dir:
            seed(state_dir)
            proc, _ = run_script(SESSION_START, {"session_id": "sess-9",
                                                "source": "compact"}, state_dir=state_dir)
            self.assertEqual(proc.returncode, 0)
            cue = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("guidance_read.manage_instructions.resolve", cue)
            self.assertIn("cannot be refreshed", cue)

    def test_codex_envelope_matches_documented_shape(self):
        with tempfile.TemporaryDirectory() as state_dir:
            seed(state_dir, host="codex")
            proc, _ = run_script(SESSION_START, {"session_id": "sess-9",
                                                "source": "compact"}, host="codex",
                                 state_dir=state_dir)
            body = json.loads(proc.stdout)
            specific = body["hookSpecificOutput"]
            self.assertEqual(specific["hookEventName"], "SessionStart")
            self.assertIn("rk-kept", specific["additionalContext"])

    def test_missing_mapping_is_recoverable(self):
        with tempfile.TemporaryDirectory() as state_dir:
            proc, _ = run_script(SESSION_START, {"session_id": "nope",
                                                "source": "compact"}, state_dir=state_dir)
            cue = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("unavailable", cue)
            self.assertIn("connect skill", cue)
            self.assertIn("original key is still visible", cue)
            self.assertIn("call bootstrap merely because of compaction", cue)
            self.assertNotIn("rk-", cue)
            self.assertNotIn("Re-orient by reading", cue)

    def test_non_compact_source_stays_silent(self):
        for source in ("startup", "resume", "clear"):
            proc, _ = run_script(SESSION_START, {"session_id": "sess-9",
                                                "source": source})
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")


class SessionEndTest(unittest.TestCase):
    def test_cleanup_removes_only_own_record(self):
        with tempfile.TemporaryDirectory() as state_dir:
            seed(state_dir)
            victim = os.path.join(state_dir, "claude.sess-9.json")
            keep = os.path.join(state_dir, "keep.json")
            with open(keep, "w", encoding="utf-8") as handle:
                handle.write("{}")
            proc, _ = run_script(SESSION_END, {"session_id": "sess-9"},
                                 state_dir=state_dir)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")
            self.assertFalse(os.path.exists(victim))
            self.assertTrue(os.path.exists(keep))

    def test_cleanup_missing_mapping_is_silent(self):
        with tempfile.TemporaryDirectory() as state_dir:
            proc, _ = run_script(SESSION_END, {"session_id": "ghost"},
                                 state_dir=state_dir)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
