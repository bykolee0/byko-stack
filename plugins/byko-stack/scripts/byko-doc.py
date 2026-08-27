#!/usr/bin/env python3
"""byko-doc — byko-stack 사람용 HTML 문서 도구.

사람이 여는 문서(index / spec / implementation-plan)의 보일러플레이트, 생성 영역,
검증을 담당한다. 에이전트는 내용만 쓰고, 반복되는 것은 전부 여기서 처리한다.

  init  <workdir>                      assets(css/js) 배치
  new   --kind spec|plan --title T --out PATH [--project P]
                                       저작용 HTML 골격 생성
  build <workdir|file...>              생성 영역 갱신(목차·검토 큐·id) + manifest.md → index.html
  check <workdir|file...>              구조 검증 (오류 시 exit 1)
  text  <file.html>                    평문 추출 (codex 요청에 문서를 복사할 때)
  pack  <file.html> [-o OUT]           css/js를 인라인한 단일 파일 (공유용)

파이썬 표준 라이브러리만 사용한다.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ASSET_DIR = SCRIPT_DIR.parent / "assets"
ASSET_FILES = ("byko-doc.css", "byko-doc.js")

# 검토 악센트 — 사람이 반드시 확인해야 하는 것들
RV_KINDS = {
    "new": ("새 개념", "◆"),
    "type": ("새 타입·구조", "▣"),
    "data": ("데이터 변경", "▲"),
    "decision": ("자체 결정", "●"),
    "risk": ("되돌리기 어려움", "⚠"),
    "open": ("미해결", "?"),
}
RV_ORDER = ["open", "risk", "data", "type", "new", "decision"]

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}
# 닫히지 않으면 문서 구조가 실제로 깨지는 태그만 균형을 검사한다
STRICT_TAGS = {"div", "section", "article", "aside", "details", "summary",
               "figure", "figcaption", "table", "thead", "tbody", "ul", "ol",
               "blockquote", "pre", "main", "header", "footer", "nav"}

REGION_RE = {
    "chapnav": re.compile(r"(<!--\s*byko:chapnav:start\s*-->)(.*?)(<!--\s*byko:chapnav:end\s*-->)", re.S),
    "review-queue": re.compile(
        r"(<!--\s*byko:review-queue:start\s*-->)(.*?)(<!--\s*byko:review-queue:end\s*-->)", re.S),
    "toc": re.compile(r"(<!--\s*byko:toc:start\s*-->)(.*?)(<!--\s*byko:toc:end\s*-->)", re.S),
}


# --------------------------------------------------------------------------
# HTML 스캐너
# --------------------------------------------------------------------------

class DocScan(HTMLParser):
    """저작된 HTML에서 헤딩·검토 항목·리소스·태그 균형을 수집한다."""

    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.text = text
        self.line_start = [0]
        for line in text.splitlines(keepends=True):
            self.line_start.append(self.line_start[-1] + len(line))

        self.headings: list[dict] = []          # {level, id, text, section}
        self.chapters: list[dict] = []          # {id, nav, title} — 챕터 네비 생성용
        self.reviews: list[dict] = []           # {kind, id, title, tag, start, tag_end, section}
        self.external: list[str] = []           # 외부 리소스 URL
        self.links: list[str] = []              # 상대 링크 href
        self.imbalance: list[str] = []
        self.stack: list[tuple[str, int]] = []
        self.has_ac_table = False
        self.has_tldr = False
        self.has_hero = False
        self.has_scenario = False
        self.has_remember = False
        self.chapters_without_id = 0

        self._open_rv: list[dict] = []
        self._open_head: dict | None = None
        self._svg_depth = 0
        self._skip_text = 0                     # script/style 내부
        self._noindex: list[str] = []           # 목차/검토 큐 등 생성 영역 (헤딩 수집 제외)
        self._section = ""                      # 현재 h2 제목 (검토 큐 위치 표시용)
        self.feed(text)
        self.close()

    # 위치 계산 ------------------------------------------------------------
    def _offset(self) -> int:
        line, col = self.getpos()
        return self.line_start[line - 1] + col

    # 태그 ----------------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        raw = self.get_starttag_text() or ""
        start = self._offset()

        if tag == "svg":
            self._svg_depth += 1
        if tag in ("script", "style"):
            self._skip_text += 1

        if self._svg_depth == 0 and tag in STRICT_TAGS:
            self.stack.append((tag, self.getpos()[0]))

        # 외부 리소스 / 링크
        for key in ("src", "href"):
            v = (a.get(key) or "").strip()
            if not v:
                continue
            if tag in ("link", "script", "img", "iframe", "object", "embed", "video", "audio", "source"):
                if re.match(r"^(https?:)?//", v) or v.startswith("http"):
                    self.external.append(v)
            if tag == "a" and not re.match(r"^(https?:|mailto:|#|//)", v):
                self.links.append(v)

        cls = (a.get("class") or "").split()
        if "ac-table" in cls:
            self.has_ac_table = True
        if "tldr" in cls:
            self.has_tldr = True
        if "hero" in cls:
            self.has_hero = True
        if "scenario" in cls:
            self.has_scenario = True
        if "remember" in cls:
            self.has_remember = True
        if tag == "section" and "chapter" in cls and not a.get("id"):
            self.chapters_without_id += 1

        # 생성 영역과 내비게이션의 제목은 수집하지 않는다 — 넣으면 build가 수렴하지 않는다
        if tag == "nav" or "review-queue" in cls or "decisions" in cls or "toc" in cls or "doc-nav" in cls:
            self._noindex.append(tag)

        # 챕터: <section class="chapter" id="..." data-nav="..."> — 제목은 안쪽 첫 h2에서 가져온다
        if tag == "section" and "chapter" in cls and a.get("id"):
            self.chapters.append({"id": a["id"], "nav": (a.get("data-nav") or "").strip(), "title": ""})

        if tag in ("h2", "h3") and self._svg_depth == 0 and not self._noindex:
            self._open_head = {"level": int(tag[1]), "id": a.get("id", ""), "text": ""}
        if tag == "br" and self._open_head is not None:
            self._open_head["text"] += " "   # 제목 안의 줄바꿈이 단어를 붙이지 않게

        # 검토 항목은 .rv(블록) / .rv-i(인라인)만. data-rv 단독은 색만 쓰는 장식이다
        if "data-rv" in a and self._svg_depth == 0 and ("rv" in cls or "rv-i" in cls):
            rec = {
                "kind": (a.get("data-rv") or "").strip(),
                "id": a.get("id", ""),
                "title": (a.get("data-rv-title") or "").strip(),
                "tag": tag,
                "start": start,
                "tag_end": start + len(raw),
                "raw": raw,
                "text": "",
                "section": self._section,
                "line": self.getpos()[0],
                "depth": 0,
            }
            self.reviews.append(rec)
            if tag not in VOID_TAGS:
                self._open_rv.append(rec)

    def handle_startendtag(self, tag, attrs):
        """<br/>, <rect/> 처럼 자기완결 태그 — 열림 상태를 남기지 않는다."""
        if tag in ("script", "style"):
            return
        depth_before = len(self.stack)
        rv_before = len(self._open_rv)
        svg_before = self._svg_depth
        self.handle_starttag(tag, attrs)
        del self.stack[depth_before:]
        del self._open_rv[rv_before:]
        self._svg_depth = svg_before

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip_text:
            self._skip_text -= 1

        if self._svg_depth == 0 and tag in STRICT_TAGS:
            if self.stack and self.stack[-1][0] == tag:
                self.stack.pop()
            else:
                near = self.stack[-1] if self.stack else None
                self.imbalance.append(
                    f"line {self.getpos()[0]}: </{tag}> 가 짝이 맞지 않는다"
                    + (f" (열려 있는 것: <{near[0]}> line {near[1]})" if near else "")
                )

        if tag == "svg" and self._svg_depth > 0:
            self._svg_depth -= 1

        if self._noindex and self._noindex[-1] == tag:
            self._noindex.pop()

        if self._open_head and tag in ("h2", "h3"):
            h = self._open_head
            h["text"] = re.sub(r"\s+", " ", h["text"]).strip().rstrip("#").strip()
            if h["level"] == 2:
                self._section = h["text"]
            h["section"] = self._section
            self.headings.append(h)
            if h["level"] == 2 and self.chapters and not self.chapters[-1]["title"]:
                self.chapters[-1]["title"] = h["text"]
            self._open_head = None

        while self._open_rv and self._open_rv[-1]["tag"] == tag:
            self._open_rv.pop()

    def handle_data(self, data):
        if self._skip_text:
            return
        if self._open_head is not None:
            self._open_head["text"] += data
        for rec in self._open_rv:
            if len(rec["text"]) < 300:
                rec["text"] += data

    def unclosed(self) -> list[str]:
        return [f"line {ln}: <{t}> 가 닫히지 않았다" for t, ln in self.stack]


# --------------------------------------------------------------------------
# 생성 영역: 목차 · 검토 큐
# --------------------------------------------------------------------------

def slugify(text: str, fallback: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9가-힣\s-]", "", text).strip().lower()
    s = re.sub(r"[\s-]+", "-", s)
    s = s.strip("-")
    if not s or not re.search(r"[a-z0-9가-힣]", s):
        return fallback
    return s[:48]


def review_title(rec: dict) -> str:
    t = rec["title"] or re.sub(r"\s+", " ", rec["text"]).strip()
    t = t.strip(" :·-—")
    return t[:80] if t else RV_KINDS.get(rec["kind"], ("검토 항목",))[0]


def ensure_review_ids(text: str, scan: DocScan) -> tuple[str, DocScan]:
    """id 없는 [data-rv] 요소에 안정적인 id를 넣는다 (뒤에서부터 삽입)."""
    used = {h["id"] for h in scan.headings if h["id"]}
    used |= {r["id"] for r in scan.reviews if r["id"]}
    patches: list[tuple[int, str]] = []
    counter: dict[str, int] = {}

    for rec in scan.reviews:
        if rec["id"]:
            continue
        kind = rec["kind"] or "item"
        counter[kind] = counter.get(kind, 0) + 1
        base = "rv-" + slugify(review_title(rec), f"{kind}-{counter[kind]}")
        cand, n = base, 1
        while cand in used:
            n += 1
            cand = f"{base}-{n}"
        used.add(cand)
        insert_at = rec["start"] + 1 + len(rec["tag"])
        patches.append((insert_at, f' id="{cand}"'))

    if not patches:
        return text, scan
    for pos, frag in sorted(patches, reverse=True):
        text = text[:pos] + frag + text[pos:]
    return text, DocScan(text)


def render_toc(scan: DocScan) -> str:
    items = [h for h in scan.headings if h["id"] and h["text"]]
    if not items:
        return "\n"
    out = ['<h2>목차</h2>', '<ul>']
    for h in items:
        out.append(
            f'<li class="lvl-{h["level"]}"><a href="#{html.escape(h["id"])}">'
            f'{html.escape(h["text"])}</a></li>'
        )
    out.append("</ul>")
    return "\n" + "\n".join(out) + "\n"


def render_chapnav(scan: DocScan) -> str:
    """챕터 네비 — 문서를 읽는 경로 자체를 위에 보여준다."""
    if not scan.chapters:
        return "\n"
    out = ["\n<ol>"]
    for c in scan.chapters:
        label = c["nav"] or c["title"] or c["id"]
        out.append(f'<li><a href="#{html.escape(c["id"])}">{html.escape(label)}</a></li>')
    out.append("</ol>\n")
    return "\n".join(out)


def render_decisions(scan: DocScan) -> str:
    """사람이 판단해야 하는 항목 목록 — 본문에 단 악센트에서 자동 수집된다."""
    items = [r for r in scan.reviews if r["kind"] in RV_KINDS]
    if not items:
        return ('\n<p class="scn-note">표시된 결정 항목이 없다 — 새 개념·구조·데이터 변경·자체 결정이 '
                '정말 없는지 한 번 확인할 것.</p>\n')

    by_kind: dict[str, list[dict]] = {}
    for r in items:
        by_kind.setdefault(r["kind"], []).append(r)
    counts = " · ".join(f"{RV_KINDS[k][0]} {len(by_kind[k])}" for k in RV_ORDER if k in by_kind)

    # 항목이 전부 같은 장에 있으면 장 이름을 반복해 적지 않는다
    sections = {r["section"] for r in items}
    show_where = len(sections) > 1

    out = [f'\n<p class="scn-note">사람 확인이 필요한 항목 <b>{len(items)}건</b> — {html.escape(counts)}</p>',
           '<div class="decisions">']
    for kind in RV_ORDER:
        for r in by_kind.get(kind, []):
            label, icon = RV_KINDS[kind]
            where = (f'<span class="d-where">{html.escape(r["section"])}</span>'
                     if show_where and r["section"] else '<span class="d-where"></span>')
            out.append(
                f'<a href="#{html.escape(r["id"])}" data-rv="{kind}">'
                f'<span class="chip" data-rv="{kind}" data-icon="{icon}">{label}</span>'
                f'<span class="d-title">{html.escape(review_title(r))}</span>{where}</a>'
            )
    out += ["</div>\n"]
    return "\n".join(out)


def replace_region(text: str, name: str, body: str) -> tuple[str, bool]:
    pattern = REGION_RE[name]
    m = pattern.search(text)
    if not m:
        return text, False
    if m.group(2) == body:
        return text, False
    return text[:m.start(2)] + body + text[m.end(2):], True


# --------------------------------------------------------------------------
# 마크다운(부분집합) → HTML : manifest 프로즈 렌더용
# --------------------------------------------------------------------------

def md_inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", lambda m: f"<strong>{m.group(1)}</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", lambda m: f"<em>{m.group(1)}</em>", s)
    return s


def md_to_html(lines: list[str]) -> str:
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            j = i + 1
            buf = []
            while j < n and not lines[j].startswith("```"):
                buf.append(lines[j])
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            i = j + 1
            continue
        if line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            j = i + 2
            rows = []
            while j < n and lines[j].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            out.append('<div class="table-wrap"><table><thead><tr>'
                       + "".join(f"<th>{md_inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in r) + "</tr>"
                                 for r in rows)
                       + "</tbody></table></div>")
            i = j
            continue
        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+[.)]\s+", line):
            ordered = bool(re.match(r"^\s*\d+[.)]\s+", line))
            tag = "ol" if ordered else "ul"
            items = []
            while i < n and (re.match(r"^\s*[-*]\s+", lines[i]) or re.match(r"^\s*\d+[.)]\s+", lines[i])):
                items.append(md_inline(re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", lines[i])))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{t}</li>" for t in items) + f"</{tag}>")
            continue
        if line.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote><p>" + "<br>".join(md_inline(b) for b in buf) + "</p></blockquote>")
            continue
        if line.startswith("#"):
            lvl = min(len(line) - len(line.lstrip("#")), 4)
            out.append(f"<h{max(lvl,3)}>{md_inline(line.lstrip('# ').strip())}</h{max(lvl,3)}>")
            i += 1
            continue
        buf = []
        while i < n and lines[i].strip() and not lines[i].startswith(("#", ">", "```", "|")) \
                and not re.match(r"^\s*(?:[-*]|\d+[.)])\s+", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>" + md_inline(" ".join(buf)) + "</p>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# manifest.md → index.html
# --------------------------------------------------------------------------

def parse_manifest(text: str) -> dict:
    lines = text.splitlines()
    doc = {"title": "", "meta": [], "sections": []}
    cur = None
    for line in lines:
        if line.startswith("# "):
            doc["title"] = line[2:].strip()
            continue
        if line.startswith("## "):
            cur = {"title": line[3:].strip(), "lines": []}
            doc["sections"].append(cur)
            continue
        if cur is None:
            if line.startswith(">"):
                doc["meta"].append(line.lstrip("> ").strip())
            continue
        cur["lines"].append(line)
    return doc


def section_lines(doc: dict, *names: str) -> list[str] | None:
    for sec in doc["sections"]:
        for name in names:
            if name in sec["title"]:
                return sec["lines"]
    return None


def parse_table(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        if re.match(r"^\|[\s:|-]+\|$", s):
            continue
        rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows[1:] if rows else []


def build_index(workdir: Path) -> Path | None:
    manifest = workdir / "manifest.md"
    if not manifest.exists():
        return None
    doc = parse_manifest(manifest.read_text(encoding="utf-8"))
    name = re.sub(r"^Work Manifest:\s*", "", doc["title"]).strip() or workdir.name

    # 단계 상태
    steps = []
    for line in section_lines(doc, "단계 상태", "단계") or []:
        m = re.match(r"^\s*-\s*\[([ xX~!])\]\s*(.+)$", line)
        if m:
            steps.append({"done": m.group(1).lower() == "x", "text": m.group(2).strip()})
    done_n = sum(1 for s in steps if s["done"])
    pct = round(done_n / len(steps) * 100) if steps else 0
    now_marked = False
    pipeline = []
    for s in steps:
        if s["done"]:
            cls, mark = "done", "✓"
        elif not now_marked:
            cls, mark, now_marked = "now", "▸", True
        else:
            cls, mark = "todo", "·"
        pipeline.append(
            f'<li class="{cls}"><span class="pl-mark">{mark}</span>'
            f'<span>{md_inline(s["text"])}</span>'
            f'<span class="badge">{"완료" if cls == "done" else "진행" if cls == "now" else "예정"}</span></li>'
        )

    # 산출물
    cards = []
    human_docs = []
    for row in parse_table(section_lines(doc, "산출물") or []):
        if len(row) < 2:
            continue
        label, path = row[0], re.sub(r"`", "", row[1]).strip()
        status = row[2] if len(row) > 2 else ""
        path_clean = re.sub(r"^\./", "", path)
        exists = (workdir / path_clean).exists() if path_clean and "<" not in path_clean else False
        is_human = path_clean.endswith(".html")
        cls = "card" + ("" if is_human else " is-agent") + ("" if exists else " is-missing")
        title = html.escape(label)
        if exists:
            title = f'<a href="{html.escape(path_clean)}">{title}</a>'
        badge = ('<span class="badge">사람용</span>' if is_human
                 else '<span class="badge">에이전트용</span>')
        cards.append(
            f'<li class="{cls}"><span class="card-title">{title} {badge}</span>'
            f'<span class="card-path">{html.escape(path_clean or "—")}</span>'
            + (f'<span class="card-note">{md_inline(status)}</span>' if status.strip("—- ") else "")
            + ('<span class="badge">아직 생성되지 않음</span>' if not exists and path_clean and "<" not in path_clean else "")
            + "</li>")
        if is_human and exists:
            human_docs.append((label, path_clean))

    problem = section_lines(doc, "문제 정의", "문제") or []
    decisions = section_lines(doc, "핵심 결정") or []
    openq = [l for l in (section_lines(doc, "미해결") or []) if l.strip()]

    known = ("문제 정의", "산출물", "단계 상태", "핵심 결정", "미해결")
    extra = [s for s in doc["sections"] if not any(k in s["title"] for k in known)]

    nav = " ".join(
        '<a href="%s">%s</a>' % (html.escape(p), html.escape(l)) for l, p in human_docs
    )
    meta = " ".join("<span>%s</span>" % md_inline(m) for m in doc["meta"])

    pct_badge = "ok" if pct == 100 and steps else ""
    problem_html = md_to_html(problem) or "<p>문제 정의가 매니페스트에 없다.</p>"
    pipeline_html = "\n".join(pipeline) or (
        '<li class="todo"><span class="pl-mark">·</span><span>기록된 단계가 없다</span>'
        '<span class="badge">—</span></li>')
    cards_html = "\n".join(cards) or (
        '<li class="card is-missing"><span class="card-title">기록된 산출물이 없다</span></li>')
    if openq:
        open_html = ('<div class="rv" data-rv="open"><div class="rv-head">'
                     '<span class="chip" data-rv="open" data-icon="?">미해결</span>'
                     '<span class="rv-title">사람 확인이 필요한 항목</span></div>'
                     + md_to_html(openq) + "</div>")
    else:
        open_html = '<p class="rq-empty">미해결 항목 없음.</p>'
    decisions_html = md_to_html(decisions) or '<p class="rq-empty">기록된 결정이 없다.</p>'
    extra_html = "".join(
        '<h2 id="sec-%d">%s</h2>%s' % (i, html.escape(s["title"]), md_to_html(s["lines"]))
        for i, s in enumerate(extra)
    )

    body = f"""<!doctype html>
<html lang="ko" data-byko-doc="index">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(name)} — 작업 현황</title>
<link rel="stylesheet" href="assets/byko-doc.css">
</head>
<body>
<div class="progress"><span></span></div>

<header class="hero" style="min-height:auto;padding:4rem 0 2rem">
  <div class="wrap">
    <p class="kicker">작업 현황 · {html.escape(name)}</p>
    <h1 style="font-size:clamp(32px,4.4vw,56px)">지금 어디까지<br><span class="accent">와 있나</span></h1>
    <div class="hero-sub">{problem_html}</div>
    <div class="hero-cta">{nav}</div>
    <div class="meter" style="margin-top:2rem"><span style="width:{pct}%"></span></div>
    <ul class="stats">
      <li class="stat"><b>{pct}%</b><span>진행 · {done_n}/{len(steps)} 단계</span></li>
      <li class="stat"><b>{len(human_docs)}</b><span>사람이 볼 문서</span></li>
      <li class="stat" data-rv="open"><b>{len(openq)}</b><span>미해결 항목</span></li>
    </ul>
    <p class="scn-note" style="margin-top:1.5rem">{meta}</p>
    <div class="toolbar" style="margin-top:1.5rem"></div>
  </div>
</header>

<main>
<section class="chapter" id="pipeline">
  <div class="wrap">
    <p class="chapter-no">진행</p>
    <h2>어느 단계까지 왔나</h2>
    <ul class="pipeline">
{pipeline_html}
    </ul>
  </div>
</section>

<section class="chapter" id="open">
  <div class="wrap">
    <p class="chapter-no">확인 필요</p>
    <h2>사람이 답해야<br>넘어가는 것</h2>
    {open_html}
  </div>
</section>

<section class="chapter" id="artifacts">
  <div class="wrap">
    <p class="chapter-no">산출물</p>
    <h2>어떤 문서가<br>어디에 있나</h2>
    <ul class="cards">
{cards_html}
    </ul>
  </div>
</section>

<section class="chapter" id="decisions">
  <div class="wrap">
    <p class="chapter-no">기록</p>
    <h2>지금까지의 핵심 결정</h2>
    {decisions_html}
    {extra_html}
  </div>
</section>
</main>

<footer class="doc-footer">
  <div class="wrap">
    <p>이 페이지는 <code>manifest.md</code>에서 생성됩니다 — 직접 고치지 말고 매니페스트를 고친 뒤
      <code>byko-doc build</code>를 실행하세요.</p>
  </div>
</footer>
<script src="assets/byko-doc.js"></script>
</body>
</html>
"""
    out = workdir / "index.html"
    out.write_text(body, encoding="utf-8")
    refresh_file(out, quiet=True)
    return out


# --------------------------------------------------------------------------
# 저작 문서 골격
# --------------------------------------------------------------------------

SPEC_CHAPTERS = """
<section class="chapter" id="c0" data-nav="0. 한 문장">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 0 · 한 문장</p>
    <h2 class="reveal">먼저, 이 변경을<br>한 문장으로</h2>
    <!-- 결론부터. "A를 B로 바꾼다" 한 문장 + 그래서 무엇이 따라 바뀌는가 -->
    <p class="chapter-intro reveal">…</p>
    <div class="callout reveal">
      <span class="ct">지금까지</span>
      <p>…무엇이 불편했는가. 숫자나 사례로 —</p>
    </div>
    <h3 class="reveal">이 문서에서 미리 확정하지 않는 것</h3>
    <ul class="reveal"><li>…</li></ul>
  </div>
</section>

<section class="chapter" id="c1" data-nav="1. 개념">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 1 · 기초</p>
    <h2 class="reveal">이 스펙을 읽으려면<br>알아야 할 것</h2>
    <p class="chapter-intro reveal">…</p>
    <!-- 코드 이름부터 던지지 않는다. 실물에 빗대어 정의한다 (X는 영수증 한 장, Y는 그 한 줄) -->
    <div class="terms cols-3">
      <div class="term reveal">
        <span class="big-word">용어</span>
        <p><span class="like">…에 해당한다.</span> 무엇을 담고 있는지 한두 줄.</p>
      </div>
    </div>
  </div>
</section>

<section class="chapter" id="c2" data-nav="2. 현재 구조">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 2 · 현재 구조</p>
    <h2 class="reveal">지금은<br>이렇게 되어 있다</h2>
    <p class="chapter-intro reveal">…</p>
    <!-- 관련된 구성요소가 각각 무엇을 책임지는지. 근거는 code-ref로 -->
    <div class="map cols-3">
      <div class="map-box reveal">
        <span class="plane-tag">도메인/계층</span>
        <span class="name">구성요소</span>
        <span class="role">무엇을 책임지나</span>
        <span class="code-ref">path/file.py:12</span>
      </div>
    </div>
  </div>
</section>

<section class="chapter" id="c3" data-nav="3. 정상 흐름">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 3 · 정상 흐름</p>
    <h2 class="reveal">아무 문제 없는 날,<br>한 건을 따라가 보자</h2>
    <p class="chapter-intro reveal">…지금 코드에서 실제로 일어나는 일. 인물·상황을 세워 구체적으로</p>
    <div class="story">
      <div class="story-step reveal">
        <div class="story-index">1</div>
        <div class="story-copy"><h3>…</h3><p>…</p></div>
      </div>
    </div>
  </div>
</section>

<section class="chapter" id="c4" data-nav="4. 막히는 지점">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 4 · 문제</p>
    <h2 class="reveal">그런데 …하면<br>여기서 끊긴다</h2>
    <p class="chapter-intro reveal">같은 흐름을 다시 따라가되, 이번엔 문제가 되는 조건으로</p>
    <div class="story">
      <div class="story-step problem reveal">
        <div class="story-index">1</div>
        <div class="story-copy"><h3>…</h3><p>…</p></div>
      </div>
    </div>
    <div class="callout bad reveal">
      <span class="ct">근본 원인</span>
      <p>증상이 아니라 원인을 한 문장으로 —</p>
    </div>
  </div>
</section>

<section class="chapter" id="c5" data-nav="5. 바꾸는 것">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 5 · 해법</p>
    <h2 class="reveal">그래서 …를<br>…로 바꾼다</h2>
    <p class="chapter-intro reveal">…</p>
    <div class="beforeafter">
      <div class="ba-card from reveal"><span class="label">지금</span><ul><li>…</li></ul></div>
      <div class="ba-arrow reveal">→</div>
      <div class="ba-card to reveal"><span class="label">바꾼 뒤</span><ul><li>…</li></ul></div>
    </div>
    <h3 class="reveal">바뀐 뒤의 흐름</h3>
    <div class="story">
      <div class="story-step fix reveal">
        <div class="story-index">1</div>
        <div class="story-copy"><h3>…</h3><p>…</p></div>
      </div>
    </div>
  </div>
</section>

<section class="chapter" id="c6" data-nav="6. 결정할 것">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 6 · 승인</p>
    <h2 class="reveal">여기서부터는<br>사람이 정해야 한다</h2>
    <p class="chapter-intro reveal">코드로 답할 수 없거나, 한 번 정하면 되돌리기 비싼 것들. 나머지는 기존 컨벤션을 따랐다.</p>

<!-- byko:review-queue:start --><!-- byko:review-queue:end -->

    <!-- data-rv: new(새 개념) type(새 구조) data(데이터 변경) decision(자체 결정) risk(되돌릴 수 없음) open(미해결) -->
    <div class="rv reveal" data-rv="new" data-rv-title="목록에서 읽힐 한 문장">
      <div class="rv-head">
        <span class="chip" data-rv="new" data-icon="◆">새 개념</span>
        <span class="rv-title">…</span>
        <span class="rv-why">왜 사람이 봐야 하나</span>
      </div>
      <p>무엇을 정했는지 · 왜 그렇게 정했는지 · <strong>검토했던 대안</strong>과 기각 이유</p>
    </div>
  </div>
</section>

<section class="chapter" id="c7" data-nav="7. 완성 조건">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 7 · 완성 조건</p>
    <h2 class="reveal">무엇이 되면<br>다 만든 것인가</h2>
    <p class="chapter-intro reveal">AC를 목록으로 읽으면 와닿지 않는다. 상황을 눌러 보게 한다.</p>
    <div class="scenario reveal">
      <div class="scn-bar" role="tablist">
        <button class="scn-btn" role="tab">정상</button>
        <button class="scn-btn" role="tab">경계값</button>
        <button class="scn-btn" role="tab">실패</button>
      </div>
      <div class="scn-panel">
        <div class="scn-io">
          <div><span class="label">상황 · 요청</span><p class="scn-note">…</p><code>…</code></div>
          <div class="out"><span class="label">그러면</span><p class="scn-note">…</p></div>
        </div>
        <p class="scn-note"><span class="scn-ac">AC-1</span> · 검증 방법</p>
      </div>
      <div class="scn-panel" hidden>…</div>
      <div class="scn-panel" hidden>…</div>
    </div>
    <details class="agent-only" id="ac-table">
      <summary>AC 표 (구현·검증용 전체 목록)</summary>
      <div class="table-wrap"><table class="ac-table">
        <thead><tr><th>ID</th><th>조건</th><th>검증</th></tr></thead>
        <tbody><tr><td>AC-1</td><td>…를 입력하면 …가 반환된다</td><td>integration</td></tr></tbody>
      </table></div>
    </details>
  </div>
</section>

<section class="chapter" id="c8" data-nav="8. 만드는 순서">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 8 · 순서</p>
    <h2 class="reveal">되돌릴 수 있는 것부터<br>만든다</h2>
    <p class="chapter-intro reveal">되돌릴 수 없는 단계를 가장 뒤에 둔다. 그 앞의 문제는 전부 공짜로 고칠 수 있다.</p>
    <ul class="pipeline reveal">
      <li class="done"><span class="pl-mark">1</span><span>…</span><span class="badge">롤백 가능</span></li>
      <li class="now"><span class="pl-mark">2</span><span>…</span><span class="badge bad">되돌릴 수 없음</span></li>
    </ul>
    <h3 class="reveal">테스트는 AC를 그대로 옮긴다</h3>
    <p class="reveal">…따를 기존 패턴과 근거 <span class="code-ref">tests/…:12</span></p>
    <details class="agent-only">
      <summary>기계적 변경 목록</summary>
      <ul><li>리네임·이동·반복 치환처럼 판단이 필요 없는 것</li></ul>
    </details>
  </div>
</section>

<section class="chapter" id="c9" data-nav="9. 기억할 것">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 9 · 머릿속 지도</p>
    <h2 class="reveal">다음에 이 도메인을 만질 때<br>기억할 것</h2>
    <div class="terms cols-2">
      <div class="term reveal"><span class="big-word">…</span><p>…</p></div>
    </div>
  </div>
</section>
"""

PLAN_CHAPTERS = """
<section class="chapter" id="c0" data-nav="0. 한 문장">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 0 · 한 문장</p>
    <h2 class="reveal">어떤 순서로<br>어디를 건드리나</h2>
    <p class="chapter-intro reveal">…총 N단계 · 수정 파일 M개. 되돌릴 수 없는 단계가 어디인지 여기서 밝힌다.</p>
  </div>
</section>

<section class="chapter" id="c1" data-nav="1. 왜 이 순서">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 1 · 접근</p>
    <h2 class="reveal">왜 이 순서인가</h2>
    <p class="chapter-intro reveal">무엇을 먼저 세우고 무엇을 나중에 붙이는가, 그 기준은 무엇인가</p>
    <ul class="reveal"><li><strong>…</strong> …</li></ul>
  </div>
</section>

<section class="chapter" id="c2" data-nav="2. 단계">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 2 · 단계</p>
    <h2 class="reveal">단계별로<br>무엇을 만드나</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>단계</th><th>내용</th><th>대상 파일</th><th>검증</th><th>의존</th></tr></thead>
      <tbody><tr><td>S1</td><td>…</td><td><code>…</code></td><td>AC-1</td><td>—</td></tr></tbody>
    </table></div>
    <!-- 갈래가 있으면 map/flow로 병렬 가능 구간을 보여준다 -->
  </div>
</section>

<section class="chapter" id="c3" data-nav="3. 영향 범위">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 3 · 영향</p>
    <h2 class="reveal">이 변경이<br>어디까지 닿나</h2>
    <p class="chapter-intro reveal">호출 체인·공유 상태·트랜잭션 경계</p>
    <div class="rv reveal" data-rv="risk" data-rv-title="목록에서 읽힐 한 문장">
      <div class="rv-head">
        <span class="chip" data-rv="risk" data-icon="⚠">되돌릴 수 없음</span>
        <span class="rv-title">…</span>
      </div>
      <p>…</p>
    </div>
  </div>
</section>

<section class="chapter" id="c4" data-nav="4. 승인할 것">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 4 · 승인</p>
    <h2 class="reveal">착수 전에<br>확인받을 것</h2>
<!-- byko:review-queue:start --><!-- byko:review-queue:end -->
  </div>
</section>

<section class="chapter" id="c5" data-nav="5. AC 매핑">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 5 · 대조</p>
    <h2 class="reveal">빠진 AC가<br>없다는 확인</h2>
    <p class="chapter-intro reveal">기계 대조표는 <code>traceability.md</code>. 여기서는 빈 칸이 없다는 사실만 본다.</p>
    <div class="table-wrap"><table>
      <thead><tr><th>AC</th><th>단계</th><th>테스트</th></tr></thead>
      <tbody><tr><td>AC-1</td><td>S1</td><td><code>tests/…</code></td></tr></tbody>
    </table></div>
    <details class="agent-only"><summary>기계적 변경 · 파일 목록</summary><ul><li>…</li></ul></details>
  </div>
</section>
"""


def scaffold(kind: str, title: str, project: str, out: Path, workdir: Path) -> str:
    """표지 + 챕터 골격. 이 문서는 명세서가 아니라 이해시키는 해설이다."""
    rel = Path(_relpath(workdir, out.parent))
    css = str(rel / "assets" / "byko-doc.css")
    js = str(rel / "assets" / "byko-doc.js")
    index_link = str(rel / "index.html")
    kicker = {"spec": "SPEC", "plan": "PLAN"}.get(kind, "DOC")
    chapters = {"spec": SPEC_CHAPTERS, "plan": PLAN_CHAPTERS}.get(
        kind, '\n<section class="chapter" id="c0" data-nav="0."><div class="wrap">'
              '<h2>…</h2></div></section>\n')
    sub = {
        "spec": ("이 도메인을 처음 보는 사람도 지금 구조를 먼저 따라가 본 뒤, 어디에서 막히는지와 "
                 "무엇을 바꾸는지를 한 편의 이야기처럼 이해하도록 만든 스펙입니다."),
        "plan": ("무엇을 어떤 순서로 건드리는지, 어디부터 되돌릴 수 없는지를 착수 전에 "
                 "확인할 수 있도록 만든 구현 계획입니다."),
    }.get(kind, "…")

    return f"""<!doctype html>
<html lang="ko" data-byko-doc="{kind}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{html.escape(css)}">
</head>
<body>

<div class="progress"><span></span></div>

<nav class="chapnav" aria-label="챕터">
  <div class="wrap">
<!-- byko:chapnav:start --><!-- byko:chapnav:end -->
  </div>
</nav>

<header class="hero">
  <div class="wrap">
    <p class="kicker">BYKO-STACK {kicker}{f" · {html.escape(project.upper())}" if project else ""} · <!-- YYYY-MM-DD --></p>
    <!-- 제목은 라벨이 아니라 장면·주장으로. 두 줄, 뒷줄을 .accent로 -->
    <h1>{html.escape(title)}</h1>
    <p class="hero-sub">{sub}</p>
    <div class="hero-cta">
      <a class="primary" href="#c0">처음부터 읽기</a>
      <a href="#c6">내가 결정할 것만 보기</a>
      <a href="{html.escape(index_link)}">작업 현황</a>
    </div>
    <!-- 끝까지 붙잡을 단어 2~3개. 이것만 기억하면 나머지가 읽힌다 -->
    <div class="remember">
      <span class="n">3</span>
      <p>이 문서에서 끝까지 기억할 단어는 세 개뿐입니다. <strong>…</strong>은 …, <strong>…</strong>은 …, <strong>…</strong>은 …입니다.</p>
    </div>
    <div class="toolbar" style="margin-top:2rem"></div>
  </div>
</header>

<main>
{chapters}</main>

<footer class="doc-footer">
  <div class="wrap">
    <p>사람이 읽고 승인하는 산출물입니다. 기계 상태(<code>manifest.md</code>)·근거(<code>analysis/</code>)는
      같은 디렉토리의 마크다운에 있습니다. 챕터 목차와 결정 목록은 <code>byko-doc build</code>가 생성합니다.</p>
  </div>
</footer>

<script src="{html.escape(js)}"></script>
</body>
</html>
"""

def _relpath(target: Path, start: Path) -> str:
    """start에서 target으로 가는 상대 경로 ('' 이면 '.')."""
    try:
        import os
        rel = os.path.relpath(target.resolve(), start.resolve())
    except ValueError:
        return str(target)
    return rel


# --------------------------------------------------------------------------
# 명령
# --------------------------------------------------------------------------

def copy_assets(workdir: Path, quiet: bool = False) -> None:
    dest = workdir / "assets"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ASSET_FILES:
        src = ASSET_DIR / name
        if not src.exists():
            sys.exit(f"에셋을 찾을 수 없다: {src}")
        tgt = dest / name
        data = src.read_text(encoding="utf-8")
        if not tgt.exists() or tgt.read_text(encoding="utf-8") != data:
            tgt.write_text(data, encoding="utf-8")
            if not quiet:
                print(f"  assets/{name} 갱신")


def refresh_file(path: Path, quiet: bool = False) -> bool:
    original = path.read_text(encoding="utf-8")
    scan = DocScan(original)
    text, scan = ensure_review_ids(original, scan)
    text, _ = replace_region(text, "chapnav", render_chapnav(scan))
    text, _ = replace_region(text, "review-queue", render_decisions(scan))
    text, _ = replace_region(text, "toc", render_toc(scan))
    changed = text != original
    if changed:
        path.write_text(text, encoding="utf-8")
        if not quiet:
            n = len([r for r in scan.reviews if r["kind"] in RV_KINDS])
            print(f"  {path.name}: 목차 {len([h for h in scan.headings if h['id']])}개, 검토 항목 {n}건")
    return changed


def html_targets(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_dir():
            out += [q for q in sorted(p.rglob("*.html")) if "assets" not in q.parts]
        elif p.suffix == ".html":
            out.append(p)
    return out


def cmd_init(args) -> int:
    wd = Path(args.workdir)
    wd.mkdir(parents=True, exist_ok=True)
    print(f"init {wd}")
    copy_assets(wd)
    return 0


def cmd_new(args) -> int:
    out = Path(args.out)
    workdir = Path(args.workdir) if args.workdir else out.parent
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not args.force:
        sys.exit(f"이미 존재한다: {out} (덮어쓰려면 --force)")
    copy_assets(workdir, quiet=True)
    out.write_text(scaffold(args.kind, args.title, args.project or "", out, workdir), encoding="utf-8")
    refresh_file(out, quiet=True)
    print(f"생성: {out}")
    print("다음: 챕터를 채우고 `byko-doc build <workdir>` — 챕터 목차와 결정 목록이 자동 생성된다.")
    print("실제로 채워진 예시: <플러그인>/examples/spec-example.html")
    return 0


def cmd_build(args) -> int:
    paths = [Path(p) for p in args.paths]
    dirs = [p for p in paths if p.is_dir()]
    for d in dirs:
        copy_assets(d, quiet=True)
    files = html_targets(paths)
    print(f"build: HTML {len(files)}개")
    for f in files:
        if f.name == "index.html" and (f.parent / "manifest.md").exists():
            continue  # 아래에서 재생성
        refresh_file(f)
    for d in dirs:
        idx = build_index(d)
        if idx:
            print(f"  index.html ← manifest.md")
    return 0


def cmd_check(args) -> int:
    files = html_targets([Path(p) for p in args.paths])
    if not files:
        print("검사할 HTML이 없다.")
        return 0
    errors, warns = [], []
    for f in files:
        text = f.read_text(encoding="utf-8")
        scan = DocScan(text)
        rel = f.name

        for msg in scan.unclosed() + scan.imbalance:
            errors.append(f"{rel} — 태그 구조: {msg}")
        for url in scan.external:
            errors.append(f"{rel} — 외부 리소스 참조 (오프라인에서 깨진다): {url}")
        for href in scan.links:
            target = (f.parent / href.split("#")[0]).resolve() if href.split("#")[0] else None
            if target and not target.exists():
                warns.append(f"{rel} — 깨진 링크: {href}")
        css = re.search(r'<link[^>]+href="([^"]*byko-doc\.css)"', text)
        if not css:
            errors.append(f"{rel} — byko-doc.css 링크가 없다")
        elif not (f.parent / css.group(1)).exists():
            errors.append(f"{rel} — CSS 파일 없음: {css.group(1)} (`byko-doc build <workdir>` 실행)")

        for kind in {r["kind"] for r in scan.reviews}:
            if kind not in RV_KINDS:
                errors.append(f"{rel} — 알 수 없는 data-rv 값: '{kind}' (가능: {', '.join(RV_KINDS)})")

        kind_attr = re.search(r'data-byko-doc="([^"]+)"', text)
        doc_kind = kind_attr.group(1) if kind_attr else ""
        if doc_kind in ("spec", "plan", "index"):
            fixed, _ = ensure_review_ids(text, scan)
            probe, fscan = fixed, DocScan(fixed)
            probe, _ = replace_region(probe, "chapnav", render_chapnav(fscan))
            probe, _ = replace_region(probe, "review-queue", render_decisions(fscan))
            probe, _ = replace_region(probe, "toc", render_toc(fscan))
            if probe != text:
                warns.append(f"{rel} — 생성 영역이 최신이 아니다 (`byko-doc build` 실행)")
        if doc_kind in ("spec", "plan"):
            if not scan.has_hero:
                errors.append(f"{rel} — 표지(.hero)가 없다 — 무엇을 왜 읽는지 알려주는 자리다")
            if len(scan.chapters) < 3:
                errors.append(
                    f"{rel} — 챕터가 {len(scan.chapters)}개뿐이다 — 이 문서는 명세 나열이 아니라 "
                    "배경→현재→문제→해법→결정 순서로 이해시키는 해설이어야 한다")
            if not scan.has_remember:
                warns.append(f"{rel} — 표지에 '기억할 것'(.remember)이 없다 — 독자가 붙잡을 단어를 주자")
            if not any(r["kind"] in RV_KINDS for r in scan.reviews):
                warns.append(f"{rel} — 결정 악센트가 하나도 없다 — 정말 사람이 정할 게 없는가")
        if doc_kind == "spec" and not (scan.has_scenario or scan.has_ac_table):
            errors.append(f"{rel} — 완성 조건이 없다 — 시나리오(.scenario)나 AC 표(.ac-table) 중 하나는 있어야 한다")
        if scan.chapters_without_id:
            warns.append(f"{rel} — id 없는 챕터 {scan.chapters_without_id}개 (챕터 네비에서 빠진다)")

    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(files)}개 검사 — 오류 {len(errors)}, 경고 {len(warns)}")
    return 1 if errors else 0


class TextExtract(HTMLParser):
    """HTML → 평문. 목차·검토 큐·다이어그램처럼 생성되거나 시각 전용인 것은 뺀다."""

    SKIP_TAGS = ("script", "style", "svg", "nav")
    SKIP_CLASSES = ("review-queue", "toolbar", "doc-footer")

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skipping: list[str] = []

    def handle_starttag(self, tag, attrs):
        cls = (dict(attrs).get("class") or "").split()
        if tag in self.SKIP_TAGS or any(c in cls for c in self.SKIP_CLASSES):
            self.skipping.append(tag)
            return
        if self.skipping:
            return
        if tag in ("p", "li", "tr", "h1", "h2", "h3", "h4", "section", "div", "summary", "br"):
            self.parts.append("\n")
        if tag in ("h2", "h3"):
            self.parts.append("\n## ")
        elif tag == "li":
            self.parts.append("- ")
        elif tag in ("td", "th"):
            self.parts.append(" | ")

    def handle_endtag(self, tag):
        if self.skipping and self.skipping[-1] == tag:
            self.skipping.pop()
        elif not self.skipping and tag in ("b", "span", "strong", "em", "code", "td", "th"):
            self.parts.append(" ")   # 인라인 요소가 붙어 있으면 단어가 엉킨다

    def handle_data(self, data):
        if not self.skipping:
            self.parts.append(data)

    def text(self) -> str:
        s = "".join(self.parts)
        s = re.sub(r"[ \t]+", " ", s)
        s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
        return "\n".join(line.strip() for line in s.splitlines()).strip() + "\n"


def cmd_text(args) -> int:
    p = TextExtract()
    p.feed(Path(args.path).read_text(encoding="utf-8"))
    sys.stdout.write(p.text())
    return 0


def cmd_pack(args) -> int:
    src = Path(args.path)
    text = src.read_text(encoding="utf-8")

    def inline_css(m):
        f = src.parent / m.group(1)
        return f'<style>\n{f.read_text(encoding="utf-8")}\n</style>' if f.exists() else m.group(0)

    def inline_js(m):
        f = src.parent / m.group(1)
        return f'<script>\n{f.read_text(encoding="utf-8")}\n</script>' if f.exists() else m.group(0)

    text = re.sub(r'<link[^>]+href="([^"]+\.css)"[^>]*>', inline_css, text)
    text = re.sub(r'<script src="([^"]+\.js)"></script>', inline_js, text)
    out = Path(args.output) if args.output else src.with_name(src.stem + ".packed.html")
    out.write_text(text, encoding="utf-8")
    print(f"단일 파일 생성: {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="byko-doc", description="byko-stack 사람용 HTML 문서 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="작업 디렉토리에 assets 배치")
    p.add_argument("workdir")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("new", help="저작용 HTML 골격 생성")
    p.add_argument("--kind", required=True, choices=["spec", "plan"])
    p.add_argument("--title", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--project", default="")
    p.add_argument("--workdir", default="")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("build", help="생성 영역 갱신 + manifest.md → index.html")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("check", help="구조 검증")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("text", help="평문 추출")
    p.add_argument("path")
    p.set_defaults(func=cmd_text)

    p = sub.add_parser("pack", help="css/js 인라인한 단일 파일")
    p.add_argument("path")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_pack)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
