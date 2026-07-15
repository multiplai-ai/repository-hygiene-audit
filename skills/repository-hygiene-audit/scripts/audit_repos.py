#!/usr/bin/env python3
"""Read-only structural hygiene audit for one or more Git repositories."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import yaml


DEFAULTS: dict[str, Any] = {
    "context_dir": "context",
    "ignore_parts": [".git", ".agents", "node_modules", ".venv", "__pycache__", "generated"],
    "raw_context_suffixes": [".csv", ".tsv", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".tar", ".gz"],
    "allowed_context_dirs": ["foundations", "projects", "reporting", "functions", "entities", "decisions", "references", "legacy"],
    "allowed_context_files": ["README.md"],
    "legacy_context_map": {
        "strategy": "foundations/",
        "voice": "foundations/brand-voice.md",
        "content": "functions/content/",
        "analysis": "reporting/analyses/",
        "planning": "projects/active/<project-id>/",
        "marketing": "functions/marketing-ops/",
    },
    "project_statuses": ["active", "paused", "completed", "cancelled"],
}
PROJECT_REQUIRED = {
    "schema_version", "id", "title", "status", "owner", "started", "updated",
    "summary", "task_system", "task_refs", "workstreams",
}


def make_finding(repo: str, code: str, severity: str, confidence: str, path: str, message: str, recommendation: str) -> dict[str, str]:
    return {"repo": repo, "code": code, "severity": severity, "confidence": confidence, "path": path, "message": message, "recommendation": recommendation}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def load_config(path: Path | None) -> dict[str, Any]:
    config = dict(DEFAULTS)
    if path:
        config.update(load_yaml(path))
    return config


def discover_repositories(workspace_root: Path, requested: Iterable[str] | None = None) -> list[Path]:
    root = workspace_root.resolve()
    if requested:
        return [root / name for name in requested]
    if (root / ".git").exists():
        return [root]
    return sorted(path for path in root.iterdir() if path.is_dir() and (path / ".git").exists())


def iter_files(root: Path, ignored: set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and not ignored.intersection(path.relative_to(root).parts):
            yield path


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def normalized_stem(path: Path) -> str:
    value = path.stem.lower()
    value = re.sub(r"^\d{4}-\d{2}-\d{2}[-_ ]*", "", value)
    value = re.sub(r"(?:[-_ ](?:final|copy|draft|rev|v)\d*)+$", "", value)
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def project_dirs(projects: Path, statuses: set[str]) -> Iterable[tuple[str, Path]]:
    for status in statuses:
        status_root = projects / status
        if not status_root.is_dir():
            continue
        if status in {"completed", "cancelled"}:
            for year in status_root.iterdir():
                if year.is_dir():
                    for project in year.iterdir():
                        if project.is_dir():
                            yield status, project
        else:
            for project in status_root.iterdir():
                if project.is_dir():
                    yield status, project


def audit_repository(root: Path, config: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, list[str]]]:
    repo = root.name
    findings: list[dict[str, str]] = []
    hashes: dict[str, list[str]] = defaultdict(list)
    ignored = set(config["ignore_parts"])
    if not root.is_dir() or not (root / ".git").exists():
        return [make_finding(repo, "REPO_MISSING", "high", "high", str(root), "Repository is missing or is not a Git checkout.", "Correct the workspace or repository selection.")], hashes

    status = subprocess.run(["git", "status", "--porcelain"], cwd=root, text=True, capture_output=True, check=False)
    if status.returncode or status.stdout.strip():
        findings.append(make_finding(repo, "WORKTREE_NOT_CLEAN", "medium", "high", ".", "Working tree is not clean.", "Preserve and understand active work before any remediation."))

    for nested in root.rglob(".git"):
        if nested == root / ".git" or ignored.intersection(nested.relative_to(root).parts[:-1]):
            continue
        findings.append(make_finding(repo, "NESTED_GIT_REPOSITORY", "high", "high", rel(nested, root), "Nested Git metadata found.", "Review the nested checkout before an approved migration."))

    context = root / str(config["context_dir"])
    allowed_dirs = set(config["allowed_context_dirs"])
    allowed_files = set(config["allowed_context_files"])
    legacy_map = dict(config["legacy_context_map"])
    raw_suffixes = {str(item).lower() for item in config["raw_context_suffixes"]}
    if context.is_dir():
        for entry in sorted(context.iterdir()):
            if entry.is_dir() and entry.name in legacy_map:
                findings.append(make_finding(repo, "CONTEXT_LEGACY_LOCATION", "low", "high", rel(entry, root), f"Legacy context location; suggested destination is {legacy_map[entry.name]}.", "Classify and migrate through a reviewed change; do not mass-move."))
            elif entry.is_dir() and entry.name not in allowed_dirs:
                findings.append(make_finding(repo, "CONTEXT_UNCLASSIFIED_LOCATION", "low", "medium", rel(entry, root), "Top-level context directory is outside the configured taxonomy.", "Classify it under an approved category or update the config intentionally."))
            elif entry.is_file() and entry.name not in allowed_files:
                findings.append(make_finding(repo, "CONTEXT_UNCLASSIFIED_FILE", "low", "medium", rel(entry, root), "Loose top-level context file needs classification.", "Place it under the appropriate category after review."))

        names: dict[str, list[str]] = defaultdict(list)
        for path in iter_files(context, ignored):
            relative_path = rel(path, root)
            if path.suffix.lower() in raw_suffixes:
                findings.append(make_finding(repo, "EXTERNAL_DATA_RISK", "high", "high", relative_path, "Raw, archived, or rendered data-like file is stored under durable context.", "Verify authorization and move it to approved external or session storage."))
            if re.search(r"(?:^|[-_ ])(?:final|copy|v\d+|draft)(?:[-_ .]|$)", path.name.lower()):
                findings.append(make_finding(repo, "VERSIONED_FILENAME", "low", "medium", relative_path, "Filename suggests a manual revision copy.", "Determine whether one canonical filename plus Git history is sufficient."))
            if path.stat().st_size:
                hashes[hashlib.sha256(path.read_bytes()).hexdigest()].append(relative_path)
            stem = normalized_stem(path)
            if stem:
                names[stem].append(relative_path)
        for paths in hashes.values():
            if len(paths) > 1:
                findings.append(make_finding(repo, "EXACT_DUPLICATE", "medium", "high", ", ".join(paths), "Files are byte-for-byte identical.", "Confirm canonical ownership and references before removing any copy."))
        for paths in names.values():
            if len(paths) > 1:
                findings.append(make_finding(repo, "SIMILAR_NAME_CANDIDATE", "low", "low", ", ".join(sorted(paths)), "Files have similar normalized names and may overlap.", "Compare purpose, approval, provenance, and contents; do not choose by date alone."))

        projects = context / "projects"
        statuses = set(config["project_statuses"])
        if projects.is_dir():
            for entry in sorted(projects.iterdir()):
                if entry.is_dir() and entry.name not in statuses:
                    findings.append(make_finding(repo, "PROJECT_LEGACY_LOCATION", "low", "high", rel(entry, root), "Project is not nested under a configured status folder.", "Classify its status before moving it."))
            for expected_status, project in project_dirs(projects, statuses):
                metadata_path = project / "project.yaml"
                if not metadata_path.is_file():
                    findings.append(make_finding(repo, "PROJECT_METADATA_MISSING", "medium", "high", rel(project, root), "Project directory has no project.yaml index.", "Add reviewed project metadata and task-system pointers."))
                    continue
                metadata = load_yaml(metadata_path)
                missing = sorted(PROJECT_REQUIRED.difference(metadata))
                if missing:
                    findings.append(make_finding(repo, "PROJECT_METADATA_INCOMPLETE", "medium", "high", rel(metadata_path, root), "Missing project fields: " + ", ".join(missing), "Complete the project index."))
                if metadata.get("status") != expected_status:
                    findings.append(make_finding(repo, "PROJECT_STATUS_MISMATCH", "medium", "high", rel(metadata_path, root), f"Metadata status {metadata.get('status')!r} does not match folder {expected_status!r}.", "Correct metadata or move the entire project after review."))

    for path in iter_files(root, ignored):
        lower = path.name.lower()
        credential_like = lower == ".env" or lower.startswith(".env.") or bool(re.search(r"(?:^|[-_.])(?:credentials?|passwords?|secrets?|api[-_]?keys?|private[-_]?keys?|access[-_]?tokens?)(?:[-_.]|$)", lower))
        if credential_like:
            findings.append(make_finding(repo, "CREDENTIAL_FILENAME_RISK", "high", "medium", rel(path, root), "Filename suggests credential or secret material.", "Verify without exposing contents and move secrets to an approved credential store."))
    return findings, hashes


def audit_workspace(workspace_root: Path, repositories: Iterable[str] | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    root = workspace_root.resolve()
    config = config or dict(DEFAULTS)
    repo_paths = discover_repositories(root, repositories)
    findings: list[dict[str, str]] = []
    cross_hashes: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for repo_root in repo_paths:
        repo_findings, hashes = audit_repository(repo_root, config)
        findings.extend(repo_findings)
        for digest, paths in hashes.items():
            cross_hashes[digest].extend((repo_root.name, path) for path in paths)
    for locations in cross_hashes.values():
        if len({repo for repo, _ in locations}) > 1:
            display = ", ".join(f"{repo}:{path}" for repo, path in sorted(locations))
            findings.append(make_finding("cross-repo", "CROSS_REPO_EXACT_DUPLICATE", "medium", "medium", display, "Identical context content exists in multiple repositories.", "Confirm whether this is intentional shared context or a misplaced duplicate."))
    severity_order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda item: (severity_order[item["severity"]], item["repo"], item["code"], item["path"]))
    return {"schema_version": 1, "audit_date": date.today().isoformat(), "workspace_root": str(root), "repositories": [path.name for path in repo_paths], "changed_files": False, "findings": findings}


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Repository Hygiene Audit", "", f"- Date: {report['audit_date']}", f"- Repositories scanned: {len(report['repositories'])}", f"- Findings: {len(report['findings'])}", "- Files changed: no", ""]
    if not report["findings"]:
        return "\n".join(lines + ["No hygiene findings detected.", ""])
    for severity in ("high", "medium", "low"):
        group = [item for item in report["findings"] if item["severity"] == severity]
        if not group:
            continue
        lines.extend((f"## {severity.title()} severity", ""))
        for item in group:
            lines.extend((f"### {item['repo']} — {item['code']}", "", f"- Path: `{item['path']}`", f"- Confidence: {item['confidence']}", f"- Finding: {item['message']}", f"- Recommendation: {item['recommendation']}", ""))
    return "\n".join(lines + ["No files were changed by this audit.", ""])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--repo", action="append", dest="repos")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_workspace(args.workspace_root, args.repos, load_config(args.config))
    content = json.dumps(report, indent=2) + "\n" if args.format == "json" else render_markdown(report)
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
