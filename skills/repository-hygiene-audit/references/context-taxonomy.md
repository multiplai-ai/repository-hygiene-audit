# Suggested Context Taxonomy

This optional contract prevents a durable knowledge folder from becoming a
catch-all. Adopt it directly or override the defaults in a config file.

```text
context/
├── README.md
├── foundations/
├── projects/
│   ├── active/<project-id>/
│   ├── paused/<project-id>/
│   ├── completed/<year>/<project-id>/
│   └── cancelled/<year>/<project-id>/
├── reporting/
│   ├── recurring/<report-id>/<year>/
│   ├── analyses/<topic>/
│   └── snapshots/<system>/
├── functions/<function-id>/
├── entities/<entity-id>/
├── decisions/
└── references/
```

Create folders only when they contain real material. Do not fill the tree with
placeholder files.

## Foundations

Keep current, approved documents that govern most work. Useful canonical files
include:

- `business.md`
- `offers-and-pricing.md`
- `customers-and-buying.md`
- `problems-and-solutions.md`
- `positioning-and-messaging.md`
- `competitive-landscape.md`
- `brand-voice.md`
- `proof.md`

Update the canonical file through Git instead of creating `final`, `copy`, or
`v2` variants.

## Projects

Use `projects/<status>/<project-id>/project.yaml` as the project index:

```yaml
schema_version: 1
id: launch-project
title: Launch Project
status: active
owner: team-or-person
started: 2026-01-15
updated: 2026-02-01
summary: Ship the approved launch outcome.
task_system: external
task_refs: []
workstreams: []
```

Use an external task system for volatile task/subtask state. Keep durable
artifacts under project `workstreams/`, decisions, outputs, or references.

## Reporting and functions

- Store retained reports and durable analyses in `reporting/`.
- Store ongoing discipline knowledge in `functions/<function-id>/`.
- Keep finite initiatives under `projects/` even when they concern a function.
- Keep raw exports, source workbooks, sensitive files, and rendered client
  deliverables outside the repository in approved storage.

## Placement test

1. Governs most work → `foundations/`.
2. Delivers a finite outcome → `projects/`.
3. Preserves a measurement or analysis → `reporting/`.
4. Supports an ongoing discipline → `functions/`.
5. Applies to a distinct entity → `entities/<id>/`.
6. Records a cross-cutting choice → `decisions/`.
7. Points to external information → `references/`.
8. Is raw, sensitive, temporary, or rendered → external/session storage.
