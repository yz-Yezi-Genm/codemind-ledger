"""A3 负责：收入/支出类别管理。

类别采用固定清单（见 docs/CONTRACT.md），本期不提供可编辑类别，
因此本模块不读写任何文件，也不依赖 core.storage。

对外约定：
- get_categories()          契约函数，返回 {"income": [...], "expense": [...]}
- get_categories_for(type)  按类型取类别列表；未知类型抛 ValueError
- is_valid_category(type, category)  判断类别是否属于该类型
"""

# 类别唯一来源：修改此处必须同步 docs/CONTRACT.md，并通知 A2/D2。
INCOME_CATEGORIES = ("工资", "奖学金", "兼职", "其他收入")
EXPENSE_CATEGORIES = ("餐饮", "交通", "购物", "学习", "娱乐", "医疗", "其他支出")

# 记录类型 -> 允许的类别；顺序与契约一致，前端下拉框直接按此顺序渲染。
_CATEGORIES_BY_TYPE = {
    "income": INCOME_CATEGORIES,
    "expense": EXPENSE_CATEGORIES,
}

RECORD_TYPES = tuple(_CATEGORIES_BY_TYPE)


def get_categories():
    """返回 {"income": [...], "expense": [...]}。

    每次调用都返回新的列表，调用方随意增删都不会影响模块内部的常量。
    """
    return {record_type: list(categories) for record_type, categories in _CATEGORIES_BY_TYPE.items()}


def get_categories_for(record_type):
    """返回指定类型的类别列表（新列表）。

    未知类型（含非字符串）抛 ValueError，与 A2 校验风格保持一致。
    """
    try:
        categories = _CATEGORIES_BY_TYPE[record_type]
    except (KeyError, TypeError):
        raise ValueError(f"未知的记录类型：{record_type}") from None
    return list(categories)


def is_valid_category(record_type, category):
    """判断 category 是否属于 record_type 允许的类别集合。

    未知类型一律返回 False，不抛异常，方便 A2 在校验 category 时直接调用。
    """
    try:
        return category in _CATEGORIES_BY_TYPE[record_type]
    except (KeyError, TypeError):
        return False
