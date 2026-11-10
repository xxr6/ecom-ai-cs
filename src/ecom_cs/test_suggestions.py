"""追问推荐测试：数量、相关性、以及"点了能答"的闭环校验。"""

from ecom_cs.intent import LOGISTICS, OTHER, REFUND
from ecom_cs.service import handle
from ecom_cs.suggestions import MAX_SUGGESTIONS, suggest


class TestSuggest:
    def test_logistics_intent_returns_at_most_three(self):
        items = suggest(LOGISTICS)
        assert 1 <= len(items) <= MAX_SUGGESTIONS

    def test_other_intent_returns_empty(self):
        assert suggest(OTHER) == []

    def test_every_suggestion_can_be_answered(self):
        # 闭环校验：推荐的话术点下去必须能得到答案，而不是被转人工
        # 判定标准是"不需要转人工"，而不是"检测出某个意图"——
        # 像"发票怎么开"这类问题意图是 other，但知识库能答，同样算闭环。
        for intent in (LOGISTICS, REFUND):
            for item in suggest(intent):
                result = handle(item)
                assert result["need_human"] is False, f"推荐语点了答不上：{item}"


class TestServiceIntegration:
    def test_answer_carries_suggestions(self):
        result = handle("双11买的衣服7天无理由退货吗？")
        assert result["suggestions"]
        assert len(result["suggestions"]) <= 3

    def test_transfer_to_human_has_no_suggestions(self):
        result = handle("你们老板是谁")
        assert result["need_human"] is True
        assert result["suggestions"] == []
