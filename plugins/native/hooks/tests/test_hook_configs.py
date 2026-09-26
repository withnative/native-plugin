# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Hook config contracts: Native-only matchers and quotable plugin paths."""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.dirname(HOOKS)


def load_config(name):
    with open(os.path.join(HOOKS, name), encoding="utf-8") as handle:
        return json.load(handle)


def post_tool_use_matcher(config):
    hooks = config.get("hooks", config)
    for entry in hooks["PostToolUse"]:
        if entry.get("matcher"):
            return entry["matcher"]
    return ""


ALLOWED = ("mcp__native__bootstrap",
           "mcp__native__coordination_write",
           "mcp__plugin_native_native__bootstrap",
           "mcp__plugin_native_native__coordination_write")
REJECTED = ("mcp__other__bootstrap",
            "mcp__other_native__bootstrap",
            "mcp__native_evil__coordination_write",
            "mcp__withnative__bootstrap",
            "Read", "Bash",
            "mcp__native__get_run_activity")


class HookConfigTest(unittest.TestCase):
    def test_claude_post_tool_use_matches_native_only(self):
        matcher = post_tool_use_matcher(load_config("hooks.json"))
        self.assertTrue(matcher.startswith("^") and matcher.endswith("$"),
                        "matcher must be anchored whole-string")
        for tool in ALLOWED:
            self.assertIsNotNone(re.search(matcher, tool), tool)
            self.assertIsNotNone(re.fullmatch(matcher, tool), tool)
        for tool in REJECTED:
            self.assertIsNone(re.search(matcher, tool), tool)
            self.assertIsNone(re.fullmatch(matcher, tool), tool)

    def test_codex_post_tool_use_matches_native_only(self):
        matcher = post_tool_use_matcher(load_config("codex.hooks.json"))
        self.assertTrue(matcher.startswith("^") and matcher.endswith("$"),
                        "matcher must be anchored whole-string")
        for tool in ALLOWED:
            self.assertIsNotNone(re.search(matcher, tool), tool)
            self.assertIsNotNone(re.fullmatch(matcher, tool), tool)
        for tool in REJECTED:
            self.assertIsNone(re.search(matcher, tool), tool)
            self.assertIsNone(re.fullmatch(matcher, tool), tool)

    def test_codex_commands_quote_plugin_root(self):
        config = load_config("codex.hooks.json")
        commands = [hook["command"]
                    for entries in config["hooks"].values()
                    for entry in entries for hook in entry["hooks"]]
        self.assertTrue(commands)
        for command in commands:
            self.assertIn('"${PLUGIN_ROOT}"', command)

    def test_quoted_command_runs_from_path_with_spaces(self):
        config = load_config("codex.hooks.json")
        template = config["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
        with tempfile.TemporaryDirectory(prefix="native hooks ") as root:
            spaced_hooks = os.path.join(root, "hooks")
            os.makedirs(spaced_hooks)
            for script in ("native_hook_state.py", "native_post_tool_use.py"):
                shutil.copy(os.path.join(HOOKS, script), spaced_hooks)
            state_dir = os.path.join(root, "state")
            command = template.replace("${PLUGIN_ROOT}", root)
            payload = json.dumps({"session_id": "sess-1",
                                  "tool_name": "mcp__native__bootstrap",
                                  "tool_response": {"structuredContent": {
                                      "run_key": "rk-spaced"}}})
            env = dict(os.environ, NATIVE_COMPACTION_STATE_DIR=state_dir)
            proc = subprocess.run(command, shell=True, input=payload,
                                  capture_output=True, text=True,
                                  env=env, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            with open(os.path.join(state_dir, "codex.sess-1.json")) as handle:
                self.assertEqual(json.load(handle)["run_key"], "rk-spaced")

    def test_no_duplicate_hook_registration(self):
        with open(os.path.join(PLUGIN, "plugin.json"), encoding="utf-8") as handle:
            overlay = json.load(handle)["extensions"]["com.openai"]
        with open(os.path.join(PLUGIN, ".codex-plugin", "plugin.json"),
                  encoding="utf-8") as handle:
            legacy = json.load(handle)
        self.assertEqual(overlay.get("hooks"), "./hooks/codex.hooks.json")
        self.assertEqual(legacy.get("hooks"), "./hooks/codex.hooks.json")
        with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"),
                  encoding="utf-8") as handle:
            self.assertNotIn("hooks", json.load(handle))


if __name__ == "__main__":
    unittest.main()
