"""对话编排：意图识别 → 知识检索 → 兜底转人工。

这是整个服务最核心的模块，也是风险最高的地方（CODEOWNERS 里单独列了它）。
改动这里要格外小心：任何"答不出来却硬答"的行为，都会直接伤害商家的商业信任。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import knowledge
from .intent import LOGISTICS, ORDER, REFUND, detect_intent, extract_order_id
from .suggestions import suggest

ASK_ORDER_ID = "麻烦提供一下订单号（8-20 位数字），我帮您查询～"
TRANSFER_TEXT = "这个问题我需要转接人工客服为您处理，请稍等。"

# 检索到知识但分数低于该值时，视为"不可信"，转人工而不是硬答
MIN_KNOWLEDGE_SCORE = 1


@dataclass
class Session:
    """会话上下文：记住用户上一轮给的订单号，避免反复追问。"""

    order_id: str | None = None
    order_status: str | None = None
    history: list[str] = field(default_factory=list)


def _reply(
    text: str,
    intent: str,
    *,
    transfer_to_human: bool = False,
    sources: list[str] | None = None,
    action: str = "answer",
) -> dict[str, Any]:
    # 转人工与追问订单号时不推荐，避免用户被引到别的话题
    followups = [] if transfer_to_human or action != "answer" else suggest(intent)
    return {
        "reply": text,
        "intent": intent,
        "need_human": transfer_to_human,
        "sources": sources or [],
        "action": action,
        "suggestions": followups,
    }


def handle(text: str, session: Session | None = None) -> dict[str, Any]:
    """处理一条用户消息，返回结构化结果。

    返回字段：
        reply       : 回复给用户的话术
        intent      : 识别出的意图
        need_human  : 是否需要转人工
        sources     : 引用到的知识 ID（可追溯，防幻觉）
        action      : 内部动作，便于前端做不同交互（answer / ask_order_id / transfer_human）
    """
    session = session or Session()
    session.history.append(text)

    intent = detect_intent(text)
    order_id = extract_order_id(text) or session.order_id
    if order_id:
        session.order_id = order_id

    # 订单/物流类必须先拿到订单号，否则绝不猜测
    if intent in (ORDER, LOGISTICS) and not order_id:
        return _reply(ASK_ORDER_ID, intent, action="ask_order_id")

    if intent == LOGISTICS:
        status = session.order_status or "已揽收，预计 1-2 天送达"
        return _reply(f"订单 {order_id} 当前物流状态：{status}。", intent)

    if intent == ORDER:
        return _reply(
            f"订单 {order_id} 已为您查询到，如需了解物流进度可以直接问我。",
            intent,
        )

    if intent == REFUND:
        hits = knowledge.search(text)
        if hits and hits[0][1] >= MIN_KNOWLEDGE_SCORE:
            faq = hits[0][0]
            return _reply(faq.answer, intent, sources=[faq.id])
        # 政策类问题检索不到就转人工，不允许模型自由发挥
        return _reply(
            TRANSFER_TEXT, intent, transfer_to_human=True, action="transfer_human"
        )

    answer, sources = knowledge.search_with_sources(text)
    if answer:
        return _reply(answer, intent, sources=sources)

    return _reply(
        TRANSFER_TEXT, intent, transfer_to_human=True, action="transfer_human"
    )
