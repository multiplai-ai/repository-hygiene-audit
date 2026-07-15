from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "repository-hygiene-audit" / "scripts" / "audit_repos.py"
SPEC = importlib.util.spec_from_file_location("audit_repos", SCRIPT)
audit_repos = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(audit_repos)


class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.repo = self.workspace / "example-repo"
        (self.repo / ".git").mkdir(parents=True)
        (self.repo / "context").mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def findings(self):
        return audit_repos.audit_workspace(self.workspace)["findings"]

    def test_discovers_child_repository(self):
        self.assertEqual(audit_repos.audit_workspace(self.workspace)["repositories"], ["example-repo"])

    def test_discovers_workspace_repository(self):
        report = audit_repos.audit_workspace(self.repo)
        self.assertEqual(report["repositories"], ["example-repo"])

    def test_flags_legacy_context(self):
        (self.repo / "context" / "strategy").mkdir()
        self.assertTrue(any(item["code"] == "CONTEXT_LEGACY_LOCATION" for item in self.findings()))

    def test_flags_exact_duplicate(self):
        (self.repo / "context" / "one.md").write_text("same", encoding="utf-8")
        (self.repo / "context" / "two.md").write_text("same", encoding="utf-8")
        self.assertTrue(any(item["code"] == "EXACT_DUPLICATE" for item in self.findings()))

    def test_flags_raw_context_file(self):
        (self.repo / "context" / "export.csv").write_text("id\n1\n", encoding="utf-8")
        self.assertTrue(any(item["code"] == "EXTERNAL_DATA_RISK" for item in self.findings()))

    def test_flags_missing_project_metadata(self):
        (self.repo / "context" / "projects" / "active" / "launch").mkdir(parents=True)
        self.assertTrue(any(item["code"] == "PROJECT_METADATA_MISSING" for item in self.findings()))

    def test_flags_project_status_mismatch(self):
        project = self.repo / "context" / "projects" / "active" / "launch"
        project.mkdir(parents=True)
        (project / "project.yaml").write_text(yaml.safe_dump({
            "schema_version": 1, "id": "launch", "title": "Launch", "status": "paused",
            "owner": "team", "started": "2026-01-01", "updated": "2026-01-02",
            "summary": "Launch.", "task_system": "external", "task_refs": [], "workstreams": [],
        }), encoding="utf-8")
        self.assertTrue(any(item["code"] == "PROJECT_STATUS_MISMATCH" for item in self.findings()))

    def test_custom_context_directory(self):
        (self.repo / "knowledge").mkdir()
        (self.repo / "knowledge" / "old").mkdir()
        config = dict(audit_repos.DEFAULTS)
        config.update({"context_dir": "knowledge", "legacy_context_map": {"old": "foundations/"}})
        report = audit_repos.audit_workspace(self.workspace, config=config)
        self.assertTrue(any(item["code"] == "CONTEXT_LEGACY_LOCATION" for item in report["findings"]))

    def test_report_declares_no_changes(self):
        report = audit_repos.audit_workspace(self.workspace)
        self.assertFalse(report["changed_files"])
        self.assertIn("Files changed: no", audit_repos.render_markdown(report))


if __name__ == "__main__":
    unittest.main()
