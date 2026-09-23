"""Portable, explicitly user-owned backup format for Streamlit sessions."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from guanbian_engine import resolve_reading, validate_coin_tosses
from guanbian_birth import validate_profile
from guanbian_llm import validate_snapshot


BACKUP_VERSION = 2
MAX_BACKUP_BYTES = 5_000_000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_record(question: str, lines: list[int], action: str, review_days: int, *,
                birth_profile: dict | None = None, ai: dict | None = None, followups: list | None = None,
                coin_tosses: list | None = None) -> dict[str, Any]:
    reading = resolve_reading(lines)
    if not 8 <= len(question.strip()) <= 180:
        raise ValueError("问题应为 8 至 180 个字符")
    if review_days not in (7, 30):
        raise ValueError("复盘间隔只能是 7 或 30 天")
    record = {
        "id": f"{reading.stable_id}-{uuid.uuid4().hex}",
        "question": question.strip(),
        "lines": list(reading.lines),
        "action": action.strip()[:300],
        "review_days": review_days,
        "created_at": utc_now(),
        "reflection": "",
        "engine_version": 2, "birth_profile": birth_profile,
        "ai": ai, "followups": followups or [],
        "coin_tosses": coin_tosses,
    }
    _validate_extensions(record)
    return record


def _validate_extensions(record: dict) -> None:
    validate_coin_tosses(record.get("coin_tosses"), record["lines"])
    profile = validate_profile(record["birth_profile"])
    ai = validate_snapshot(record["ai"], record["question"], record["lines"], profile)
    followups = record["followups"]
    if not isinstance(followups, list) or len(followups) > 3 or (followups and ai is None):
        raise ValueError("追问记录无效")
    if record["engine_version"] == 1 and (profile or ai or followups):
        raise ValueError("旧版记录不支持新的个人背景或 AI 快照")
    for item in followups:
        if not isinstance(item, dict) or set(item) != {"question", "response"}:
            raise ValueError("追问格式无效")
        if not isinstance(item["question"], str) or not 1 <= len(item["question"].strip()) <= 180:
            raise ValueError("追问内容无效")
        if item["response"] is None:
            raise ValueError("追问缺少回答")
        validate_snapshot(item["response"], record["question"], record["lines"], profile)


def export_records(records: list[dict[str, Any]]) -> bytes:
    payload = json.dumps({"version": BACKUP_VERSION, "records": records}, ensure_ascii=False, indent=2).encode("utf-8")
    if len(payload) > MAX_BACKUP_BYTES:
        raise ValueError("备份超过 5 MB，请减少记录后再导出")
    return payload


def import_records(payload: bytes) -> list[dict[str, Any]]:
    if len(payload) > MAX_BACKUP_BYTES:
        raise ValueError("备份文件超过 5 MB")
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("不是有效的 UTF-8 JSON 备份") from exc
    if not isinstance(document, dict) or type(document.get("version")) is not int or document.get("version") not in (1, BACKUP_VERSION):
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
        engine_version = item.get("engine_version", 1)
        resolve_reading(lines, engine_version=engine_version)
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
        record = {
            "id": record_id, "question": question.strip(), "lines": lines,
            "action": action, "review_days": review_days,
            "created_at": created_at, "reflection": reflection,
            "engine_version": engine_version, "birth_profile": item.get("birth_profile"),
            "ai": item.get("ai"), "followups": item.get("followups", []),
            "coin_tosses": item.get("coin_tosses"),
        }
        _validate_extensions(record)
        records.append(record)
        seen.add(record_id)
    return records
