from services.charts import category_statistics


def test_empty_records():
    assert category_statistics([]) == []


def test_only_income_returns_empty():
    records = [
        {"type": "income", "category": "工资", "amount": 5000.0},
    ]
    assert category_statistics(records) == []


def test_expense_grouped_and_summed():
    records = [
        {"type": "expense", "category": "餐饮", "amount": 25.0},
        {"type": "expense", "category": "交通", "amount": 10.0},
        {"type": "expense", "category": "餐饮", "amount": 15.5},
        {"type": "income", "category": "奖学金", "amount": 2000.0},
    ]
    result = category_statistics(records)

    assert len(result) == 2
    assert result[0]["category"] == "餐饮"
    assert result[0]["amount"] == 40.5
    assert result[1]["category"] == "交通"
    assert result[1]["amount"] == 10.0


def test_decimal_precision():
    records = [
        {"type": "expense", "category": "餐饮", "amount": 10.005},
        {"type": "expense", "category": "餐饮", "amount": 20.1},
    ]
    result = category_statistics(records)
    assert result[0]["amount"] == 30.11
