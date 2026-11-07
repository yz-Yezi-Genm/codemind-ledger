"""B1 隔离测试：模拟 A1/A2，不依赖其完成状态或真实账本文件。"""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services import record_add


@pytest.fixture
def data():
    return {
        "type": "expense",
        "date": "2026-11-07",
        "amount": 25.5,
        "category": "餐饮",
        "note": "午餐",
    }


@pytest.fixture
def dependencies(monkeypatch):
    stored = []

    def save(records):
        stored[:] = deepcopy(records)

    validate = Mock(return_value=None)
    load = Mock(side_effect=lambda: deepcopy(stored))
    persist = Mock(side_effect=save)
    monkeypatch.setattr(record_add, "validate_record", validate)
    monkeypatch.setattr(record_add, "load_records", load)
    monkeypatch.setattr(record_add, "save_records", persist)
    return SimpleNamespace(records=stored, validate=validate, load=load, save=persist)


@pytest.mark.parametrize("kind, category", [("expense", "餐饮"), ("income", "工资")])
def test_add_saves_record_and_preserves_input(dependencies, data, kind, category):
    data.update(type=kind, category=category)
    original = deepcopy(data)

    result = record_add.add_record(data)

    assert isinstance(result["id"], str) and result["id"].strip()
    assert {key: result[key] for key in original} == original
    assert dependencies.records == [result]
    assert data == original
    dependencies.validate.assert_called()


def test_add_keeps_existing_records_and_generates_unique_ids(dependencies, data):
    existing = dict(data, id="existing")
    dependencies.records.append(deepcopy(existing))

    first = record_add.add_record(data)
    second = record_add.add_record(data)

    assert len({existing["id"], first["id"], second["id"]}) == 3
    assert dependencies.records == [existing, first, second]


def test_id_collision_is_retried(dependencies, data, monkeypatch):
    dependencies.records.append(dict(data, id="rec_used"))
    ids = iter([SimpleNamespace(hex="used"), SimpleNamespace(hex="fresh")])
    monkeypatch.setattr(record_add, "uuid4", lambda: next(ids))

    result = record_add.add_record(data)

    assert result["id"] == "rec_fresh"
    assert len(dependencies.records) == 2


@pytest.mark.parametrize("amount", [0, -1])
def test_invalid_amount_rejected_by_validator_is_not_saved(dependencies, data, amount):
    # 验证 B1 对 A2 校验失败的处理，不代替 A2 的金额规则测试。
    data["amount"] = amount
    dependencies.validate.side_effect = ValueError("金额必须大于 0")

    with pytest.raises(ValueError):
        record_add.add_record(data)

    assert dependencies.validate.call_args.args[0]["amount"] == amount
    dependencies.save.assert_not_called()
    assert dependencies.records == []


@pytest.mark.parametrize("dependency", ["load", "save"])
def test_storage_error_is_reported(dependencies, data, dependency):
    failing = getattr(dependencies, dependency)
    failing.side_effect = OSError("模拟存储失败")

    with pytest.raises(OSError):
        record_add.add_record(data)

    failing.assert_called()
    if dependency == "load":
        dependencies.save.assert_not_called()
    assert dependencies.records == []


def test_missing_note_defaults_to_empty_string(dependencies, data):
    del data["note"]

    result = record_add.add_record(data)

    assert result["note"] == ""
    assert "note" not in data
    assert dependencies.records == [result]


@pytest.mark.parametrize("invalid", [None, [], {"note": None}])
def test_invalid_input_is_rejected_without_saving(dependencies, invalid):
    with pytest.raises(ValueError):
        record_add.add_record(invalid)

    dependencies.save.assert_not_called()


def test_client_id_is_replaced(dependencies, data):
    data["id"] = "client_id"

    result = record_add.add_record(data)

    assert result["id"] != "client_id"
    assert data["id"] == "client_id"
    assert dependencies.records == [result]
