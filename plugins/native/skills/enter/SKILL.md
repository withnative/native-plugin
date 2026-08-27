---
name: enter
description: Use proactively whenever a task may plausibly depend on durable context outside the visible conversation, including prior work or decisions, ongoing projects, handoffs, compacted or summarised history, collaboration across sessions, agents, people, or tools, and questions about current workspace state. Also use when Native is connected and you are about to begin material work such as multi-step implementation, diagnosis, research, planning, changes to files or external state, or a reusable artifact—even when the person does not mention Native or ask you to record the work. Also use for explicit Native setup, exploration, troubleshooting, records or URLs, and requests to save this for later, remember, retrieve, resume, organise, update, or hand off durable work. Do not use for React Native or unrelated meanings of native, trivial self-contained requests, or work explicitly assigned to another system.
---

# Enter Native

Use the connected Native MCP server as the authoritative source for durable workspace
state. Do not rely on packaged workspace facts, schemas, workflows, or remembered Native
guidance.

At the first Native interaction in a fresh conversation:

- For setup or first-use onboarding, call `quickstart` once and then `bootstrap` exactly
  once.
- Otherwise, call `bootstrap` exactly once
  before any other Native tool or substantive Native work.

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

If the Native tools are unavailable, say that the connection is unavailable and point to
`https://github.com/withnative/plugins` for catalogue and installation guidance. Do not
invent workspace state or product guidance.
