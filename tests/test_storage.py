import json
import os
from pathlib import Path
import tempfile

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


def test_save_replaces_only_after_new_file_is_complete(records_path, monkeypatch):
    storage.save_records([{"note": "旧账本"}])
    old_content = records_path.read_bytes()
    new_records = [{"note": "新账本"}]
    replace = os.replace
    replaced = []

    def inspect_replace(source, target):
        source = Path(source)
        assert source.parent == records_path.parent
        assert source != records_path
        assert Path(target) == records_path
        assert records_path.read_bytes() == old_content
        assert json.loads(source.read_text(encoding="utf-8")) == new_records
        # Windows 下替换前必须关闭临时文件。
        replace(source, target)
        replaced.append(source)

    monkeypatch.setattr(os, "replace", inspect_replace)
    storage.save_records(new_records)
    assert len(replaced) == 1
    assert storage.load_records() == new_records
    assert list(records_path.parent.iterdir()) == [records_path]


def test_partial_write_failure_preserves_old_file(records_path, monkeypatch):
    storage.save_records([{"note": "旧账本"}])
    old_content = records_path.read_bytes()
    create_temp = tempfile.NamedTemporaryFile

    def failing_temp(*args, **kwargs):
        file = create_temp(*args, **kwargs)
        write = file.write

        def partial_write(content):
            write(content[:5])
            raise OSError("模拟磁盘写入失败")

        file.write = partial_write
        return file

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", failing_temp)
    with pytest.raises(OSError, match="模拟磁盘写入失败"):
        storage.save_records([{"note": "新账本"}])
    assert records_path.read_bytes() == old_content
    assert list(records_path.parent.iterdir()) == [records_path]


def test_sync_failure_preserves_old_file(records_path, monkeypatch):
    storage.save_records([{"note": "旧账本"}])
    old_content = records_path.read_bytes()

    def fail_sync(fd):
        raise OSError("模拟同步失败")

    monkeypatch.setattr(os, "fsync", fail_sync)
    with pytest.raises(OSError, match="模拟同步失败"):
        storage.save_records([])
    assert records_path.read_bytes() == old_content
    assert list(records_path.parent.iterdir()) == [records_path]


@pytest.mark.parametrize("existing", [True, False])
def test_replace_failure_preserves_state(records_path, monkeypatch, existing):
    records_path.parent.mkdir()
    if existing:
        records_path.write_text("[]", encoding="utf-8")

    def fail_replace(source, target):
        raise PermissionError("模拟文件被占用")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(PermissionError, match="模拟文件被占用"):
        storage.save_records([{"note": "新账本"}])
    if existing:
        assert records_path.read_text(encoding="utf-8") == "[]"
    else:
        assert not records_path.exists()
    assert not list(records_path.parent.glob("*.tmp"))


def test_temp_creation_failure_preserves_old_file(records_path, monkeypatch):
    storage.save_records([{"note": "旧账本"}])
    old_content = records_path.read_bytes()

    def fail_creation(*args, **kwargs):
        raise PermissionError("模拟目录无写入权限")

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", fail_creation)
    with pytest.raises(PermissionError, match="模拟目录无写入权限"):
        storage.save_records([])
    assert records_path.read_bytes() == old_content
    assert list(records_path.parent.iterdir()) == [records_path]
