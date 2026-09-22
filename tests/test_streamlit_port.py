import itertools
import json
import unittest

from guanbian_engine import HEXAGRAMS, cast_line, resolve_reading
from guanbian_records import export_records, import_records, make_record


class HexagramEngineTests(unittest.TestCase):
    def test_catalog_contains_all_unique_patterns(self):
        self.assertEqual(len(HEXAGRAMS), 64)
        self.assertEqual(len({item.binary for item in HEXAGRAMS}), 64)
        self.assertEqual((HEXAGRAMS[0].name, HEXAGRAMS[0].binary), ("乾", "111111"))
        self.assertEqual((HEXAGRAMS[1].name, HEXAGRAMS[1].binary), ("坤", "000000"))

    def test_all_4096_line_states_resolve(self):
        for values in itertools.product((6, 7, 8, 9), repeat=6):
            reading = resolve_reading(values)
            self.assertIn(reading.primary, HEXAGRAMS)
            self.assertIn(reading.changed, HEXAGRAMS)
            self.assertEqual(resolve_reading(values).stable_id, reading.stable_id)

    def test_stable_and_moving_line_examples(self):
        self.assertEqual(resolve_reading([7] * 6).primary.name, "乾")
        self.assertEqual(resolve_reading([7] * 6).changed.name, "乾")
        self.assertEqual(resolve_reading([9] * 6).changed.name, "坤")
        self.assertEqual(resolve_reading([6, 7, 7, 7, 7, 7]).moving, (1,))

    def test_cast_returns_allowed_values(self):
        self.assertTrue(all(cast_line() in (6, 7, 8, 9) for _ in range(100)))

    def test_rejects_invalid_input(self):
        with self.assertRaises(ValueError):
            resolve_reading([7] * 5)
        with self.assertRaises(ValueError):
            resolve_reading([True] * 6)


class BackupTests(unittest.TestCase):
    def test_export_import_roundtrip(self):
        record = make_record("我是否应该换一份工作？", [6, 7, 8, 9, 7, 8], "先联系两位同行", 7)
        record["reflection"] = "已联系，得到岗位反馈"
        self.assertEqual(import_records(export_records([record])), [record])

    def test_rejects_malformed_and_oversized_backups(self):
        with self.assertRaises(ValueError):
            import_records(b"not json")
        with self.assertRaises(ValueError):
            import_records(json.dumps({"version": 1, "records": [{"id": "bad"}]}).encode())
        with self.assertRaises(ValueError):
            import_records(b"x" * 1_000_001)


if __name__ == "__main__":
    unittest.main()
