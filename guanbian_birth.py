"""Optional cultural context; never an input to random casting.

Only derived pillars, method and uncertainty leave this module. Raw birth dates
are deliberately absent from the saved / model-facing profile.
"""

from datetime import date, time
import re

from lunar_python import Solar


PILLAR_KEYS = ("year", "month", "day", "hour")
CYCLE = {"甲乙丙丁戊己庚辛壬癸"[i % 10] + "子丑寅卯辰巳午未申酉戌亥"[i % 12] for i in range(60)}
METHOD = "公历；固定 UTC+8；立春换年、节令换月；日柱按零点换日（sect=2）；未校正真太阳时或历史夏令时。lunar-python 1.4.8"
MANUAL_METHOD = "用户提供四柱；仅校验干支格式，未校验历法一致性。"


def _pillars(day: date, clock: time) -> dict:
    chart = Solar.fromYmdHms(day.year, day.month, day.day, clock.hour, clock.minute, clock.second).getLunar().getEightChar()
    chart.setSect(2)
    return dict(zip(PILLAR_KEYS, (chart.getYear(), chart.getMonth(), chart.getDay(), chart.getTime())))


def from_birthday(day: date, clock: time | None = None) -> dict:
    if type(day) is not date or not date(1900, 1, 1) <= day <= date.today():
        raise ValueError("请选择 1900 年至今天之间的公历出生日期")
    if clock is not None and (type(clock) is not time or clock.tzinfo is not None):
        raise ValueError("出生时间应为已换算到 UTC+8 的时间")
    pillars = _pillars(day, clock or time(0))
    uncertainty = "流派、地点与时间误差可能影响排盘；仅作文化体验，不代表预测准确率。"
    if clock is None:
        end = _pillars(day, time(23, 59, 59))
        for key in ("year", "month", "day"):
            if pillars[key] != end[key]:
                pillars[key] = None
        pillars["hour"] = None
        uncertainty = "出生时间不详，时柱留空；若当天跨年/月边界，相应柱也留空，不能据此推断。" + uncertainty
    return {"source": "birthday", "pillars": pillars, "method": METHOD, "uncertainty": uncertainty}


def from_manual(text: str) -> dict:
    compact = re.sub(r"[\s,，、]+", "", text.strip())
    if len(compact) not in (6, 8):
        raise ValueError("请按年、月、日、时顺序填写四柱；时柱不详可只填前三柱")
    values = [compact[i:i + 2] for i in range(0, len(compact), 2)]
    if any(value not in CYCLE for value in values):
        raise ValueError("每柱须为有效干支，例如甲子、乙丑；请检查输入")
    if len(values) == 3:
        values.append(None)
    return {"source": "manual", "pillars": dict(zip(PILLAR_KEYS, values)), "method": MANUAL_METHOD,
            "uncertainty": "未核验出生历法，不能据此确认命运或预测准确率；空缺柱不得推断。"}


def validate_profile(profile: dict | None) -> dict | None:
    if profile is None:
        return None
    if not isinstance(profile, dict) or set(profile) != {"source", "pillars", "method", "uncertainty"}:
        raise ValueError("个人背景格式无效")
    if profile["source"] not in ("birthday", "manual"):
        raise ValueError("个人背景来源无效")
    pillars = profile["pillars"]
    if not isinstance(pillars, dict) or set(pillars) != set(PILLAR_KEYS):
        raise ValueError("四柱字段无效")
    if any(value is not None and (not isinstance(value, str) or value not in CYCLE) for value in pillars.values()):
        raise ValueError("四柱值无效")
    expected = METHOD if profile["source"] == "birthday" else MANUAL_METHOD
    if profile["method"] != expected:
        raise ValueError("不支持的排盘口径")
    if not isinstance(profile["uncertainty"], str) or not 1 <= len(profile["uncertainty"]) <= 300:
        raise ValueError("个人背景说明无效")
    return profile


def profile_label(profile: dict) -> str:
    return "　".join(f"{label}：{profile['pillars'][key] or '不详'}" for key, label in zip(PILLAR_KEYS, ("年", "月", "日", "时")))
