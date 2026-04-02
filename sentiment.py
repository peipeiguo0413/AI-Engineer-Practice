import json
import re
from anthropic import Anthropic

client = Anthropic()

def parse_json(raw):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    
    # print(f"清洗后：{repr(cleaned)}")
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # 用正则直接提取三个字段，跳过 JSON 解析
        sentiment = re.search(r'"sentiment"\s*:\s*"(\w+)"', cleaned)
        confidence = re.search(r'"confidence"\s*:\s*([\d.]+)', cleaned)
        reason = re.search(r'"reason"\s*:\s*"(.+?)"(?:\s*})', cleaned, re.DOTALL)
        
        return {
            "sentiment": sentiment.group(1) if sentiment else "unknown",
            "confidence": float(confidence.group(1)) if confidence else 0.0,
            "reason": reason.group(1) if reason else "解析失败"
        }

def analyze(text):
    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": f"""分析以下文本的情感，只返回纯 JSON，不要用 markdown 代码块包裹，不要任何其他文字：

    文本："{text}"

    返回格式：
    {{
    "sentiment": "positive" 或 "negative" 或 "neutral",
    "confidence": 0到1之间的小数,
    "reason": "一句话说明原因"
    }}"""
            }]
        )
        
        raw = response.content[0].text.strip()
        # print(f"原始返回：{repr(raw)}") 
        return parse_json(raw)
    except Exception as e:
        print(f"报错类型：{type(e).__name__}")
        print(f"报错信息：{e}")
        return None

# 测试几句话
tests = [
    "今天天气真好，心情棒极了！",
    "这个产品质量太差了，完全是浪费钱。",
    "明天会议在三点开始。",
]

for text in tests:
    result = analyze(text)
    print(f"文本：{text}")
    print(f"结果：{result}\n")