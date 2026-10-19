import copy
import unittest

from uploads import accept


class AcceptTests(unittest.TestCase):
    def test_first_accept_preserves_public_record_shape(self):
        records = []

        result = accept(records, "customer-a", "request-1", "file.txt", b"hello")

        self.assertEqual(result, 1)
        self.assertEqual(records, [{
            "id": 1, "customer_id": "customer-a", "request_id": "request-1",
            "filename": "file.txt", "content": b"hello",
        }])

    def test_equal_bytes_retry_preserves_id_and_all_records(self):
        records = []
        first = accept(records, "customer-a", "request-1", "file.txt", bytes([0, 255]))
        before = copy.deepcopy(records)

        result = accept(records, "customer-a", "request-1", "file.txt", bytes([0, 255]))

        self.assertEqual(result, first)
        self.assertEqual(records, before)

    def test_renamed_retry_preserves_original_filename_and_content(self):
        records = []
        first = accept(records, "customer-a", "request-1", "old.txt", b"hello")
        before = copy.deepcopy(records)

        result = accept(records, "customer-a", "request-1", "new.txt", b"hello")

        self.assertEqual(result, first)
        self.assertEqual(records, before)

    def test_conflicting_retry_preserves_all_records(self):
        for original, changed in [(b"abc", b"abd"), (b"", b"x"), (b"x", b"")]:
            with self.subTest(original=original, changed=changed):
                records = []
                accept(records, "customer-a", "request-1", "old.txt", original)
                before = copy.deepcopy(records)

                with self.assertRaises(ValueError):
                    accept(records, "customer-a", "request-1", "new.txt", changed)

                self.assertEqual(records, before)

    def test_distinct_requests_can_have_same_filename_and_content(self):
        records = []
        first = accept(records, "customer-a", "request-1", "file.txt", b"hello")
        second = accept(records, "customer-a", "request-2", "file.txt", b"hello")

        self.assertEqual((first, second), (1, 2))
        self.assertEqual([record["request_id"] for record in records],
                         ["request-1", "request-2"])

    def test_customers_can_reuse_request_id_with_different_content(self):
        records = []
        first = accept(records, "customer-a", "request-1", "file.txt", b"first")
        second = accept(records, "customer-b", "request-1", "file.txt", b"second")
        before = copy.deepcopy(records)

        self.assertEqual((first, second), (1, 2))
        self.assertEqual(accept(records, "customer-b", "request-1", "renamed", b"second"), second)
        self.assertEqual(records, before)

    def test_empty_content_retry_is_idempotent(self):
        records = []
        first = accept(records, "customer-a", "request-1", "file.txt", b"")
        before = copy.deepcopy(records)

        self.assertEqual(accept(records, "customer-a", "request-1", "file.txt", b""), first)
        self.assertEqual(records, before)

    def test_retry_older_request_after_other_accept_and_conflict(self):
        records = []
        first = accept(records, "customer-a", "request-1", "file.txt", b"first")
        accept(records, "customer-a", "request-2", "file.txt", b"second")
        before = copy.deepcopy(records)

        with self.assertRaises(ValueError):
            accept(records, "customer-a", "request-1", "file.txt", b"wrong")
        self.assertEqual(accept(records, "customer-a", "request-1", "other.txt", b"first"), first)
        self.assertEqual(records, before)
        self.assertEqual(accept(records, "customer-a", "request-3", "file.txt", b"third"), 3)


if __name__ == "__main__":
    unittest.main()
