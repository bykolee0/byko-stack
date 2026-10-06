import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PLUGIN = Path(__file__).resolve().parents[1]


class PrepareAgentTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / "installed package" / "0.4.0"
        shutil.copytree(PLUGIN, self.package, ignore=shutil.ignore_patterns("__pycache__"))

    def run_role(self, role):
        return subprocess.run(
            [sys.executable, str(self.package / "scripts/prepare_agent.py"), role],
            cwd=self.root, capture_output=True, text=True,
        )

    def test_all_roles_work_outside_checkout(self):
        expected = {
            "byko-analyst": ["byko-analyze"],
            "byko-implementer": ["byko-implement"],
            "byko-reviewer": ["byko-review-code", "byko-review-document", "byko-review-viewer"],
            "byko-viewer": ["byko-build-viewer"],
        }
        for role, skills in expected.items():
            with self.subTest(role=role):
                result = self.run_role(role)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(output["model"], "gpt-6.1-sol")
                self.assertEqual(output["reasoning_effort"], "high")
                self.assertNotIn(str(PLUGIN), output["message"])
                for skill in skills:
                    self.assertIn(str(self.package / f"skills/{skill}/SKILL.md"), output["message"])

    def test_reads_configuration_instead_of_hardcoding(self):
        path = self.package / "agents/byko-analyst.toml"
        path.write_text(path.read_text().replace('"gpt-6.1-sol"', '"test-model"').replace('"high"', '"medium"'))
        output = json.loads(self.run_role("byko-analyst").stdout)
        self.assertEqual((output["model"], output["reasoning_effort"]), ("test-model", "medium"))

    def test_unknown_role_cannot_traverse_paths(self):
        result = self.run_role("../../outside")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_missing_skill_does_not_emit_partial_config(self):
        (self.package / "skills/byko-analyze/SKILL.md").unlink()
        result = self.run_role("byko-analyst")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_external_symlink_is_not_a_bundled_role(self):
        role = self.package / "agents/byko-analyst.toml"
        outside = self.root / "outside.toml"
        role.rename(outside)
        role.symlink_to(outside)
        self.assertEqual(self.run_role("byko-analyst").returncode, 2)

    def test_invalid_or_unsupported_config_is_not_silently_ignored(self):
        path = self.package / "agents/byko-analyst.toml"
        original = path.read_text()
        variants = [
            "invalid = [", original.replace('model = "gpt-6.1-sol"', 'model = 7'),
            original.replace('name = "byko-analyst"', 'name = "another"'),
            original.replace('model_reasoning_effort = "high"', ''),
            original + '\nsandbox_mode = "read-only"\n',
        ]
        for variant in variants:
            with self.subTest(variant=variant[:50]):
                path.write_text(variant)
                result = self.run_role("byko-analyst")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
