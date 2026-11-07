"""B3 最近记录模块的隔离测试。

A1 的 core.storage 尚未合并到 main，因此这里用 monkeypatch 替换
record_list.load_records，只验证 B3 自己的排序、limit 校验与不变性。
"""

from copy import deepcopy

import pytest

from services import record_list


def _record(record_id, date, amount=10.0, record_type="expense", category="餐饮"):
    return {
        "id": record_id,
        "type": record_type,
        "date": date,
        "amount": amount,
        "category": category,
        "note": "",
    }


def _sample_records():
    """故意乱序，并包含同日两条记录。"""
    return [
        _record("rec_001", "2026-11-05"),
        _record("rec_002", "2026-11-07"),
        _record("rec_003", "2026-11-06"),
        _record("rec_004", "2026-11-07"),
    ]


def _patch_records(monkeypatch, records):
    monkeypatch.setattr(record_list, "load_records", lambda: records)


def test_returns_records_in_descending_date_order(monkeypatch):
    records = _sample_records()
    _patch_records(monkeypatch, records)

    result = record_list.get_recent_records()

    assert [item["id"] for item in result] == [
        "rec_004",
        "rec_002",
        "rec_003",
        "rec_001",
    ]


def test_same_date_later_added_comes_first(monkeypatch):
    records = [
        _record("old", "2026-11-07"),
        _record("new", "2026-11-07"),
        _record("newest", "2026-11-07"),
    ]
    _patch_records(monkeypatch, records)

    result = record_list.get_recent_records()

    assert [item["id"] for item in result] == ["newest", "new", "old"]


def test_respects_limit(monkeypatch):
    records = _sample_records()
    _patch_records(monkeypatch, records)

    result = record_list.get_recent_records(limit=2)

    assert [item["id"] for item in result] == ["rec_004", "rec_002"]


def test_default_limit_is_five(monkeypatch):
    records = [
        _record(f"rec_{index:03d}", f"2026-11-{index:02d}") for index in range(1, 9)
    ]
    _patch_records(monkeypatch, records)

    result = record_list.get_recent_records()

    assert len(result) == 5
    assert result[0]["id"] == "rec_008"


def test_limit_larger_than_total_returns_all(monkeypatch):
    records = _sample_records()
    _patch_records(monkeypatch, records)

    result = record_list.get_recent_records(limit=99)

    assert len(result) == len(records)


def test_empty_storage_returns_empty_list(monkeypatch):
    _patch_records(monkeypatch, [])

    assert record_list.get_recent_records() == []


def test_does_not_modify_original_records(monkeypatch):
    records = _sample_records()
    snapshot = deepcopy(records)
    _patch_records(monkeypatch, records)

    record_list.get_recent_records(limit=3)

    assert records == snapshot


def test_returned_items_are_copies(monkeypatch):
    records = _sample_records()
    _patch_records(monkeypatch, records)

    result = record_list.get_recent_records()
    result[0]["amount"] = 999.0
    result[0]["note"] = "被调用方改坏了"

    assert records[3]["amount"] == 10.0
    assert records[3]["note"] == ""


def test_sorted_across_year_boundary(monkeypatch):
    records = [
        _record("rec_2025", "2025-12-31"),
        _record("rec_2026", "2026-01-01"),
        _record("rec_mid", "2026-06-15"),
    ]
    _patch_records(monkeypatch, records)

    result = record_list.get_recent_records()

    assert [item["id"] for item in result] == ["rec_mid", "rec_2026", "rec_2025"]


@pytest.mark.parametrize("bad_limit", [0, -1, -5, 3.0, 2.5, "3", None, True, False])
def test_invalid_limit_raises_value_error(monkeypatch, bad_limit):
    records = _sample_records()
    _patch_records(monkeypatch, records)

    with pytest.raises(ValueError, match="limit 必须为正整数"):
        record_list.get_recent_records(limit=bad_limit)


def test_missing_date_does_not_crash(monkeypatch):
    """契约要求日期合法，但读取时应容错，不能让整页崩掉。"""
    records = [
        {"id": "no_date", "type": "expense", "amount": 1.0, "category": "餐饮", "note": ""},
        _record("dated", "2026-11-07"),
    ]
    _patch_records(monkeypatch, records)

    result = record_list.get_recent_records()

    assert [item["id"] for item in result] == ["dated", "no_date"]
