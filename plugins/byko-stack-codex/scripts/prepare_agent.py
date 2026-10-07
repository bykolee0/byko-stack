#!/usr/bin/env python3
"""번들 TOML과 스킬 경로를 읽어 동적 생성에 전달할 JSON을 출력한다."""

import argparse
import json
from pathlib import Path
import sys
import tomllib


ROLE_SKILLS = {
    "byko-analyst": ("byko-analyze",),
    "byko-implementer": ("byko-implement",),
    "byko-reviewer": (
        "byko-review-code", "byko-review-document", "byko-review-viewer",
    ),
    "byko-viewer": ("byko-build-viewer",),
}
FIELDS = {"name", "description", "model", "model_reasoning_effort", "developer_instructions"}


def bundled_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"플러그인 내부 파일이어야 합니다: {relative}")
    return path


def prepare(root: Path, role: str) -> dict:
    root = root.resolve()
    if role not in ROLE_SKILLS:
        raise ValueError(f"지원하지 않는 역할: {role}")
    config = tomllib.loads(bundled_file(root, f"agents/{role}.toml").read_text())
    if set(config) != FIELDS:
        raise ValueError("역할 필드가 누락됐거나 동적 생성 helper가 지원하지 않는 설정이 있습니다")
    for field in FIELDS:
        if not isinstance(config[field], str) or not config[field].strip():
            raise ValueError(f"비어 있지 않은 문자열이어야 합니다: {field}")
    if config["name"] != role:
        raise ValueError("요청한 역할과 TOML name이 다릅니다")
    paths = [bundled_file(root, f"skills/{skill}/SKILL.md") for skill in ROLE_SKILLS[role]]
    instructions = config["developer_instructions"].strip()
    references = "\n".join(f"- {path.parent.name}: {path}" for path in paths)
    return {
        "role": role,
        "model": config["model"],
        "reasoning_effort": config["model_reasoning_effort"],
        "message": f"{instructions}\n\n이 패키지의 전문 스킬 경로입니다. 현재 작업에 필요한 것만 읽으세요.\n{references}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=ROLE_SKILLS)
    args = parser.parse_args()
    try:
        result = prepare(Path(__file__).resolve().parents[1], args.role)
    except (OSError, ValueError) as exc:
        print(f"역할 준비 실패: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
