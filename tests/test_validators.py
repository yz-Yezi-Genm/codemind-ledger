"""A2 模块测试：core/validators.py。

依赖 A3 的 is_valid_category()，本测试用 monkeypatch 注入模拟类别，
使 A2 的校验逻辑可独立验证，不阻塞于 A3 尚未实现。

覆盖 CONTRACT.md 要求的校验点：
  type / date / amount / category / note，以及编辑时的部分字段校验。
"""
import pytest

import core.validators as v

from decimal import Decimal

# 与 docs/CONTRACT.md 一致的模拟类别（A3 完成后应完全一致）
MOCK_CATEGORIES = {
    "income": ["工资", "奖学金", "兼职", "其他收入"],
    "expense": ["餐饮", "交通", "购物", "学习", "娱乐", "医疗", "其他支出"],
}


@pytest.fixture(autouse=True)
def _mock_categories(monkeypatch):
    """把 A3 的 is_valid_category 替换为模拟实现，隔离未完成依赖。"""
    monkeypatch.setattr(
        v,
        "is_valid_category",
        lambda record_type, category: category in MOCK_CATEGORIES.get(record_type, []),
    )


def _valid_record(**overrides):
    base = {
        "type": "expense",
        "date": "2026-11-07",
        "amount": 25.50,
        "category": "餐饮",
        "note": "午餐",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# validate_record：合法用例
# ---------------------------------------------------------------------------

def test_valid_expense():
    assert v.validate_record(_valid_record()) is None


def test_valid_income():
    rec = _valid_record(type="income", category="工资", amount=8000)
    assert v.validate_record(rec) is None


def test_valid_note_empty():
    assert v.validate_record(_valid_record(note="")) is None


def test_valid_note_absent():
    rec = _valid_record()
    del rec["note"]
    assert v.validate_record(rec) is None


def test_valid_amount_integer():
    assert v.validate_record(_valid_record(amount=100)) is None


# ---------------------------------------------------------------------------
# validate_record：非法 type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_type", ["支出", "EXPENSE", "income ", "", None, 123])
def test_invalid_type(bad_type):
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(type=bad_type))


# ---------------------------------------------------------------------------
# validate_record：非法 date
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_date", ["2026/11/07", "2026-13-01", "2026-02-30", "20261107", "", None, 20261107])
def test_invalid_date(bad_date):
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(date=bad_date))


def test_invalid_date_not_real():
    # 2026-02-30 不是真实日期（2 月没有 30 号）
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(date="2026-02-30"))


# ---------------------------------------------------------------------------
# validate_record：非法 amount
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_amount", [0, -1, -0.01, "25.5", None, True])
def test_invalid_amount(bad_amount):
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(amount=bad_amount))


def test_invalid_amount_too_many_decimals():
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(amount=1.234))


@pytest.mark.parametrize("bad_amount", [float("inf"), float("-inf"), float("nan")])
def test_invalid_amount_not_finite(bad_amount):
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(amount=bad_amount))


def test_valid_decimal_amount():
    # Decimal 是后端精确金额的常见类型，应被接受
    assert v.validate_record(_valid_record(amount=Decimal("25.50"))) is None


def test_valid_float_with_tiny_tail():
    # 0.1 + 0.2 的浮点尾数不应被误判为「超过两位小数」
    assert v.validate_record(_valid_record(amount=0.1 + 0.2)) is None


def test_invalid_decimal_not_finite():
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(amount=Decimal("Infinity")))


def test_invalid_decimal_too_many_decimals():
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(amount=Decimal("1.234")))


def test_valid_decimal_huge_number():
    # 超大金额不应在量化时抛出 InvalidOperation
    assert v.validate_record(_valid_record(amount=Decimal("1E+100"))) is None


@pytest.mark.parametrize("tiny", [Decimal("0.0000000001"), 1e-10])
def test_invalid_amount_tiny_tail(tiny):
    # Decimal/int 为精确值，float 的相对误差容忍不允许极小金额蒙混过关
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(amount=tiny))


# ---------------------------------------------------------------------------
# validate_record：非法 category
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_category", ["", "   ", None, 123, "不存在的类别"])
def test_invalid_category(bad_category):
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(category=bad_category))


def test_category_mismatch_type():
    # 「工资」是收入类别，不能用于支出
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(type="expense", category="工资"))


def test_category_belongs_to_income():
    # 收入记录用收入类别合法
    assert v.validate_record(_valid_record(type="income", category="兼职")) is None


# ---------------------------------------------------------------------------
# validate_record：非法 note / 非字典
# ---------------------------------------------------------------------------

def test_invalid_note_type():
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(note=123))


def test_invalid_note_none():
    # 明确传入 note=None 应被拒绝：提供了就必须是字符串
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(note=None))


def test_invalid_id_none():
    # 明确传入 id=None 应被拒绝：提供了就必须是非空字符串
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(id=None))


def test_invalid_id_empty():
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(id=""))


def test_valid_id_string():
    # 合法 id 应能通过
    assert v.validate_record(_valid_record(id="rec_001")) is None


def test_record_must_be_dict():
    for bad in [None, "not a dict", 42, [1, 2, 3]]:
        with pytest.raises(v.ValidationError):
            v.validate_record(bad)


# ---------------------------------------------------------------------------
# validate_partial：编辑时的部分字段校验
# ---------------------------------------------------------------------------

def test_partial_valid_single_field():
    assert v.validate_partial({"note": "新的备注"}) is None
    assert v.validate_partial({"amount": 50}) is None


def test_partial_valid_multiple_fields():
    assert v.validate_partial({"amount": 50, "date": "2026-11-08"}) is None


def test_partial_reject_id_change():
    with pytest.raises(v.ValidationError):
        v.validate_partial({"id": "rec_999"})


def test_partial_invalid_field():
    with pytest.raises(v.ValidationError):
        v.validate_partial({"amount": -1})


def test_partial_must_be_dict():
    with pytest.raises(v.ValidationError):
        v.validate_partial(None)


# ---------------------------------------------------------------------------
# 未知字段白名单
# ---------------------------------------------------------------------------

def test_record_reject_unknown_field():
    with pytest.raises(v.ValidationError):
        v.validate_record(_valid_record(foo=1))


def test_partial_reject_unknown_field():
    with pytest.raises(v.ValidationError):
        v.validate_partial({"foo": 1})


# ---------------------------------------------------------------------------
# ValidationError 是 ValueError 的子类（契约要求抛出 ValueError）
# ---------------------------------------------------------------------------

def test_validation_error_is_value_error():
    assert issubclass(v.ValidationError, ValueError)
