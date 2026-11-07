"""C1 filter_records 的单元测试：全部使用模拟数据，不依赖 JSON 存储。"""
import copy

import pytest

from services.filters import filter_records


RECORDS = [
    {"id": "rec_001", "type": "expense", "date": "2026-11-01",
     "amount": 20.0, "category": "餐饮", "note": "早餐"},
    {"id": "rec_002", "type": "expense", "date": "2026-11-03",
     "amount": 100.0, "category": "交通", "note": "打车"},
    {"id": "rec_003", "type": "income", "date": "2026-11-05",
     "amount": 2000.0, "category": "工资", "note": "月薪"},
    {"id": "rec_004", "type": "expense", "date": "2026-11-07",
     "amount": 59.9, "category": "餐饮", "note": "晚餐"},
    {"id": "rec_005", "type": "income", "date": "2026-11-10",
     "amount": 500.0, "category": "奖学金", "note": "助学金"},
]


def ids(records):
    return [record["id"] for record in records]


def test_no_filters_returns_all_in_new_list():
    result = filter_records(RECORDS)
    assert ids(result) == ["rec_001", "rec_002", "rec_003", "rec_004", "rec_005"]
    assert result is not RECORDS  # 返回的是新列表，而不是原列表对象


def test_start_date_is_inclusive():
    result = filter_records(RECORDS, start_date="2026-11-05")
    assert ids(result) == ["rec_003", "rec_004", "rec_005"]


def test_end_date_is_inclusive():
    result = filter_records(RECORDS, end_date="2026-11-03")
    assert ids(result) == ["rec_001", "rec_002"]


def test_date_range_keeps_both_bounds():
    result = filter_records(RECORDS, start_date="2026-11-03", end_date="2026-11-07")
    assert ids(result) == ["rec_002", "rec_003", "rec_004"]


def test_filter_by_record_type():
    assert ids(filter_records(RECORDS, record_type="income")) == ["rec_003", "rec_005"]
    assert ids(filter_records(RECORDS, record_type="expense")) == [
        "rec_001", "rec_002", "rec_004"]


def test_filter_by_category():
    assert ids(filter_records(RECORDS, category="餐饮")) == ["rec_001", "rec_004"]


def test_min_amount_is_inclusive():
    result = filter_records(RECORDS, min_amount=100)
    assert ids(result) == ["rec_002", "rec_003", "rec_005"]


def test_max_amount_is_inclusive():
    result = filter_records(RECORDS, max_amount=59.9)
    assert ids(result) == ["rec_001", "rec_004"]


def test_amount_range_keeps_both_bounds():
    result = filter_records(RECORDS, min_amount=20, max_amount=100)
    assert ids(result) == ["rec_001", "rec_002", "rec_004"]


def test_all_conditions_are_combined_with_and():
    result = filter_records(
        RECORDS,
        start_date="2026-11-01",
        end_date="2026-11-10",
        record_type="expense",
        category="餐饮",
        min_amount=10,
        max_amount=60,
    )
    assert ids(result) == ["rec_001", "rec_004"]


def test_empty_input_returns_empty_list():
    assert filter_records([]) == []


def test_no_match_returns_empty_list():
    assert filter_records(RECORDS, category="医疗") == []
    assert filter_records(RECORDS, start_date="2027-01-01") == []


def test_blank_string_filters_are_ignored():
    result = filter_records(
        RECORDS,
        start_date="", end_date="", record_type="",
        category="", min_amount="", max_amount="",
    )
    assert ids(result) == ids(RECORDS)


def test_numeric_string_amount_is_accepted():
    # HTTP 查询参数都是字符串，D1 可直接传入，由本函数完成转换
    assert ids(filter_records(RECORDS, min_amount="500")) == ["rec_003", "rec_005"]


def test_invalid_amount_raises_value_error():
    with pytest.raises(ValueError):
        filter_records(RECORDS, min_amount="abc")


def test_invalid_date_raises_value_error():
    with pytest.raises(ValueError):
        filter_records(RECORDS, start_date="not-a-date")


def test_original_records_are_not_modified():
    snapshot = copy.deepcopy(RECORDS)
    filter_records(
        RECORDS,
        start_date="2026-11-03",
        record_type="expense",
        min_amount=50,
        max_amount=500,
    )
    assert RECORDS == snapshot
