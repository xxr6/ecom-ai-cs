"""追问推荐：回答后引导用户继续提问。

硬性要求（PRD 验收标准第 4 条）：每条推荐都必须是本系统能正确识别的问法，
否则用户点了一下反而得到"转人工"，体验比没有推荐更差。
"""

from __future__ import annotations

from .intent import LOGISTICS, ORDER, REFUND

# 每个意图对应的推荐问法
_SUGGESTIONS: dict[str, list[str]] = {
    LOGISTICS: ["退款多久到账", "物流不更新怎么办", "发票怎么开"],
    ORDER: ["我的快递到哪了", "退款多久到账", "发票怎么开"],
    REFUND: ["退款多久到账", "发票怎么开", "我的订单到哪了"],
}

MAX_SUGGESTIONS = 3


def suggest(intent: str) -> list[str]:
    """返回该意图下的推荐追问，最多 3 条；无匹配时返回空列表。"""
    return list(_SUGGESTIONS.get(intent, []))[:MAX_SUGGESTIONS]
