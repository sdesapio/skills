---
name: project-docs
description: Bootstrap, update, and optimize project documentation for AI-assisted development. Use for requests to init, update, or optimize project docs, maintain working state, or structure architecture documentation for agents with on-demand loading.
---

# Project Docs

Maintain a small project overview, current working state, and focused architecture sections that agents read on demand. Preserve decisions, constraints, and evidence that prevent repeated investigation or regressions.

## Choose the scope

- **Init:** establish documentation or fill gaps in a partial setup.
- **Update:** refresh current state and any documentation affected by the work.
- **Optimize:** reduce routinely loaded context while preserving useful information.

Infer the mode from the request and repository. Ask only when an unresolved choice materially changes the work. An assessment request calls for findings, not scaffolding or edits.

## Inspect before editing

Identify the repository root, applicable instructions, existing documentation, and the agent or editor that will load it. Inspect current changes so documentation work preserves unrelated edits.

Reuse established paths and formats, including an existing history archive. Do not create a parallel documentation system just because its filenames differ from these defaults. Inspect existing files before merging additions; rerunning a workflow should not duplicate rules, indexes, or history entries.

Explore relevant code, configuration, tests, and recent changes before interviewing the user. Distinguish observed behavior, developer-confirmed decisions, proposals, and unknowns. Recover rationale from available evidence; ask about consequential gaps rather than inventing explanations.

Read [templates.md](templates.md) when creating or restructuring files. Adapt the templates to the project; omit empty sections and unfilled placeholders.

## Init

1. Establish the project's purpose, structural boundaries, configuration, core abstractions, build/test entry points, current work, and non-obvious constraints. For an empty project with meaningful design decisions, document those as planned; if there is little substance, keep the result minimal.
2. Create or merge **`docs/architecture-overview.md`**. Include a short orientation and one authoritative index of additional architecture sections with one-line descriptions. Keep detailed behavior in the relevant section. Aim well below 250 lines; use size as a review signal, not a quota.
3. Create or merge **`docs/state.md`** for current work, unresolved questions, next actions, and concise recent outcomes with evidence links. Include an updated date and relevant branch/revision when it helps interpret the state. Create **`docs/state-history.md`** only when there is history to archive.
4. Add context-loading guidance in the host's supported instruction mechanism:
   - **Codex:** merge a short section into the applicable **`AGENTS.md`**. Inspect `AGENTS.override.md` and scoped instructions so the addition reaches the intended tasks. Do not replace unrelated instructions or add Cursor frontmatter.
   - **Cursor:** merge **`.cursor/rules/project-context.mdc`** with `alwaysApply: true` when Cursor is the intended host.
   - **Other hosts:** use their established instruction mechanism. Do not assume changing frontmatter makes a rule portable.
   - If multiple hosts are requested, let each loader point to the same docs. Keep the section index only in the overview.
5. Create focused **`docs/architecture-<concern>.md`** sections where detail merits separate loading. Group by concern, such as data, UI, authentication, infrastructure, or testing. Avoid empty stubs and fragmentation merely to meet line limits.

## Update

Read the overview and current state, then inspect sections relevant to the changes. Load history only when needed to resolve a past decision or status.

- Reconcile current state with the conversation and available repository evidence. Distinguish implemented, tested, merged, and deployed; a commit alone does not prove a release or successful verification.
- Preserve active work from other tasks. Update the affected entries rather than rewriting unrelated work as complete or removing it.
- Record newly discovered decisions, behavioral constraints, footguns, configuration changes, and operational guidance in the relevant architecture section—even when no structural change occurred. Avoid documenting routine feature work that adds no enduring knowledge.
- Keep current blockers, unresolved questions, and constraints in current state. Move superseded outcomes and detailed release narratives into the existing history archive, retaining dates and evidence links. Keep a brief current outcome when it still helps continuation.
- Label the archive as historical, including superseded pending statuses and recovery targets. History is evidence, not current instructions or fresh authorization. Reuse the archive rather than creating a new state file for each handoff.
- Keep enduring project rules in the appropriate instructions or architecture docs, with a link from state when useful. Do not bury an active constraint solely in the archive.
- Update the overview's index when sections are added, renamed, or removed. Update affected links and the state's last-updated date.

## Optimize

### Inventory the context actually loaded

List documentation and instruction files, their line/byte sizes, and whether they are routinely loaded or on demand. Start with headings and the loading instructions; read the content being changed rather than indiscriminately loading every report and archive.

Include the overview, current state, context-loading guidance, and other applicable always-on instructions in the baseline. Count each file once and disclose exclusions. Report token counts only when measured with an identified tokenizer, or clearly label estimates and their method. A reduction in lines is not a measured token saving.

### Reduce the baseline

- Extract detail from an oversized overview into sections with distinct concerns. Split large sections only when it improves retrieval; a long cohesive section may be preferable to several fragments.
- Archive completed or superseded state. Keep current state short enough to scan; around 100 lines is a useful review trigger, but dense paragraphs also warrant review. Preserve current blockers and recovery guidance needed for active work.
- Remove duplicate section indexes and repeated content. Keep the overview as the routing index, with explicit links from sections where needed.
- Review task-specific always-on rules using the host's actual loading semantics. Propose narrower activation only when their applicability can be preserved. Do not weaken enduring project constraints to save context. Apply changes within the user's requested scope; otherwise report the recommendations.

### Preserve content when splitting or moving docs

For a monolithic architecture document or other migration:

1. Identify useful content and its destination, including decisions, caveats, examples, commands, and evidence links. State the intended grouping; proceed with a clear, authorized reorganization and ask only about consequential unresolved choices.
2. Create or merge destination files and adjust relative links for their new locations. Preserve existing custom content.
3. Compare the old content with the result for semantic coverage. Explain intentional removals of stale or duplicated information; equal line counts do not prove preservation.
4. Search the repository for references to moved paths and headings. Repair links and anchors, including instruction files and scripts that consume the docs. If external references may need compatibility, retain a small redirect/index stub at the old path.
5. Remove the superseded original only after coverage and reference checks pass. Keep it until unresolved preservation issues are addressed.

## Verify and report

Check that new or changed local links and anchors resolve, the overview lists the intended sections, current state and history do not conflict about what is current, and the host's effective instructions point to the right files. Describe configured loading separately from loading observed in a fresh agent session; do not claim a runtime check you did not perform.

Report what changed, important remaining unknowns, and validation performed. For optimization, include before/after routinely loaded sizes and on-demand sizes using the same measurement method and scope. For small updates, a short change summary is enough.

## Writing principles

- **Precision before brevity:** preserve why a decision exists and what breaks if a constraint is ignored. Link to detailed evidence rather than copying entire reports into current state.
- **Docs guide verification:** use documentation to focus exploration; verify task-relevant claims against current code, tests, and configuration. Record discrepancies without treating every documented fact as needing a full re-audit.
- **Self-contained sections:** make each section understandable on its own, with explicit file references instead of “see above.” Avoid duplicating shared detail merely to achieve self-containment.
- **Judgment-based loading:** use the overview's descriptions to choose relevant sections as the task evolves. Avoid a separate topic-to-file lookup system.
