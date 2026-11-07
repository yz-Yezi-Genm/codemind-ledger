"""A2 负责：验证收支数据（见 docs/CONTRACT.md）。

设计说明
--------
- validate_record(data)     完整校验，用于新增记录，要求必填字段齐全。
- validate_partial(updates) 部分校验，用于编辑记录（配合 B2 的 update_record），
  只校验 updates 中出现的字段；字段缺失时跳过，不把"没传"当成"非法"。

两类函数共用同一套字段级规则，避免校验口径不一致。
"""
from __future__ import annotations

import datetime
import math
from decimal import Decimal, localcontext

from core.categories import is_valid_category


class ValidationError(ValueError):
    """记录校验失败时抛出，携带中文错误信息。"""


# 记录允许出现的字段；多余字段视为非法，避免脏数据被静默保存
_ALLOWED_FIELDS = {"id", "type", "date", "amount", "category", "note"}


# ---------------------------------------------------------------------------
# 字段级校验（每项独立，供完整/部分校验复用）
# ---------------------------------------------------------------------------

def _validate_type(value):
    """type 必须为 income 或 expense，不接受中文。"""
    if not isinstance(value, str):
        raise ValidationError("type 必须是字符串")
    if value not in ("income", "expense"):
        raise ValidationError("type 只能是 income 或 expense")


def _validate_date(value):
    """date 必须为 YYYY-MM-DD，且为真实有效日期。"""
    if not isinstance(value, str):
        raise ValidationError("date 必须是字符串")
    # 严格限定 YYYY-MM-DD：长度固定、分隔符为连字符，
    # 避免 fromisoformat 接受 20261107 这类紧凑格式
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise ValidationError("date 必须是 YYYY-MM-DD 格式")
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        raise ValidationError("date 必须是 YYYY-MM-DD 格式的真实日期")


def _validate_amount(value):
    """amount 必须是数字且严格大于 0，最多两位小数，且为有限数。

    接受 int / float / decimal.Decimal。
    两位小数的判断用 Decimal 精确量化：
    - float 因二进制表示可能带微小尾数（如 0.1 + 0.2，误差量级约 1e-16），
      按固定绝对容忍量 1e-12 吸收，远小于一分、又远大于尾数误差；
    - int / Decimal 是精确值，不做任何容忍，超出两位即非法。
    """
    if isinstance(value, bool):
        raise ValidationError("amount 必须是数字")

    is_float = False
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValidationError("amount 必须是有限数字")
        d = value
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValidationError("amount 必须是有限数字")
        # 用 str 构造 Decimal，避免二进制浮点误差被带入十进制
        d = Decimal(str(value))
        is_float = True
    elif isinstance(value, int):
        d = Decimal(value)
    else:
        raise ValidationError("amount 必须是数字")

    if d <= 0:
        raise ValidationError("amount 必须大于 0")

    # 最多两位小数：量化到 0.01 后与原值比较。
    # 动态精度上下文（按最高位指数估算所需位数），
    # 避免超大数值量化时抛出 InvalidOperation
    with localcontext() as ctx:
        ctx.prec = max(d.adjusted() + 4, 28)
        quantized = d.quantize(Decimal("0.01"))
    diff = (d - quantized).copy_abs()
    # 只有浮点输入才容忍其固有的二进制尾数误差；
    # 容忍量固定为 1e-12（远小于一分、远大于 ~1e-16 的尾数误差），
    # 精确的 int / Decimal 零容忍。
    tolerance = Decimal("1e-12") if is_float else Decimal("0")
    if diff > tolerance:
        raise ValidationError("amount 最多保留两位小数")


def _validate_category(value, record_type=None):
    """category 必须为中文非空字符串；若给出 type，须属于该 type 的允许类别。"""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("category 必须是非空字符串")
    if record_type is not None:
        if not is_valid_category(record_type, value):
            raise ValidationError(f"category 不属于 {record_type} 的允许类别")


def _validate_note(value):
    """note 必须为字符串（可为空）。"""
    if not isinstance(value, str):
        raise ValidationError("note 必须是字符串")


def _validate_id(value):
    """id 必须为非空字符串（编辑时不允许改变 id）。"""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("id 必须是非空字符串")


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------

def validate_record(data):
    """完整校验一条记录，合法返回 None，非法抛出 ValidationError。

    用于新增记录：type/date/amount/category 为必填，note 可选。
    category 的合法性会结合 type 一起判断。
    """
    if not isinstance(data, dict):
        raise ValidationError("记录必须是字典")

    unknown = set(data) - _ALLOWED_FIELDS
    if unknown:
        raise ValidationError(f"记录包含未知字段: {', '.join(sorted(unknown))}")

    _validate_type(data.get("type"))
    _validate_date(data.get("date"))
    _validate_amount(data.get("amount"))
    _validate_category(data.get("category"), record_type=data.get("type"))

    # note 可选：未提供时跳过；但一旦提供（含 None），必须是字符串
    if "note" in data:
        _validate_note(data["note"])

    # id 可选：新增时无需提供；但一旦提供（含 None），必须是非空字符串
    if "id" in data:
        _validate_id(data["id"])

    return None


def validate_partial(updates):
    """校验编辑时的部分字段，合法返回 None，非法抛出 ValidationError。

    只校验 updates 中出现的字段；不要求所有字段齐全。
    B2 合并旧数据与本函数通过后的字段，再做一次 validate_record 兜底。
    """
    if not isinstance(updates, dict):
        raise ValidationError("更新内容必须是字典")

    unknown = set(updates) - _ALLOWED_FIELDS
    if unknown:
        raise ValidationError(f"更新内容包含未知字段: {', '.join(sorted(unknown))}")

    # 禁止通过编辑改变 id
    if "id" in updates:
        raise ValidationError("不允许修改 id")

    if "type" in updates:
        _validate_type(updates["type"])

    if "date" in updates:
        _validate_date(updates["date"])

    if "amount" in updates:
        _validate_amount(updates["amount"])

    if "category" in updates:
        # 类别合法性依赖 type：若本次未改 type，则无法独立判断，仅校验非空
        _validate_category(updates["category"], record_type=updates.get("type"))

    if "note" in updates:
        _validate_note(updates["note"])

    return None
