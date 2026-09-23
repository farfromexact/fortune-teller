from datetime import date
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from guanbian_records import export_records, import_records
from test_personalization import LINES, QUESTION, mock_transport


APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def button(app, label):
    return next(item for item in app.button if item.label == label)


class StreamlitFlowTests(unittest.TestCase):
    def test_birthday_cast_ai_followup_save_review_and_reset(self):
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-only", "DEEPSEEK_MODEL": "deepseek-flash"}), \
             patch("guanbian_llm.build_opener", return_value=mock_transport()) as opener:
            app = AppTest.from_file(str(APP), default_timeout=10).run()
            self.assertEqual(len(app.exception), 0)
            app.text_area(key="question_input").set_value(QUESTION)
            app.radio(key="birth_input_mode").set_value("填写生日").run()
            self.assertTrue(button(app, "开始观变  →").disabled)
            app.date_input(key="birth_input_date").set_value(date(2005, 12, 23)).run()
            button(app, "开始观变  →").click().run()
            self.assertEqual(app.session_state.stage, "cast")
            self.assertIsNone(app.session_state.birth_profile["pillars"]["hour"])
            app.checkbox(key="simple_cast").check().run()
            coin_faces = [[3, 2, 2] if v == 7 else [3, 3, 2] for v in LINES]
            with patch("guanbian_engine.cast_coins", side_effect=coin_faces):
                for index in range(6):
                    button(app, f"第 {index + 1} 次投掷").click().run()
            self.assertEqual(app.session_state.stage, "cast")
            self.assertEqual(app.session_state.coin_tosses, coin_faces)
            button(app, "查看风向与解读 →").click().run()
            self.assertEqual(app.session_state.stage, "reading")
            self.assertEqual(app.session_state.question, QUESTION)
            self.assertEqual(app.session_state.lines, LINES)
            opener.assert_not_called()
            button(app, "结合我的问题生成建议").click().run()
            self.assertEqual(len(app.exception), 0)
            original = app.session_state.ai.copy()
            self.assertEqual(opener.call_count, 1)
            self.assertTrue(any('先核实，再选择' in item.value for item in app.markdown))
            self.assertTrue(any('此问风向' in item.value for item in app.markdown))
            app.run()
            self.assertEqual(opener.call_count, 1)  # Reruns do not bill again.
            app.text_input(key="followup_input_0").set_value("下一步需要了解哪些情况？").run()
            button(app, "发送追问").click().run()
            self.assertEqual(opener.call_count, 2)
            self.assertEqual(app.session_state.ai, original)
            self.assertEqual(app.session_state.lines, LINES)
            self.assertEqual(len(app.session_state.followups), 1)
            app.text_input(key="action").set_value("本周联系同行").run()
            button(app, "保存到变化档案").click().run()
            self.assertEqual(len(app.exception), 0)
            record = app.session_state.records[0]
            self.assertEqual(record["ai"], original)
            self.assertEqual(record["coin_tosses"], coin_faces)
            self.assertEqual(record["birth_profile"]["pillars"]["day"], "辛巳")
            app.text_area(key=f"reflection_{record['id']}").set_value("已经完成访谈，有了新的信息").run()
            button(app, "完成复盘").click().run()
            self.assertEqual(app.session_state.records[0]["reflection"], "已经完成访谈，有了新的信息")
            self.assertEqual(import_records(export_records(app.session_state.records)), app.session_state.records)
            button(app, "＋ 新的观变").click().run()
            self.assertIsNone(app.session_state.ai)
            self.assertIsNone(app.session_state.birth_profile)
            self.assertEqual(app.session_state.lines, [])
            self.assertEqual(opener.call_count, 2)

    def test_anonymous_no_birth_no_api_key_and_safety_gate(self):
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}):
            app = AppTest.from_file(str(APP), default_timeout=10).run()
            app.text_area(key="question_input").set_value("我想自残，应该怎么办呢？").run()
            self.assertTrue(button(app, "开始观变  →").disabled)
            self.assertTrue(app.warning)
            app.text_area(key="question_input").set_value(QUESTION).run()
            button(app, "开始观变  →").click().run()
            app.checkbox(key="simple_cast").check().run()
            with patch("guanbian_engine.cast_coins", return_value=(3, 2, 2)):
                for index in range(6):
                    button(app, f"第 {index + 1} 次投掷").click().run()
            button(app, "查看风向与解读 →").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(button(app, "结合我的问题生成建议").disabled)
            self.assertFalse(button(app, "保存到变化档案").disabled)
            self.assertIsNone(app.session_state.birth_profile)


if __name__ == "__main__":
    unittest.main()
