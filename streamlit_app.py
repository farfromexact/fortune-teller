"""观变 — Streamlit Community Cloud entrypoint."""

from __future__ import annotations

import html
import os
from datetime import date, datetime, timedelta

import streamlit as st

from guanbian_engine import cast_line, line_glyph, line_label, resolve_reading
from guanbian_records import export_records, import_records, make_record
from guanbian_birth import from_birthday, from_manual, profile_label
from guanbian_llm import AdviceError, Config, DEFAULT_MODEL, generate_advice, safety_notice


st.set_page_config(page_title="观变 · 以易观时，以行验知", page_icon="䷀", layout="centered")

STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"] { background: #f3efe5; color: #1e2925; }
[data-testid="stAppViewContainer"] { background-image: radial-gradient(circle at 15% 0%, rgba(255,255,255,.75), transparent 28rem); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 800px; padding-top: 1.5rem; padding-bottom: 4rem; }
h1, h2, h3, p, label, .gb-serif { font-family: 'Noto Serif SC','Songti SC','SimSun',serif !important; }
h1 { font-weight: 500 !important; letter-spacing: .05em; }
h2, h3 { font-weight: 600 !important; }
.gb-logo { display: flex; align-items: center; gap: .85rem; padding: .3rem 0 1.2rem; border-bottom: 1px solid rgba(30,41,37,.16); margin-bottom: 2rem; }
.gb-seal { display: grid; place-items: center; height: 42px; width: 42px; border-radius: 3px; background: #a53e32; color: #f3efe5; font-size: 23px; }
.gb-wordmark { font-size: 22px; font-weight: 700; letter-spacing: .18em; line-height: 1.1; }
.gb-tagline { display: block; color: #6f756e; font-size: 11px; letter-spacing: .18em; margin-top: 5px; }
.gb-eyebrow { color: #a53e32; font: 700 11px system-ui,sans-serif; letter-spacing: .27em; text-transform: uppercase; margin-bottom: 1.2rem; }
.gb-lead { font-size: 1.09rem; line-height: 1.9; color: #656e66; margin-bottom: 1.6rem; }
.gb-query { padding: 1rem 1.2rem; border-left: 3px solid #a53e32; background: rgba(255,255,255,.42); margin: 1rem 0 1.7rem; }
.gb-hex { font-family: 'Noto Serif SC','SimSun',serif; font-size: 2.6rem; color: #a53e32; line-height: 1.2; }
.gb-theme { color: #6f756e; font-size: .92rem; line-height: 1.8; }
.gb-yao { font: 1.05rem Consolas,monospace; letter-spacing: .04em; line-height: 1.65; white-space: pre; }
.gb-moving { color: #a53e32; }
.gb-note { color: #6f756e; font-size: .78rem; line-height: 1.7; }
.gb-source { background: rgba(66,93,81,.07); border-left: 2px solid #425d51; padding: .8rem 1rem; font-size: .82rem; line-height: 1.8; }
div.stButton > button[kind="primary"] { background: #425d51; border-color: #425d51; color: white; }
div.stButton > button[kind="primary"]:hover { background: #344b40; border-color: #344b40; }
div.stButton > button[kind="secondary"] { border-color: rgba(30,41,37,.24); }
div[data-testid="stVerticalBlockBorderWrapper"] { background: rgba(251,249,242,.7); }
div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input { background: #fbf9f2; }
@media(max-width: 640px) { [data-testid="stMainBlockContainer"] { padding-left: 1rem; padding-right: 1rem; } h1 { font-size: 2.3rem !important; } }
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)


def init_state() -> None:
    defaults = {
        "stage": "ask", "question": "", "lines": [], "records": [],
        "followups": [], "action": "", "review_days": 7,
        "birth_profile": None, "ai": None, "ai_calls": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go(stage: str) -> None:
    st.session_state.stage = stage
    st.rerun()


def new_question() -> None:
    st.session_state.lines = []
    st.session_state.followups = []
    st.session_state.action = ""
    st.session_state.question = ""
    st.session_state.question_input = ""
    st.session_state.birth_profile = None
    st.session_state.ai = None
    for key in list(st.session_state):
        if key.startswith("birth_input_"):
            del st.session_state[key]
    go("ask")


def llm_config() -> Config:
    def setting(name: str, default: str = "") -> str:
        value = os.environ.get(name)
        if value is None:
            try:
                value = st.secrets.get(name, default)
            except Exception:
                # Never render a parser exception: it may contain a secret line.
                value = default
        return str(value).strip()
    return Config(setting("DEEPSEEK_API_KEY"), setting("DEEPSEEK_MODEL", DEFAULT_MODEL))


def birth_input() -> tuple[dict | None, bool]:
    profile = None
    valid = True
    with st.expander("加入生辰背景（可选）"):
        st.caption("增加文化体验和个性化视角，不代表提高预测准确率；不填也能完整体验。")
        mode = st.radio("提供方式", ["不提供", "填写生日", "已有八字"], key="birth_input_mode", horizontal=True)
        try:
            if mode == "填写生日":
                day = st.date_input("公历出生日期", value=None, min_value=date(1900, 1, 1), max_value=date.today(), key="birth_input_date")
                known = st.checkbox("我知道出生时间（已换算为 UTC+8）", key="birth_input_known")
                clock = st.time_input("出生时间", value=None, key="birth_input_time") if known else None
                valid = day is not None and (not known or clock is not None)
                if valid:
                    profile = from_birthday(day, clock)
                else:
                    st.caption("请选择日期和已知时间；也可选“不提供”直接继续。")
                st.caption("使用固定 UTC+8，不自动处理出生地、真太阳时或历史夏令时；接近节令交界时请谨慎核对。")
            elif mode == "已有八字":
                text = st.text_input("年柱、月柱、日柱、时柱", placeholder="例如：乙酉 戊子 辛巳 壬辰", max_chars=32, key="birth_input_manual")
                st.caption("时柱不详可只填前三柱；这里只检查干支格式，不保证四柱对应同一出生时刻。")
                valid = bool(text.strip())
                if valid:
                    profile = from_manual(text)
            if profile:
                st.text(profile_label(profile))
                st.caption(profile["method"])
                st.caption(profile["uncertainty"])
        except ValueError as exc:
            st.warning(str(exc))
            valid = False
        st.caption("生日只用于本次会话内排盘。点击生成 AI 建议时，会把问题、卦象和四柱发给 DeepSeek，不发送原始生日；四柱也属于个人信息，保存与备份前请自行考虑。")
    return profile, valid


def show_advice(snapshot: dict) -> None:
    advice = snapshot["advice"]
    for title, key in (("01 · 当前局势", "situation"), ("02 · 关键变化", "change"), ("03 · 机会与风险", "opportunities_risks")):
        st.markdown(f"#### {title}")
        st.text(advice[key])
    st.markdown("#### 04 · 建议行动")
    for index, action in enumerate(advice["actions"], 1):
        st.text(f"{index}. {action}")
    st.markdown("#### 05 · 依据与边界")
    st.text(advice["boundary"])
    if advice["birth_context"] != "未提供个人背景":
        st.markdown("#### 生辰背景 · 文化反思")
        st.text(advice["birth_context"])
    st.caption(f"{snapshot['provider']} · {snapshot['model']} · {snapshot['created_at'][:19]} UTC · {snapshot['prompt_version']}")


def request_advice(followup: str = "") -> dict | None:
    if st.session_state.ai_calls >= 12:
        st.warning("本会话的 12 次模型请求已用完，已生成的结果仍可保存与复盘。")
        return None
    st.session_state.ai_calls += 1
    try:
        with st.spinner("正在结合问题与固定卦象整理建议……"):
            return generate_advice(llm_config(), st.session_state.question, st.session_state.lines,
                                   st.session_state.birth_profile,
                                   previous=st.session_state.ai["advice"] if st.session_state.ai else None,
                                   followups=st.session_state.followups, followup=followup)
    except AdviceError as exc:
        st.error(str(exc))
        return None


def header() -> None:
    left, right = st.columns([3, 1])
    with left:
        st.markdown('<div class="gb-logo"><span class="gb-seal">观</span><span><span class="gb-wordmark">观变</span><span class="gb-tagline">以易观时 · 以行验知</span></span></div>', unsafe_allow_html=True)
    with right:
        if st.button(f"变化档案 · {len(st.session_state.records)}", use_container_width=True):
            go("journal")


def ask_view() -> None:
    if "question_input" not in st.session_state:
        st.session_state.question_input = st.session_state.question
    st.markdown('<div class="gb-eyebrow">在不确定中，看见变化的方向</div>', unsafe_allow_html=True)
    st.title("此刻，你想看清哪一个选择？")
    st.markdown('<div class="gb-lead">观变不替你预言命运。它借《周易》的变化视角，帮你整理处境、风险与下一步行动。</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.text_area("写下一个真实而具体的问题", key="question_input", height=130, max_chars=180, placeholder="例如：我是否应该在未来三个月内转换工作方向？")
        profile, valid_profile = birth_input()
        notice = safety_notice(st.session_state.question_input)
        if notice:
            st.warning(notice)
        if st.button("开始观变  →", type="primary", use_container_width=True, disabled=not 8 <= len(st.session_state.question_input.strip()) <= 180 or not valid_profile or bool(notice)):
            st.session_state.question = st.session_state.question_input.strip()
            st.session_state.lines = []
            st.session_state.followups = []
            st.session_state.birth_profile = profile
            st.session_state.ai = None
            go("cast")
    st.caption("问题与生辰不会改变随机卦象。完成起卦后，可选择让 DeepSeek 结合这些背景生成建议。")
    st.markdown("#### 不知道怎么问？")
    st.markdown("可以试着问：我是否应该接受这份新工作？｜这段关系中，我真正需要看清什么？｜这个合作现在适合继续推进吗？")
    st.divider()
    st.caption("不作绝对预言　◇　卦象可复核　◇　结果留待行动验证")


def cast_view() -> None:
    if st.button("← 修改问题"):
        go("ask")
    st.markdown('<div class="gb-eyebrow">三枚铜钱 · 六次成卦</div>', unsafe_allow_html=True)
    st.title("让问题安静下来")
    st.markdown(f'<div class="gb-query">“{html.escape(st.session_state.question)}”</div>', unsafe_allow_html=True)
    lines = st.session_state.lines
    with st.container(border=True):
        for index in range(5, -1, -1):
            label = ("初", "二", "三", "四", "五", "上")[index]
            value = lines[index] if index < len(lines) else None
            glyph = line_glyph(value) if value else "┄┄┄┄┄┄"
            css = "gb-yao gb-moving" if value in (6, 9) else "gb-yao"
            description = line_label(value) if value else "待投"
            st.markdown(f'<div class="{css}">{label}　{glyph}　<span class="gb-note">{description}</span></div>', unsafe_allow_html=True)
    st.progress(len(lines) / 6, text=f"已完成 {len(lines)} / 6 次")
    if len(lines) < 6:
        if st.button(f"第 {len(lines) + 1} 次投掷", type="primary", use_container_width=True):
            st.session_state.lines = [*lines, cast_line()]
            if len(st.session_state.lines) == 6:
                go("reading")
            st.rerun()
    else:
        if st.button("查看结果", type="primary", use_container_width=True):
            go("reading")
    st.caption("每次由三枚独立的虚拟铜钱生成一个爻；六爻由下至上排列。")


def reading_view() -> None:
    lines = st.session_state.lines
    if len(lines) != 6:
        go("ask")
    reading = resolve_reading(lines)
    if st.button("← 新的问题"):
        new_question()
    st.markdown(f'<div class="gb-eyebrow">第 {reading.primary.number} 卦</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gb-hex">{reading.primary.symbol}　{reading.primary.name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gb-theme">{html.escape(reading.primary.theme)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gb-query">“{html.escape(st.session_state.question)}”</div>', unsafe_allow_html=True)
    left, middle, right = st.columns([2, 1, 2])
    with left:
        st.caption("本卦")
        for value in reversed(lines):
            css = "gb-yao gb-moving" if value in (6, 9) else "gb-yao"
            st.markdown(f'<div class="{css}">{line_glyph(value)}</div>', unsafe_allow_html=True)
        st.write(reading.primary.name)
    with middle:
        st.markdown("### →")
        st.caption("、".join(map(str, reading.moving)) + " 爻动" if reading.moving else "无动爻")
    with right:
        st.caption("变卦")
        for value in reversed(lines):
            changed_value = 7 if value == 6 else 8 if value == 9 else value
            st.markdown(f'<div class="gb-yao">{line_glyph(changed_value)}</div>', unsafe_allow_html=True)
        st.write(reading.changed.name)

    notice = safety_notice(st.session_state.question)
    if notice:
        st.warning(notice)
        return

    st.divider()
    st.subheader("把卦象放回你的问题")
    if st.session_state.birth_profile:
        with st.expander("本次使用的生辰背景"):
            st.text(profile_label(st.session_state.birth_profile))
            st.caption(st.session_state.birth_profile["method"])
            st.caption(st.session_state.birth_profile["uncertainty"])
    config = llm_config()
    if not st.session_state.ai:
        st.caption("只在你点击后调用模型：发送本次问题、固定卦象及可选四柱。AI 可能出错，不是经典原文或命运预测。")
        if not config.api_key:
            st.info("尚未配置 DeepSeek。管理员可在 Streamlit Secrets 中填写 DEEPSEEK_API_KEY；不影响基础体验。")
        if st.button("结合我的问题生成建议", type="primary", disabled=not config.api_key or st.session_state.ai_calls >= 12):
            response = request_advice()
            if response:
                st.session_state.ai = response
                st.rerun()
    if st.session_state.ai:
        with st.container(border=True):
            show_advice(st.session_state.ai)
    else:
        with st.container(border=True):
            st.markdown("#### 基础反思提示 · 非个性化解读")
            st.write(reading.primary.counsel)
            st.caption(f"本卦主题：{reading.primary.theme}；变化后的主题：{reading.changed.theme}。这是随机卦象带来的观察角度，不是对现实处境的判断。")

    with st.container(border=True):
        st.subheader("原典索引与内容边界")
        st.write(f"本卦：第 {reading.primary.number} 卦《周易》·{reading.primary.traditional}；变卦：第 {reading.changed.number} 卦《周易》·{reading.changed.traditional}。")
        st.markdown("卦序与卦象采用通行本结构；这里的主题和建议是**现代编辑性转译，不是经文或古注原文**。当前版本尚未完成逐条卦爻辞双源校勘，因此不展示未核对的原文。")
        st.link_button("查看《周易》原典", "https://ctext.org/book-of-changes")

    if st.session_state.ai:
        with st.expander("继续追问这一个卦（最多三次）"):
            for number, item in enumerate(st.session_state.followups, 1):
                st.text(f"{number}. {item['question']}")
                show_advice(item["response"])
            if len(st.session_state.followups) < 3:
                followup = st.text_input("你的追问", key=f"followup_input_{len(st.session_state.followups)}", max_chars=180)
                followup_notice = safety_notice(followup)
                if followup_notice:
                    st.warning(followup_notice)
                if st.button("发送追问", disabled=not followup.strip() or bool(followup_notice) or st.session_state.ai_calls >= 12):
                    response = request_advice(followup.strip())
                    if response:
                        st.session_state.followups = [*st.session_state.followups, {"question": followup.strip(), "response": response}]
                        st.rerun()
            st.caption("追问沿用原卦和原回答，不重抽、不覆盖；每次发送都会调用 DeepSeek。")

    st.divider()
    st.text_input("写下一件你愿意验证的小事", key="action", max_chars=300, placeholder="例如：本周约两位业内朋友聊聊真实情况")
    st.radio("计划多久后复盘？", options=[7, 30], format_func=lambda days: f"{days} 天后", horizontal=True, key="review_days")
    if st.button("保存到变化档案", type="primary", use_container_width=True):
        record = make_record(st.session_state.question, lines, st.session_state.action, st.session_state.review_days,
                             birth_profile=st.session_state.birth_profile, ai=st.session_state.ai, followups=st.session_state.followups)
        st.session_state.records = [record, *st.session_state.records][:100]
        go("journal")


def journal_view() -> None:
    st.markdown('<div class="gb-eyebrow">变化档案</div>', unsafe_allow_html=True)
    st.title("答案不在卦里结束")
    st.markdown('<div class="gb-lead">记录行动与结果，慢慢看清属于你自己的变化模式。</div>', unsafe_allow_html=True)
    if st.button("＋ 新的观变", type="primary"):
        new_question()
    st.info("这版 Streamlit 原型只在当前浏览器会话中保留记录；刷新或断线可能丢失。请每次更新后下载 JSON 备份，下次用下方入口导入。它不会自动同步账号。")

    records = st.session_state.records
    if not records:
        st.markdown("### 还没有留下记录")
        st.write("完成一次观变并写下行动，档案会从这里开始。")
    for record in records:
        reading = resolve_reading(record["lines"], engine_version=record.get("engine_version", 1))
        created = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
        due = created + timedelta(days=record["review_days"])
        with st.container(border=True):
            st.caption(f"{created.astimezone().strftime('%Y-%m-%d')} · {reading.primary.name} → {reading.changed.name}")
            st.subheader(record["question"])
            if record.get("engine_version", 1) == 1:
                st.warning("旧版记录：保留当时的卦名映射以复现历史。旧引擎曾颠倒爻序，不能作为新版本校验依据。")
            if record.get("birth_profile"):
                st.text(profile_label(record["birth_profile"]))
            if record.get("ai"):
                with st.expander("查看当时的 AI 建议与追问"):
                    st.caption("这是保存/导入的原回答，未重新生成；导入文件内容不代表已由服务端验证真实性。")
                    show_advice(record["ai"])
                    for item in record.get("followups", []):
                        st.text("追问：" + item["question"])
                        show_advice(item["response"])
            if record["action"]:
                st.write("当时决定：", record["action"])
            st.caption("复盘日期：" + due.astimezone().strftime("%Y-%m-%d"))
            if record["reflection"]:
                st.write("后来发生：", record["reflection"])
            else:
                key = f"reflection_{record['id']}"
                reflection = st.text_area("实际发生了什么？你的判断改变了吗？", key=key, max_chars=1000)
                if st.button("完成复盘", key=f"save_{record['id']}", disabled=not reflection.strip()):
                    record["reflection"] = reflection.strip()
                    st.rerun()

    st.divider()
    st.subheader("备份与恢复")
    if records:
        try:
            backup = export_records(records)
            st.download_button("下载我的记录 JSON", data=backup, file_name="guanbian-records.json", mime="application/json", use_container_width=True)
        except ValueError as exc:
            st.error(str(exc))
    uploaded = st.file_uploader("导入之前下载的观变记录", type=["json"], max_upload_size=5)
    if uploaded and st.button("导入记录", use_container_width=True):
        try:
            st.session_state.records = import_records(uploaded.getvalue())
        except ValueError as exc:
            st.error(f"导入失败：{exc}")
        else:
            st.success("记录已导入当前会话。")
            st.rerun()
    st.caption("备份包含问题、可选四柱、AI 原回答、行动与复盘，不含 API 密钥或原始生日。请私密保管。导入会替换当前会话的记录。")


init_state()
header()
stage = st.session_state.stage
if stage == "ask":
    ask_view()
elif stage == "cast":
    cast_view()
elif stage == "reading":
    reading_view()
elif stage == "journal":
    journal_view()
else:
    go("ask")

st.divider()
st.caption("观变 · 文化体验与决策参考 · 不替代医疗、法律、投资等专业意见")
