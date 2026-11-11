"""하네스 문서 규격 검사 (agent-harness-builder 예시).

리포의 테스트 폴더에 두고 pytest로 실행한다. 표준 라이브러리만 쓴다.
리포에 맞게 아래 '설정' 상수만 고친다. 리포 문서가 영어면 GUIDE와 메시지도 옮긴다.
규격 설명은 리포 AGENTS.md의 '문서 규격' 절에 있다.
"""
import os
import re
import unicodedata
import warnings
from pathlib import Path
from urllib.parse import unquote

# ── 설정 ──────────────────────────────────────────────────────────────
GUIDE = "AGENTS.md의 '문서 규격' 절"
DEFINITION_HEADING = "## 정의"  # 영어 문서면 "## Definition"
WIKI_DIR = "docs/wiki"
POLICY_DIR = f"{WIKI_DIR}/policies"
REFERENCES_DIR = "docs/references"
REQUIRED_KEYS = ("title", "summary", "scope", "sources", "verified")
POLICY_STATUS = ("confirmed", "from-code")
MAX_AGENTS_BYTES = 32 * 1024  # Codex가 읽는 AGENTS.md 합계 상한
WARN_AGENTS_LINES = 200  # Claude Code 권장: CLAUDE.md(가져온 AGENTS.md 포함)는 200줄 미만
SKIP_DIRS = ("node_modules", "vendor", "venv", "dist", "build", "target")  # AGENTS.md를 찾지 않는 폴더. 점으로 시작하는 폴더도 건너뛴다
# ────────────────────────────────────────────────────────────────────

VERIFIED = re.compile(r"^\d{4}-\d{2}-\d{2}( [0-9a-f]{7,40})?$")
# [글](대상), [글](<대상>), [글](대상 "제목")
LINK = re.compile(r"\]\(\s*(<[^>\n]*>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
LINE_SUFFIX = re.compile(r":\d+(-\d+)?$")  # sources의 `경로:줄`, `경로:시작-끝`
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
CODE_SPAN = re.compile(r"`[^`\n]*`")
IMPORT = re.compile(r"^\s*@(\./|\.\./)?AGENTS\.md\s*$")  # @AGENTS.md, @./AGENTS.md, .claude/CLAUDE.md의 @../AGENTS.md


def find_root():
    """HARNESS_ROOT, 아니면 .git이 있는 가장 가까운 폴더, 아니면 AGENTS.md가 있는 가장 가까운 폴더."""
    env = os.environ.get("HARNESS_ROOT")
    if env:
        return Path(env).resolve()
    parents = Path(__file__).resolve().parents
    # 하위 폴더에도 AGENTS.md가 있을 수 있으니 .git을 먼저 본다.
    for marker in (".git", "AGENTS.md"):
        for parent in parents:
            if (parent / marker).exists():
                return parent
    raise RuntimeError("리포 루트(.git이나 AGENTS.md가 있는 폴더)를 찾지 못했다")


ROOT = find_root()


def rel(path):
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def report(problems, why):
    return "\n".join(problems) + f"\n왜: {why}\n고치는 법: {GUIDE}을 본다"


def read(path):
    return path.read_text(encoding="utf-8-sig")  # BOM이 있어도 읽는다


def key(path):
    """경로 비교용. macOS는 한글 이름을 NFD로 둘 수 있어 NFC로 맞춘다."""
    return unicodedata.normalize("NFC", str(path.resolve()))


def hidden(path, base):
    return any(part.startswith(".") for part in path.relative_to(base).parts)


def notify(message):
    """실패시키지 않고 알린다. 경고를 오류로 다루는 설정에서도 경고 요약에 나온다."""
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        warnings.warn(message, stacklevel=2)


def without_code(text):
    """코드 블록과 인라인 코드를 뺀다. 그 안의 링크·가져오기는 예시일 뿐이다."""
    lines, fence = [], None
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
                fence = None
            continue
        if match:
            fence = match.group(1)
            continue
        lines.append(CODE_SPAN.sub("", line))
    return "\n".join(lines)


def split_frontmatter(text):
    """(프론트매터 dict 또는 None, 본문)을 돌려준다. 형식: `키: 값`, 목록은 `[a, b]`."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    data = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return data, "\n".join(lines[index + 1:])
        name, sep, value = line.partition(":")
        if not sep or not name.strip() or line.startswith((" ", "#")):
            continue
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip("'\"") for item in value[1:-1].split(",")]
            data[name.strip()] = [item for item in items if item]
        else:
            data[name.strip()] = value.strip("'\"")
    return None, text


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def local_links(text):
    targets = []
    for target in LINK.findall(without_code(text)):
        target = target[1:-1] if target.startswith("<") else target
        if target and "://" not in target and not target.startswith(("#", "mailto:")):
            targets.append(target)
    return targets


def link_target(base_dir, target):
    target = unquote(target.split("#")[0])
    if target.startswith("/"):  # 마크다운에서 '/'로 시작하면 리포 루트 기준이다
        return ROOT / target.lstrip("/")
    return base_dir / target


def repo_path(value):
    """sources·enforced_by 값에서 리포 경로만 남긴다: `경로::이름`, `경로#절`, `경로:줄`."""
    value = LINE_SUFFIX.sub("", value.split("::")[0].split("#")[0])
    return ROOT / value.strip().lstrip("/")


def wiki_pages():
    wiki = ROOT / WIKI_DIR
    if not wiki.exists():
        return []
    return sorted(p for p in wiki.rglob("*.md") if p.name != "index.md" and not hidden(p, wiki))


def is_policy(page):
    return (ROOT / POLICY_DIR).resolve() in page.resolve().parents


def owner(path, folder):
    """이 파일을 색인에 실어야 하는 폴더. 자기 index.md가 있는 가장 가까운 폴더다.
    하위 폴더의 index.md는 그 위 폴더의 색인이 싣는다."""
    current = path.parent.parent if path.name == "index.md" else path.parent
    while current != folder and folder in current.parents:
        if (current / "index.md").exists():
            return current
        current = current.parent
    return folder


def owned_files(folder):
    owned = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or hidden(path, folder):
            continue
        if path.parent == folder and path.name == "index.md":
            continue  # 폴더 자신의 색인
        if owner(path, folder) == folder:
            owned.append(path)
    return owned


def index_folders():
    folders = []
    wiki = ROOT / WIKI_DIR
    if wiki.exists():
        # wiki 루트의 페이지는 AGENTS.md가 색인한다. 하위 폴더는 모두 자기 index.md가 있어야 한다.
        folders += [
            d for d in wiki.rglob("*")
            if d.is_dir() and not hidden(d, wiki) and any(f.is_file() and not f.name.startswith(".") for f in d.iterdir())
        ]
    for name in (POLICY_DIR, REFERENCES_DIR):
        if (ROOT / name).exists():
            folders.append(ROOT / name)
    references = ROOT / REFERENCES_DIR
    if references.exists():
        # references의 하위 폴더는 자기 index.md를 두었을 때만 따로 본다. 아니면 위 폴더의 index가 싣는다.
        folders += [d for d in references.rglob("*") if d.is_dir() and not hidden(d, references) and (d / "index.md").exists()]
    unique = {}
    for folder in folders:
        unique.setdefault(key(folder), folder)
    return [unique[k] for k in sorted(unique)]


def test_wiki_frontmatter():
    problems = []
    for page in wiki_pages():
        data, _ = split_frontmatter(read(page))
        if data is None:
            problems.append(f"{rel(page)}: 맨 위에 '---'로 열고 닫는 프론트매터가 없다")
            continue
        for name in REQUIRED_KEYS:
            if not data.get(name):
                problems.append(f"{rel(page)}: '{name}'가 비어 있거나 없다")
        verified = data.get("verified")
        if verified and (not isinstance(verified, str) or not VERIFIED.match(verified)):
            problems.append(f"{rel(page)}: verified '{verified}'는 'YYYY-MM-DD' 뒤에 짧은 커밋을 붙인 한 줄이어야 한다")
        if is_policy(page):
            if data.get("status") not in POLICY_STATUS:
                problems.append(f"{rel(page)}: status는 {' 또는 '.join(POLICY_STATUS)} 중 하나여야 한다")
            if "enforced_by" not in data:
                problems.append(f"{rel(page)}: 'enforced_by'가 없다(강제 검사가 없으면 [])")
    assert not problems, report(problems, "검색·색인·낡음 확인이 이 필드에 기대고, 근거 없는 정의는 믿을 수 없다")


def test_definition_comes_first():
    problems = []
    for page in wiki_pages():
        _, body = split_frontmatter(read(page))
        first = next((line.strip() for line in body.splitlines() if line.startswith("## ")), None)
        if first != DEFINITION_HEADING:
            problems.append(f"{rel(page)}: 첫 '## ' 절이 '{DEFINITION_HEADING}'가 아니다({first or '없음'})")
    assert not problems, report(problems, "wiki는 최종 정의가 원본이고, 설명은 그 아래에 붙는 부차 정보다")


def test_indexes_match_files():
    problems = []
    for folder in index_folders():
        index = folder / "index.md"
        files = owned_files(folder)
        if not index.exists():
            if files:
                problems.append(f"{rel(folder)}: index.md가 없다({len(files)}개 파일)")
            continue
        links = [link_target(folder, t) for t in local_links(read(index))]
        targets = {key(p) for p in links}
        for path in files:
            accepted = {key(path)} | ({key(path.parent)} if path.name == "index.md" else set())
            if not accepted & targets:
                problems.append(f"{rel(path)}: {rel(index)}에 링크가 없다")
        for target in {key(p): p for p in links}.values():
            if not target.exists():
                problems.append(f"{rel(index)}: 없는 파일을 가리킨다({rel(target)})")
    assert not problems, report(problems, "색인에 없는 파일은 이유를 모른 채 남고, 없는 파일을 가리키는 색인은 헛걸음을 시킨다")


def test_sources_and_checks_exist():
    problems = []
    for page in wiki_pages():
        data, _ = split_frontmatter(read(page))
        for name in ("sources", "enforced_by"):
            for value in as_list((data or {}).get(name)):
                if "://" in value:
                    continue
                if not repo_path(value).exists():
                    problems.append(f"{rel(page)}: {name}의 '{value}'가 없다")
    assert not problems, report(problems, "근거와 강제 검사가 없는 경로를 가리키면 정의를 확인할 수 없다")


def test_agents_md():
    agents = ROOT / "AGENTS.md"
    assert agents.exists(), report(["AGENTS.md가 없다"], "하네스의 중심 파일이다")
    data = agents.read_bytes()
    text = data.decode("utf-8-sig")
    problems = []
    if len(data) > MAX_AGENTS_BYTES:
        problems.append(f"AGENTS.md: {len(data)}바이트로 {MAX_AGENTS_BYTES}바이트 상한을 넘는다. 세부는 wiki로 옮긴다")
    for target in local_links(text):
        if not link_target(ROOT, target).exists():
            problems.append(f"AGENTS.md: 없는 경로를 가리킨다({target})")
    lines = len(text.splitlines())
    if lines >= WARN_AGENTS_LINES:
        notify(f"AGENTS.md가 {lines}줄이다. {WARN_AGENTS_LINES}줄 미만을 권장한다")
    assert not problems, report(problems, "항상 로드되는 파일이라 틀리면 모든 작업에 영향을 준다")


def test_agents_md_indexes_areas():
    agents = ROOT / "AGENTS.md"
    if not agents.exists():
        return  # test_agents_md가 알린다
    targets = {key(link_target(ROOT, t)) for t in local_links(read(agents))}
    areas = []
    wiki = ROOT / WIKI_DIR
    if wiki.exists():
        areas += [p for p in wiki.iterdir() if not p.name.startswith(".") and p.name != "index.md"]
    references = ROOT / REFERENCES_DIR
    if references.exists():
        areas.append(references)
    problems = []
    for area in sorted(areas):
        candidates = {key(area)}
        if area.is_dir():
            candidates.add(key(area / "index.md"))
        if not candidates & targets:
            problems.append(f"AGENTS.md: {rel(area)}를 색인에서 가리키지 않는다")
    assert not problems, report(problems, "항상 로드되는 색인에 없는 영역은 에이전트가 찾지 않는다")


def test_paths_match_agents_md():
    agents = ROOT / "AGENTS.md"
    if not agents.exists():
        return  # test_agents_md가 알린다
    assert WIKI_DIR.strip("/") in read(agents), report(
        [f"AGENTS.md가 이 검사의 WIKI_DIR('{WIKI_DIR}')를 말하지 않는다"],
        "검사 파일의 경로 상수가 리포의 문서 규격과 다르면 엉뚱한 곳을 보고 아무것도 없이 통과한다. "
        "검사 파일의 경로 상수를 문서 규격 블록과 같게 맞춘다",
    )


def agents_dirs():
    """AGENTS.md가 있는 폴더들. 점으로 시작하는 폴더와 SKIP_DIRS는 보지 않는다."""
    found = []
    for current, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
        if "AGENTS.md" in files:
            found.append(Path(current))
    return found


def claude_files(folder):
    """Claude Code가 AGENTS.md 대신 읽는 그 폴더의 CLAUDE.md들."""
    return [p for p in (folder / "CLAUDE.md", folder / ".claude" / "CLAUDE.md") if p.exists()]


def imports_agents(claude):
    return any(IMPORT.match(line) for line in without_code(read(claude)).splitlines())


def test_claude_md_imports_agents():
    root_counts = bool(claude_files(ROOT))
    problems = []
    for folder in agents_dirs():
        files = claude_files(folder)
        if files:
            if not any(imports_agents(f) for f in files):
                problems.append(f"{rel(files[0])}: 코드 밖에 '@AGENTS.md' 가져오기 줄이 없다")
        elif root_counts and folder != ROOT:
            problems.append(f"{rel(folder / 'AGENTS.md')}: 옆에 '@AGENTS.md'를 담은 CLAUDE.md가 없다")
    assert not problems, report(
        problems,
        "CLAUDE.md가 그 폴더나 리포 루트에 있으면 Claude Code는 그 폴더의 AGENTS.md를 직접 읽지 않는다. "
        "코드 블록이나 인라인 코드 안의 가져오기도 무시된다",
    )
