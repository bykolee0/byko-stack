import json
from pathlib import Path

def add_task(path, label):
    path = Path(path)
    rows = json.loads(path.read_text()) if path.exists() else []
    task_id = max((row["id"] for row in rows), default=0) + 1
    rows.append({"id": task_id, "label": label})
    path.write_text(json.dumps(rows, ensure_ascii=False))
    return task_id
