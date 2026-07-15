---
name: repository-hygiene-audit
description: Audit one or more Git repositories for exact duplicates, suspicious near-duplicates, misplaced context, inconsistent project structure, dirty worktrees, nested repositories, raw-data risks, credential-like files, and other structural drift. Use for recurring repository cleanup reviews, context-folder governance, pre-refactor inventories, or scheduled read-only hygiene reports.
---

# Repository Hygiene Audit

Audit repositories without changing them. Treat every finding as evidence for
review, not permission to delete, move, merge, or rewrite a file.

## Run the deterministic scan

1. Read `references/context-taxonomy.md` when the repositories use a durable
   context or knowledge folder.
2. Choose the workspace containing the repositories.
3. Run:

   ```bash
   python3 scripts/audit_repos.py \
     --workspace-root "/path/to/workspace" \
     --format markdown
   ```

   The scanner audits the workspace itself when it is a Git repository;
   otherwise it discovers direct child repositories. Use repeated `--repo`
   arguments to select specific child directories. Pass `--config` to override
   taxonomy defaults.

4. Verify high-severity findings against filenames, repository structure, and
   Git history. Do not expose sensitive file contents in the report.
5. Return a concise report with prioritized findings and backlog counts.

## Classify findings

- **Deterministic:** dirty worktree, nested Git metadata, missing project
  metadata, project status mismatch, exact byte-for-byte duplicate, or a raw
  data-like file under durable context.
- **Needs judgment:** similar filenames, overlapping strategy documents,
  possible contradictions, legacy locations, or unclear canonical ownership.
- **Sensitive-risk:** credential-like filename, raw export, archive, or rendered
  deliverable stored in a durable knowledge folder.

## Safety rules

- Make no changes during an audit.
- Never select a canonical document by filename date alone.
- Never delete based only on hash or filename similarity; confirm references,
  purpose, ownership, and Git history.
- Never quote suspected secrets or sensitive client/customer data.
- If remediation is authorized later, use one branch and pull request per
  repository.
- Preserve history with `git mv` for reviewed migrations.
- Stop remediation in any dirty worktree until its active work is understood.

## Report contract

Include:

1. Workspace and repositories scanned.
2. Finding counts by severity and code.
3. Every high-severity finding.
4. Up to 25 prioritized medium/low findings.
5. Counts for the remaining backlog.
6. Recommended human next actions.
7. An explicit statement that no files were changed.
