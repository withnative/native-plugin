<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
-->

# Install and manage the Native plugin

This Native-owned guide covers installing, updating, removing, and recovering Native on
its supported plugin surfaces. Installation registers the shared `withnative/plugins`
marketplace, then explicitly installs `native@withnative`; adding the marketplace alone does
not install Native. The known package-install surfaces described here are Claude Code
(including its desktop application), ChatGPT/Codex Desktop, and Codex CLI where its plugin
commands are enabled. This list is not exhaustive: host, account, workspace, role, region,
and surface controls can change what is available. A plugin that declares an MCP server may
be limited to a desktop or other supported surface.

## Start with the repository link

Paste this into Claude or ChatGPT/Codex, on desktop or CLI:

```text
Open https://github.com/withnative/native-plugin and follow the setup guide for the Native plugin.
```

### For agents following this guide

Use this order, and keep the Native package distinct from the hosted MCP connection:

1. Inspect the host's existing marketplace, plugin, and MCP connection state. Do not add a
   second marketplace, plugin, or standalone Native connection when the desired item is
   already present. Ask before changing an existing standalone Native MCP connection.
2. If the client CLI or another direct installation capability is available, perform the
   installation yourself. Add `withnative/plugins` only when it is absent, install
   `native@withnative`, and verify the package with the host's list/status command. Do not
   substitute a curated catalogue search for the repository the user supplied, and do not
   send interactive commands back to the user when you can run the non-interactive CLI.
3. If direct installation is unavailable, use a host-provided plugin suggestion or approval
   flow when one is offered. Follow the host's resulting authentication and reload steps.
4. If Native is visible in an in-product Plugins Directory, guide the person to select the
   Native listing, review it, choose Install, authenticate, and start a fresh conversation.
5. If the listing is absent, say so plainly and check whether the host exposes a
   marketplace-add flow. Do not infer that CLI or administrator setup is the only route from
   an absent listing. If the host's marketplace controls are unavailable for this account,
   workspace policy, or surface, offer the shortest copyable CLI route or ask a workspace
   administrator to import `withnative/plugins` from GitHub and make the plugin available.
6. Use the direct MCP connection below only as the final fallback. It supplies the hosted
   MCP tools but not the packaged skill or its proactive bootstrap behavior.

Verify the installed plugin afterwards and follow any reload or restart instruction reported
by the client. If the current conversation cannot load the newly installed plugin, give the
user this copyable continuation prompt before ending:

```text
Use Native's quickstart tool to help me finish setting up Native.
```

If you are on mobile, in a browser-only chat, or on another unlisted surface, use a
supported desktop or CLI client instead; the plugin flow is not verified there. A host may
still expose a separate direct MCP connector flow, but that is the reduced-capability
fallback documented below.

## ChatGPT/Codex Desktop

### ChatGPT desktop: ordinary-user route

Availability depends on the account, workspace policy, and host surface. In ChatGPT
Desktop, open **Settings → Plugins → Add → Add a marketplace**. In the source field, enter
`withnative/plugins`; leave the ref at its default `main` and leave sparse paths empty.
Choose **Add**, open the resulting `withnative/plugins` marketplace or listing, select
**Native**, and choose **Install**. Complete the Native authentication prompt and start a
fresh conversation.

If **Add a marketplace** is unavailable, or the marketplace/listing is not shown after the
add flow, explain that availability is controlled by the account or workspace rather than
claiming the source is universally unavailable. Then offer the CLI or administrator route
below.

### Codex CLI: agent route

When the Codex CLI is available, an agent should install Native directly. The install verb
is `add`, not `install`:

```sh
codex plugin marketplace add withnative/plugins
codex plugin add native@withnative
```

Confirm the result with `codex plugin list`, then restart ChatGPT/Codex Desktop.

If a ChatGPT or Codex Plugins Directory lists Native, an ordinary user can install it
in-product instead:

1. Open **Plugins Directory** in the available ChatGPT or Codex surface.
2. Select **Native**, review its capabilities and setup requirements, and choose **Install**.
3. Complete the Native sign-in or connection prompt.
4. Start a fresh conversation and invoke Native as described below.

If Native is not listed, check whether the marketplace-add flow above is available before
falling back. If the host does not provide that control for the current account or policy,
use the CLI above when `codex plugin` is available or ask an eligible workspace
administrator to import `https://github.com/withnative/plugins`. Choose one route per host.
The CLI and desktop app share the same Codex configuration, so installing with both routes
can produce duplicate skills and tools.

Start a new conversation and say
`Use Native's quickstart tool to help me finish setting up Native.` You can invoke Native
explicitly as `@native`, select `$enter` where the client exposes skill selectors, or make
an ordinary request such as `What is current in my Native workspace?`

## Claude Code

### Claude desktop: ordinary-user route

Availability depends on the account, workspace policy, and host surface. In Claude, open
**Customize → Plugins → Personal plugins → + → Add marketplace → Add from a repository**.
Enter `withnative/plugins`, add the marketplace, then select and install **Native** from
the resulting listing. Complete Native authentication and start a fresh conversation.

If the marketplace-add controls or listing are unavailable, explain that the host account
or policy is limiting the UI. Offer the CLI route below or an administrator-managed
distribution; do not claim that every Claude surface must use CLI setup.

### Claude Code CLI: agent route

When the Claude CLI is available, an agent should install Native directly. The default scope
is `user`:

```sh
claude plugin marketplace add withnative/plugins
claude plugin install native@withnative
```

Confirm the result with `claude plugin list`. Restart the desktop application, or run
`/reload-plugins` in a Claude Code terminal session if the installation summary asks for
it. The equivalent interactive commands are:

```text
/plugin marketplace add withnative/plugins
/plugin install native@withnative
```

If Native is visible in the Claude desktop plugin browser, select **Add plugin**, choose
Native, install it, complete sign-in, and start a fresh conversation. If it is not visible,
check the **Add marketplace → Add from a repository** route above before using CLI or
administrator distribution.

Start a new conversation and say
`Use Native's quickstart tool to help me finish setting up Native.` To invoke the entry
skill explicitly, use `/native:enter`.

## Authentication and first use

The installed plugin supplies Native's entry skill and an authenticated connection to
`https://plugin.withnative.ai/mcp`. The host owns the OAuth flow. Complete sign-in in the
window it opens; never paste a bearer token into a conversation, command, plugin file, or
repository issue.

The entry skill's broad trigger makes its activation proactive when durable context outside
the visible conversation could materially change the answer or action, and before material
multi-step work, file or external-state changes, and reusable artifacts, so you should not have
to mention Native or explicitly ask for recording.
Whenever the skill activates, first-use setup calls `quickstart` once and then `bootstrap`
exactly once. Otherwise, at the first Native interaction in a fresh
conversation, it calls `bootstrap` exactly once before any other Native tool or substantive
Native work. Bootstrap is bounded orientation, not permission for broad workspace scans,
imports, or unrelated writes. The agent retrieves relevant Native context before acting or
asking you to repeat it. For material work, it follows Bootstrap's recording and authority
boundaries to declare intent once it is clear and establish or update a durable work anchor when
the work is substantial or resumable, before execution begins.

Direct MCP-only connections do not load the packaged entry skill. An unconditional
once-per-fresh-conversation bootstrap rule for MCP-only clients requires a corresponding
update to the hosted Native service's MCP instructions. Those instructions are deployed with
the service; they are not part of this repository, so this repository change cannot satisfy
the MCP-only runtime path by itself.

The current hosted connection supports one Native workspace membership per signed-in account.
If the service cannot identify one unambiguous workspace, it stops rather than choosing one
silently.

## Direct MCP fallback

Use this only after the packaged plugin and the host's in-product/plugin suggestion routes
are unavailable. In the host's Add connector, Add MCP server, or equivalent control, enter:

| Field | Value |
| --- | --- |
| URL | `https://plugin.withnative.ai/mcp` |
| Transport | Streamable HTTP |
| Authorization | Host-managed OAuth/Bearer token obtained from Native sign-in; never paste manually |

Clients use different labels—connector, MCP server, or integration—but these are the same
three values. Authentication is host-managed OAuth/sign-in: users must not obtain or paste
a bearer token into a conversation, plugin file, command history, or issue. Use the
host-specific route that matches the client, verify that the connection is enabled and
Native tools are available, then start a fresh conversation.

### ChatGPT desktop

In the ChatGPT desktop app, open **Settings → MCP servers → Add server**. Enter the name
`native`, choose **Streamable HTTP**, and enter
`https://plugin.withnative.ai/mcp` as the URL. Save the server and choose **Restart** when
prompted. If the server list marks Native as needing OAuth, choose **Authenticate** and
complete the Native sign-in in the host-managed browser flow. In the composer, use `/mcp`
to view connected servers. ChatGPT web does not read local Codex configuration; use a
plugin listed in its Plugins Directory there instead.

### Codex CLI and shared Codex configuration

The Codex CLI, ChatGPT desktop app, and Codex IDE extension share the local Codex MCP
configuration. Add and verify Native from a terminal:

```sh
codex mcp add native --url https://plugin.withnative.ai/mcp
codex mcp list
```

If Codex reports that Native needs authorization, or when starting OAuth explicitly, run:

```sh
codex mcp login native
```

Complete the browser sign-in that Codex opens; do not retrieve or paste a bearer token.
The equivalent supported user configuration is:

```toml
[mcp_servers.native]
url = "https://plugin.withnative.ai/mcp"
```

After authentication, use `codex mcp list` again to verify the configured server. In the
Codex TUI, `/mcp` shows active MCP servers.

### Claude Code

Add Native as a user-scoped remote HTTP server, then verify it:

```sh
claude mcp add --transport http --scope user native https://plugin.withnative.ai/mcp
claude mcp list
```

In a Claude Code session, run `/mcp`; select Native's authentication action if shown and
complete the browser sign-in through Claude Code. Claude Code stores and refreshes OAuth
credentials through the host; do not obtain or paste a bearer token. `/mcp` also shows the
connected server and its tool count.

This direct connection reaches Native's hosted MCP tools, but it is a subset of the
packaged plugin experience: it does not include the `enter` skill or its proactive bootstrap
behavior. In particular, the host will not automatically receive the plugin's context-entry
guidance before relevant work. Invoke Native explicitly according to the host's MCP
controls. Direct MCP-only clients also require the hosted service's MCP instructions to
provide any unconditional first-use bootstrap rule; that service-side update is outside
this repository.

## Updates

For ChatGPT/Codex Desktop, refresh the marketplace snapshot and reinstall:

```sh
codex plugin marketplace upgrade withnative
codex plugin remove native@withnative
codex plugin add native@withnative
```

For Claude Code, refresh the marketplace and reinstall:

```sh
claude plugin marketplace update withnative
claude plugin uninstall native@withnative
claude plugin install native@withnative
```

Restart or reload the client after a package update and begin a new conversation.

## Uninstall

For ChatGPT/Codex Desktop:

```sh
codex plugin remove native@withnative
```

For Claude Code:

```sh
claude plugin uninstall native@withnative
```

To stop tracking the shared marketplace as well, run
`codex plugin marketplace remove withnative` or
`claude plugin marketplace remove withnative` for the relevant client. Do this only when
you no longer need any package from that marketplace. Removing the Native plugin removes
its packaged skill and connection; it does not delete data held by Native.

## Recovery and troubleshooting

If Native is absent after installation:

- Confirm `https://github.com/withnative/native-plugin` is publicly reachable.
- Confirm the package appears in `codex plugin list` or `claude plugin list`.
- Restart ChatGPT/Codex Desktop, or reload/restart Claude Code.
- Inspect the client's MCP controls and confirm the plugin-provided `native` server is
  enabled and connected.
- Confirm `https://plugin.withnative.ai/mcp` is reachable from the client environment.
- Start a new conversation after installation or update.

If a standalone connection already targets exactly `https://plugin.withnative.ai/mcp`, it
may duplicate the connection supplied by the plugin. Do not remove or rewrite it
automatically. Identify the exact entry, explain the overlap, ask before changing it, and
verify that the plugin-provided connection still works after any approved cleanup.

If Native's tools remain unavailable, do not invent workspace state or continue from
remembered guidance. Report that the connection is unavailable and return to these
installation checks.

These routes are supported only on the named desktop and CLI surfaces. Browser-only and
mobile clients must be verified on the specific account and client before support is
claimed.

## jcode and other stdio-only clients

jcode requires a command-based stdio server and cannot use the marketplace's HTTP declaration
directly. The `@withnative/mcp-stdio` adapter is being prepared as a separately versioned
compatibility route, but `0.1.0` is not yet published to npm. Do not copy its `npx` examples
into a live configuration until that exact release exists and its acceptance gate passes.

The candidate source and pre-release operating notes are in
[`packages/mcp-stdio/README.md`](../packages/mcp-stdio/README.md). The adapter routes to the
hosted Native service; it does not install a second tool set.
