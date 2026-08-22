#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Validate the standalone Native plugin and stdio adapter repository."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "native"
ADAPTER = ROOT / "packages" / "mcp-stdio"
ENDPOINT = "https://plugin.withnative.ai/mcp"
REPOSITORY = "https://github.com/withnative/native-plugin"
DESCRIPTION = (
    "Proactively recover relevant durable context and continue work through Native's "
    "hosted MCP service."
)
DEFAULT_PROMPT = (
    "Use $enter to check Native for context beyond this conversation, recover what "
    "matters, and help me continue this work."
)
MPL_2_0_SHA256 = "3f3d9e0024b1921b067d6f7f88deb4a60cbe7a78e76c64e3f1d7fc3b779b9d04"
MPL_NOTICE = (
    "This Source Code Form is subject to the terms of the Mozilla Public\n"
    "License, v. 2.0. If a copy of the MPL was not distributed with this\n"
    "file, You can obtain one at https://mozilla.org/MPL/2.0/."
)
HASH_NOTICE = "\n".join(f"# {line}" for line in MPL_NOTICE.splitlines()) + "\n"
HTML_NOTICE = f"<!--\n{MPL_NOTICE}\n-->\n"


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(f"{path.relative_to(ROOT)} is not valid JSON: {exc}") from exc
    require(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain an object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_license() -> None:
    for path in (ROOT / "LICENSE", ADAPTER / "LICENSE"):
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == MPL_2_0_SHA256,
            f"{path.relative_to(ROOT)} must contain the canonical, unmodified MPL 2.0 text",
        )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    require(readme.startswith(HTML_NOTICE), "README is missing the MPL Exhibit A notice")
    require(
        "contents of this repository—including JSON and other\n"
        "formats that do not support comments—are licensed under the [Mozilla Public License\n"
        "2.0](LICENSE) (`MPL-2.0`)." in readme,
        "README must declare MPL-2.0 coverage for commentless formats",
    )
    require(
        "Copyright © 2026 AI Native Work, Inc." in readme,
        "README copyright notice drifted",
    )

    notice_prefixes = {
        ROOT / ".github" / "workflows" / "validate.yml": HASH_NOTICE,
        ROOT / ".gitignore": HASH_NOTICE,
        ROOT / "SECURITY.md": HTML_NOTICE,
        ROOT / "docs" / "plugin-installation.md": HTML_NOTICE,
        PLUGIN / "skills" / "enter" / "agents" / "openai.yaml": HASH_NOTICE,
        ADAPTER / "README.md": HTML_NOTICE,
        ADAPTER / "THIRD_PARTY_NOTICES.md": HTML_NOTICE,
        ROOT / "scripts" / "validate.py": f"#!/usr/bin/env python3\n{HASH_NOTICE}",
    }
    for path, prefix in notice_prefixes.items():
        require(
            path.read_text(encoding="utf-8").startswith(prefix),
            f"{path.relative_to(ROOT)} is missing the MPL Exhibit A notice",
        )


def validate_manifests() -> None:
    codex = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
    claude = load_json(PLUGIN / ".claude-plugin" / "plugin.json")
    common = {
        "name": "native",
        "version": "0.1.2",
        "description": DESCRIPTION,
        "author": {"name": "Native", "url": "https://www.withnative.ai/"},
        "homepage": "https://personal.withnative.ai/",
        "repository": REPOSITORY,
        "keywords": ["native", "workspace", "context", "mcp"],
        "skills": "./skills/",
        "mcpServers": "./.mcp.json",
    }
    for key, value in common.items():
        require(codex.get(key) == value, f"Codex manifest has unexpected {key}")
        require(claude.get(key) == value, f"Claude manifest has unexpected {key}")

    require(
        set(claude) == set(common),
        "Claude manifest contains unexpected fields",
    )
    interface = codex.get("interface", {})
    require(set(codex) == set(common) | {"interface"}, "Codex manifest contains unexpected fields")
    require(interface.get("displayName") == "Native", "Codex display name must be Native")
    require(
        interface.get("shortDescription") == "Proactively recover relevant durable context.",
        "Codex short description drifted",
    )
    require(
        interface.get("longDescription")
        == "Connect to Native's hosted MCP service to check for context beyond the visible "
        "conversation, recover what matters, continue work, and record requested updates.",
        "Codex long description drifted",
    )
    require(interface.get("developerName") == "Native", "Codex developer must be Native")
    require(interface.get("category") == "Productivity", "Codex category drifted")
    require(interface.get("capabilities") == ["Read", "Write"], "Capabilities drifted")
    require(interface.get("websiteURL") == "https://personal.withnative.ai/", "Website drifted")
    require(interface.get("defaultPrompt") == [DEFAULT_PROMPT], "Default prompt drifted")


def validate_mcp() -> None:
    mcp = load_json(PLUGIN / ".mcp.json")
    require(
        mcp == {"mcpServers": {"native": {"type": "http", "url": ENDPOINT}}},
        "MCP declaration must contain only the canonical hosted Native server",
    )


def validate_skill() -> None:
    skill_path = PLUGIN / "skills" / "enter" / "SKILL.md"
    skill = skill_path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(?P<header>.*?)\n---\n(?P<body>.*)\Z", skill, re.DOTALL)
    require(match is not None, "Skill must contain YAML frontmatter")
    header = match.group("header")
    body = match.group("body")
    require(re.search(r"^name: enter$", header, re.MULTILINE) is not None, "Skill name drifted")
    positive_triggers = (
        "outside the visible conversation",
        "prior work or decisions",
        "ongoing projects",
        "handoffs",
        "compacted or summarised history",
        "collaboration across sessions, agents, people, or tools",
        "current workspace state",
        "even when the person does not mention Native",
        "save this for later",
    )
    negative_boundaries = (
        "React Native",
        "genuinely self-contained tasks",
        "work explicitly assigned to another system",
    )
    for phrase in positive_triggers + negative_boundaries:
        require(phrase in header, f"Skill activation contract is missing {phrase!r}")

    body_contract = (
        "At the first Native interaction in a fresh conversation",
        "call `bootstrap` exactly once",
        "call `quickstart` once and then",
        "before any other Native tool or substantive Native work",
        "before acting or asking the person to repeat it",
        "not permission to scan the workspace broadly",
        "do not perform indiscriminate scans or imports",
        "not unrelated writes",
        "https://github.com/withnative/plugins",
    )
    for phrase in body_contract:
        require(phrase in body, f"Skill continuity contract is missing {phrase!r}")

    presentation = (skill_path.parent / "agents" / "openai.yaml").read_text(encoding="utf-8")
    for phrase in (
        'display_name: "Enter your Native workspace"',
        'short_description: "Proactively recover relevant durable context."',
        f'default_prompt: "{DEFAULT_PROMPT}"',
        "allow_implicit_invocation: true",
    ):
        require(phrase in presentation, f"OpenAI presentation metadata is missing {phrase!r}")


def validate_thin_boundary() -> None:
    expected = {
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        ".mcp.json",
        "skills/enter/SKILL.md",
        "skills/enter/agents/openai.yaml",
    }
    actual = {
        path.relative_to(PLUGIN).as_posix()
        for path in PLUGIN.rglob("*")
        if path.is_file()
    }
    require(actual == expected, f"Thin plugin file boundary drifted: {sorted(actual ^ expected)}")
    for path in PLUGIN.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            require("[TODO:" not in text, f"Placeholder remains in {path.relative_to(ROOT)}")
            require("staging.plugin.withnative.ai" not in text, "Plugin must use production URL")

    for path in (
        ROOT / ".agents" / "plugins" / "marketplace.json",
        ROOT / ".claude-plugin" / "marketplace.json",
    ):
        require(not path.exists(), f"Standalone repository must not contain {path.relative_to(ROOT)}")


def validate_docs() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "plugin-installation.md").read_text(encoding="utf-8")
    require("Installation still registers the shared" in readme, "README must explain marketplace registration")
    require("not itself a marketplace" in readme, "README must explain repository ownership")
    require("/native:enter" in readme and "/native:enter" in guide, "Native command documentation drifted")
    require("withnative/plugins" in readme and "withnative/plugins" in guide, "Shared marketplace instructions missing")
    require("https://plugin.withnative.ai/mcp" in readme and ENDPOINT in guide, "MCP endpoint docs drifted")
    require("clean-root repository was extracted" in readme, "Provenance statement missing")
    require("4268ac0bc5f0c73eff9ffe7e3bb244c113932b2d" in readme, "Provenance commit drifted")
    require("does not preserve the source repository's Git history" in readme, "History disclaimer missing")
    require("advances both plugin manifests" in readme, "Relocation changes missing from provenance")
    require("unreleased `0.1.0` candidate" in readme, "Adapter release status missing")
    require("private vulnerability reporting" in readme, "Private security reporting missing")
    require("not yet published to npm" in guide, "Guide must not present the adapter as published")
    for phrase in (
        "broad proactive trigger",
        "should not have to mention Native",
        "Whenever the skill activates",
        "first Native interaction in a fresh conversation",
        "`bootstrap` exactly once",
        "before acting or asking you to repeat it",
        "unconditional once-per-fresh-conversation bootstrap rule",
        "cannot by itself",
        "MCP-only runtime path",
    ):
        require(phrase in readme, f"README continuity guidance is missing {phrase!r}")
    require(
        "Whenever the skill activates" in guide
        and "requires a corresponding" in guide
        and "update to the hosted Native service's MCP instructions" in guide,
        "Installation guide must identify the unresolved hosted MCP instruction update",
    )
    for text in (readme, guide):
        require("privacyPolicyURL" not in text and "termsOfServiceURL" not in text, "Deferred legal URL invented")
        require("clean-client acceptance" not in text.lower(), "Unverified acceptance claim present")


def validate_adapter() -> None:
    expected_files = {
        "LICENSE",
        "README.md",
        "THIRD_PARTY_NOTICES.md",
        "package-lock.json",
        "package.json",
        "scripts/clean.mjs",
        "scripts/pack-smoke.mjs",
        "src/bin/mcp-stdio-auth.ts",
        "src/bin/mcp-stdio.ts",
        "src/contract.ts",
        "src/runner.ts",
        "src/state.ts",
        "test/contract.test.ts",
        "test/oauth.test.ts",
        "test/runner.test.ts",
        "test/state.test.ts",
        "test/transport.test.ts",
        "tsconfig.json",
        "vitest.config.ts",
    }
    actual_files = {
        path.relative_to(ADAPTER).as_posix()
        for path in ADAPTER.rglob("*")
        if path.is_file()
        and path.relative_to(ADAPTER).parts[0] not in {"dist", "node_modules"}
        and path.suffix != ".tgz"
    }
    require(actual_files == expected_files, f"Adapter source tree drifted: {sorted(actual_files ^ expected_files)}")

    manifest = load_json(ADAPTER / "package.json")
    lock = load_json(ADAPTER / "package-lock.json")
    require(manifest.get("name") == "@withnative/mcp-stdio", "Adapter name drifted")
    require(manifest.get("version") == "0.1.0", "Adapter version drifted")
    require(manifest.get("license") == "MPL-2.0", "Adapter license metadata drifted")
    require(manifest.get("engines") == {"node": ">=22"}, "Adapter Node release gate drifted")
    require(
        manifest.get("bin")
        == {
            "mcp-stdio": "dist/bin/mcp-stdio.js",
            "mcp-stdio-auth": "dist/bin/mcp-stdio-auth.js",
        },
        "Adapter executable metadata drifted",
    )
    require(
        manifest.get("files") == ["dist", "LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"],
        "Adapter package boundary drifted",
    )
    require(
        manifest.get("publishConfig")
        == {"access": "public", "registry": "https://registry.npmjs.org/"},
        "Adapter publish gate drifted",
    )
    require(manifest.get("dependencies") == {"mcp-remote": "0.1.38"}, "Adapter dependency pin drifted")
    require(
        manifest.get("scripts")
        == {
            "build": "tsc -p tsconfig.json",
            "clean": "node scripts/clean.mjs",
            "test": "npm run build && vitest run",
            "test:pack": "npm run build && node scripts/pack-smoke.mjs",
            "check": "npm test && npm run test:pack",
            "prepack": "npm run build",
        },
        "Adapter release scripts drifted",
    )
    require(
        manifest.get("repository")
        == {"type": "git", "url": f"{REPOSITORY}.git", "directory": "packages/mcp-stdio"},
        "Adapter repository metadata drifted",
    )
    require(
        manifest.get("homepage") == f"{REPOSITORY}/tree/main/packages/mcp-stdio",
        "Adapter homepage drifted",
    )
    require(manifest.get("bugs") == {"url": f"{REPOSITORY}/issues"}, "Adapter bugs URL drifted")
    require(lock.get("name") == manifest["name"] and lock.get("version") == "0.1.0", "Adapter lock metadata drifted")
    require(lock.get("packages", {}).get("", {}).get("version") == "0.1.0", "Adapter lock root version drifted")

    contract = (ADAPTER / "src" / "contract.ts").read_text(encoding="utf-8")
    require("export const PACKAGE_VERSION = '0.1.0'" in contract, "Adapter runtime version drifted")
    require(f"export const REMOTE_URL = '{ENDPOINT}'" in contract, "Adapter endpoint drifted")
    require(
        f"client_uri: '{REPOSITORY}/tree/main/packages/mcp-stdio'" in contract,
        "Adapter OAuth client_uri drifted",
    )


def main() -> int:
    checks = (
        validate_license,
        validate_manifests,
        validate_mcp,
        validate_skill,
        validate_thin_boundary,
        validate_docs,
        validate_adapter,
    )
    try:
        for check in checks:
            check()
    except (AssertionError, OSError, UnicodeDecodeError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print("Native plugin and stdio adapter validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
