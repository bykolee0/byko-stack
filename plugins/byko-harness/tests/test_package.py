"""설치 패키지(매니페스트·스킬 발견·내부 참조)와 검사 예시 코드를 검사한다. 모델 행동 평가는 별도다."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from urllib.parse import unquote
import warnings


PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / 'skills' / 'agent-harness-builder'
PY_EXAMPLE = SKILL / 'examples' / 'python' / 'test_harness_docs.py'
NODE_EXAMPLE = SKILL / 'examples' / 'node' / 'harness-docs.test.mjs'
CHECKS = {
    'wiki_frontmatter', 'definition_comes_first', 'indexes_match_files', 'sources_and_checks_exist',
    'agents_md', 'agents_md_indexes_areas', 'paths_match_agents_md', 'claude_md_imports_agents',
}


class PackageTest(unittest.TestCase):
    def test_manifests_agree(self):
        claude = json.loads((PLUGIN / '.claude-plugin/plugin.json').read_text())
        codex = json.loads((PLUGIN / '.codex-plugin/plugin.json').read_text())
        for manifest in (claude, codex):
            self.assertEqual(manifest['name'], PLUGIN.name)
            self.assertRegex(manifest['version'], r'^\d+\.\d+\.\d+$')
        self.assertEqual(claude['version'], codex['version'])
        self.assertNotIn('skills', claude, 'Claude는 기본 skills/를 읽는다')
        self.assertEqual((PLUGIN / codex['skills']).resolve(), (PLUGIN / 'skills').resolve())

    def test_discoverable_skill(self):
        skills = sorted((PLUGIN / 'skills').glob('*/SKILL.md'))
        self.assertEqual([p.parent.name for p in skills], ['agent-harness-builder'])
        content = skills[0].read_text()
        self.assertTrue(content.startswith('---\n'))
        header = content.split('---', 2)[1]
        self.assertRegex(header, r'(?m)^name:\s*agent-harness-builder\s*$')
        description = re.search(r'(?m)^description:\s*(.+)$', header).group(1)
        self.assertLessEqual(len(description), 1024, 'Agent Skills description 상한')
        self.assertIn('$agent-harness-builder', (SKILL / 'agents/openai.yaml').read_text())

    def test_relative_links_stay_in_package(self):
        for path in PLUGIN.rglob('*.md'):
            text = path.read_text()
            # 코드 블록 안의 예시 링크(템플릿)는 대상 리포 기준이므로 뺀다.
            text = re.sub(r'```.*?```', '', text, flags=re.S)
            text = re.sub(r'`[^`\n]*`', '', text)
            for target in re.findall(r'\]\(([^)\s]+)\)', text):
                if '://' in target or target.startswith('#'):
                    continue
                resolved = (path.parent / unquote(target.split('#')[0])).resolve()
                with self.subTest(document=str(path.relative_to(PLUGIN)), target=target):
                    self.assertTrue(resolved.is_relative_to(PLUGIN), '패키지 밖을 가리킨다')
                    self.assertTrue(resolved.exists(), '없는 대상')


def write(root, rel, text, encoding='utf-8', newline=None):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding=encoding, newline=newline) as handle:
        handle.write(text)


POLICY = """---
title: 환불 정책
summary: 환불 기간과 금액의 최종 정의
scope: [src/billing.py]
status: from-code
enforced_by: [tests/test_refund.py]
sources: [src/billing.py, tests/test_refund.py]
verified: 2026-11-11 a1b2c3d
---
## 정의
- 결제 후 14일이 지나면 환불하지 않는다.
"""

DOMAIN = """---
title: 도메인
summary: 결제와 환불 개체의 정의
scope: [src/billing.py]
sources: [src/billing.py]
verified: 2026-11-11
---
## 정의
- 결제(Payment)는 환불(Refund)을 여러 개 가질 수 있다.
"""

AGENTS = """# 예시 서비스
결제와 환불을 처리한다.

## 색인
- [정책](docs/wiki/policies/index.md) — 기능 동작을 바꾸기 전에 연다
- [도메인](docs/wiki/domain.md) — 용어가 헷갈릴 때 연다
- [참고 자료](docs/references/index.md) — DB 작업 때 연다
"""

REFERENCES_INDEX = '# 참고 자료\n- [schema.sql](schema.sql) — 스키마 덤프 · `make dump-schema`\n'


def build_valid_repo(root):
    write(root, 'AGENTS.md', AGENTS)
    write(root, 'CLAUDE.md', '@AGENTS.md\n')
    write(root, 'docs/wiki/policies/index.md', '# 정책\n- [환불](refund.md) — 환불 규칙 · from-code\n')
    write(root, 'docs/wiki/policies/refund.md', POLICY)
    write(root, 'docs/wiki/domain.md', DOMAIN)
    write(root, 'docs/references/index.md', REFERENCES_INDEX)
    write(root, 'docs/references/schema.sql', 'create table payment (id int);\n')
    write(root, 'src/billing.py', 'REFUND_DAYS = 14\n')
    write(root, 'tests/test_refund.py', 'def test_refund_window():\n    assert True\n')


def add_nested_references(root, linked=True):
    write(root, 'docs/references/schemas/index.md', '# 스키마\n- [payment.sql](payment.sql) — 결제 테이블 · `make dump-schema`\n')
    write(root, 'docs/references/schemas/payment.sql', 'create table payment (id int);\n')
    if linked:
        write(root, 'docs/references/index.md', REFERENCES_INDEX + '- [스키마](schemas/index.md) — 테이블별 덤프\n')


def move_wiki_to_notes(root):
    """wiki를 notes/로 옮긴 리포. 검사 상수를 기본값으로 두면 엉뚱한 곳을 본다."""
    shutil.move(str(root / 'docs/wiki'), str(root / 'notes'))
    write(root, 'AGENTS.md', AGENTS.replace('docs/wiki/', 'notes/'))


def replace(root, rel, old, new):
    path = root / rel
    text = path.read_text(encoding='utf-8')
    assert old in text, (rel, old)
    path.write_text(text.replace(old, new), encoding='utf-8')


# 고장 사례: 이름 → (고장 내기, 실패해야 하는 검사들)
BROKEN = {
    'missing_verified': (
        lambda r: replace(r, 'docs/wiki/policies/refund.md', 'verified: 2026-11-11 a1b2c3d\n', ''),
        ['wiki_frontmatter']),
    'missing_title': (
        lambda r: replace(r, 'docs/wiki/domain.md', 'title: 도메인\n', ''),
        ['wiki_frontmatter']),
    'empty_sources': (
        lambda r: replace(r, 'docs/wiki/domain.md', 'sources: [src/billing.py]', 'sources: []'),
        ['wiki_frontmatter']),
    'bad_verified_format': (
        lambda r: replace(r, 'docs/wiki/domain.md', 'verified: 2026-11-11', 'verified: yesterday'),
        ['wiki_frontmatter']),
    'verified_as_list': (
        lambda r: replace(r, 'docs/wiki/domain.md', 'verified: 2026-11-11', 'verified: [2026-11-11]'),
        ['wiki_frontmatter']),
    'bad_status': (
        lambda r: replace(r, 'docs/wiki/policies/refund.md', 'status: from-code', 'status: maybe'),
        ['wiki_frontmatter']),
    'missing_enforced_by': (
        lambda r: replace(r, 'docs/wiki/policies/refund.md', 'enforced_by: [tests/test_refund.py]\n', ''),
        ['wiki_frontmatter']),
    'no_frontmatter': (
        lambda r: write(r, 'docs/wiki/domain.md', '## 정의\n- 결제는 환불을 여러 개 가질 수 있다.\n'),
        ['wiki_frontmatter']),
    'definition_not_first': (
        lambda r: replace(r, 'docs/wiki/domain.md', '## 정의', '## 배경\n설명\n\n## 정의'),
        ['definition_comes_first']),
    'unindexed_reference': (
        lambda r: write(r, 'docs/references/diagram.png', 'png'),
        ['indexes_match_files']),
    'index_points_to_missing_file': (
        lambda r: write(r, 'docs/wiki/policies/index.md', '# 정책\n- [환불](refund.md)\n- [사라짐](gone.md)\n'),
        ['indexes_match_files']),
    'missing_policy_index': (
        lambda r: (r / 'docs/wiki/policies/index.md').unlink(),
        ['agents_md', 'indexes_match_files']),
    'nested_reference_unindexed': (
        lambda r: (add_nested_references(r), write(r, 'docs/references/schemas/extra.sql', 'select 1;\n')),
        ['indexes_match_files']),
    'nested_index_not_linked': (
        lambda r: add_nested_references(r, linked=False),
        ['indexes_match_files']),
    'missing_source': (
        lambda r: replace(r, 'docs/wiki/domain.md', 'sources: [src/billing.py]', 'sources: [src/gone.py]'),
        ['sources_and_checks_exist']),
    'missing_source_with_line': (
        lambda r: replace(r, 'docs/wiki/domain.md', 'sources: [src/billing.py]', 'sources: [src/gone.py:3]'),
        ['sources_and_checks_exist']),
    'agents_broken_link': (
        lambda r: write(r, 'AGENTS.md', AGENTS + '- [없음](docs/wiki/none.md) — 없는 페이지\n'),
        ['agents_md']),
    'agents_too_large': (
        lambda r: write(r, 'AGENTS.md', AGENTS + ('x' * 100 + '\n') * 330),
        ['agents_md']),
    'area_not_indexed': (
        lambda r: replace(r, 'AGENTS.md', '- [도메인](docs/wiki/domain.md) — 용어가 헷갈릴 때 연다\n', ''),
        ['agents_md_indexes_areas']),
    'references_not_indexed': (
        lambda r: replace(r, 'AGENTS.md', '- [참고 자료](docs/references/index.md) — DB 작업 때 연다\n', ''),
        ['agents_md_indexes_areas']),
    'stale_wiki_constant': (move_wiki_to_notes, ['paths_match_agents_md']),
    'claude_without_import': (
        lambda r: write(r, 'CLAUDE.md', '# Claude 전용 메모\n'),
        ['claude_md_imports_agents']),
    'claude_import_in_code_block': (
        lambda r: write(r, 'CLAUDE.md', '```\n@AGENTS.md\n```\n'),
        ['claude_md_imports_agents']),
    'claude_import_in_code_span': (
        lambda r: write(r, 'CLAUDE.md', '`@AGENTS.md`\n'),
        ['claude_md_imports_agents']),
    'nested_agents_without_claude': (
        lambda r: write(r, 'pkg/AGENTS.md', '# pkg 규칙\n'),
        ['claude_md_imports_agents']),
}

# 규격이 허용하는 변형. 모두 통과해야 한다.
ACCEPTED = {
    'source_with_line_and_root_slash': lambda r: replace(
        r, 'docs/wiki/domain.md', 'sources: [src/billing.py]', 'sources: [src/billing.py:1, /tests/test_refund.py:1-2]'),
    'url_source': lambda r: replace(
        r, 'docs/wiki/domain.md', 'sources: [src/billing.py]', 'sources: [src/billing.py, https://example.com/spec]'),
    'agents_link_from_repo_root': lambda r: replace(r, 'AGENTS.md', '(docs/wiki/domain.md)', '(/docs/wiki/domain.md)'),
    'percent_in_file_name': lambda r: (
        write(r, 'docs/references/100%.txt', 'raw\n'),
        write(r, 'docs/references/index.md', REFERENCES_INDEX + '- [100%.txt](100%.txt) — 원자료\n')),
    'angle_and_title_links': lambda r: (
        write(r, 'docs/references/diagram v2.png', 'png'),
        write(r, 'docs/references/index.md',
              '# 참고 자료\n- [schema.sql](schema.sql "덤프") — 스키마\n- [다이어그램](<diagram v2.png>) — 구조도\n')),
    'nested_reference_index': add_nested_references,
    'bom_files': lambda r: (
        write(r, 'docs/wiki/domain.md', DOMAIN, encoding='utf-8-sig'),
        write(r, 'CLAUDE.md', '@AGENTS.md\n', encoding='utf-8-sig')),
    'crlf_files': lambda r: (
        write(r, 'docs/wiki/domain.md', DOMAIN, newline='\r\n'),
        write(r, 'docs/wiki/policies/index.md', '# 정책\n- [환불](refund.md)\n', newline='\r\n')),
    'example_links_in_code': lambda r: write(
        r, 'AGENTS.md', AGENTS + '\n## 문서 규격\n- index 항목 형식: `- [파일](상대경로) — 요약`\n\n```\n[예시](없는/경로.md)\n```\n'),
    'dot_folder_in_wiki': lambda r: write(r, 'docs/wiki/.obsidian/app.json', '{}\n'),
    'nested_agents_with_claude': lambda r: (write(r, 'pkg/AGENTS.md', '# pkg 규칙\n'), write(r, 'pkg/CLAUDE.md', '@AGENTS.md\n')),
    'claude_dot_slash_import': lambda r: write(r, 'CLAUDE.md', '# Claude 전용\n@./AGENTS.md\n'),
    'agents_in_skipped_folder': lambda r: write(r, 'node_modules/lib/AGENTS.md', '# 외부 패키지\n'),
}


def load_example(root, example=PY_EXAMPLE):
    """예시를 모듈로 불러온다. root가 None이면 HARNESS_ROOT 없이 루트를 스스로 찾게 한다."""
    saved = os.environ.pop('HARNESS_ROOT', None)
    if root is not None:
        os.environ['HARNESS_ROOT'] = str(root)
    try:
        spec = importlib.util.spec_from_file_location(f'harness_example_{id(root)}_{id(example)}', example)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        os.environ.pop('HARNESS_ROOT', None)
        if saved is not None:
            os.environ['HARNESS_ROOT'] = saved


def run_python(root, example=PY_EXAMPLE, strict_warnings=False):
    """(실패한 검사 이름, 알림 문구). strict_warnings는 pytest `filterwarnings = error`를 흉내 낸다."""
    module = load_example(root, example)
    failed = []
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('error' if strict_warnings else 'default')
        for name in sorted(n for n in dir(module) if n.startswith('test_')):
            try:
                getattr(module, name)()
            except AssertionError:
                failed.append(name.removeprefix('test_'))
    return failed, [str(note.message) for note in notes]


def failing_checks(root, example=PY_EXAMPLE):
    return run_python(root, example)[0]


def copy_with_constants(example, folder, changes):
    """설정 상수를 바꾼 예시 사본을 만든다."""
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / example.name
    text = example.read_text(encoding='utf-8')
    for old, new in changes:
        assert old in text, old
        text = text.replace(old, new)
    target.write_text(text, encoding='utf-8')
    return target


class PythonExampleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='harness-py-'))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def repo(self, name, change=None):
        root = self.tmp / name
        build_valid_repo(root)
        if change:
            change(root)
        return root

    def test_valid_repo_passes(self):
        self.assertEqual(failing_checks(self.repo('valid')), [])

    def test_agents_only_repo_passes(self):
        write(self.tmp, 'AGENTS.md', '# 새 리포\n\n## 문서 규격\n- docs/wiki: 최종 정의\n')
        self.assertEqual(failing_checks(self.tmp), [])

    def test_each_break_is_caught_by_its_check(self):
        for name, (breaker, expected) in BROKEN.items():
            with self.subTest(case=name):
                self.assertEqual(failing_checks(self.repo(name, breaker)), sorted(expected))

    def test_accepted_variants_pass(self):
        for name, change in ACCEPTED.items():
            with self.subTest(case=name):
                self.assertEqual(failing_checks(self.repo(name, change)), [])

    @unittest.skipUnless(sys.platform == 'darwin', 'NFD 이름을 그대로 두는 파일 시스템(APFS)에서만 생기는 경우')
    def test_nfd_file_name_matches_nfc_link(self):
        name = '환불표.png'
        root = self.repo('nfd', lambda r: (
            write(r, 'docs/references/' + unicodedata.normalize('NFD', name), 'png'),
            write(r, 'docs/references/index.md', REFERENCES_INDEX + f'- [환불표]({name}) — 표\n')))
        self.assertEqual(failing_checks(root), [])

    def test_long_agents_md_notifies_without_failing_even_when_warnings_are_errors(self):
        for lines, expect_note in ((199, False), (200, True)):
            with self.subTest(lines=lines):
                body = AGENTS + '\n'.join(f'- 줄 {i}' for i in range(lines - AGENTS.count('\n'))) + '\n'
                root = self.repo(f'lines-{lines}', lambda r: write(r, 'AGENTS.md', body))
                failed, notes = run_python(root, strict_warnings=True)
                self.assertEqual(failed, [])
                self.assertEqual(any('AGENTS.md가' in n for n in notes), expect_note, notes)

    def test_renamed_wiki_still_checks_policies(self):
        example = copy_with_constants(PY_EXAMPLE, self.tmp / 'checker', [('WIKI_DIR = "docs/wiki"', 'WIKI_DIR = "notes"')])
        root = self.repo('renamed', move_wiki_to_notes)
        self.assertEqual(failing_checks(root, example), [])
        replace(root, 'notes/policies/refund.md', 'status: from-code\n', '')
        self.assertEqual(failing_checks(root, example), ['wiki_frontmatter'])

    def test_trailing_slash_in_path_constants(self):
        example = copy_with_constants(PY_EXAMPLE, self.tmp / 'checker', [
            ('WIKI_DIR = "docs/wiki"', 'WIKI_DIR = "docs/wiki/"'),
            ('REFERENCES_DIR = "docs/references"', 'REFERENCES_DIR = "docs/references/"')])
        self.assertEqual(failing_checks(self.repo('slash-valid'), example), [])
        unindexed = self.repo('slash-unindexed', BROKEN['unindexed_reference'][0])
        self.assertEqual(failing_checks(unindexed, example), ['indexes_match_files'])

    def test_finds_repo_root_past_nested_agents_md(self):
        root = self.repo('nested-root', lambda r: (
            (r / '.git').mkdir(),
            write(r, 'pkg/AGENTS.md', '# pkg 규칙\n'),
            write(r, 'pkg/CLAUDE.md', '@AGENTS.md\n'),
            replace(r, 'docs/wiki/domain.md', 'verified: 2026-11-11\n', '')))
        example = copy_with_constants(PY_EXAMPLE, root / 'pkg' / 'tests', [])
        self.assertEqual(failing_checks(None, example), ['wiki_frontmatter'])


def node_failures(example, root=None, timeout=60):
    """node --test 결과에서 실패한 검사 이름. root가 None이면 HARNESS_ROOT 없이 돈다."""
    env = {k: v for k, v in os.environ.items() if k != 'HARNESS_ROOT'}
    if root is not None:
        env['HARNESS_ROOT'] = str(root)
    result = subprocess.run(['node', '--test', '--test-reporter=tap', str(example)],
                            env=env, capture_output=True, text=True, timeout=timeout)
    failed = sorted({m.group(1) for m in re.finditer(r'(?m)^\s*not ok \d+ - (\S+)', result.stdout)} & CHECKS)
    return failed, result


@unittest.skipUnless(shutil.which('node'), 'node가 없다')
class NodeExampleTest(unittest.TestCase):
    """Node 예시가 Python 예시와 검사마다 같은 판정을 내리는지 본다."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='harness-node-'))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def repo(self, name, change=None):
        root = self.tmp / name
        build_valid_repo(root)
        if change:
            change(root)
        return root

    def assertNode(self, root, expected, example=NODE_EXAMPLE):
        failed, result = node_failures(example, root)
        self.assertEqual(failed, sorted(expected), result.stdout[-3000:] + result.stderr[-2000:])
        self.assertEqual(result.returncode != 0, bool(expected), result.stdout[-2000:])

    def test_valid_repo_passes(self):
        self.assertNode(self.repo('valid'), [])

    def test_each_break_is_caught_by_its_check(self):
        for name, (breaker, expected) in BROKEN.items():
            with self.subTest(case=name):
                self.assertNode(self.repo(name, breaker), expected)

    def test_accepted_variants_pass(self):
        for name, change in ACCEPTED.items():
            with self.subTest(case=name):
                self.assertNode(self.repo(name, change), [])

    @unittest.skipUnless(sys.platform == 'darwin', 'NFD 이름을 그대로 두는 파일 시스템(APFS)에서만 생기는 경우')
    def test_nfd_file_name_matches_nfc_link(self):
        name = '환불표.png'
        self.assertNode(self.repo('nfd', lambda r: (
            write(r, 'docs/references/' + unicodedata.normalize('NFD', name), 'png'),
            write(r, 'docs/references/index.md', REFERENCES_INDEX + f'- [환불표]({name}) — 표\n'))), [])

    def test_renamed_wiki_still_checks_policies(self):
        example = copy_with_constants(NODE_EXAMPLE, self.tmp / 'checker', [('const WIKI_DIR = "docs/wiki";', 'const WIKI_DIR = "notes";')])
        root = self.repo('renamed', move_wiki_to_notes)
        self.assertNode(root, [], example)
        replace(root, 'notes/policies/refund.md', 'status: from-code\n', '')
        self.assertNode(root, ['wiki_frontmatter'], example)

    def test_trailing_slash_in_path_constants(self):
        example = copy_with_constants(NODE_EXAMPLE, self.tmp / 'checker', [
            ('const WIKI_DIR = "docs/wiki";', 'const WIKI_DIR = "docs/wiki/";'),
            ('const REFERENCES_DIR = "docs/references";', 'const REFERENCES_DIR = "docs/references/";')])
        self.assertNode(self.repo('slash-valid'), [], example)
        self.assertNode(self.repo('slash-unindexed', BROKEN['unindexed_reference'][0]), ['indexes_match_files'], example)
        # 색인이 없을 때 멈추지 않고 실패해야 한다(이전 판은 여기서 끝나지 않았다).
        self.assertNode(self.repo('slash-no-index', lambda r: (r / 'docs/references/index.md').unlink()),
                        ['agents_md', 'indexes_match_files'], example)

    def test_finds_repo_root_past_nested_agents_md(self):
        root = self.repo('nested-root', lambda r: (
            (r / '.git').mkdir(),
            write(r, 'pkg/AGENTS.md', '# pkg 규칙\n'),
            write(r, 'pkg/CLAUDE.md', '@AGENTS.md\n'),
            replace(r, 'docs/wiki/domain.md', 'verified: 2026-11-11\n', '')))
        example = copy_with_constants(NODE_EXAMPLE, root / 'pkg' / 'tests', [])
        failed, result = node_failures(example)
        self.assertEqual(failed, ['wiki_frontmatter'], result.stdout[-2000:])

    def test_long_agents_md_notifies_without_failing(self):
        for lines, expect_note in ((199, False), (200, True)):
            with self.subTest(lines=lines):
                body = AGENTS + '\n'.join(f'- 줄 {i}' for i in range(lines - AGENTS.count('\n'))) + '\n'
                failed, result = node_failures(NODE_EXAMPLE, self.repo(f'lines-{lines}', lambda r: write(r, 'AGENTS.md', body)))
                self.assertEqual(failed, [])
                self.assertEqual('알림: AGENTS.md가' in result.stdout + result.stderr, expect_note)


if __name__ == '__main__':
    unittest.main()
