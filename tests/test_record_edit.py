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


def _patch_dependencies(
    monkeypatch,
    records,
    validate=None,
    partial_validate=None,
):
    saved = []
    validated = []
    partially_validated = []

    monkeypatch.setattr(record_edit, "load_records", lambda: records)
    monkeypatch.setattr(
        record_edit,
        "save_records",
        lambda updated_records: saved.append(updated_records),
    )

    def default_partial_validate(updates):
        partially_validated.append(deepcopy(updates))

    monkeypatch.setattr(
        record_edit,
        "validate_partial",
        partial_validate if partial_validate is not None else default_partial_validate,
    )

    def validate_and_record(record):
        validated.append(deepcopy(record))
        if validate is not None:
            validate(record)

    monkeypatch.setattr(
        record_edit,
        "validate_record",
        validate_and_record,
    )
    return saved, validated, partially_validated


def test_update_record_merges_fields_and_preserves_id(monkeypatch):
    records = _sample_records()
    saved, validated, partially_validated = _patch_dependencies(monkeypatch, records)

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
    assert partially_validated == [{"amount": 32.8, "note": "晚餐"}]
    assert validated == [result]
    assert saved == [[result, records[1]]]
    assert records == _sample_records()


def test_update_record_accepts_unchanged_id_in_updates(monkeypatch):
    records = _sample_records()
    saved, _, partially_validated = _patch_dependencies(monkeypatch, records)

    result = record_edit.update_record("rec_002", {"id": "rec_002", "note": "月薪"})

    assert result["id"] == "rec_002"
    assert result["note"] == "月薪"
    assert partially_validated == [{"note": "月薪"}]
    assert len(saved) == 1


def test_update_record_rejects_changed_id(monkeypatch):
    records = _sample_records()
    saved, validated, partially_validated = _patch_dependencies(monkeypatch, records)

    with pytest.raises(ValueError, match="不允许修改记录 ID"):
        record_edit.update_record("rec_001", {"id": "rec_999"})

    assert saved == []
    assert validated == []
    assert partially_validated == []
    assert records == _sample_records()


def test_update_record_rejects_non_object_updates(monkeypatch):
    records = _sample_records()
    saved, validated, partially_validated = _patch_dependencies(monkeypatch, records)

    with pytest.raises(ValueError, match="更新内容必须是对象"):
        record_edit.update_record("rec_001", None)

    assert saved == []
    assert validated == []
    assert partially_validated == []
    assert records == _sample_records()


def test_update_record_does_not_save_when_validation_fails(monkeypatch):
    records = _sample_records()

    def reject_record(record):
        raise ValueError("金额必须大于 0")

    saved, validated, partially_validated = _patch_dependencies(
        monkeypatch,
        records,
        validate=reject_record,
    )

    with pytest.raises(ValueError, match="金额必须大于 0"):
        record_edit.update_record("rec_001", {"amount": -1})

    assert len(validated) == 1
    assert partially_validated == [{"amount": -1}]
    assert saved == []
    assert records == _sample_records()


def test_update_record_returns_none_for_unknown_id(monkeypatch):
    records = _sample_records()
    saved, validated, partially_validated = _patch_dependencies(monkeypatch, records)

    result = record_edit.update_record("rec_404", {"note": "不存在"})

    assert result is None
    assert saved == []
    assert validated == []
    assert partially_validated == []


def test_partial_validation_rejects_unknown_field_before_full_validation(monkeypatch):
    records = _sample_records()
    saved = []
    fully_validated = []
    monkeypatch.setattr(record_edit, "load_records", lambda: records)
    monkeypatch.setattr(
        record_edit,
        "save_records",
        lambda updated_records: saved.append(updated_records),
    )
    monkeypatch.setattr(
        record_edit,
        "validate_record",
        lambda record: fully_validated.append(record),
    )

    with pytest.raises(ValueError, match="未知字段"):
        record_edit.update_record("rec_001", {"unexpected": "value"})

    assert saved == []
    assert fully_validated == []
    assert records == _sample_records()


def test_full_validation_rejects_type_and_category_mismatch(monkeypatch):
    records = _sample_records()
    saved = []
    monkeypatch.setattr(record_edit, "load_records", lambda: records)
    monkeypatch.setattr(
        record_edit,
        "save_records",
        lambda updated_records: saved.append(updated_records),
    )

    with pytest.raises(ValueError, match="category 不属于 income"):
        record_edit.update_record("rec_001", {"type": "income"})

    assert saved == []
    assert records == _sample_records()


def test_delete_record_removes_only_target_and_saves(monkeypatch):
    records = _sample_records()
    saved, _, _ = _patch_dependencies(monkeypatch, records)

    result = record_edit.delete_record("rec_001")

    assert result is True
    assert saved == [[_sample_records()[1]]]
    assert records == _sample_records()


def test_delete_record_returns_false_for_unknown_id(monkeypatch):
    records = _sample_records()
    saved, _, _ = _patch_dependencies(monkeypatch, records)

    result = record_edit.delete_record("rec_404")

    assert result is False
    assert saved == []
    assert records == _sample_records()


def test_update_and_delete_with_real_storage_and_validation(monkeypatch, tmp_path):
    from core import storage

    monkeypatch.setattr(storage, "RECORDS_PATH", tmp_path / "records.json")
    storage.save_records(_sample_records())

    updated = record_edit.update_record(
        "rec_001",
        {"amount": 32.8, "note": "晚餐"},
    )

    assert updated["id"] == "rec_001"
    assert updated["amount"] == 32.8
    assert updated["note"] == "晚餐"
    assert storage.load_records()[0] == updated

    assert record_edit.delete_record("rec_001") is True
    assert storage.load_records() == [_sample_records()[1]]
