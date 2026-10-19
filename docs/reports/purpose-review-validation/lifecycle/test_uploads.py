import copy
import inspect
import unittest

from uploads import accept


class RecordingList(list):
    def __init__(self, items=()):
        super().__init__(items)
        self.append_count = 0

    def append(self, item):
        self.append_count += 1
        super().append(item)


class AcceptTests(unittest.TestCase):
    def assert_unchanged(self, records, before, first_record, append_count):
        self.assertEqual(records, before)
        self.assertIs(records[0], first_record)
        self.assertEqual(records.append_count, append_count)

    def test_public_signature_and_first_acceptance(self):
        self.assertEqual(
            list(inspect.signature(accept).parameters),
            ["records", "customer_id", "request_id", "filename", "content"],
        )
        records = RecordingList()
        result = accept(records, "alice", "req-1", "report.txt", b"original")
        self.assertEqual(result, 1)
        self.assertEqual(records, [{
            "id": 1, "customer_id": "alice", "request_id": "req-1",
            "filename": "report.txt", "content": b"original",
        }])
        self.assertEqual(records.append_count, 1)

    def test_retries_preserve_id_record_and_append_count(self):
        records = RecordingList()
        original_id = accept(records, "alice", "req-1", "first.txt", b"original")
        before = copy.deepcopy(list(records))
        first_record = records[0]
        for filename in ["first.txt", "renamed.txt", "first.txt"]:
            with self.subTest(filename=filename):
                self.assertEqual(
                    accept(records, "alice", "req-1", filename, b"original"),
                    original_id,
                )
                self.assert_unchanged(records, before, first_record, 1)

    def test_conflict_preserves_existing_state_and_can_retry_afterwards(self):
        records = RecordingList()
        original_id = accept(records, "alice", "req-1", "first.txt", b"abc")
        before = copy.deepcopy(list(records))
        first_record = records[0]
        for changed_content in [b"abd", b"", b"abcd"]:
            with self.subTest(content=changed_content):
                with self.assertRaises(ValueError):
                    accept(records, "alice", "req-1", "changed.txt", changed_content)
                self.assert_unchanged(records, before, first_record, 1)
        self.assertEqual(accept(records, "alice", "req-1", "first.txt", b"abc"), original_id)
        self.assertEqual(accept(records, "alice", "req-2", "next.txt", b"next"), 2)
        self.assertEqual(records.append_count, 2)

    def test_distinct_requests_with_same_filename_are_separate(self):
        for second_content in [b"same", b"different"]:
            with self.subTest(content=second_content):
                records = RecordingList()
                first = accept(records, "alice", "req-1", "same.txt", b"same")
                second = accept(records, "alice", "req-2", "same.txt", second_content)
                self.assertNotEqual(first, second)
                self.assertEqual(len(records), 2)
                self.assertEqual(records.append_count, 2)

    def test_customers_can_reuse_request_id_and_retry_independently(self):
        records = RecordingList()
        alice = accept(records, "alice", "req-1", "same.txt", b"alice")
        bob = accept(records, "bob", "req-1", "same.txt", b"bob")
        self.assertNotEqual(alice, bob)
        before = copy.deepcopy(list(records))
        self.assertEqual(accept(records, "alice", "req-1", "renamed.txt", b"alice"), alice)
        self.assertEqual(accept(records, "bob", "req-1", "same.txt", b"bob"), bob)
        with self.assertRaises(ValueError):
            accept(records, "bob", "req-1", "same.txt", b"alice")
        self.assertEqual(records, before)
        self.assertEqual(records.append_count, 2)

    def test_existing_records_return_their_original_id(self):
        existing = {"id": 73, "customer_id": "alice", "request_id": "old",
                    "filename": "before.txt", "content": b"saved"}
        records = RecordingList([existing])
        before = copy.deepcopy(list(records))
        self.assertEqual(accept(records, "alice", "old", "after.txt", b"saved"), 73)
        with self.assertRaises(ValueError):
            accept(records, "alice", "old", "before.txt", b"changed")
        self.assert_unchanged(records, before, existing, 0)

    def test_empty_bytes_and_retry_after_other_acceptances(self):
        records = RecordingList()
        first = accept(records, "alice", "empty", "empty.txt", b"")
        accept(records, "alice", "later", "empty.txt", b"later")
        accept(records, "bob", "empty", "empty.txt", b"")
        before = copy.deepcopy(list(records))
        self.assertEqual(accept(records, "alice", "empty", "renamed.txt", b""), first)
        with self.assertRaises(ValueError):
            accept(records, "alice", "empty", "empty.txt", b"nonempty")
        self.assertEqual(records, before)
        self.assertEqual(records.append_count, 3)


if __name__ == "__main__":
    unittest.main()
