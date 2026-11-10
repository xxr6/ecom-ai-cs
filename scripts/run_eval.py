"""AI 评测集跑分脚本。

作用：每次改 Prompt / 检索策略 / 话术后，用同一套真实问题跑一遍，
用数字判断"这次改动是变好还是变坏"，而不是凭感觉。

用法：
    python scripts/run_eval.py                 # 默认合格率门槛 85%
    python scripts/run_eval.py --min-pass 0.9  # CI 里收紧门槛
    python scripts/run_eval.py -v              # 打印每题详情
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ecom_cs.service import Session, handle  # noqa: E402

CASES_PATH = ROOT / "tests" / "eval" / "cases.jsonl"


def load_cases(path: Path) -> list[dict]:
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))
    return cases


def check_case(case: dict) -> tuple[bool, list[str]]:
    result = handle(case["question"], Session(order_status="已揽收，预计明日送达"))
    reply = result["reply"]
    problems: list[str] = []

    for keyword in case.get("must_include", []):
        if keyword not in reply:
            problems.append(f"缺少关键内容「{keyword}」")

    for keyword in case.get("must_not_include", []):
        if keyword in reply:
            problems.append(f"出现禁止内容「{keyword}」")

    if "expect_human" in case and result["need_human"] != case["expect_human"]:
        problems.append(f"转人工判定错误（期望 {case['expect_human']}，实际 {result['need_human']}）")

    return (not problems), problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-pass", type=float, default=0.85, help="合格率门槛，默认 0.85")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    cases = load_cases(CASES_PATH)
    if not cases:
        print("评测集为空，请检查 tests/eval/cases.jsonl")
        return 1

    failed: list[tuple[str, list[str]]] = []
    for case in cases:
        ok, problems = check_case(case)
        mark = "PASS" if ok else "FAIL"
        if args.verbose or not ok:
            print(f"[{mark}] {case['id']}  {case['question']}")
            for problem in problems:
                print(f"       - {problem}")
        if not ok:
            failed.append((case["id"], problems))

    total = len(cases)
    passed = total - len(failed)
    rate = passed / total
    print("-" * 52)
    print(f"共 {total} 题 | 通过 {passed} | 合格率 {rate:.0%} | 门槛 {args.min_pass:.0%}")

    if rate < args.min_pass:
        print("结论：低于门槛，本次改动不允许合并。")
        return 1
    print("结论：达标，可以进入评审。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
