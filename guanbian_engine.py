"""Deterministic Zhouyi hexagram logic shared by the Streamlit front end.

The existing TypeScript catalog is the single source of truth for the 64
hexagram names, line patterns, and editorial summaries. This module does not
claim that those summaries are classical quotations.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from pathlib import Path


CATALOG_PATH = Path(__file__).parent / "app" / "iching.ts"
_ROW = re.compile(r'^\s*\["([^"]+)", "([^"]+)", "([01]{6})", "([^"]+)"\],?\s*$', re.MULTILINE)
VALID_LINES = {6, 7, 8, 9}


@dataclass(frozen=True)
class Hexagram:
    number: int
    name: str
    traditional: str
    binary: str
    theme: str
    counsel: str

    @property
    def symbol(self) -> str:
        return chr(0x4DC0 + self.number - 1)


def load_catalog(path: Path = CATALOG_PATH) -> tuple[Hexagram, ...]:
    source = path.read_text(encoding="utf-8")
    rows = _ROW.findall(source)
    if len(rows) != 64 or len({row[2] for row in rows}) != 64:
        raise ValueError("六十四卦目录不完整或卦象重复")
    result = []
    for number, (name, traditional, binary, notes) in enumerate(rows, 1):
        theme, separator, counsel = notes.partition("|")
        if not separator or not theme or not counsel:
            raise ValueError(f"第 {number} 卦缺少主题或建议")
        result.append(Hexagram(number, name, traditional, binary, theme, counsel))
    if result[0].name != "乾" or result[0].binary != "111111":
        raise ValueError("乾卦序号或卦象错误")
    if result[1].name != "坤" or result[1].binary != "000000":
        raise ValueError("坤卦序号或卦象错误")
    return tuple(result)


HEXAGRAMS = load_catalog()
BY_BINARY = {item.binary: item for item in HEXAGRAMS}


@dataclass(frozen=True)
class Reading:
    lines: tuple[int, ...]  # bottom to top
    primary: Hexagram
    changed: Hexagram
    moving: tuple[int, ...]  # 1-based, bottom to top

    @property
    def stable_id(self) -> str:
        return f"{''.join(map(str, self.lines))}-{self.primary.number}-{self.changed.number}"


def cast_line() -> int:
    """Three independent fair coins: tails=2, heads=3."""
    return sum(cast_coins())


def cast_coins() -> tuple[int, int, int]:
    """Keep the actual three faces, so animation and audit use the same draw."""
    return tuple(2 + secrets.randbelow(2) for _ in range(3))


def validate_coin_tosses(tosses, lines) -> None:
    if tosses is None:  # Older records contain only line sums.
        return
    if not isinstance(tosses, list) or len(tosses) != len(lines):
        raise ValueError("铜钱记录与爻数不一致")
    for coins, line in zip(tosses, lines):
        if not isinstance(coins, list) or len(coins) != 3 or any(type(v) is not int or v not in (2, 3) for v in coins) or sum(coins) != line:
            raise ValueError("铜钱正反面与爻值不一致")


def resolve_reading(lines: list[int] | tuple[int, ...], *, engine_version: int = 2) -> Reading:
    if len(lines) != 6 or any(type(line) is not int or line not in VALID_LINES for line in lines):
        raise ValueError("必须提供由下至上的六个爻值（6、7、8、9）")
    if type(engine_version) is not int or engine_version not in (1, 2):
        raise ValueError("不支持的卦象引擎版本")
    # Catalog bits are top-to-bottom; tosses are bottom-to-top.
    # Version 1 exists ONLY to reproduce records made before this correction.
    ordered = reversed(lines) if engine_version == 2 else lines
    values = tuple(ordered)
    primary_binary = "".join("1" if line in (7, 9) else "0" for line in values)
    changed_binary = "".join("1" if line in (6, 7) else "0" for line in values)
    moving = tuple(index for index, line in enumerate(lines, 1) if line in (6, 9))
    return Reading(tuple(lines), BY_BINARY[primary_binary], BY_BINARY[changed_binary], moving)


def line_label(value: int) -> str:
    return {6: "老阴 · 动", 7: "少阳", 8: "少阴", 9: "老阳 · 动"}[value]


def line_glyph(value: int) -> str:
    glyph = "━━━━━━" if value in (7, 9) else "━━  ━━"
    return f"{glyph}  {'○' if value == 9 else '×' if value == 6 else ''}"
