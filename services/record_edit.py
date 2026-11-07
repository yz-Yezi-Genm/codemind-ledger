"""B2 负责：编辑与删除记录。"""

from core.storage import load_records, save_records
from core.validators import validate_record


def _find_record_index(records, record_id):
    """返回目标记录的下标；不存在时返回 None。"""
    for index, record in enumerate(records):
        if isinstance(record, dict) and record.get("id") == record_id:
            return index
    return None


def update_record(record_id, updates):
    """根据 id 更新记录；成功返回更新后的 dict，不存在返回 None。

    应保留原 id，并验证合并后的完整记录。
    """
    records = load_records()
    record_index = _find_record_index(records, record_id)
    if record_index is None:
        return None

    if not isinstance(updates, dict):
        raise ValueError("更新内容必须是对象")

    if "id" in updates and updates["id"] != record_id:
        raise ValueError("不允许修改记录 ID")

    # 创建新字典，避免校验失败时污染数据层返回的原对象。
    updated_record = {**records[record_index], **updates}
    updated_record["id"] = record_id
    validate_record(updated_record)

    updated_records = list(records)
    updated_records[record_index] = updated_record
    save_records(updated_records)
    return dict(updated_record)


def delete_record(record_id):
    """根据 id 删除记录；成功返回 True，不存在返回 False。

    """
    records = load_records()
    record_index = _find_record_index(records, record_id)
    if record_index is None:
        return False

    updated_records = list(records)
    del updated_records[record_index]
    save_records(updated_records)
    return True
