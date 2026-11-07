"""B3 负责：获取最近的收支记录。

接口契约见 docs/CONTRACT.md：
- get_recent_records(limit=5) 返回按日期倒序排列、最多 limit 条的新列表；
- 同日记录"后来保存的排在前面"，与 B1/A1 的追加顺序保持一致；
- limit 必须为正整数，调用方传错时抛 ValueError；
- 不修改 core.storage 中的原始数据。
"""

from core.storage import load_records

DEFAULT_LIMIT = 5


def _validate_limit(limit):
    """校验 limit 为正整数。

    bool 是 int 的子类（True == 1），必须显式排除，否则会被当成 1 条。
    """
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit 必须为正整数")
    if limit <= 0:
        raise ValueError("limit 必须为正整数")
    return limit


def get_recent_records(limit=DEFAULT_LIMIT):
    """返回按日期降序排列的最近 limit 笔记录。

    日期是 YYYY-MM-DD 字符串，可直接按字符串比较（等价于时间先后），
    无需解析成 date 对象；同日则以在文件中的位置倒序，后来添加的优先。
    返回值是每条记录的浅拷贝，调用方修改结果不会影响存储层数据。
    """
    limit = _validate_limit(limit)
    records = load_records()

    ordered = sorted(
        enumerate(records),
        key=lambda item: (str(item[1].get("date") or ""), item[0]),
        reverse=True,
    )
    return [dict(record) for _, record in ordered[:limit]]
