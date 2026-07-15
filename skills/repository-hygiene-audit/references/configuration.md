# Configuration

The scanner works without configuration. Pass `--config <yaml-file>` to
override defaults:

```yaml
context_dir: knowledge
allowed_context_dirs:
  - foundations
  - projects
  - reporting
  - functions
  - entities
  - decisions
  - references
allowed_context_files:
  - README.md
legacy_context_map:
  strategy: foundations/
  analysis: reporting/analyses/
project_statuses:
  - active
  - paused
  - completed
  - cancelled
raw_context_suffixes:
  - .csv
  - .xlsx
  - .pptx
ignore_parts:
  - .git
  - .agents
  - node_modules
  - .venv
  - __pycache__
  - generated
```

Values replace, rather than extend, the matching default list or mapping.
Repository selection remains a command-line concern: use repeated `--repo`
arguments or allow direct-child discovery.
