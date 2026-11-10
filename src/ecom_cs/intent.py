"""意图识别。

真实项目里这一步通常由大模型分类器完成，这里先用关键词规则实现，
保证零依赖、可测试；后续替换为大模型时，只需保持 detect_intent 的函数签名不变。
"""

from __future__ import annotations

import re

# 意图常量：用常量而不用裸字符串，避免拼写错误导致逻辑分支失效
ORDER = "order_query"
LOGISTICS = "logistics"
REFUND = "refund"
OTHER = "other"

# 订单号：8~20 位连续数字，前后不能再接数字（避免从长串里截错）
_ORDER_ID_RE = re.compile(r"(?<!\d)(\d{8,20})(?!\d)")

# 判定顺序有讲究：先判退款，再判物流，最后判订单。
# 因为"无理由退货"这类句子同时含"买了"，必须让退款优先级更高。
_KEYWORDS: dict[str, tuple[str, ...]] = {
    REFUND: ("退货", "退款", "换货", "无理由"),
    LOGISTICS: ("快递", "物流", "到哪", "发货", "签收", "配送"),
    ORDER: ("订单", "下单", "买了", "购买记录", "付款"),
}


def detect_intent(text: str) -> str:
    """返回 text 对应的意图。无法识别时返回 OTHER。"""
    if not text or not text.strip():
        return OTHER
    for intent in (REFUND, LOGISTICS, ORDER):
        if any(keyword in text for keyword in _KEYWORDS[intent]):
            return intent
    return OTHER


def extract_order_id(text: str) -> str | None:
    """从用户输入里抽取订单号，没有则返回 None。"""
    match = _ORDER_ID_RE.search(text or "")
    return match.group(1) if match else None
