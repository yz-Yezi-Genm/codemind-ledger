"""C1 负责：组合筛选；纯函数，不直接读写 JSON 文件。"""
from datetime import date


def _parse_date(value):
    """把 YYYY-MM-DD 字符串（或 date 对象）转换为 date 再比较。

    非法格式会抛出 ValueError，由调用方（如 Flask 路由）捕获后转成 400 响应。
    """
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _is_enabled(value):
    """None 与空字符串都视为“未提供该筛选项”。

    HTTP 查询参数可能以空字符串形式出现，这里统一兜底，避免误过滤掉全部记录。
    """
    return value is not None and value != ""


def filter_records(
    records,
    start_date=None,
    end_date=None,
    record_type=None,
    category=None,
    min_amount=None,
    max_amount=None,
):
    """传入记录列表和可选筛选项，返回符合全部条件的新列表。

    多个条件之间是“与”关系，必须同时满足；日期和金额上下限均为包含边界。
    本函数为纯函数：不修改 records，也不读写 JSON 文件；
    返回的新列表保持各记录在原列表中的相对顺序。

    参数：
        records: 记录字典列表，字段约定见 docs/CONTRACT.md。
        start_date, end_date: YYYY-MM-DD 字符串，组成日期闭区间。
        record_type: "income" 或 "expense"，精确匹配。
        category: 中文类别名，精确匹配。
        min_amount, max_amount: 数字或数字字符串，组成金额闭区间。

    任一筛选项传 None 或空字符串表示不启用该条件；
    日期或金额格式非法时抛出 ValueError。
    """
    start = _parse_date(start_date) if _is_enabled(start_date) else None
    end = _parse_date(end_date) if _is_enabled(end_date) else None
    lower = float(min_amount) if _is_enabled(min_amount) else None
    upper = float(max_amount) if _is_enabled(max_amount) else None
    type_filter = record_type if _is_enabled(record_type) else None
    category_filter = category if _is_enabled(category) else None

    result = []
    for record in records:
        if start is not None or end is not None:
            record_date = _parse_date(record["date"])
            if start is not None and record_date < start:
                continue
            if end is not None and record_date > end:
                continue

        if type_filter is not None and record["type"] != type_filter:
            continue
        if category_filter is not None and record["category"] != category_filter:
            continue

        amount = record["amount"]
        if lower is not None and amount < lower:
            continue
        if upper is not None and amount > upper:
            continue

        result.append(record)

    return result
