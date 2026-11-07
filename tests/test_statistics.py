from copy import deepcopy

from services.statistics import calculate_summary


def test_empty_records():
    assert calculate_summary([]) == {
        "income": 0.0,
        "expense": 0.0,
        "balance": 0.0,
        "count": 0,
    }


def test_mixed_records():
    records = [
        {"type": "income", "amount": 100},
        {"type": "expense", "amount": 30.5},
        {"type": "income", "amount": 20},
    ]
    assert calculate_summary(records) == {
        "income": 120.0,
        "expense": 30.5,
        "balance": 89.5,
        "count": 3,
    }


def test_decimal_amounts():
    records = [
        {"type": "income", "amount": 0.1},
        {"type": "income", "amount": 0.2},
        {"type": "expense", "amount": 0.3},
    ]
    assert calculate_summary(records) == {
        "income": 0.3,
        "expense": 0.3,
        "balance": 0.0,
        "count": 3,
    }


def test_expense_only():
    records = [{"type": "expense", "amount": 25.5}]
    assert calculate_summary(records) == {
        "income": 0.0,
        "expense": 25.5,
        "balance": -25.5,
        "count": 1,
    }


def test_records_unchanged():
    records = [
        {"type": "income", "amount": 100, "note": "兼职"},
        {"type": "expense", "amount": 20, "note": "午餐"},
    ]
    original = deepcopy(records)

    calculate_summary(records)

    assert records == original