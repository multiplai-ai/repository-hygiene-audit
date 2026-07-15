# Repository Hygiene Audit for Codex

A read-only Codex skill and deterministic scanner for finding structural drift
across one or more Git repositories—without automatically deleting, moving, or
rewriting anything.

It detects:

- exact duplicate files and suspicious near-duplicate names;
- dirty worktrees and nested Git repositories;
- loose or misplaced durable context;
- raw exports, archives, and rendered files inside context folders;
- credential-like filenames without reading or exposing their contents;
- projects missing metadata or stored under the wrong status;
- identical context copied across repositories.

The scanner produces evidence. Codex reviews that evidence, prioritizes the
findings, and recommends human next steps. Cleanup remains a separate,
explicitly approved operation.

## Install with Codex

Ask Codex:

```text
Use $skill-installer to install repository-hygiene-audit from
https://github.com/multiplai-ai/repository-hygiene-audit/tree/main/skills/repository-hygiene-audit
```

Or copy the skill into a repository:

```bash
mkdir -p .agents/skills
git clone https://github.com/multiplai-ai/repository-hygiene-audit.git /tmp/repository-hygiene-audit
cp -R /tmp/repository-hygiene-audit/skills/repository-hygiene-audit .agents/skills/
python3 -m pip install PyYAML==6.0.2
```

Restart Codex if the skill does not appear immediately.

## Run

For a folder containing sibling repositories:

```bash
python3 .agents/skills/repository-hygiene-audit/scripts/audit_repos.py \
  --workspace-root "$HOME/work" \
  --format markdown
```

For one repository, use that repository as `--workspace-root`. To select
specific child repositories, repeat `--repo`:

```bash
python3 .agents/skills/repository-hygiene-audit/scripts/audit_repos.py \
  --workspace-root "$HOME/work" \
  --repo product-app \
  --repo docs-site \
  --format json \
  --output /tmp/repository-hygiene.json
```

Use [`examples/hygiene-config.yaml`](examples/hygiene-config.yaml) as a starting
point when your context folder or taxonomy differs from the defaults.

## Suggested Codex prompt

```text
Use $repository-hygiene-audit to scan this workspace. Do not change any files.
Show every high-severity finding, prioritize up to 25 remaining findings, and
summarize the rest by type. Do not expose suspected secrets or sensitive data.
```

You can use the same prompt in a weekly Codex automation. Keep the first phase
report-only. Add automated pull requests only after several reviewed runs prove
that the rules fit your repositories.

## Opinionated context structure

The included taxonomy separates durable knowledge into foundations, projects,
reporting, functions, entities, decisions, and references. It is optional and
configurable. See
[`references/context-taxonomy.md`](skills/repository-hygiene-audit/references/context-taxonomy.md).

## Safety model

- The scanner has no delete, move, Git commit, push, or pull-request code.
- It does not inspect credential contents.
- Filename similarity is always low-confidence.
- Exact duplicates still require human review of ownership and references.
- Remediation should happen later through normal branches and pull requests.

## Development

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 /path/to/skill-creator/scripts/quick_validate.py \
  skills/repository-hygiene-audit
```

Licensed under the [MIT License](LICENSE).
