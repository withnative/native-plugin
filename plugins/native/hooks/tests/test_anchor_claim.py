# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Claim-scoped anchors, TTL staleness, plugin-data root (stdlib only)."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POST_TOOL_USE = os.path.join(HOOKS, "native_post_tool_use.py")
SESSION_START = os.path.join(HOOKS, "native_session_start.py")
TOOL = "mcp__native__coordination_write"


def run(script, payload, state_dir=None, extra_env=None):
    env = dict(os.environ)
    env.pop("NATIVE_COMPACTION_STATE_DIR", None)
    if state_dir is not None:
        env["NATIVE_COMPACTION_STATE_DIR"] = state_dir
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, script, "--host", "claude"], input=json.dumps(payload),
        capture_output=True, text=True, env=env, timeout=30)


def bootstrap(session):
    return {"session_id": session, "tool_name": "mcp__native__bootstrap",
            "tool_response": {"structuredContent": {"run_key": "rk-1"}}}


def claim(session, record, claimed=True):
    return {"session_id": session, "tool_name": TOOL,
            "tool_input": {"operation": "start_work.claim",
                           "arguments": {"record_id": record}},
            "tool_response": {"structuredContent": {"claimed": claimed,
                                                    "record_id": record}}}


def release(session, record):
    payload = claim(session, record)
    payload["tool_input"] = {"operation": "start_work.release",
                             "arguments": {"record_id": record}}
    payload["tool_response"] = {"structuredContent": {"released": True}}
    return payload


def read_state(state_dir, session="s1"):
    with open(os.path.join(state_dir, f"claude.{session}.json")) as handle:
        return json.load(handle)


class AnchorScopeTest(unittest.TestCase):
    def test_unrelated_record_ids_ignored(self):
        with tempfile.TemporaryDirectory() as state_dir:
            run(POST_TOOL_USE, bootstrap("s1"), state_dir)
            for tool in ("mcp__native__set_intent", "mcp__native__get_run_activity"):
                proc = run(POST_TOOL_USE, {
                    "session_id": "s1", "tool_name": tool,
                    "tool_response": {"structuredContent": {"record_id": "wi-x"}}},
                    state_dir)
                self.assertEqual(proc.returncode, 0)
            self.assertNotIn("anchor", read_state(state_dir))

    def test_unconfirmed_claim_ignored(self):
        with tempfile.TemporaryDirectory() as state_dir:
            run(POST_TOOL_USE, bootstrap("s1"), state_dir)
            run(POST_TOOL_USE, claim("s1", "wi-1", claimed=False), state_dir)
            bare = claim("s1", "wi-1")
            del bare["tool_response"]["structuredContent"]["claimed"]
            run(POST_TOOL_USE, bare, state_dir)
            self.assertNotIn("anchor", read_state(state_dir))

    def test_matching_release_clears_anchor_keeps_key(self):
        with tempfile.TemporaryDirectory() as state_dir:
            run(POST_TOOL_USE, bootstrap("s1"), state_dir)
            run(POST_TOOL_USE, claim("s1", "wi-1"), state_dir)
            proc = run(POST_TOOL_USE, release("s1", "wi-1"), state_dir)
            self.assertEqual(proc.returncode, 0)
            record = read_state(state_dir)
            self.assertNotIn("anchor", record)
            self.assertEqual(record["run_key"], "rk-1")

    def test_mismatched_release_keeps_anchor(self):
        with tempfile.TemporaryDirectory() as state_dir:
            run(POST_TOOL_USE, bootstrap("s1"), state_dir)
            run(POST_TOOL_USE, claim("s1", "wi-1"), state_dir)
            run(POST_TOOL_USE, release("s1", "wi-2"), state_dir)
            self.assertEqual(read_state(state_dir)["anchor"], "wi-1")

    def test_untargeted_release_preserves_anchor(self):
        with tempfile.TemporaryDirectory() as state_dir:
            run(POST_TOOL_USE, bootstrap("s1"), state_dir)
            run(POST_TOOL_USE, claim("s1", "wi-1"), state_dir)
            bare = release("s1", "wi-1")
            del bare["tool_input"]["arguments"]
            proc = run(POST_TOOL_USE, bare, state_dir)
            self.assertEqual(proc.returncode, 0)
            record = read_state(state_dir)
            self.assertEqual(record["anchor"], "wi-1")
            self.assertEqual(record["run_key"], "rk-1")

    def test_stale_mapping_yields_recoverable(self):
        with tempfile.TemporaryDirectory() as state_dir:
            stale = {"version": 1, "run_key": "rk-stale", "anchor": "wi-9",
                     "updated_at": int(time.time()) - 8 * 24 * 3600}
            with open(os.path.join(state_dir, "claude.s-old.json"), "w") as handle:
                json.dump(stale, handle)
            proc = run(SESSION_START, {"session_id": "s-old", "source": "compact"},
                       state_dir)
            cue = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("unavailable", cue)
            self.assertNotIn("rk-stale", cue)

    def test_plugin_data_root_preferred(self):
        with tempfile.TemporaryDirectory() as plugin_data:
            proc = run(POST_TOOL_USE, bootstrap("s-p"),
                       extra_env={"CLAUDE_PLUGIN_DATA": plugin_data})
            self.assertEqual(proc.returncode, 0)
            expected = os.path.join(plugin_data, "native-compaction-hooks",
                                    "claude.s-p.json")
            self.assertTrue(os.path.exists(expected))


if __name__ == "__main__":
    unittest.main()
