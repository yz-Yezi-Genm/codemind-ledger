"""C2：收入、支出、结余统计。"""

from decimal import Decimal


def calculate_summary(records):
    """统计传入的记录，不修改原始数据。"""
    income = Decimal("0")
    expense = Decimal("0")

    for record in records:
        amount = Decimal(str(record["amount"]))

        if record["type"] == "income":
            income += amount
        elif record["type"] == "expense":
            expense += amount

    return {
        "income": float(income),
        "expense": float(expense),
        "balance": float(income - expense),
        "count": len(records),
    }