# ecom-ai-cs · 电商 AI 客服（企业流程演练版）

一个**可以真跑起来**的最小电商 AI 客服服务，同时是一个**企业级开发流程的练习场**。

> 目的不是做一个完整产品，而是让你在一个真实仓库里，把「领需求 → 拉分支 → 提交 → PR → CI → 评审 → 合并 → 发布 → 线上救火」全流程亲手走一遍。

## 快速开始

```bash
pip install -r requirements.txt
pytest -q                          # 跑测试（当前 18 个用例）
python scripts/run_eval.py         # 跑 AI 评测集（10 题，合格率门槛 85%）
python chat.py "我的快递到哪了 2024110001"   # 手动试一句
```

无需创建虚拟环境也能跑；建议仍然用 venv 隔离依赖：

```bash
python -m venv .venv && source .venv/Scripts/activate
```

## 目录结构

```
ecom-ai-cs/
├── .github/
│   ├── workflows/ci.yml              # CI 流水线（push/PR 自动跑测试）
│   ├── ISSUE_TEMPLATE/               # 需求 / Bug 模板（= Backlog 卡片格式）
│   ├── pull_request_template.md      # PR 自查清单
│   └── CODEOWNERS                    # 代码归属，谁必须评审
├── src/ecom_cs/
│   ├── intent.py                     # 意图识别（规则优先，可换大模型）
│   ├── knowledge.py                  # 知识库检索（模拟 RAG 的召回）
│   ├── service.py                    # 对话编排 + 转人工兜底
│   └── cli.py                        # 命令行入口，方便手动验证
├── tests/                            # 单元测试（CI 会跑）
│   └── eval/cases.jsonl              # AI 评测集（带标准答案）
├── scripts/run_eval.py               # 评测跑分脚本
├── docs/
│   ├── adr/                          # 架构决策记录（为什么这么选）
│   ├── prd/                          # 需求文档
│   ├── runbook.md                    # 线上值班/应急手册
│   └── onboarding/                   # 新人上手，含流程演练手册
├── CONTRIBUTING.md                   # 开发规范（分支/提交/PR 规则）
├── Makefile
└── pyproject.toml
```

## 分支模型

| 分支 | 用途 | 谁能合入 |
|------|------|---------|
| `main` | 生产分支，每次提交都可发布，打 tag | 仅通过 PR + 评审 |
| `develop` | 集成分支，日常功能先合这里 | 通过 PR + CI |
| `feature/*` | 功能分支，如 `feature/followup-suggest` | 作者自己 |
| `hotfix/*` | 线上紧急修复，从 main 拉 | 快速评审后合 main |

## 核心规则（详见 CONTRIBUTING.md）

1. 不许直接 push `main` / `develop`
2. 所有改动走 PR，CI 绿灯 + 至少 1 人批准才可合并
3. 提交信息遵循 Conventional Commits：`feat(chat): xxx`
4. 核心模块（`src/ecom_cs/service.py`）改动需 CODEOWNERS 指定人评审
5. 紧急故障走 hotfix 通道，事后必须补登 Issue
