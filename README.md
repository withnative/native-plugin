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

- the `enter` skill, exposed as `/native:enter` in Claude Code; and
- a hosted HTTPS MCP connection named `native` at `https://plugin.withnative.ai/mcp`.

It does not include a local executable, shell hooks, credentials, copied workspace data, or
Native server code. Your client manages OAuth sign-in, and the hosted service remains the
authoritative source for workspace state and current Native guidance.

## How agents enter Native

The packaged `enter` skill has a broad proactive trigger: it should activate when durable
context outside the visible conversation could materially change an answer or action, or
before material multi-step work, file or external-state changes, and reusable artifacts, so
you should not have to mention Native or explicitly ask for recording.
Whenever the skill activates, it enforces
the first Native interaction in a fresh conversation: first-use setup calls `quickstart`
once and then `bootstrap` exactly once; otherwise it calls
`bootstrap` exactly once before any other Native tool or substantive Native work.

Bootstrap provides bounded orientation; it does not authorize a broad workspace scan, import,
or write. When a task plausibly depends on prior work or decisions, an ongoing project, a
handoff, compacted or summarised history, collaboration, or current workspace state, the agent
should retrieve only the relevant Native context before acting or asking you to repeat it.
For material work, the agent follows Bootstrap's recording and authority boundaries to declare
intent once it is clear and establish or update a durable work anchor when the work is
substantial or resumable, before execution begins.

A client connected only to the hosted MCP endpoint does not load the packaged skill. An
unconditional once-per-fresh-conversation bootstrap rule for MCP-only clients requires a
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

Or ask: `Use Native's quickstart tool to help me finish setting up Native.`

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
plugins/native/          Native plugin manifests, MCP declaration, and enter skill
packages/mcp-stdio/      Independently versioned stdio compatibility adapter
docs/                    Native installation and operations documentation
scripts/validate.py      Standalone repository contract validation
```

The plugin manifests use version `0.1.3` as the material-work recording-guidance release and
cache signal. The stdio adapter remains an unreleased `0.1.0` candidate behind its independent
npm ownership and acceptance gates. Its source and pre-release documentation live in
[`packages/mcp-stdio/`](packages/mcp-stdio/); do not use its `npx` examples until that exact
version is published to npm.

## Development

Run the repository checks with:

```sh
python3 scripts/validate.py
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
