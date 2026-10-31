"""설치 패키지의 발견·내부 참조를 검사한다. 모델 행동 평가는 별도다."""
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote


PLUGIN = Path(__file__).resolve().parents[1]


class PackageTest(unittest.TestCase):
    def test_manifest_and_discoverable_skills(self):
        manifest = json.loads((PLUGIN / '.codex-plugin/plugin.json').read_text())
        self.assertEqual(manifest['name'], PLUGIN.name)
        self.assertRegex(manifest['version'], r'^\d+\.\d+\.\d+$')
        root = (PLUGIN / manifest['skills']).resolve()
        self.assertTrue(root.is_relative_to(PLUGIN))
        names = set()
        for path in root.glob('*/SKILL.md'):
            content = path.read_text()
            self.assertTrue(content.startswith('---\n'), str(path))
            header = content.split('---', 2)[1]
            match = re.search(r'^name:\s*([a-z0-9-]+)\s*$', header, re.M)
            self.assertIsNotNone(match, str(path))
            name = match.group(1)
            self.assertEqual(name, path.parent.name)
            self.assertNotIn(name, names)
            names.add(name)
            self.assertRegex(header, r'(?m)^description:\s*\S.+')
            metadata = path.parent / 'agents/openai.yaml'
            self.assertTrue(metadata.is_file(), str(path))
            self.assertIn(f'${name}', metadata.read_text())
        self.assertTrue(names, 'No discoverable skills')

    def test_relative_document_links_stay_in_installed_package(self):
        for path in PLUGIN.rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                target = unquote(target.split('#')[0])
                resolved = (path.parent / target).resolve()
                with self.subTest(document=str(path), target=target):
                    self.assertTrue(resolved.is_relative_to(PLUGIN), 'Outside package')
                    self.assertTrue(resolved.exists(), 'Missing target')

    def test_retired_entrypoints_are_not_discovery_duplicates(self):
        for name in ('codex-spec-dev', 'codex-spec-designer', 'codex-review'):
            self.assertFalse((PLUGIN / 'skills' / name).exists())
        for path in (PLUGIN / 'skills').rglob('*.md'):
            self.assertNotRegex(path.read_text(), r'\]\([^)]*/codex-(?:spec-dev|spec-designer|review)/')


if __name__ == '__main__':
    unittest.main()
