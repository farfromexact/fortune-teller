"""Portable, explicitly user-owned backup format for Streamlit sessions."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from guanbian_engine import resolve_reading


BACKUP_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_record(question: str, lines: list[int], action: str, review_days: int) -> dict[str, Any]:
    reading = resolve_reading(lines)
    if not 8 <= len(question.strip()) <= 180:
        raise ValueError("问题应为 8 至 180 个字符")
    if review_days not in (7, 30):
        raise ValueError("复盘间隔只能是 7 或 30 天")
    return {
        "id": f"{reading.stable_id}-{uuid.uuid4().hex}",
        "question": question.strip(),
        "lines": list(reading.lines),
        "action": action.strip()[:300],
        "review_days": review_days,
        "created_at": utc_now(),
        "reflection": "",
    }


def export_records(records: list[dict[str, Any]]) -> bytes:
    return json.dumps({"version": BACKUP_VERSION, "records": records}, ensure_ascii=False, indent=2).encode("utf-8")


def import_records(payload: bytes) -> list[dict[str, Any]]:
    if len(payload) > 1_000_000:
        raise ValueError("备份文件超过 1 MB")
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("不是有效的 UTF-8 JSON 备份") from exc
    if not isinstance(document, dict) or document.get("version") != BACKUP_VERSION:
        raise ValueError("不支持的备份版本")
    raw = document.get("records")
    if not isinstance(raw, list) or len(raw) > 100:
        raise ValueError("记录列表无效或超过 100 条")
    records = []
    seen = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("记录格式无效")
        record_id = item.get("id")
        question = item.get("question")
        lines = item.get("lines")
        action = item.get("action", "")
        reflection = item.get("reflection", "")
        review_days = item.get("review_days")
        created_at = item.get("created_at")
        if not isinstance(record_id, str) or not 1 <= len(record_id) <= 160 or record_id in seen:
            raise ValueError("记录 ID 重复或无效")
        if not isinstance(question, str) or not 8 <= len(question.strip()) <= 180:
            raise ValueError("问题长度无效")
        if not isinstance(lines, list):
            raise ValueError("投掷记录无效")
        resolve_reading(lines)
        if not isinstance(action, str) or len(action) > 300:
            raise ValueError("行动记录无效")
        if not isinstance(reflection, str) or len(reflection) > 1000:
            raise ValueError("复盘记录无效")
        if type(review_days) is not int or review_days not in (7, 30):
            raise ValueError("复盘间隔无效")
        if not isinstance(created_at, str):
            raise ValueError("记录日期无效")
        try:
            datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("记录日期无效") from exc
        records.append({
            "id": record_id, "question": question.strip(), "lines": lines,
            "action": action, "review_days": review_days,
            "created_at": created_at, "reflection": reflection,
        })
        seen.add(record_id)
    return records
