# LLM Learning Journey

## Week 1 - 原生 API 基础

- 多轮对话 + 记忆管理
- Token 成本控制
- 结构化输出 + 防御性解析

## Week 2 - Prompt 工程

- Few-shot：客服工单分类
- Chain-of-Thought：贷款审批
- System Prompt：角色与边界控制

## 技术栈

- Python 3
- [Anthropic Messages API](https://docs.anthropic.com/)（`anthropic` SDK）

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
```

示例脚本：`chat.py`、`sentiment.py`、`few_shot.py`、`cto.py`、`system_prompt.py`。请勿将 API Key 提交到仓库。
