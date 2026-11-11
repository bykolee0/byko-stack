// 하네스 문서 규격 검사 (agent-harness-builder 예시).
// 리포의 테스트 폴더에 두고 `node --test`로 실행한다. 의존성이 없다.
// 리포에 맞게 아래 '설정' 상수만 고친다. 리포 문서가 영어면 GUIDE와 메시지도 옮긴다.
// 규격 설명은 리포 AGENTS.md의 '문서 규격' 절에 있다.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// ── 설정 ──────────────────────────────────────────────────────────────
const GUIDE = "AGENTS.md의 '문서 규격' 절";
const DEFINITION_HEADING = "## 정의"; // 영어 문서면 "## Definition"
const WIKI_DIR = "docs/wiki";
const POLICY_DIR = `${WIKI_DIR}/policies`;
const REFERENCES_DIR = "docs/references";
const REQUIRED_KEYS = ["title", "summary", "scope", "sources", "verified"];
const POLICY_STATUS = ["confirmed", "from-code"];
const MAX_AGENTS_BYTES = 32 * 1024; // Codex가 읽는 AGENTS.md 합계 상한
const WARN_AGENTS_LINES = 200; // Claude Code 권장: CLAUDE.md(가져온 AGENTS.md 포함)는 200줄 미만
const SKIP_DIRS = ["node_modules", "vendor", "venv", "dist", "build", "target"]; // AGENTS.md를 찾지 않는 폴더. 점으로 시작하는 폴더도 건너뛴다
// ────────────────────────────────────────────────────────────────────

const VERIFIED = /^\d{4}-\d{2}-\d{2}( [0-9a-f]{7,40})?$/;
// [글](대상), [글](<대상>), [글](대상 "제목")
const LINK = /\]\(\s*(<[^>\n]*>|[^)\s]+)(?:\s+(?:"[^"]*"|'[^']*'))?\s*\)/g;
const LINE_SUFFIX = /:\d+(-\d+)?$/; // sources의 `경로:줄`, `경로:시작-끝`
const FENCE = /^ {0,3}(`{3,}|~{3,})/;
const CODE_SPAN = /`[^`\n]*`/g;
const IMPORT = /^\s*@(\.\/|\.\.\/)?AGENTS\.md\s*$/; // @AGENTS.md, @./AGENTS.md, .claude/CLAUDE.md의 @../AGENTS.md

const isFile = (p) => fs.existsSync(p) && fs.statSync(p).isFile();
const isDir = (p) => fs.existsSync(p) && fs.statSync(p).isDirectory();

// HARNESS_ROOT, 아니면 .git이 있는 가장 가까운 폴더, 아니면 AGENTS.md가 있는 가장 가까운 폴더.
// 하위 폴더에도 AGENTS.md가 있을 수 있으니 .git을 먼저 본다.
function findRoot() {
  if (process.env.HARNESS_ROOT) return path.resolve(process.env.HARNESS_ROOT);
  for (const marker of [".git", "AGENTS.md"]) {
    let dir = path.dirname(fileURLToPath(import.meta.url));
    for (;;) {
      if (fs.existsSync(path.join(dir, marker))) return dir;
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }
  throw new Error("리포 루트(.git이나 AGENTS.md가 있는 폴더)를 찾지 못했다");
}

const ROOT = findRoot();
const at = (name) => path.resolve(ROOT, name); // 끝에 '/'가 있어도 같은 폴더가 된다
const rel = (p) => path.relative(ROOT, p).split(path.sep).join("/");
const report = (problems, why) => `${problems.join("\n")}\n왜: ${why}\n고치는 법: ${GUIDE}을 본다`;
const read = (p) => fs.readFileSync(p, "utf8").replace(/^﻿/, ""); // BOM이 있어도 읽는다
// 경로 비교용. macOS는 한글 이름을 NFD로 둘 수 있어 NFC로 맞춘다.
const key = (p) => path.resolve(p).normalize("NFC");
const hidden = (p, base) => path.relative(base, p).split(path.sep).some((part) => part.startsWith("."));
const countLines = (text) => (text === "" ? 0 : text.replace(/(\r\n|\r|\n)$/, "").split(/\r\n|\r|\n/).length);

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(full, ...walk(full));
    else out.push(full);
  }
  return out;
}

// 코드 블록과 인라인 코드를 뺀다. 그 안의 링크·가져오기는 예시일 뿐이다.
function withoutCode(text) {
  const lines = [];
  let fence = null;
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(FENCE);
    if (fence) {
      if (match && match[1][0] === fence[0] && match[1].length >= fence.length) fence = null;
      continue;
    }
    if (match) {
      fence = match[1];
      continue;
    }
    lines.push(line.replace(CODE_SPAN, ""));
  }
  return lines.join("\n");
}

// [프론트매터 객체 또는 null, 본문]을 돌려준다. 형식: `키: 값`, 목록은 `[a, b]`.
function splitFrontmatter(text) {
  const lines = text.split(/\r?\n/);
  if (lines[0]?.trim() !== "---") return [null, text];
  const data = {};
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim() === "---") return [data, lines.slice(i + 1).join("\n")];
    const sep = line.indexOf(":");
    if (sep < 0 || line.startsWith(" ") || line.startsWith("#")) continue;
    const name = line.slice(0, sep).trim();
    const value = line.slice(sep + 1).trim();
    if (!name) continue;
    if (value.startsWith("[") && value.endsWith("]")) {
      data[name] = value.slice(1, -1).split(",").map((v) => v.trim().replace(/^['"]|['"]$/g, "")).filter(Boolean);
    } else {
      data[name] = value.replace(/^['"]|['"]$/g, "");
    }
  }
  return [null, text];
}

const asList = (v) => (v == null ? [] : Array.isArray(v) ? v : [v]);

function localLinks(text) {
  return [...withoutCode(text).matchAll(LINK)]
    .map((m) => (m[1].startsWith("<") ? m[1].slice(1, -1) : m[1]))
    .filter((t) => t && !t.includes("://") && !t.startsWith("#") && !t.startsWith("mailto:"));
}

function decode(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value; // '%'가 그대로 든 경로
  }
}

function linkTarget(baseDir, target) {
  const clean = decode(target.split("#")[0]);
  // 마크다운에서 '/'로 시작하면 리포 루트 기준이다
  return clean.startsWith("/") ? path.resolve(ROOT, clean.replace(/^\/+/, "")) : path.resolve(baseDir, clean);
}

// sources·enforced_by 값에서 리포 경로만 남긴다: `경로::이름`, `경로#절`, `경로:줄`
const repoPath = (value) => path.join(ROOT, value.split("::")[0].split("#")[0].replace(LINE_SUFFIX, "").trim().replace(/^\/+/, ""));

function wikiPages() {
  const wiki = at(WIKI_DIR);
  if (!isDir(wiki)) return [];
  return walk(wiki)
    .filter((p) => p.endsWith(".md") && path.basename(p) !== "index.md" && isFile(p) && !hidden(p, wiki))
    .sort();
}

const isPolicy = (page) => path.resolve(page).startsWith(at(POLICY_DIR) + path.sep);

// 이 파일을 색인에 실어야 하는 폴더. 자기 index.md가 있는 가장 가까운 폴더다.
// 하위 폴더의 index.md는 그 위 폴더의 색인이 싣는다.
function owner(file, folder) {
  let current = path.basename(file) === "index.md" ? path.dirname(path.dirname(file)) : path.dirname(file);
  while (current !== folder && current.startsWith(folder + path.sep)) {
    if (isFile(path.join(current, "index.md"))) return current;
    current = path.dirname(current);
  }
  return folder;
}

function ownedFiles(folder) {
  return walk(folder)
    .filter((p) => isFile(p) && !hidden(p, folder))
    .filter((p) => !(path.dirname(p) === folder && path.basename(p) === "index.md")) // 폴더 자신의 색인
    .filter((p) => owner(p, folder) === folder)
    .sort();
}

function indexFolders() {
  const folders = [];
  const wiki = at(WIKI_DIR);
  if (isDir(wiki)) {
    // wiki 루트의 페이지는 AGENTS.md가 색인한다. 하위 폴더는 모두 자기 index.md가 있어야 한다.
    for (const p of walk(wiki)) {
      if (isDir(p) && !hidden(p, wiki) && fs.readdirSync(p).some((n) => !n.startsWith(".") && isFile(path.join(p, n)))) folders.push(p);
    }
  }
  for (const name of [POLICY_DIR, REFERENCES_DIR]) if (isDir(at(name))) folders.push(at(name));
  const references = at(REFERENCES_DIR);
  if (isDir(references)) {
    // references의 하위 폴더는 자기 index.md를 두었을 때만 따로 본다. 아니면 위 폴더의 index가 싣는다.
    for (const p of walk(references)) if (isDir(p) && !hidden(p, references) && isFile(path.join(p, "index.md"))) folders.push(p);
  }
  const unique = new Map();
  for (const folder of folders) if (!unique.has(key(folder))) unique.set(key(folder), path.resolve(folder));
  return [...unique.keys()].sort().map((k) => unique.get(k));
}

test("wiki_frontmatter — wiki 프론트매터", () => {
  const problems = [];
  for (const page of wikiPages()) {
    const [data] = splitFrontmatter(read(page));
    if (data === null) {
      problems.push(`${rel(page)}: 맨 위에 '---'로 열고 닫는 프론트매터가 없다`);
      continue;
    }
    for (const name of REQUIRED_KEYS) {
      const value = data[name];
      if (value == null || value === "" || (Array.isArray(value) && value.length === 0)) problems.push(`${rel(page)}: '${name}'가 비어 있거나 없다`);
    }
    const verified = data.verified;
    const filled = verified != null && verified !== "" && !(Array.isArray(verified) && verified.length === 0);
    if (filled && (typeof verified !== "string" || !VERIFIED.test(verified))) {
      problems.push(`${rel(page)}: verified '${verified}'는 'YYYY-MM-DD' 뒤에 짧은 커밋을 붙인 한 줄이어야 한다`);
    }
    if (isPolicy(page)) {
      if (!POLICY_STATUS.includes(data.status)) problems.push(`${rel(page)}: status는 ${POLICY_STATUS.join(" 또는 ")} 중 하나여야 한다`);
      if (!("enforced_by" in data)) problems.push(`${rel(page)}: 'enforced_by'가 없다(강제 검사가 없으면 [])`);
    }
  }
  assert.deepEqual(problems, [], report(problems, "검색·색인·낡음 확인이 이 필드에 기대고, 근거 없는 정의는 믿을 수 없다"));
});

test("definition_comes_first — 정의가 맨 위", () => {
  const problems = [];
  for (const page of wikiPages()) {
    const [, body] = splitFrontmatter(read(page));
    const first = body.split(/\r?\n/).find((line) => line.startsWith("## "));
    if (first?.trim() !== DEFINITION_HEADING) problems.push(`${rel(page)}: 첫 '## ' 절이 '${DEFINITION_HEADING}'가 아니다(${first?.trim() ?? "없음"})`);
  }
  assert.deepEqual(problems, [], report(problems, "wiki는 최종 정의가 원본이고, 설명은 그 아래에 붙는 부차 정보다"));
});

test("indexes_match_files — 색인 일치", () => {
  const problems = [];
  for (const folder of indexFolders()) {
    const index = path.join(folder, "index.md");
    const files = ownedFiles(folder);
    if (!isFile(index)) {
      if (files.length) problems.push(`${rel(folder)}: index.md가 없다(${files.length}개 파일)`);
      continue;
    }
    const links = new Map(localLinks(read(index)).map((t) => linkTarget(folder, t)).map((p) => [key(p), p]));
    for (const file of files) {
      const accepted = [key(file), ...(path.basename(file) === "index.md" ? [key(path.dirname(file))] : [])];
      if (!accepted.some((k) => links.has(k))) problems.push(`${rel(file)}: ${rel(index)}에 링크가 없다`);
    }
    for (const target of links.values()) if (!fs.existsSync(target)) problems.push(`${rel(index)}: 없는 파일을 가리킨다(${rel(target)})`);
  }
  assert.deepEqual(problems, [], report(problems, "색인에 없는 파일은 이유를 모른 채 남고, 없는 파일을 가리키는 색인은 헛걸음을 시킨다"));
});

test("sources_and_checks_exist — 근거와 강제 검사 경로", () => {
  const problems = [];
  for (const page of wikiPages()) {
    const [data] = splitFrontmatter(read(page));
    for (const name of ["sources", "enforced_by"]) {
      for (const value of asList(data?.[name])) {
        if (value.includes("://")) continue;
        if (!fs.existsSync(repoPath(value))) problems.push(`${rel(page)}: ${name}의 '${value}'가 없다`);
      }
    }
  }
  assert.deepEqual(problems, [], report(problems, "근거와 강제 검사가 없는 경로를 가리키면 정의를 확인할 수 없다"));
});

test("agents_md — AGENTS.md", () => {
  const agents = path.join(ROOT, "AGENTS.md");
  assert.ok(isFile(agents), report(["AGENTS.md가 없다"], "하네스의 중심 파일이다"));
  const data = fs.readFileSync(agents);
  const text = data.toString("utf8").replace(/^﻿/, "");
  const problems = [];
  if (data.length > MAX_AGENTS_BYTES) problems.push(`AGENTS.md: ${data.length}바이트로 ${MAX_AGENTS_BYTES}바이트 상한을 넘는다. 세부는 wiki로 옮긴다`);
  for (const target of localLinks(text)) if (!fs.existsSync(linkTarget(ROOT, target))) problems.push(`AGENTS.md: 없는 경로를 가리킨다(${target})`);
  const lines = countLines(text);
  if (lines >= WARN_AGENTS_LINES) console.warn(`알림: AGENTS.md가 ${lines}줄이다. ${WARN_AGENTS_LINES}줄 미만을 권장한다`);
  assert.deepEqual(problems, [], report(problems, "항상 로드되는 파일이라 틀리면 모든 작업에 영향을 준다"));
});

test("agents_md_indexes_areas — AGENTS.md가 영역을 색인", () => {
  const agents = path.join(ROOT, "AGENTS.md");
  if (!isFile(agents)) return; // agents_md가 알린다
  const targets = new Set(localLinks(read(agents)).map((t) => key(linkTarget(ROOT, t))));
  const areas = [];
  const wiki = at(WIKI_DIR);
  if (isDir(wiki)) for (const name of fs.readdirSync(wiki)) if (!name.startsWith(".") && name !== "index.md") areas.push(path.join(wiki, name));
  const references = at(REFERENCES_DIR);
  if (isDir(references)) areas.push(references);
  const problems = [];
  for (const area of areas.sort()) {
    const candidates = [key(area), ...(isDir(area) ? [key(path.join(area, "index.md"))] : [])];
    if (!candidates.some((c) => targets.has(c))) problems.push(`AGENTS.md: ${rel(area)}를 색인에서 가리키지 않는다`);
  }
  assert.deepEqual(problems, [], report(problems, "항상 로드되는 색인에 없는 영역은 에이전트가 찾지 않는다"));
});

test("paths_match_agents_md — 경로 상수가 문서 규격과 같음", () => {
  const agents = path.join(ROOT, "AGENTS.md");
  if (!isFile(agents)) return; // agents_md가 알린다
  assert.ok(
    read(agents).includes(WIKI_DIR.replace(/^\/+|\/+$/g, "")),
    report(
      [`AGENTS.md가 이 검사의 WIKI_DIR('${WIKI_DIR}')를 말하지 않는다`],
      "검사 파일의 경로 상수가 리포의 문서 규격과 다르면 엉뚱한 곳을 보고 아무것도 없이 통과한다. 검사 파일의 경로 상수를 문서 규격 블록과 같게 맞춘다",
    ),
  );
});

// AGENTS.md가 있는 폴더들. 점으로 시작하는 폴더와 SKIP_DIRS는 보지 않는다.
function agentsDirs(dir = ROOT) {
  const found = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  if (entries.some((e) => e.isFile() && e.name === "AGENTS.md")) found.push(dir);
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    if (entry.isDirectory() && !entry.name.startsWith(".") && !SKIP_DIRS.includes(entry.name)) found.push(...agentsDirs(path.join(dir, entry.name)));
  }
  return found;
}

// Claude Code가 AGENTS.md 대신 읽는 그 폴더의 CLAUDE.md들.
const claudeFiles = (folder) => [path.join(folder, "CLAUDE.md"), path.join(folder, ".claude", "CLAUDE.md")].filter(isFile);
const importsAgents = (claude) => withoutCode(read(claude)).split("\n").some((line) => IMPORT.test(line));

test("claude_md_imports_agents — CLAUDE.md가 AGENTS.md를 가져옴", () => {
  const rootCounts = claudeFiles(ROOT).length > 0;
  const problems = [];
  for (const folder of agentsDirs()) {
    const files = claudeFiles(folder);
    if (files.length) {
      if (!files.some(importsAgents)) problems.push(`${rel(files[0])}: 코드 밖에 '@AGENTS.md' 가져오기 줄이 없다`);
    } else if (rootCounts && folder !== ROOT) {
      problems.push(`${rel(path.join(folder, "AGENTS.md"))}: 옆에 '@AGENTS.md'를 담은 CLAUDE.md가 없다`);
    }
  }
  assert.deepEqual(
    problems,
    [],
    report(problems, "CLAUDE.md가 그 폴더나 리포 루트에 있으면 Claude Code는 그 폴더의 AGENTS.md를 직접 읽지 않는다. 코드 블록이나 인라인 코드 안의 가져오기도 무시된다"),
  );
});
