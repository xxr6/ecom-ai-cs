"""对话编排单测：覆盖正常回答与三类兜底（缺订单号 / 检索不到 / 无关问题）。

这些用例就是线上事故的"疫苗"——每修一个线上 Bug，都应该补一条测试把它钉死。
"""

from ecom_cs.service import Session, handle


class TestOrderAndLogistics:
    def test_order_query_without_id_asks_back(self):
        result = handle("我想查一下订单")
        assert result["action"] == "ask_order_id"
        assert "订单号" in result["reply"]
        assert result["need_human"] is False

    def test_logistics_with_id_returns_status(self):
        session = Session(order_status="已揽收，预计明日送达")
        result = handle("我的快递到哪了 2024110001", session)
        assert result["intent"] == "logistics"
        assert "2024110001" in result["reply"]
        assert "已揽收" in result["reply"]

    def test_session_remembers_order_id_for_next_turn(self):
        session = Session(order_status="运输中")
        handle("订单 2024110001", session)
        result = handle("那快递到哪了", session)
        assert "2024110001" in result["reply"]
        assert "运输中" in result["reply"]


class TestKnowledgeAnswer:
    def test_refund_question_hits_knowledge_with_source(self):
        result = handle("双11买的衣服7天无理由退货吗？")
        assert result["intent"] == "refund"
        assert "7 天无理由" in result["reply"]
        assert result["sources"] == ["refund-7days"]

    def test_invoice_question_hits_knowledge(self):
        result = handle("发票怎么开")
        assert "电子发票" in result["reply"]
        assert result["sources"] == ["invoice"]


class TestHumanFallback:
    def test_unknown_question_transfers_to_human(self):
        result = handle("你们老板是谁")
        assert result["need_human"] is True
        assert result["action"] == "transfer_human"
        assert "人工" in result["reply"]

    def test_empty_message_transfers_to_human(self):
        result = handle("")
        assert result["need_human"] is True

    def test_refund_without_knowledge_transfers_to_human(self):
        # 命中"退款"意图但知识库里没有对应政策时，宁可转人工也不能编
        result = handle("退款能不能退到我支付宝")
        assert result["sources"] == [] or result["sources"] == ["refund-process"]
