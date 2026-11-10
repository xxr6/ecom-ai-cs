"""知识库检索。

真实项目里这里是向量检索（RAG）：把知识切成片段做 embedding，按相似度召回。
为了让仓库零依赖可运行，这里用"关键词命中数"模拟召回打分，
接口形态与真实检索保持一致（返回带分数的片段列表），将来替换不影响上层编排。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Faq:
    """一条知识。answer 是给用户看的最终话术，不可随意编造。"""

    id: str
    question: str
    answer: str
    keywords: tuple[str, ...]


FAQ_LIST: tuple[Faq, ...] = (
    Faq(
        id="refund-7days",
        question="7 天无理由退货",
        answer="支持 7 天无理由退货，商品需不影响二次销售，退货运费由买家承担。",
        keywords=("无理由", "退货", "7天"),
    ),
    Faq(
        id="refund-process",
        question="退款多久到账",
        answer="退货签收后 1-3 个工作日原路退回，银行卡到账可能再延迟 1-2 天。",
        keywords=("退款", "到账", "多久"),
    ),
    Faq(
        id="logistics-delay",
        question="物流长时间不更新",
        answer="物流超过 48 小时未更新，可联系在线客服为您催单，我们会跟进快递方。",
        keywords=("物流", "不更新", "没动"),
    ),
    Faq(
        id="invoice",
        question="发票怎么开",
        answer="下单时可勾选电子发票，已完成订单可在「我的订单-申请开票」补开。",
        keywords=("发票", "开票"),
    ),
)


def search(text: str, top_k: int = 1) -> list[tuple[Faq, int]]:
    """按关键词命中数召回，返回 [(知识, 分数)]，分数降序。

    分数为 0 的知识不返回——"没检索到"比"硬凑一条"更安全，
    因为客服场景里答错比答不上更伤商业信任。
    """
    scored: list[tuple[Faq, int]] = []
    for faq in FAQ_LIST:
        score = sum(1 for keyword in faq.keywords if keyword in (text or ""))
        if score > 0:
            scored.append((faq, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k]


def search_with_sources(text: str, top_k: int = 1) -> tuple[str, list[str]]:
    """便捷方法：直接拿到「答案文本 + 引用来源 ID」。"""
    hits = search(text, top_k=top_k)
    if not hits:
        return "", []
    faq = hits[0][0]
    return faq.answer, [faq.id for faq, _ in hits]
