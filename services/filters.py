"""C1 负责：组合筛选；纯函数，不直接读写 JSON 文件。"""
import math
import re
from datetime import date


# 严格限定 YYYY-MM-DD 形状：4 位年、2 位月、2 位日，分隔符必须是短横线
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_date(value):
    """把 YYYY-MM-DD 字符串（或 date 对象）转换为 date 再比较。

    先做正则形状校验，拒绝 20261107、2026/11/07 等非契约格式；
    再用 fromisoformat 校验是否为真实日期，拒绝 2026-13-40 这类值。
    非法输入统一抛出 ValueError，由调用方（如 Flask 路由）转成 400 响应。
    """
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        raise ValueError(f"日期必须为 YYYY-MM-DD 格式：{value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"日期必须是真实有效的日期：{value!r}") from None


def _parse_amount(value):
    """把金额参数转换为 float，并拒绝 nan、inf 等非有限数值。

    兼容数字和数字字符串；非法输入抛出 ValueError，
    由调用方（如 Flask 路由）捕获后转成 400 响应。
    """
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"金额必须为数字：{value!r}") from None
    if not math.isfinite(amount):
        raise ValueError(f"金额必须为有限数字，不能为 nan 或 inf：{value!r}")
    return amount


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
        start_date, end_date: 严格 YYYY-MM-DD 字符串，组成日期闭区间。
        record_type: "income" 或 "expense"，精确匹配。
        category: 中文类别名，精确匹配。
        min_amount, max_amount: 有限数字或数字字符串，组成金额闭区间。

    任一筛选项传 None 或空字符串表示不启用该条件；
    日期格式不合法、日期不真实或金额为非有限数字（nan/inf）时抛出 ValueError。
    """
    start = _parse_date(start_date) if _is_enabled(start_date) else None
    end = _parse_date(end_date) if _is_enabled(end_date) else None
    lower = _parse_amount(min_amount) if _is_enabled(min_amount) else None
    upper = _parse_amount(max_amount) if _is_enabled(max_amount) else None
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
