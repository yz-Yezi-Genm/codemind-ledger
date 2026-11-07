"""A1 负责：JSON 数据文件读写。

统一文件路径：data/records.json（运行时生成，不提交）。
与 B1/B2/B3 的接口已经约定，请勿擅自更名。
"""

import json
from pathlib import Path


RECORDS_PATH = Path(__file__).resolve().parent.parent / "data" / "records.json"


def load_records():
    """读取所有记录，返回 list[dict]；首次不存在文件时返回空列表。

    损坏 JSON、错误结构和文件访问异常交由调用方处理。
    """
    try:
        with RECORDS_PATH.open("r", encoding="utf-8") as file:
            records = json.load(file)
    except FileNotFoundError:
        return []

    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError("记录数据必须是字典组成的列表")
    return records


def save_records(records):
    """将完整记录列表写入 JSON 文件；成功时返回 None。

    仅检查存储结构；金额、日期等业务校验由 A2 负责。
    """
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError("记录数据必须是字典组成的列表")

    # 先序列化，避免非法数据导致原文件被提前清空。
    content = json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False)
    RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECORDS_PATH.write_text(content, encoding="utf-8")
