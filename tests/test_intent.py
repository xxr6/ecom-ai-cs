"""意图识别单测。

测试命名规则：test_<被测行为>_<前提条件>_<期望结果>
读代码的人光看测试名就知道系统承诺了什么。
"""

from ecom_cs.intent import (
    LOGISTICS,
    ORDER,
    OTHER,
    REFUND,
    detect_intent,
    extract_order_id,
)


class TestDetectIntent:
    def test_refund_question_returns_refund(self):
        assert detect_intent("双11买的衣服7天无理由退货吗？") == REFUND

    def test_logistics_question_returns_logistics(self):
        assert detect_intent("我的快递到哪了") == LOGISTICS

    def test_order_question_returns_order(self):
        assert detect_intent("帮我查一下订单") == ORDER

    def test_unrelated_text_returns_other(self):
        assert detect_intent("你们老板是谁") == OTHER

    def test_empty_text_returns_other(self):
        assert detect_intent("   ") == OTHER

    def test_refund_has_priority_over_order_when_both_matched(self):
        # "买了" 命中订单关键词，"无理由" 命中退款关键词，应以退款为准
        assert detect_intent("我买了这个能无理由退吗") == REFUND


class TestExtractOrderId:
    def test_extract_plain_order_id(self):
        assert extract_order_id("订单 2024110001 到哪了") == "2024110001"

    def test_extract_order_id_with_noise(self):
        assert extract_order_id("我的快递到哪了，单号20241100012345谢谢") == "20241100012345"

    def test_no_order_id_returns_none(self):
        assert extract_order_id("我的快递到哪了") is None

    def test_short_number_is_not_order_id(self):
        # 7 位数字不是合法订单号，不能误抓
        assert extract_order_id("我要 1234567 件") is None
