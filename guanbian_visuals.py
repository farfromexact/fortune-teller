"""Code-native artwork. Share exports deliberately accept no personal data."""

from html import escape
from pathlib import Path
import re

import streamlit as st

from guanbian_engine import Reading


ASSETS = Path(__file__).parent / "assets"
def register_visual_components():
    """Register in the active Streamlit runtime, not on a bare Python import."""
    coins = st.components.v2.component(
        "coin_ritual", html=(ASSETS / "ritual.html").read_text(encoding="utf-8"),
        css=(ASSETS / "ritual.css").read_text(encoding="utf-8"),
        js=(ASSETS / "ritual.js").read_text(encoding="utf-8"),
    )
    exporter = st.components.v2.component(
        "wind_export", html='<button type="button">↓ 保存风向卡 · PNG</button><span role="status" aria-live="polite"></span>',
        css=':host{display:block}button{width:100%;background:transparent;border:1px solid #435d5140;border-radius:7px;padding:13px;color:#345044;cursor:pointer;font:14px system-ui,sans-serif;min-height:46px}button:hover{background:#435d5110}button:focus-visible{outline:2px solid #a53e32;outline-offset:3px}button:disabled{opacity:.55}span{display:block;font:11px system-ui,sans-serif;color:#65756a;margin:7px 0}',
        js=(ASSETS / "wind_export.js").read_text(encoding="utf-8"),
    )
    return coins, exporter


VISUAL_STYLES = """<style>
.wind-card{position:relative;isolation:isolate;overflow:hidden;border-radius:16px;padding:28px 32px 25px;background:radial-gradient(ellipse at 95% 0%,#40574a 0,transparent 65%),#21382f;color:#f1eadb;border:1px solid #61716070;box-shadow:0 15px 36px -25px #132b26;margin:12px 0 20px;}
.wind-card:before,.wind-card:after{content:'';position:absolute;z-index:-1;right:-90px;top:-170px;width:410px;height:410px;border-radius:50%;border:1px solid #e9ddbb16;pointer-events:none;}.wind-card:after{right:-128px;top:-130px;width:490px;height:490px;}
.wind-top{display:flex;justify-content:space-between;font:10px system-ui,sans-serif;letter-spacing:.22em;color:#c0c8b6;}.wind-top b{font-weight:400;color:#d2a286;}
.wind-body{display:grid;grid-template-columns:1fr 130px;align-items:center;gap:20px;padding:32px 0 20px;}.wind-title{font:500 29px/1.55 'Noto Serif SC','SimSun',serif;letter-spacing:.05em;margin:0 0 13px;color:#f4eddf;}.wind-copy{font:14px/1.95 'Noto Serif SC','SimSun',serif;color:#c6cebc;max-width:440px;margin:0;}.wind-sign{border-left:1px solid #dee6ca30;padding-left:24px;display:flex;flex-direction:column;align-items:center;gap:12px;}.wind-name{font:64px/1.2 'Noto Serif SC','SimSun',serif;color:#e9dcbf;}.wind-sign svg{width:74px;height:66px;}
.wind-bottom{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;border-top:1px solid #dde2c822;padding-top:17px;font:11px system-ui,sans-serif;color:#c0c8b6;}.wind-caption{font:10px system-ui,sans-serif;color:#a1b49e;margin-top:13px;letter-spacing:.08em;}
.brief-card{background:#fcfaf3;border:1px solid #d8d7c8;border-radius:14px;padding:27px 30px;margin:12px 0 18px;position:relative;box-shadow:0 10px 25px -25px #3b5041;}.brief-eyebrow{font:10px system-ui,sans-serif;letter-spacing:.2em;color:#9b4737;margin-bottom:15px;}.brief-title{font:500 27px/1.5 'Noto Serif SC','SimSun',serif;color:#253b30;margin:0 0 20px;}.brief-section{display:grid;grid-template-columns:90px 1fr;gap:18px;padding:16px 0;border-top:1px solid #deddd0;}.brief-section b{font:12px/1.9 system-ui,sans-serif;color:#72806e;font-weight:400;}.brief-section p{font-size:15px;line-height:1.85;margin:0;color:#344737;overflow-wrap:anywhere;}.brief-section.action{background:#435d5108;margin:0 -12px;padding:16px 12px;border-radius:6px;border-top:0;}.brief-section.action b{color:#994b3e;}.brief-note{font:11px/1.8 system-ui,sans-serif;color:#778373;margin-top:9px;}
.brief-card h2.brief-title{font-size:27px!important;line-height:1.5!important;font-weight:500!important;color:#253b30!important;margin:0 0 20px!important;padding:0!important}.wind-card h2.wind-title{font-size:29px!important;line-height:1.55!important;font-weight:500!important;color:#f4eddf!important;margin:0 0 13px!important;padding:0!important}.brief-card [data-testid="stHeaderActionElements"],.wind-card [data-testid="stHeaderActionElements"]{display:none}
@media(max-width:480px){.wind-card{padding:24px 22px 20px}.wind-body{grid-template-columns:1fr 76px;gap:15px;padding:25px 0 20px}.wind-title{font-size:23px}.wind-copy{font-size:12px;line-height:1.9}.wind-sign{padding-left:15px}.wind-name{font-size:46px}.wind-sign svg{width:51px;height:52px}.wind-top{font-size:9px;letter-spacing:.13em}.wind-bottom{font-size:10px}.brief-card{padding:23px 22px}.brief-title{font-size:24px}.brief-section{grid-template-columns:1fr;gap:7px;padding:15px 0}.brief-section p{font-size:14px}.brief-section b{font-size:11px}.brief-section.action{margin:0 -10px;padding:15px 10px}}
@media(max-width:480px){.brief-card h2.brief-title{font-size:24px!important}.wind-card h2.wind-title{font-size:23px!important}}
</style>"""


def hexagram_svg(reading: Reading) -> str:
    marks = []
    for row, value in enumerate(reversed(reading.lines)):
        color = "#ce826b" if value in (6, 9) else "#d5dcc1"
        y = row * 12
        if value in (7, 9):
            marks.append(f'<rect x="0" y="{y}" width="90" height="6" rx="1" fill="{color}"/>')
        else:
            marks.extend(f'<rect x="{x}" y="{y}" width="38" height="6" rx="1" fill="{color}"/>' for x in (0, 52))
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 90 68" role="img" aria-label="本卦六爻；朱砂色为动爻">' + ''.join(marks) + '</svg>'


def moving_label(reading: Reading) -> str:
    names = ("初", "二", "三", "四", "五", "上")
    return "、".join(names[i - 1] for i in reading.moving) + "爻动" if reading.moving else "六爻静 · 本卦不变"


def wind_card_html(reading: Reading) -> str:
    title = reading.primary.theme.split("，")[0]
    return f'''<section class="wind-card" aria-label="此问风向卡"><div class="wind-top"><span>此问风向 / A MOMENT OF CHANGE</span><b>NO. {reading.primary.number:02d}</b></div><div class="wind-body"><div><h2 class="wind-title">{escape(title)}</h2><p class="wind-copy">{escape(reading.primary.counsel)}</p></div><div class="wind-sign"><span class="wind-name">{escape(reading.primary.name)}</span>{hexagram_svg(reading)}</div></div><div class="wind-bottom"><span>本卦 · {escape(reading.primary.name)}　→　变卦 · {escape(reading.changed.name)}</span><span>{moving_label(reading)}</span></div><div class="wind-caption">来自卦象的现代编辑性提示 · 文化反思，不是未来预报</div></section>'''


def brief_html(advice: dict) -> str:
    brief = advice.get("brief")
    if brief:
        headline, focus, reconsider = brief["headline"], brief["focus"], brief["reconsider_if"]
        badge = "先看这一页 / THE SHORT ANSWER"
    else:
        # Old snapshots have no generated summary. Keep their original words,
        # rather than silently generating a new interpretation for old records.
        headline, focus, reconsider = "把答案带回生活", advice["situation"], advice["opportunities_risks"]
        badge = "原回答摘录 / SAVED ADVICE"
    return f'''<section class="brief-card" aria-label="短答案"><div class="brief-eyebrow">{badge}</div><h2 class="brief-title">{escape(headline)}</h2><div class="brief-section"><b>值得关注</b><p>{escape(focus)}</p></div><div class="brief-section action"><b>先做这一件事</b><p>{escape(advice["actions"][0])}</p></div><div class="brief-section"><b>{'重新考虑的信号' if brief else '原回答的风险提示'}</b><p>{escape(reconsider)}</p></div><div class="brief-note">与下方完整解读来自同一份回答 · 建议仍需现实证据验证</div></section>'''


def _svg_text(text: str, x: int, y: int, *, size: int, columns: int, color="#eee8d8") -> str:
    # Editorial strings are short, but wrap by codepoint to keep all CJK text.
    rows = [text[i:i + columns] for i in range(0, len(text), columns)]
    return ''.join(f'<text x="{x}" y="{y + index * int(size * 1.75)}" font-size="{size}" fill="{color}">{escape(row)}</text>' for index, row in enumerate(rows))


def wind_card_svg(reading: Reading) -> str:
    """1080 x 1350 postcard. No question, birthday, profile, or AI text accepted."""
    glyph = re.sub(r'<svg[^>]*>|</svg>', '', hexagram_svg(reading))
    title = reading.primary.theme.split("，")[0]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350"><defs><linearGradient id="ink" x2="1" y2="1"><stop stop-color="#344e40"/><stop offset="1" stop-color="#172c24"/></linearGradient><clipPath id="edge"><rect x="48" y="48" width="984" height="1254" rx="26"/></clipPath></defs><rect width="1080" height="1350" fill="#eeeade"/><rect x="48" y="48" width="984" height="1254" rx="26" fill="url(#ink)"/><g clip-path="url(#edge)" fill="none" stroke="#bdc9aa" stroke-opacity=".12"><circle cx="926" cy="173" r="285"/><circle cx="926" cy="173" r="369"/><path d="M-80 1110Q320 810 1110 1110M-60 1150Q300 850 1110 1150"/></g><g font-family="Songti SC, STSong, SimSun, serif"><rect x="112" y="119" width="57" height="57" rx="3" fill="#a94e3c"/><text x="126" y="159" font-size="34" fill="#f4ead5">观</text><text x="190" y="156" font-size="32" fill="#e9e7d4" letter-spacing="8">观变</text><text x="845" y="152" font-family="monospace" font-size="22" fill="#bfbea5">NO. {reading.primary.number:02d}</text><text x="113" y="265" font-size="23" letter-spacing="9" fill="#c3cbb5">此问风向</text><g transform="translate(115 344) scale(3)">{glyph}</g><text x="657" y="530" font-size="170" fill="#e9ddbd">{escape(reading.primary.name)}</text>{_svg_text(title,112,695,size=52,columns=16)}{_svg_text(reading.primary.counsel,112,863,size=29,columns=27,color="#c5d0b8")}<line x1="112" y1="1040" x2="968" y2="1040" stroke="#c4cfb5" stroke-opacity=".27"/>{_svg_text(f'本卦 · {reading.primary.name}　→　变卦 · {reading.changed.name}',112,1104,size=26,columns=32,color="#cfdbc1")}{_svg_text(moving_label(reading),112,1156,size=22,columns=32,color="#c28c73")}<text x="112" y="1238" font-size="20" fill="#abbba1">现代编辑性提示 · 文化反思，不是未来预报</text></g></svg>'''
