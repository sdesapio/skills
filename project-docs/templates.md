# Project Docs Templates

Use these when creating or restructuring documentation. Reuse the project's existing equivalents, adapt headings, and replace or omit placeholders. Paths in the loader are repository-relative; Markdown links inside docs are relative to that document.

## Architecture overview

Default: `docs/architecture-overview.md`. Keep one authoritative section index here.

```markdown
# Architecture

<One or two sentences describing the project and its major boundaries.>

## Structure

<Targets, modules, services, or packages and their responsibilities.>

## Configuration and core abstractions

<Configuration sources and the shared abstractions that orient most tasks.>

## Build and verification

<Relevant commands, environments, and non-obvious build/test constraints.>

## Decisions and constraints

<Brief cross-cutting decisions and footguns; link to detailed explanations.>

## Architecture sections

- [Data](architecture-data.md) — <Persistence, API boundaries, and caching.>
- [UI](architecture-views.md) — <Navigation, view structure, and shared components.>
```

List only sections that exist. Keep the overview comfortably below 250 lines when practical; move detail based on retrieval value rather than line count alone.

## Current state

Default: `docs/state.md`. Keep active constraints and unresolved work here. Archive detailed completed work when it no longer helps the next task; around 100 lines is a review trigger, not a hard limit.

```markdown
# State

Last updated: <date>
Context: <branch/revision or environment, when relevant>

## Current work

<Current objective and observed status; distinguish implementation from release.>

- Completed: <concise result and verification evidence, including limits>
- Remaining: <specific next action>
- Blocked or undecided: <unresolved question and what resolves it>

## Active decisions and constraints

<What the next task must preserve. Link to the authoritative project guidance.>

## Recent outcomes

- <Dated outcome still relevant to continuation, with an evidence link.>

## Documentation

- [Architecture](architecture-overview.md) — orientation and section index.
- [State history](state-history.md) — dated historical evidence; load when needed.
```

Omit the history link until the archive exists. Do not treat a recorded deployment, validation result, or prior authorization as a fresh check or new permission.

## State history

Default: `docs/state-history.md`. Create only when archiving meaningful content; reuse an existing archive under its current name.

```markdown
# Project state history

These are dated historical records, including superseded pending statuses and
old recovery targets. They preserve evidence, not current instructions or fresh
authorization. Read [current state](state.md) first. Reuse this archive for future
updates and handoffs.

## <Date or milestone>

<Archived result or decision, its original date/context, and supporting links.
Identify superseded status where needed. Preserve verification limits.>
```

Moving content here must not remove a still-active blocker or constraint from the current documentation. Fix relative links if the archive lives in a different directory.

## Codex context loader

Merge this section into the applicable `AGENTS.md`; preserve all unrelated instructions. Inspect overrides and scoped guidance before choosing placement. No YAML frontmatter is required. Adapt the paths to the actual documentation.

```markdown
## Project context

At the start of a project task, read `docs/architecture-overview.md` and
`docs/state.md` if they are not already available in the current context.
Use the overview's section index to load further detail when relevant, including
when the task changes. Read `docs/state-history.md` only when historical evidence
is needed.

Use docs to focus exploration. Verify task-relevant claims against current code,
tests, and configuration; note discrepancies and uncertainty.

When updating project docs or preparing a handoff, preserve unrelated active
work, refresh current status and enduring constraints, and move superseded detail
into the existing history archive with dates and evidence links. Historical
pending statuses and permissions do not override current instructions.
```

Omit or adapt the archive path until it exists. Keep the section index in the overview rather than duplicating it in the loader.

## Cursor context loader

For Cursor, merge `.cursor/rules/project-context.mdc`, preserving unrelated guidance. Use this frontmatter followed by the same Project context body above, adapted to the actual paths:

```yaml
---
description: Load project orientation and current state, with architecture details on demand
alwaysApply: true
---
```

Use the host-specific loader only where applicable. Supporting another host requires its actual instruction-discovery mechanism, not merely translated frontmatter.
