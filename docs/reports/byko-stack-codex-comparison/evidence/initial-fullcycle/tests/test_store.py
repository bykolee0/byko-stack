import json
import tempfile
import unittest
from pathlib import Path
from store import add_task

class StoreTests(unittest.TestCase):
    def test_add_new(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "tasks.json"
            self.assertEqual(add_task(path, "A"), 1)
            self.assertEqual(json.loads(path.read_text()), [{"id": 1, "label": "A"}])
