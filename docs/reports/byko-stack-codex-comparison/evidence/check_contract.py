"""Shared external behavior checks derived from REQUEST.md, before reading run outputs."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

work = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('comparison_store', work / 'store.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
add_task = module.add_task
results = []

def check(name, fn):
    with tempfile.TemporaryDirectory(prefix='contract-') as d:
        try:
            fn(Path(d) / 'tasks.json')
            results.append({'case': name, 'status': 'PASS'})
        except Exception as exc:
            results.append({'case': name, 'status': 'FAIL', 'error': f'{type(exc).__name__}: {exc}'})

def eq(actual, expected):
    assert actual == expected, f'actual={actual!r}; expected={expected!r}'

def rows(path):
    return json.loads(path.read_text())

def seed(path, value, text=None):
    path.write_text(text if text is not None else json.dumps(value, ensure_ascii=False))
    os.utime(path, ns=(123000000000, 123000000000))

def unchanged_retry(path, label, expected):
    before = path.read_bytes(), path.stat().st_mtime_ns
    eq(add_task(Path(str(path)), label), expected)
    eq((path.read_bytes(), path.stat().st_mtime_ns), before)

def first(path):
    eq(add_task(path, 'first'), 1)
    eq(rows(path), [{'id': 1, 'label': 'first'}])

def next_id(path):
    old = [{'id': 7, 'label': 'older'}, {'id': 2, 'label': 'newer'}]
    seed(path, old)
    eq(add_task(path, 'third'), 8)
    eq(rows(path), old + [{'id': 8, 'label': 'third'}])

def repeat(path):
    eq(add_task(path, 'repeat'), 1)
    os.utime(path, ns=(123000000000, 123000000000))
    unchanged_retry(path, 'repeat', 1)

def reopen(path):
    seed(path, None, '[\n  {"id": 42, "label": "reopen"}\n]\n')
    unchanged_retry(path, 'reopen', 42)

def legacy_duplicate(path):
    seed(path, [{'id': 0, 'label': 'same'}, {'id': 9, 'label': 'same'}])
    unchanged_retry(path, 'same', 0)

def distinct(path, labels):
    for expected, label in enumerate(labels, 1):
        eq(add_task(path, label), expected)
    eq(rows(path), [{'id': i, 'label': label} for i, label in enumerate(labels, 1)])
    os.utime(path, ns=(123000000000, 123000000000))
    for expected, label in enumerate(labels, 1):
        unchanged_retry(path, label, expected)

def escaped(path):
    seed(path, None, '[{"id": 4, "label": "\\u0041"}]\n')
    unchanged_retry(path, 'A', 4)

def invalid(path):
    seed(path, None, 'not JSON')
    before = path.read_bytes(), path.stat().st_mtime_ns
    try:
        add_task(path, 'A')
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError('Existing JSON parsing error was suppressed')
    eq((path.read_bytes(), path.stat().st_mtime_ns), before)

def sequence(path):
    eq(add_task(path, 'A'), 1)
    eq(add_task(path, 'B'), 2)
    os.utime(path, ns=(123000000000, 123000000000))
    unchanged_retry(path, 'A', 1)
    eq(add_task(path, 'C'), 3)
    eq(rows(path), [{'id': 1, 'label': 'A'}, {'id': 2, 'label': 'B'}, {'id': 3, 'label': 'C'}])

def empty_array(path):
    seed(path, [])
    first(path)

check('first_insert_public_json_contract', first)
check('new_label_preserves_rows_and_max_id', next_id)
check('same_label_preserves_id_bytes_mtime', repeat)
check('reopen_pretty_json_preserves_bytes_mtime', reopen)
check('legacy_duplicates_first_id_zero_no_rewrite', legacy_duplicate)
check('case_sensitive_labels', lambda p: distinct(p, ['A', 'a']))
check('whitespace_sensitive_labels', lambda p: distinct(p, ['A', ' A', 'A ']))
check('unicode_representation_sensitive_labels', lambda p: distinct(p, ['é', 'e\u0301']))
check('empty_label_preserved', lambda p: distinct(p, ['', ' ']))
check('json_escape_decodes_to_same_label', escaped)
check('control_characters_preserved', lambda p: distinct(p, ['line\nbreak', 'nul\0value']))
check('invalid_json_failure_preserves_file', invalid)
check('retry_after_other_insert', sequence)
check('existing_empty_array', empty_array)
report = {'workdir': str(work), 'passed': sum(r['status'] == 'PASS' for r in results), 'total': len(results), 'results': results}
print(json.dumps(report, ensure_ascii=False, indent=2))
