"""C3 负责：按支出类别汇总图表数据；纯函数。"""


def category_statistics(records):
    """只汇总 expense，返回 [{'category':'餐饮','amount':200.0}, ...]。"""
    summary = {}

    for record in records:
        if record.get("type") != "expense":
            continue

        category = record["category"]
        amount = record["amount"]

        if category in summary:
            summary[category] += amount
        else:
            summary[category] = amount

    result = []
    for category, amount in summary.items():
        result.append({
            "category": category,
            "amount": round(amount, 2)
        })

    result.sort(key=lambda x: x["amount"], reverse=True)

    return result
