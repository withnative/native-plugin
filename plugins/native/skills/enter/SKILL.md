---
name: enter
description: Use proactively whenever a task may plausibly depend on durable context outside the visible conversation, including prior work or decisions, ongoing projects, handoffs, compacted or summarised history, collaboration across sessions, agents, people, or tools, and questions about current workspace state. Also use when Native is connected and you are about to begin material work such as multi-step implementation, diagnosis, research, planning, changes to files or external state, or a reusable artifact—even when the person does not mention Native or ask you to record the work. Also use for explicit Native exploration, troubleshooting, records or URLs, and requests to save this for later, remember, retrieve, resume, organise, update, or hand off durable work. Do not use for React Native or unrelated meanings of native, trivial self-contained requests, or work explicitly assigned to another system.
---

# Enter Native

Use the connected Native MCP server as the authoritative source for durable workspace
state. Do not rely on packaged workspace facts, schemas, workflows, or remembered Native
guidance.

At the first Native interaction in a fresh conversation:

- For setup or first-use onboarding, call `quickstart` once and then obtain one successful
  `bootstrap` response.
- Otherwise, obtain one successful `bootstrap` response before any other Native tool or
  substantive Native work.

Bootstrap entry is once per conversation, not once per skill activation or task.
Re-triggering or re-reading this skill on a later user turn, when the task, intent, or
artifact changes, or after context compaction is still within the same conversation and
must not cause another `bootstrap` call or successful response. Retain the original returned
`run_key` across turns and compaction, and reuse it on all subsequent Native calls. When
the underlying aim materially changes, call `set_intent` with that same `run_key`.

After context compaction on a coding host, a SessionStart hook may have emitted a
compaction cue carrying the retained `run_key` (and WorkItem anchor when one was
claimed). A visible summary may also retain the original key. When the key is
available, refresh in this order without calling
`bootstrap` again in the same conversation:

- Resolve guidance first: call the Native `manage_instructions` action `resolve`
  with the retained `run_key`. Apply guidance only when `instructions.status`
  is `ready` with complete active entries, at its original user/workspace
  authority. Native does not verify that a well-formed run key was issued; the
  key's continuity comes from the host mapping or visible conversation. If
  guidance resolution is invalid, do not apply partial or frozen guides;
  surface its diagnostics and repair the source when authorized. If the Native
  tools are unavailable, use `connect`. Neither condition calls for another
  `bootstrap` in this conversation.
- Refresh task state separately from guidance: with a known anchor, read the
  current record and bounded recent history; label current versus recent, and
  never claim changed-since without a cursor. Without an anchor, use retained
  intent and visible context to find only relevant work, or ask when that is
  insufficient.

Ordinary ChatGPT/Claude chat has no automatic compaction hook. When context
uncertainty or a visible summary indicates compaction there, apply the same
agent-led steps when the original key is available, without claiming automatic
detection. If the key was lost, explain that Native run continuity cannot be
recovered from the visible context; continue from available evidence or ask for
the missing context. Do not bootstrap again merely because of compaction.

Before the first successful `bootstrap` response, if bootstrap fails with a connection-pool
timeout, transient transport failure, or HTTP 502/503/504 before returning a usable run key,
retry bootstrap at most twice, waiting one second before the first retry and two seconds
before the second. Honour a longer server `Retry-After`; if it exceeds 30 seconds, stop and
report temporary unavailability instead. A failed attempt does not require a new
conversation. Do not retry authentication, validation, or instruction-readiness failures as
transient outages. If the attempts are exhausted, report the failure and stop Native-dependent
work; do not invent workspace state. The bounded retry window closes with the first successful
response; do not retry or call `bootstrap` again after that. These retries apply only to
bootstrap, not to writes.

Treat `bootstrap` as bounded orientation, not permission to scan the workspace broadly.
If missing context outside the visible conversation could materially change the answer or
action, recover the relevant Native context before acting or asking the person to repeat it.
Keep discovery proportionate to the task; do not perform indiscriminate scans or imports.

Follow the current orientation, standing guidance, and continuations returned by Native.
Keep healthy internal machinery in the background and explain outcomes, choices, and
useful next steps.

For material work, follow Bootstrap's recording and authority boundaries to make the
activity visible before execution. Once the person's aim is clear, declare it, recover
relevant context and active work, and establish or update a durable work anchor when the
work is substantial or resumable. Keep that record current enough for coordination,
recovery, and hand-off.

Activation permits relevant discovery, not unrelated writes. Make writes only when they
are within the person's request and the current Native guidance permits them.

If the Native tools are unavailable, or the person asks to install Native, sign in,
reconnect, or repair expired authorisation, use the packaged `connect` skill. If it is not
available either, say that the connection is unavailable and point to
`https://github.com/withnative/plugins` for catalogue and installation guidance. Do not
invent workspace state or product guidance.
