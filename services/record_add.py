"""B1 负责：增加一笔收入/支出记录。"""

from uuid import uuid4

from core.storage import load_records, save_records
from core.validators import validate_record


def add_record(data):
    """输入无 id 的记录字典，返回新增后含唯一 id 的记录字典。

    调用 A2 校验，通过 A1 保存；校验或读写失败时向调用方抛出异常。
    新记录追加到末尾，B3 展示同日记录时应优先展示后加入的记录。
    """
    if not isinstance(data, dict):
        raise ValueError("新增记录必须是字典")

    record = dict(data)
    # ID 由本模块生成，不采用客户端提供的 ID。
    record.pop("id", None)
    record.setdefault("note", "")
    if not isinstance(record["note"], str):
        raise ValueError("note 必须是字符串")
    validate_record(record)

    records = load_records()
    existing_ids = {item["id"] for item in records}
    record_id = "rec_" + uuid4().hex
    while record_id in existing_ids:
        record_id = "rec_" + uuid4().hex
    record["id"] = record_id

    save_records([*records, record])
    return record
