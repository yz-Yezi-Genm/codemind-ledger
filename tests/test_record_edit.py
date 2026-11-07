"""B2 修改和删除记录模块的隔离测试。"""

from copy import deepcopy

import pytest

from services import record_edit


def _sample_records():
    return [
        {
            "id": "rec_001",
            "type": "expense",
            "date": "2026-11-07",
            "amount": 25.50,
            "category": "餐饮",
            "note": "午餐",
        },
        {
            "id": "rec_002",
            "type": "income",
            "date": "2026-11-07",
            "amount": 1000.00,
            "category": "工资",
            "note": "",
        },
    ]


def _patch_dependencies(monkeypatch, records, validate=None):
    saved = []
    validated = []

    monkeypatch.setattr(record_edit, "load_records", lambda: records)
    monkeypatch.setattr(
        record_edit,
        "save_records",
        lambda updated_records: saved.append(updated_records),
    )

    def default_validate(record):
        validated.append(deepcopy(record))

    monkeypatch.setattr(
        record_edit,
        "validate_record",
        validate if validate is not None else default_validate,
    )
    return saved, validated


def test_update_record_merges_fields_and_preserves_id(monkeypatch):
    records = _sample_records()
    saved, validated = _patch_dependencies(monkeypatch, records)

    result = record_edit.update_record(
        "rec_001",
        {"amount": 32.8, "note": "晚餐"},
    )

    assert result == {
        "id": "rec_001",
        "type": "expense",
        "date": "2026-11-07",
        "amount": 32.8,
        "category": "餐饮",
        "note": "晚餐",
    }
    assert result is not records[0]
    assert validated == [result]
    assert saved == [[result, records[1]]]
    assert records == _sample_records()


def test_update_record_accepts_unchanged_id_in_updates(monkeypatch):
    records = _sample_records()
    saved, _ = _patch_dependencies(monkeypatch, records)

    result = record_edit.update_record("rec_002", {"id": "rec_002", "note": "月薪"})

    assert result["id"] == "rec_002"
    assert result["note"] == "月薪"
    assert len(saved) == 1


def test_update_record_rejects_changed_id(monkeypatch):
    records = _sample_records()
    saved, validated = _patch_dependencies(monkeypatch, records)

    with pytest.raises(ValueError, match="不允许修改记录 ID"):
        record_edit.update_record("rec_001", {"id": "rec_999"})

    assert saved == []
    assert validated == []
    assert records == _sample_records()


def test_update_record_rejects_non_object_updates(monkeypatch):
    records = _sample_records()
    saved, validated = _patch_dependencies(monkeypatch, records)

    with pytest.raises(ValueError, match="更新内容必须是对象"):
        record_edit.update_record("rec_001", None)

    assert saved == []
    assert validated == []
    assert records == _sample_records()


def test_update_record_does_not_save_when_validation_fails(monkeypatch):
    records = _sample_records()
    validated = []
    saved = []

    def reject_record(record):
        validated.append(record)
        raise ValueError("金额必须大于 0")

    monkeypatch.setattr(record_edit, "load_records", lambda: records)
    monkeypatch.setattr(
        record_edit,
        "save_records",
        lambda updated_records: saved.append(updated_records),
    )
    monkeypatch.setattr(record_edit, "validate_record", reject_record)

    with pytest.raises(ValueError, match="金额必须大于 0"):
        record_edit.update_record("rec_001", {"amount": -1})

    assert len(validated) == 1
    assert saved == []
    assert records == _sample_records()


def test_update_record_returns_none_for_unknown_id(monkeypatch):
    records = _sample_records()
    saved, validated = _patch_dependencies(monkeypatch, records)

    result = record_edit.update_record("rec_404", {"note": "不存在"})

    assert result is None
    assert saved == []
    assert validated == []


def test_delete_record_removes_only_target_and_saves(monkeypatch):
    records = _sample_records()
    saved, _ = _patch_dependencies(monkeypatch, records)

    result = record_edit.delete_record("rec_001")

    assert result is True
    assert saved == [[_sample_records()[1]]]
    assert records == _sample_records()


def test_delete_record_returns_false_for_unknown_id(monkeypatch):
    records = _sample_records()
    saved, _ = _patch_dependencies(monkeypatch, records)

    result = record_edit.delete_record("rec_404")

    assert result is False
    assert saved == []
    assert records == _sample_records()
