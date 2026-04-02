# AI Agent Learning

Small Python scripts that call the [Anthropic API](https://docs.anthropic.com/) (`anthropic` SDK).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
```

## Scripts

| File | Description |
|------|-------------|
| `chat.py` | Simple REPL chat with history |
| `sentiment.py` | Sentiment analysis via structured JSON |
| `few_shot.py` | Few-shot style prompting |
| `cto.py` | CTO-style review / approval flow |
| `system_prompt.py` | System prompt experiments |

Do not commit API keys; use environment variables only.
