import copy
import itertools
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from guanbian_engine import cast_coins, cast_line, resolve_reading, validate_coin_tosses
from guanbian_ritual import accept_toss
from guanbian_visuals import brief_html, wind_card_html, wind_card_svg
from guanbian_llm import validate_advice, validate_snapshot, generate_advice, Config
from guanbian_records import make_record, import_records, export_records
from test_personalization import answer, LINES, QUESTION, mock_transport


class RitualTests(unittest.TestCase):
    def test_retained_callback_resolves_engine_after_module_replacement(self):
        # Reproduce a live callback imported with the pre-animation engine.
        # The source watcher then replaces sys.modules, not the callback's
        # globals. A module-level engine reference would remain stale.
        legacy_engine = ModuleType("guanbian_engine")
        namespace = {"__name__": "retained_ritual"}
        source = (Path(__file__).resolve().parents[1] / "guanbian_ritual.py").read_text(encoding="utf-8")
        with patch.dict(sys.modules, {"guanbian_engine": legacy_engine}):
            exec(compile(source, "guanbian_ritual.py", "exec"), namespace)
        state = {"stage": "cast", "cast_run_id": "updated", "lines": [], "coin_tosses": []}
        with patch("guanbian_engine.cast_coins", return_value=(2, 3, 3)) as cast:
            event = {"run_id": "updated", "index": 1}
            self.assertTrue(namespace["accept_toss"](state, event))
            self.assertFalse(namespace["accept_toss"](state, event))
            cast.assert_called_once_with()
        self.assertEqual(state["lines"], [8])
        self.assertEqual(state["coin_tosses"], [[2, 3, 3]])

    def test_actual_coin_faces_and_sums_for_all_eight_outcomes(self):
        for bits in itertools.product((0, 1), repeat=3):
            with patch("guanbian_engine.secrets.randbelow", side_effect=bits):
                self.assertEqual(cast_coins(), tuple(b + 2 for b in bits))
            with patch("guanbian_engine.secrets.randbelow", side_effect=bits):
                self.assertEqual(cast_line(), sum(bits) + 6)

    def test_duplicate_stale_and_seventh_clicks_never_redraw(self):
        state = {"stage": "cast", "cast_run_id": "run1", "lines": [], "coin_tosses": []}
        with patch("guanbian_engine.cast_coins", return_value=(3, 2, 3)) as cast:
            for index in range(1, 7):
                event = {"run_id": "run1", "index": index}
                self.assertTrue(accept_toss(state, event))
                self.assertFalse(accept_toss(state, event))
            for event in ({"run_id": "run1", "index": 7}, {"run_id": "old", "index": 7}, None):
                self.assertFalse(accept_toss(state, event))
            self.assertEqual(cast.call_count, 6)
        self.assertEqual(state["lines"], [8] * 6)
        validate_coin_tosses(state["coin_tosses"], state["lines"])

    def test_coin_backup_roundtrip_and_tamper_rejection(self):
        coins = [[3, 2, 2]] * 6
        record = make_record(QUESTION, [7] * 6, "先确认条件", 7, coin_tosses=coins)
        self.assertEqual(import_records(export_records([record])), [record])
        broken = copy.deepcopy(record)
        broken["coin_tosses"][0] = [3, 3, 3]
        with self.assertRaises(ValueError):
            import_records(export_records([broken]))


class CardTests(unittest.TestCase):
    def test_all_64_cards_export_valid_self_contained_svg(self):
        for bits in itertools.product((7, 8), repeat=6):
            reading = resolve_reading(bits)
            svg = wind_card_svg(reading)
            root = ET.fromstring(svg)
            self.assertEqual(root.attrib["width"], "1080")
            self.assertIn(reading.primary.name, svg)
            for prohibited in ("<script", "foreignObject", "http://127", "生日", "DEEPSEEK", QUESTION):
                self.assertNotIn(prohibited, svg)

    def test_brief_uses_same_action_and_escapes_model_text(self):
        advice = answer()
        advice["brief"]["focus"] = '<img src=x onerror="alert(1)">'
        result = brief_html(advice)
        self.assertNotIn('<img', result)
        self.assertIn('&lt;img', result)
        self.assertIn(advice["actions"][0], result)

    def test_old_snapshot_has_no_fabricated_new_summary(self):
        advice = answer()
        del advice["brief"]
        validate_advice(advice, resolve_reading(LINES).stable_id)
        with self.assertRaises(ValueError):
            validate_advice(advice, resolve_reading(LINES).stable_id, require_brief=True)
        result = brief_html(advice)
        self.assertIn("原回答摘录", result)
        self.assertIn(advice["situation"], result)
        with patch("guanbian_llm.build_opener", return_value=mock_transport()):
            snapshot = generate_advice(Config("test"), QUESTION, LINES)
        snapshot["prompt_version"] = "guanbian-advice-v1"
        del snapshot["advice"]["brief"]
        validate_snapshot(snapshot, QUESTION, LINES, None)

    def test_brief_validation_rejects_missing_or_oversized_fields(self):
        for bad in ({"headline": "缺字段"}, {"headline": "太长" * 30, "focus": "内容", "reconsider_if": "条件"}):
            value = answer()
            value["brief"] = bad
            with self.assertRaises(ValueError):
                validate_advice(value, resolve_reading(LINES).stable_id)


if __name__ == "__main__":
    unittest.main()
