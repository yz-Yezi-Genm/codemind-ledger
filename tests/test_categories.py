"""A3 类别管理单元测试。

类别清单以 docs/CONTRACT.md 为准，这里独立抄写一份，
当有人改动 core/categories.py 与契约不一致时测试会立刻失败。
"""
import pytest

from core.categories import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    get_categories,
    get_categories_for,
    is_valid_category,
)

CONTRACT_INCOME = ["工资", "奖学金", "兼职", "其他收入"]
CONTRACT_EXPENSE = ["餐饮", "交通", "购物", "学习", "娱乐", "医疗", "其他支出"]


def test_get_categories_structure():
    data = get_categories()
    assert set(data) == {"income", "expense"}
    assert isinstance(data["income"], list)
    assert isinstance(data["expense"], list)


def test_categories_match_contract():
    data = get_categories()
    assert data["income"] == CONTRACT_INCOME
    assert data["expense"] == CONTRACT_EXPENSE


def test_categories_are_clean_strings():
    for record_type, categories in get_categories().items():
        assert categories, f"{record_type} 不能为空"
        for name in categories:
            assert isinstance(name, str)
            assert name
            assert name == name.strip(), f"{name!r} 含首尾空白"
        assert len(set(categories)) == len(categories), f"{record_type} 存在重复类别"


def test_income_and_expense_disjoint():
    assert set(INCOME_CATEGORIES).isdisjoint(EXPENSE_CATEGORIES)


def test_caller_cannot_pollute_module_state():
    data = get_categories()
    data["income"].append("伪造类别")
    data["expense"].clear()

    again = get_categories()
    assert again["income"] == CONTRACT_INCOME
    assert again["expense"] == CONTRACT_EXPENSE


def test_get_categories_for_known_type():
    assert get_categories_for("income") == CONTRACT_INCOME
    assert get_categories_for("expense") == CONTRACT_EXPENSE


def test_get_categories_for_returns_copy():
    first = get_categories_for("expense")
    first.clear()
    assert get_categories_for("expense") == CONTRACT_EXPENSE


@pytest.mark.parametrize("bad_type", ["收入", "EXPENSE", "other", "", None, 1])
def test_get_categories_for_unknown_type(bad_type):
    with pytest.raises(ValueError, match="未知的记录类型"):
        get_categories_for(bad_type)


def test_is_valid_category_accepts_contract_items():
    assert is_valid_category("expense", "餐饮") is True
    assert is_valid_category("income", "工资") is True


def test_is_valid_category_rejects_other_group():
    assert is_valid_category("expense", "工资") is False
    assert is_valid_category("income", "餐饮") is False


def test_is_valid_category_rejects_unknown_values():
    assert is_valid_category("expense", "其它支出") is False
    assert is_valid_category("expense", "") is False
    assert is_valid_category("other", "餐饮") is False
