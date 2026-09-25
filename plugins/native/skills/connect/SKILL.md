---
name: connect
description: Use when the person asks to install, set up, sign in to, reconnect, or re-authorise Native in Claude Code, Codex, or another client; when Native's MCP tools are missing, disconnected, or report expired or missing OAuth; or when adding Native to a second client. Do not use for ordinary Native work once connected (use `enter`), for React Native, or for unrelated meanings of native.
---

# Connect to Native

This skill covers installing the Native plugin and getting its hosted MCP connection
signed in. Once Native's tools respond, ordinary Native work, including the first
`quickstart` or `bootstrap` call and its once-per-conversation rules, belongs to the
packaged `enter` skill. Follow those rules here too; this skill never justifies a second
`bootstrap` or `quickstart`.

## Install

If you are asked to install the plugin, first probe whether you can run the client CLI
yourself (`claude plugin list`, `codex plugin list` — a bare `--version` check proves only
that a binary resolves and does not authorise proceeding); if the list probe succeeds,
install it rather than relaying commands. If the probe fails, or the install itself errors,
ask whether the person prefers the terminal or the UI route — with a recommendation — then
give instructions for that route only.

## Sign in

Installation and authorisation are separate steps: after any non-interactive install, run
or name the login command (`claude mcp login native`, `codex mcp login native`) as the
immediate next action. On headless or SSH sessions, add `--no-browser`. If you control the
still-running login prompt, the person may paste the full callback URL into agent chat for
you to enter there; otherwise have them paste it directly at the terminal prompt. Explain
that the URL contains a short-lived authorization code and remains in the chat transcript.
Never ask for a bearer token or put the callback URL in durable records. For Claude Code
this needs version `2.1.186` or later and `ssh -t` when using SSH. Full procedure:
`docs/plugin-installation.md` in `https://github.com/withnative/native-plugin`.

## Confirm sign-in

Confirm sign-in as soon as it completes; do not leave the person guessing whether it
worked. When the login command exits or the person says they have signed in, check
straight away. Prefer one live Native call in this conversation, made under the `enter`
skill's rules: its first-interaction `quickstart`/`bootstrap` if Native has not yet been
entered, whose response shows the connected account and workspace; otherwise one read call
reusing the existing `run_key`. If the tools load only after a reload or new conversation,
check the client's server status (`claude mcp list`, `codex mcp list`) instead, which is a
strong clue rather than proof. Then tell the person in one line: that they are connected,
and to which account and workspace when you know them, or that sign-in succeeded and
exactly what to do next to load the tools. If the check fails, say so plainly and give the
single next step, usually a fresh run of the login command. Do not report success you have
not checked.

## Headless or remote Codex re-authentication

When Codex reports expired or missing Native OAuth on a headless or remote host, follow
`docs/plugin-installation.md` ("Headless or remote Codex re-authentication"):
`codex mcp list` is only a strong clue, then run one fresh
`codex mcp login native --no-browser`, open only its fresh authorization URL locally, and
enter the full callback URL at its still-running terminal prompt, even when the callback
page cannot load. If you control that prompt, the person may send the URL in chat for you
to enter. This path was verified with a mock OAuth server on Codex CLI `0.156.1`, not a
live Native grant. Only if paste-back fails, retry with `-c mcp_oauth_callback_port=4321`
plus local `ssh -L` forwarding to its still-running listener. Then reload the client or
start a new conversation and verify with `list` plus one live Native tool call. In an
existing conversation, reuse its `run_key` for the read call. Never reuse an old
authorization URL: a callback after its login process exits is stale.

## When it cannot connect

If installation or sign-in still fails, say that the connection is unavailable, name the
step that failed, and point to `https://github.com/withnative/plugins` for catalogue and
installation guidance. Do not invent workspace state or product guidance.
