"""命令行入口：本地随手验证一句话的返回结果。

用法：
    python -m ecom_cs.cli "我的快递到哪了 2024110001"
    python -m ecom_cs.cli "双11买的衣服7天无理由退货吗"
"""

from __future__ import annotations

import sys

from .service import Session, handle


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    text = " ".join(args).strip() or "我的快递到哪了 2024110001"

    session = Session(order_status="已揽收，预计明日送达")
    result = handle(text, session)

    print(f"用户：{text}")
    print(f"机器人：{result['reply']}")
    print(
        "详情：意图={intent} 转人工={need_human} 引用={sources}".format(
            intent=result["intent"],
            need_human=result["need_human"],
            sources=result["sources"] or "无",
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
