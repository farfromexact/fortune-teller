import copy
from datetime import date, time
import io
import json
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

from guanbian_birth import from_birthday, from_manual, validate_profile
from guanbian_engine import resolve_reading
from guanbian_llm import (AdviceError, Config, context_id, generate_advice,
                          safety_notice, validate_advice, validate_snapshot)
from guanbian_records import export_records, import_records, make_record


QUESTION = "未来三个月是否应该换工作？"
LINES = [7, 8, 8, 8, 7, 8]


def answer(lines=None):
    return {"reading_id": resolve_reading(lines or LINES).stable_id,
            "situation": "目前缺少新岗位的职责信息，先比较两个选择。", "change": "变化视角仅供反思，不是未来保证。",
            "opportunities_risks": "需要核实岗位的实际要求。", "actions": ["本周联系两位同行，记录岗位要求。", "列出三个不能接受的条件，核对新机会。"],
            "boundary": "现代编辑总结，不是经典原文。", "birth_context": "未提供个人背景"}


def mock_transport(advice=None, finish="stop", raw=None):
    transport = MagicMock()
    envelope = {"choices": [{"finish_reason": finish, "message": {"content": json.dumps(advice or answer(), ensure_ascii=False)}}]}
    transport.open.return_value.__enter__.return_value.read.return_value = raw if raw is not None else json.dumps(envelope).encode()
    return transport


class BirthTests(unittest.TestCase):
    def test_verified_upstream_calendar_example(self):
        profile = from_birthday(date(2005, 12, 23), time(8, 37))
        self.assertEqual(list(profile["pillars"].values()), ["乙酉", "戊子", "辛巳", "壬辰"])
        self.assertNotIn("2005", json.dumps(profile))
        self.assertEqual(validate_profile(profile), profile)

    def test_late_zi_hour_uses_declared_sect(self):
        profile = from_birthday(date(1988, 2, 15), time(23, 30))
        self.assertEqual(list(profile["pillars"].values()), ["戊辰", "甲寅", "庚子", "戊子"])

    def test_unknown_hour_and_term_boundary_are_not_invented(self):
        self.assertIsNone(from_birthday(date(2005, 12, 23))["pillars"]["hour"])
        pillars = from_birthday(date(2024, 2, 4))["pillars"]
        self.assertIsNone(pillars["year"])
        self.assertIsNone(pillars["month"])
        self.assertIsNotNone(pillars["day"])

    def test_manual_validation_and_no_raw_birth_fields(self):
        self.assertEqual(from_manual("乙酉 戊子 辛巳 壬辰")["pillars"]["hour"], "壬辰")
        self.assertIsNone(from_manual("乙酉 戊子 辛巳")["pillars"]["hour"])
        for value in ("甲丑 乙丑 丙寅 丁卯", "不是出生资料", "", "甲子"):
            with self.assertRaises(ValueError):
                from_manual(value)
        profile = from_manual("乙酉 戊子 辛巳")
        profile["birthday"] = "2005-12-23"
        with self.assertRaises(ValueError):
            validate_profile(profile)


class AdviceTests(unittest.TestCase):
    def test_server_request_binds_cast_and_profile(self):
        transport = mock_transport()
        profile = from_birthday(date(2005, 12, 23), time(8, 37))
        with patch("guanbian_llm.build_opener", return_value=transport):
            result = generate_advice(Config("test-only-key"), QUESTION, LINES, profile)
        request = transport.open.call_args.args[0]
        body = json.loads(request.data)
        context = json.loads(body["messages"][1]["content"])
        self.assertEqual(context["primary"]["name"], "屯")
        self.assertEqual(context["lines_bottom_to_top"], LINES)
        self.assertEqual(context["optional_birth_context"], profile)
        self.assertNotIn("2005-12-23", request.data.decode())
        self.assertNotIn("test-only-key", json.dumps(result))
        self.assertNotIn("test-only-key", repr(Config("test-only-key")))
        self.assertEqual(validate_snapshot(result, QUESTION, LINES, profile), result)
        self.assertEqual(body["thinking"], {"type": "disabled"})

    def test_followup_keeps_original_and_fixed_cast(self):
        transport = mock_transport()
        with patch("guanbian_llm.build_opener", return_value=transport):
            result = generate_advice(Config("test"), QUESTION, LINES, previous=answer(), followup="我还缺哪项信息？")
        data = json.loads(json.loads(transport.open.call_args.args[0].data)["messages"][1]["content"])
        self.assertEqual(data["original_advice"], answer())
        self.assertEqual(data["reading_id"], result["advice"]["reading_id"])

    def test_high_risk_never_calls_provider(self):
        for value in ("我是不是应该马上停药呢？", "想通过这个卦判断是否投资股票", "我不想活了，帮我算一下", "我想起诉对方怎么办？", "我被家暴了怎么办", "Should I invest in bitcoin?"):
            self.assertIsNotNone(safety_notice(value))
            with patch("guanbian_llm.build_opener") as opener, self.assertRaises(AdviceError):
                generate_advice(Config("test"), value, LINES)
            opener.assert_not_called()
        with patch("guanbian_llm.build_opener") as opener, self.assertRaises(AdviceError):
            generate_advice(Config("test"), QUESTION, LINES, followup="我想自残")
        opener.assert_not_called()

    def test_invalid_truncated_or_mismatched_responses_fail_closed(self):
        wrong = answer()
        wrong["reading_id"] = "other"
        for transport in (mock_transport(finish="length"), mock_transport(raw=b"{}"), mock_transport(raw=b"not-json"), mock_transport(wrong)):
            with patch("guanbian_llm.build_opener", return_value=transport), self.assertRaises(AdviceError):
                generate_advice(Config("test"), QUESTION, LINES)

    def test_provider_errors_are_redacted(self):
        transport = MagicMock()
        for error in (HTTPError("https://api.deepseek.com", 401, "secret-test-value", {}, io.BytesIO(b"secret-test-value")), TimeoutError("secret-test-value")):
            transport.open.side_effect = error
            with patch("guanbian_llm.build_opener", return_value=transport), self.assertRaises(AdviceError) as caught:
                generate_advice(Config("test"), QUESTION, LINES)
            self.assertNotIn("secret-test-value", str(caught.exception))

    def test_question_and_profile_change_context_not_hexagram(self):
        first = context_id(QUESTION, LINES, None)
        self.assertNotEqual(first, context_id("是否应该在下月搬家呢？", LINES, None))
        self.assertNotEqual(first, context_id(QUESTION, LINES, from_manual("乙酉 戊子 辛巳")))
        self.assertEqual(resolve_reading(LINES).primary.name, "屯")


class ExtendedBackupTests(unittest.TestCase):
    def test_ai_and_birth_roundtrip_and_context_mismatch_rejection(self):
        profile = from_manual("乙酉 戊子 辛巳 壬辰")
        with patch("guanbian_llm.build_opener", return_value=mock_transport()):
            ai = generate_advice(Config("test"), QUESTION, LINES, profile)
        record = make_record(QUESTION, LINES, "联系同行", 7, birth_profile=profile, ai=ai,
                             followups=[{"question": "下一步呢？", "response": ai}])
        self.assertEqual(import_records(export_records([record])), [record])
        broken = copy.deepcopy(record)
        broken["question"] = "我是否应该和伙伴继续合作？"
        with self.assertRaises(ValueError):
            import_records(export_records([broken]))

    def test_v1_backup_keeps_old_mapping_explicitly(self):
        record = make_record(QUESTION, LINES, "联系同行", 7)
        for key in ("engine_version", "birth_profile", "ai", "followups"):
            del record[key]
        imported = import_records(json.dumps({"version": 1, "records": [record]}).encode())[0]
        self.assertEqual(imported["engine_version"], 1)
        self.assertEqual(resolve_reading(imported["lines"], engine_version=1).primary.name, "蒙")
        self.assertEqual(import_records(export_records([imported])), [imported])


if __name__ == "__main__":
    unittest.main()
