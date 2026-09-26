<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
-->

# Native plugin

**Bring your Native workspace into the conversations where work happens.**

Native is a workspace for durable context: current work, decisions, documents, and the
relationships between them. This first-party plugin lets a supported agent connect to the
workspace you authorize, recover what is current, and continue work with you across
conversations. You should not need to say “use Native”: the entry skill applies proactively
when context outside the visible conversation could materially change an answer or action,
and before material work that should remain visible and resumable.

[Learn more about Native](https://personal.withnative.ai/).

## What it installs

The plugin is intentionally small. It adds:

- the `enter` skill, exposed as `/native:enter` in Claude Code, which brings agents into
  Native for ordinary work;
- the `connect` skill, exposed as `/native:connect`, which handles installation, sign-in,
  and reconnection, so that guidance loads only when it is needed; and
- a hosted HTTPS MCP connection named `native` at `https://plugin.withnative.ai/mcp`;
- optional local hooks for coding-host compaction that retain the Native run key and
  prompt a bounded refresh in the next model context.

It does not include a local MCP server, credentials, copied workspace data, or Native
server code. The hooks run Python scripts on the coding host after the client trusts
them. Your client manages OAuth sign-in, and the hosted service remains the authoritative
source for workspace state and current Native guidance.

## How agents enter Native

The packaged `enter` skill has a broad proactive trigger: it should activate when durable
context outside the visible conversation could materially change an answer or action, or
before material multi-step work, file or external-state changes, and reusable artifacts, so
you should not have to mention Native or explicitly ask for recording.
At the first Native interaction in a conversation, first-use setup calls `quickstart` once
and then obtains one successful `bootstrap` response; otherwise the agent obtains one
successful `bootstrap` response before any other Native tool or substantive Native work.
Bootstrap entry is once per conversation, not once per skill activation or task.
Re-triggering or re-reading the skill on a later user turn, when the task, intent, or artifact
changes, or after context compaction is still within the same conversation and must not cause
another `bootstrap` call or successful response. The agent retains the original `run_key`
across turns and compaction and reuses it on all subsequent Native calls. When the underlying
aim materially changes, call `set_intent` with that same `run_key`.

Before any successful bootstrap response, qualifying transient failures before a usable run
key is returned allow at most two retries with backoff. The skill defines the retry delays
and stopping conditions. A failed attempt does not require a new conversation. Authentication,
validation, and instruction-readiness failures require their specific repair, not this retry
path. The bounded retry window ends at the first successful response; these retries apply
only to bootstrap, not to writes.

Bootstrap provides bounded orientation; it does not authorize a broad workspace scan, import,
or write. When a task plausibly depends on prior work or decisions, an ongoing project, a
handoff, compacted or summarised history, collaboration, or current workspace state, the agent
should retrieve only the relevant Native context before acting or asking you to repeat it.
For material work, the agent follows Bootstrap's recording and authority boundaries to declare
intent once it is clear and establish or update a durable work anchor when the work is
substantial or resumable, before execution begins.

A client connected only to the hosted MCP endpoint does not load the packaged skill. A
rule requiring one successful bootstrap per conversation for MCP-only clients requires a
corresponding update to the hosted service's MCP instructions. Those instructions are
deployed with the Native service and are not owned by this repository; this repository owns
only the MCP declaration that points clients to the service, so this change cannot by itself
satisfy the MCP-only runtime path.

## Trust and control

Installing the plugin changes local client configuration; it does not by itself read, write,
or delete anything in a Native workspace. After you authorize the connection, Native's tools
can access the workspace data available to your account and act within your request and
permissions. Installation or activation does not start autonomous work.

Removing the plugin removes its local skill and connection, but does not delete data held by
Native or by your AI provider. Your AI provider processes conversation and tool traffic under
its own terms. Never paste a bearer token into a conversation, plugin file, or repository issue.

## Install

Installation still registers the shared [`withnative/plugins`](https://github.com/withnative/plugins)
marketplace. This repository owns the Native package source, but it is not itself a marketplace
and contains no marketplace manifests. Adding the shared marketplace only makes its packages
available; install `native@withnative` explicitly.

The known package-install surfaces are Claude Code (including its desktop application),
ChatGPT/Codex Desktop, and Codex CLI where its plugin commands are enabled. This list is
not exhaustive: plugin availability and installation controls vary by host, account,
workspace, role, region, and surface. A plugin that declares an MCP server may be limited
to a desktop or other supported surface.

### Agent-assisted setup

Before installing, inspect the host's existing marketplace, plugin, and MCP connection
state. If a direct plugin CLI or other installation capability is available, use it to
add the shared marketplace only when needed, install `native@withnative`, and verify the
installed package. If direct installation is unavailable, use a host-provided plugin
suggestion or approval flow when one is offered. Follow the host's authentication and
reload instructions, then start a fresh conversation.

If Native is visible in the host's Plugins Directory, select it, review the listing,
choose Install, complete authentication, and start a fresh conversation. If the listing
is absent, do not infer that CLI or administrator setup is the only route: first check
whether the host exposes its marketplace-add flow. On supported desktop surfaces, an
ordinary user may be able to add the shared marketplace in-product:

- ChatGPT Desktop: **Settings → Plugins → Add → Add a marketplace**; enter
  `withnative/plugins`, leave the ref at `main`, and leave sparse paths empty. Open the
  resulting marketplace, install **Native**, authenticate, and start a fresh conversation.
- Claude: **Customize → Plugins → Personal plugins → + → Add marketplace → Add from a
  repository**; enter `withnative/plugins`, then install **Native**, authenticate, and
  start a fresh conversation.

These controls depend on the account, workspace policy, and host surface. If they are not
available, offer the shortest copyable CLI route below or ask a workspace administrator to
import `withnative/plugins` from GitHub.

**Claude Code and its desktop application:**

```sh
claude plugin marketplace add withnative/plugins
claude plugin install native@withnative
claude plugin list
```

**ChatGPT/Codex Desktop and Codex CLI:**

```sh
codex plugin marketplace add withnative/plugins
codex plugin add native@withnative
codex plugin list
```

Choose the command set only when that client's CLI is available; do not hand commands back
to a person when the agent can run them. In ChatGPT/Codex, the Plugins Directory is an
alternative only when Native is actually listed. In a managed workspace, an administrator
can import the public GitHub marketplace and set the plugin's installation policy. Restart
or reload the client if requested. In a fresh conversation, use:

```text
/native:enter
```

Or ask: `Use Native's quickstart tool to help me finish setting up Native.` If Native's
tools are missing or its sign-in has expired, use `/native:connect`.

### Direct MCP fallback

When the packaged plugin cannot be installed, add Native as a connector/MCP server using
the host's own connection controls:

| Field | Value |
| --- | --- |
| URL | `https://plugin.withnative.ai/mcp` |
| Transport | Streamable HTTP |
| Authorization | Host-managed OAuth/Bearer token obtained from Native sign-in; never paste manually |

Clients may call this a connector, MCP server, or integration. Complete sign-in through
the host; users must not obtain or paste a bearer token into a conversation, plugin file,
or issue. See the [host-specific MCP routes](docs/plugin-installation.md#direct-mcp-fallback)
in the full guide. This direct connection reaches Native's hosted MCP tools, but it does
not include the packaged `enter` skill or its proactive bootstrap behavior. You lose the
plugin's automatic context-entry guidance; invoke Native explicitly according to the
host's MCP controls.

See the [complete installation guide](docs/plugin-installation.md) for updates, removal,
authentication, troubleshooting, and stdio-only clients.

## Repository layout

```text
plugins/native/          Portable Agent Plugins manifests, compat paths, hooks, enter and connect skills
plugins/native/plugin.json + mcp.json  Canonical packaging (skills/ and MCP auto-discovered)
plugins/native/.claude-plugin/ + .codex-plugin/ + .mcp.json  Compatibility paths (kept in sync)
plugins/native/hooks/    Compaction-hook adapters, tests, and host hook configs
packages/mcp-stdio/      Independently versioned stdio compatibility adapter
docs/                    Native installation and operations documentation
scripts/validate.py      Standalone repository contract validation
```

The canonical `plugins/native/plugin.json` declares the Agent Plugins v1 schema and
carries portable identity plus the OpenAI `extensions.com.openai` presentation overlay;
`plugins/native/mcp.json` declares the hosted `native` server with the required
`streamable-http` transport. The `.claude-plugin/`, `.codex-plugin/`, and `.mcp.json`
paths remain only for Claude Code and older Codex compatibility and must not diverge
from the canonical metadata or endpoint; the compatibility `.mcp.json` keeps the
legacy `http` transport value, which is the known alias of canonical `streamable-http`.

`plugins/native/hooks/` ships the compaction-hook adapters with their tests and two
host hook configs: the default `hooks/hooks.json` for Claude Code and the separate
`hooks/codex.hooks.json` referenced from both `extensions.com.openai.hooks` and the
legacy `.codex-plugin/plugin.json`, per the official rule that the OpenAI extension
replaces rather than merges with the legacy overlay — both references stay so older
and newer Codex resolve the same Codex config. PostToolUse matchers use one anchored
whole-string pattern, `^mcp__(native|plugin_native_native)__`
`(bootstrap|coordination_write)$`, and the adapter allowlists the same four exact
host-constructed tool names — `mcp__native__bootstrap`,
`mcp__native__coordination_write`, and their `mcp__plugin_native_native__*`
Claude plugin-bundled forms. Anchors are required on both hosts: Claude evaluates
matchers without regex characters as exact strings but runs patterns containing
`^$()` as unanchored JavaScript regex, and Codex 0.157.0 ignored an unanchored
substring probe live, so only `^...$` is exact everywhere. The namespace follows
install identity — Codex 0.157.0 names a server tool `mcp__<server>__<tool>`
(observed live: a `native_smoke` server yields `mcp__native_smoke__bootstrap`)
while a `withnative`-marketplace `native` install yields `mcp__native__bootstrap`,
matching the production tool name seen in-session; no `withnative` segment was
observed on the wire, so it is rejected rather than allowlisted on speculation.
Lookalikes such as `mcp__other_native__bootstrap`,
`mcp__native_evil__coordination_write`, or `mcp__withnative__bootstrap` are
rejected by config and script. The adapter captures the bootstrap `run_key` (only
from explicit `structuredContent` or bootstrap continuation YAML, never from
arbitrary quoted text — the live Codex MCP result envelope carries exactly
`content` plus `structuredContent`)
and the WorkItem anchor. SessionStart on
compact emits a short re-orientation cue without re-bootstrapping, and SessionEnd
removes the session record. Hook state stays in the host plugin-data directory, keeps
only the key and anchor, and expires after 7 days. Installing the plugin does not
auto-trust its hooks: each host asks for review before they run, and the cue cannot
restore guidance on its own — no server-side reads are performed.

Actual refresh behavior via the executor-qualified operation
`guidance_read.manage_instructions.resolve`: after a coding-host
compact cue with a retained `run_key`, the agent calls that operation
with the key (never `bootstrap`) and applies guidance only on
`status:ready` with complete active entries at original user/workspace authority.
If the connected Native deployment does not expose the operation — older servers
predate the mapping, so treat an unavailable or unknown operation as a version
signal, not an error — the agent surfaces that guidance
cannot be refreshed, continues from visible context or asks, and does not retry;
invalid guidance resolution likewise surfaces recoverable state with no partial or
frozen guides. Guidance read stays separate from task-state refresh: a known anchor reads
the current record plus bounded recent history (labelled current vs recent, never
claiming changed-since without a cursor), while no anchor falls back to retained
intent and visible context or asking. Ordinary ChatGPT/Claude chat has no automatic
hook and follows the same agent-led steps on visible compaction signs.

Limits: if the connected deployment predates the `resolve` mapping, the refresh
path stays dormant behind the graceful fallback above; there is no automatic
full guidance restoration; and nothing here lets Native validate an issued
`run_key` — the server refuses absent/malformed keys without an issued-key
registry, and only the `resolve` response determines validity. Live-host
evidence, dated 2026-09-26 and caveated: on Codex 0.157.0, hook `session_id`
equals the session `thread_id`, the MCP result envelope is `content` plus
`structuredContent`, and a `withnative`-marketplace install exposes
`mcp__native__bootstrap` (synthetic servers/data; production OAuth-gated tools
were not callable, so real bootstrap capture on Codex remains unproven). Codex CLI
0.157.0 and 0.157.1 did not discover bundled hooks from local-marketplace
installs: `hooks/list` via app-server returned zero plugin entries (a minimal
probe plugin included), and no plugin hook executed in `exec` or app-server
sessions, so the automatic coding-host compact cue is unverified and unavailable
in those versions outside a TUI trust-review path, which itself exits
immediately in headless terminals here. A user-level copy of the Codex hook
entries is not presented as a working path: user-level hooks fired in `exec`
but not in app-server turns, so the fallback compact cue is likewise unverified
live. On
Claude Code 2.1.281, a manual `/compact` accepted the SessionStart
`additionalContext` cue and `/exit` SessionEnd removed the namespaced state
file for the same seeded `session_id`, proving lookup/cleanup — but that mapping
was seeded manually, so real tool-name capture on Claude remains unproven.

The plugin manifests use version `0.1.11`, which adopts portable Agent Plugins v1
packaging (canonical root `plugin.json`/`mcp.json` with compatibility paths kept in
sync) and documents the post-compaction refresh via `resolve` with the retained
`run_key`. `0.1.10` moved installation, sign-in, and
reconnection guidance out of `enter` into the separate `connect` skill. `0.1.9` added
confirming sign-in to the person as soon as it completes, and `0.1.8` allowed an agent
handling a live OAuth login to receive the callback URL in chat and complete the sign-in.
The stdio adapter remains an unreleased `0.1.0` candidate behind its independent npm
ownership and acceptance gates. Its source and pre-release documentation live in
[`packages/mcp-stdio/`](packages/mcp-stdio/); do not use its `npx` examples until that exact
version is published to npm.

## Development

Run the repository checks with:

```sh
python3 scripts/validate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/native/hooks/tests
npm ci --prefix packages/mcp-stdio
npm run check --prefix packages/mcp-stdio
```

## Provenance

This clean-root repository was extracted from the public
[`withnative/plugins`](https://github.com/withnative/plugins) repository through commit
[`4268ac0`](https://github.com/withnative/plugins/commit/4268ac0bc5f0c73eff9ffe7e3bb244c113932b2d).
It does not preserve the source repository's Git history. The extraction changes repository
metadata and the OAuth client URI to this repository, and advances both plugin manifests from
`0.1.0` to `0.1.1` as the source-relocation cache signal; runtime plugin and adapter behaviour
is otherwise unchanged.

## Security

Report suspected vulnerabilities through this repository's private vulnerability reporting
flow under **Security → Advisories → Report a vulnerability**. Do not disclose credentials,
tokens, workspace data, or an unpatched vulnerability in a public issue.

## License

Except where otherwise noted, the contents of this repository—including JSON and other
formats that do not support comments—are licensed under the [Mozilla Public License
2.0](LICENSE) (`MPL-2.0`).

Copyright © 2026 AI Native Work, Inc.
