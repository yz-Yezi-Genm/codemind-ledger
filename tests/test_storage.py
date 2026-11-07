import json

import pytest

from core import storage


@pytest.fixture
def records_path(tmp_path, monkeypatch):
    path = tmp_path / "data" / "records.json"
    monkeypatch.setattr(storage, "RECORDS_PATH", path, raising=False)
    return path


def test_missing_file_returns_empty_list(records_path):
    assert storage.load_records() == []
    assert not records_path.exists()


def test_save_and_load_chinese_records(records_path, tmp_path, monkeypatch):
    records = [
        {"id": "rec_001", "type": "expense", "date": "2026-11-07",
         "amount": 25.5, "category": "餐饮", "note": "午餐"},
        {"id": "rec_002", "type": "income", "date": "2026-11-07",
         "amount": 100, "category": "兼职", "note": ""},
    ]
    monkeypatch.chdir(tmp_path)
    assert storage.save_records(records) is None
    assert json.loads(records_path.read_text(encoding="utf-8")) == records
    assert "餐饮" in records_path.read_text(encoding="utf-8")
    assert storage.load_records() == records


def test_save_replaces_previous_records(records_path):
    storage.save_records([{"id": "old"}])
    storage.save_records([])
    assert storage.load_records() == []


def test_corrupt_json_raises_without_changing_file(records_path):
    records_path.parent.mkdir()
    records_path.write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError):
        storage.load_records()
    assert records_path.read_text(encoding="utf-8") == "{broken"


@pytest.mark.parametrize("invalid", [{}, [1]])
def test_load_rejects_invalid_structure(records_path, invalid):
    records_path.parent.mkdir()
    records_path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ValueError):
        storage.load_records()


@pytest.mark.parametrize("invalid", [{}, [1], [{"note": object()}]])
def test_invalid_save_preserves_existing_file(records_path, invalid):
    records_path.parent.mkdir()
    records_path.write_text("[]", encoding="utf-8")
    with pytest.raises((ValueError, TypeError)):
        storage.save_records(invalid)
    assert records_path.read_text(encoding="utf-8") == "[]"
