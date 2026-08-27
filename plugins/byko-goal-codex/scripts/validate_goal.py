#!/usr/bin/env python3
"""Validate a byko-goal-codex durable goal directory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


TASK_ID_RE = re.compile(r"^T-(\d{3,})$")
GOAL_STATUSES = {
    "designed",
    "running",
    "waiting_user",
    "stopped_cap",
    "blocked",
    "complete",
}
TASK_STATUSES = {
    "pending",
    "in_progress",
    "needs_revision",
    "done",
    "blocked",
    "waiting_user",
    "superseded",
}
LIMIT_KEYS = {
    "worker_dispatch_limit",
    "per_task_revision_limit",
    "checkpoint_every",
    "stall_limit",
    "blocker_streak_limit",
    "autonomous_plan_revision_limit",
}
COUNTER_KEYS = {
    "worker_dispatches",
    "completed_since_checkpoint",
    "consecutive_no_progress",
    "autonomous_plan_revisions",
}
REQUIRED_FILES = ("goal.md", "plan.md", "state.json", "knowledge.md", "journal.md")
REQUIRED_DIRS = ("tasks", "handoffs", "eval", "audit")
GOAL_HEADINGS = (
    "## Objective",
    "## Definition of Done",
    "## Scope",
    "## Non-goals",
    "## Required context",
    "## Authorization boundary",
    "## Evaluation strategy",
    "## Contract change history",
)
PLAN_HEADINGS = ("## Task graph", "## Revision history")
TASK_HEADINGS = (
    "## Requirement link",
    "## Acceptance criteria",
    "## Write scope",
    "## Worker log",
    "## Discoveries for integration",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("goal_dir", help="Path to docs/goals/<slug>")
    return parser.parse_args()


def require_object(payload: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        errors.append(f"state.json `{key}` must be an object")
        return {}
    return value


def require_positive_int(payload: dict[str, Any], key: str, prefix: str, errors: list[str]) -> None:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        errors.append(f"state.json `{prefix}.{key}` must be a positive integer")


def require_nonnegative_int(payload: dict[str, Any], key: str, prefix: str, errors: list[str]) -> None:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"state.json `{prefix}.{key}` must be a non-negative integer")


def load_state(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        errors.append(f"cannot read state.json: {error}")
        return {}
    except json.JSONDecodeError as error:
        errors.append(f"state.json is invalid JSON: {error}")
        return {}
    if not isinstance(value, dict):
        errors.append("state.json root must be an object")
        return {}
    return value


def validate_dependency_graph(tasks: dict[str, Any], errors: list[str]) -> None:
    graph: dict[str, list[str]] = {}
    for task_id, task in tasks.items():
        if not isinstance(task, dict):
            continue
        dependencies = task.get("depends_on", [])
        if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
            errors.append(f"task `{task_id}` depends_on must be an array of task IDs")
            continue
        graph[task_id] = dependencies
        for dependency in dependencies:
            if dependency not in tasks:
                errors.append(f"task `{task_id}` depends on unknown task `{dependency}`")
            if dependency == task_id:
                errors.append(f"task `{task_id}` cannot depend on itself")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str, trail: list[str]) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            cycle_start = trail.index(task_id) if task_id in trail else 0
            errors.append("dependency cycle: " + " -> ".join(trail[cycle_start:] + [task_id]))
            return
        visiting.add(task_id)
        for dependency in graph.get(task_id, []):
            if dependency in graph:
                visit(dependency, trail + [task_id])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in graph:
        visit(task_id, [])


def validate_goal(goal_dir: Path) -> list[str]:
    errors: list[str] = []
    if not goal_dir.is_dir():
        return [f"goal directory does not exist: {goal_dir}"]

    for name in REQUIRED_FILES:
        if not (goal_dir / name).is_file():
            errors.append(f"missing `{name}`")
    for name in REQUIRED_DIRS:
        if not (goal_dir / name).is_dir():
            errors.append(f"missing `{name}/` directory")
    if errors:
        return errors

    goal_text = (goal_dir / "goal.md").read_text(encoding="utf-8")
    plan_text = (goal_dir / "plan.md").read_text(encoding="utf-8")
    for heading in GOAL_HEADINGS:
        if heading not in goal_text:
            errors.append(f"goal.md is missing `{heading}`")
    for heading in PLAN_HEADINGS:
        if heading not in plan_text:
            errors.append(f"plan.md is missing `{heading}`")
    if "— 검증:" not in goal_text and "verification:" not in goal_text.lower():
        errors.append("goal.md Definition of Done needs at least one explicit verification method")
    state = load_state(goal_dir / "state.json", errors)
    if not state:
        return errors

    if state.get("schema_version") != 1:
        errors.append("state.json `schema_version` must be 1")

    goal_slug = state.get("goal_slug")
    if not isinstance(goal_slug, str) or not goal_slug:
        errors.append("state.json `goal_slug` must be a non-empty string")
    elif goal_slug != goal_dir.name:
        errors.append(f"state.json goal_slug `{goal_slug}` does not match directory `{goal_dir.name}`")

    for key in ("contract_version", "plan_revision"):
        value = state.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"state.json `{key}` must be a positive integer")

    contract_version = state.get("contract_version")
    if isinstance(contract_version, int) and not re.search(
        rf"(?m)^>\s*contract_version:\s*{contract_version}\s*$", goal_text
    ):
        errors.append("goal.md contract_version does not match state.json")

    plan_revision = state.get("plan_revision")
    if isinstance(plan_revision, int) and not re.search(
        rf"(?m)^>\s*plan_revision:\s*{plan_revision}\s*$", plan_text
    ):
        errors.append("plan.md plan_revision does not match state.json")

    status = state.get("status")
    if status not in GOAL_STATUSES:
        errors.append(f"state.json goal status `{status}` is not allowed")

    limits = require_object(state, "limits", errors)
    counters = require_object(state, "counters", errors)
    for key in sorted(LIMIT_KEYS):
        require_positive_int(limits, key, "limits", errors)
    for key in sorted(COUNTER_KEYS):
        require_nonnegative_int(counters, key, "counters", errors)

    tasks = require_object(state, "tasks", errors)
    if not tasks:
        errors.append("state.json `tasks` must not be empty")

    task_numbers: list[int] = []
    for task_id, task in tasks.items():
        match = TASK_ID_RE.fullmatch(task_id)
        if match is None:
            errors.append(f"invalid task ID `{task_id}`; expected T-NNN")
            continue
        task_numbers.append(int(match.group(1)))
        if not isinstance(task, dict):
            errors.append(f"task `{task_id}` must be an object")
            continue
        task_status = task.get("status")
        if task_status not in TASK_STATUSES:
            errors.append(f"task `{task_id}` status `{task_status}` is not allowed")
        attempts = task.get("attempts")
        if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 0:
            errors.append(f"task `{task_id}` attempts must be a non-negative integer")
        superseded_by = task.get("superseded_by", [])
        if not isinstance(superseded_by, list) or not all(isinstance(item, str) for item in superseded_by):
            errors.append(f"task `{task_id}` superseded_by must be an array of task IDs")
        else:
            for replacement in superseded_by:
                if replacement not in tasks:
                    errors.append(f"task `{task_id}` is superseded by unknown task `{replacement}`")
                if replacement == task_id:
                    errors.append(f"task `{task_id}` cannot supersede itself")
            if task_status == "superseded" and not superseded_by and not task.get("last_result"):
                errors.append(f"superseded task `{task_id}` needs superseded_by or last_result evidence")
        if task_id not in plan_text:
            errors.append(f"task `{task_id}` is missing from plan.md")
        task_path = goal_dir / "tasks" / f"{task_id}.md"
        if not task_path.is_file():
            errors.append(f"missing tasks/{task_id}.md")
        else:
            task_text = task_path.read_text(encoding="utf-8")
            for heading in TASK_HEADINGS:
                if heading not in task_text:
                    errors.append(f"tasks/{task_id}.md is missing `{heading}`")
            if "— 검증:" not in task_text and "verification:" not in task_text.lower():
                errors.append(f"tasks/{task_id}.md needs an explicit verification method")

    if task_numbers and len(task_numbers) != len(set(task_numbers)):
        errors.append("task numeric IDs must be unique")

    validate_dependency_graph(tasks, errors)

    active_tasks = state.get("active_tasks")
    if not isinstance(active_tasks, list) or not all(isinstance(item, str) for item in active_tasks):
        errors.append("state.json `active_tasks` must be an array of task IDs")
    else:
        if len(active_tasks) != len(set(active_tasks)):
            errors.append("state.json `active_tasks` contains duplicates")
        for task_id in active_tasks:
            task = tasks.get(task_id)
            if task is None:
                errors.append(f"active task `{task_id}` does not exist")
            elif isinstance(task, dict) and task.get("status") != "in_progress":
                errors.append(f"active task `{task_id}` must have status in_progress")
            elif isinstance(task, dict):
                for dependency in task.get("depends_on", []):
                    dependency_task = tasks.get(dependency)
                    if isinstance(dependency_task, dict) and dependency_task.get("status") not in {
                        "done",
                        "superseded",
                    }:
                        errors.append(
                            f"active task `{task_id}` has unfinished dependency `{dependency}`"
                        )
        for task_id, task in tasks.items():
            if (
                isinstance(task, dict)
                and task.get("status") == "in_progress"
                and task_id not in active_tasks
            ):
                errors.append(f"in_progress task `{task_id}` must be listed in active_tasks")

    last_checkpoint = state.get("last_checkpoint")
    if last_checkpoint is not None and last_checkpoint not in tasks:
        errors.append(
            f"state.json last_checkpoint `{last_checkpoint}` must be null or the last completed task ID"
        )
    elif last_checkpoint is not None:
        checkpoint_task = tasks.get(last_checkpoint)
        if isinstance(checkpoint_task, dict) and checkpoint_task.get("status") not in {
            "done",
            "superseded",
        }:
            errors.append(f"state.json last_checkpoint `{last_checkpoint}` is not completed")

    blocker_streak = require_object(state, "blocker_streak", errors)
    blocker_count = blocker_streak.get("count")
    if not isinstance(blocker_count, int) or isinstance(blocker_count, bool) or blocker_count < 0:
        errors.append("state.json `blocker_streak.count` must be a non-negative integer")
    blocker_key = blocker_streak.get("key")
    if blocker_key is not None and not isinstance(blocker_key, str):
        errors.append("state.json `blocker_streak.key` must be a string or null")
    if blocker_count == 0 and blocker_key is not None:
        errors.append("blocker_streak.key must be null when count is 0")
    if isinstance(blocker_count, int) and blocker_count > 0 and not blocker_key:
        errors.append("blocker_streak.key is required when count is positive")

    artifact_owners = state.get("artifact_owners")
    if not isinstance(artifact_owners, dict):
        errors.append("state.json `artifact_owners` must be an object")
    else:
        for artifact, owners in artifact_owners.items():
            if not isinstance(artifact, str) or not artifact:
                errors.append("artifact_owners keys must be non-empty strings")
                continue
            owner_list = [owners] if isinstance(owners, str) else owners
            if not isinstance(owner_list, list) or not all(isinstance(item, str) for item in owner_list):
                errors.append(f"artifact owner for `{artifact}` must be a task ID or array of task IDs")
                continue
            for owner in owner_list:
                if owner not in tasks:
                    errors.append(f"artifact `{artifact}` has unknown owner `{owner}`")
                    continue
                owner_task = tasks.get(owner)
                if isinstance(owner_task, dict) and owner_task.get("status") not in {
                    "done",
                    "superseded",
                }:
                    errors.append(
                        f"artifact `{artifact}` owner `{owner}` must be done or superseded"
                    )

    if status == "complete":
        unfinished = [
            task_id
            for task_id, task in tasks.items()
            if isinstance(task, dict) and task.get("status") not in {"done", "superseded"}
        ]
        if unfinished:
            errors.append("complete goal has unfinished tasks: " + ", ".join(sorted(unfinished)))
        if active_tasks:
            errors.append("complete goal cannot have active_tasks")

    return errors


def main() -> None:
    args = parse_args()
    goal_dir = Path(args.goal_dir).expanduser().resolve()
    errors = validate_goal(goal_dir)
    if errors:
        print("Goal validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"Goal validation passed: {goal_dir}")


if __name__ == "__main__":
    main()
