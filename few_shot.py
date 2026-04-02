from anthropic import Anthropic
import json
import re

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

# 客服工单分类，priority 有公司自己的定义
def classify_ticket_no_example(text):
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": f"""
将以下客服工单分类，返回JSON：
{{"priority": "P0/P1/P2/P3", "category": "类别", "reason": "原因"}}

工单："{text}"
"""}]
    )
    return parse_json(response.content[0].text.strip())

def classify_ticket_with_example(text):
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[
            {"role": "user", "content": '分类工单："系统完全无法登录，影响全部用户"'},
            {"role": "assistant", "content": '{"priority":"P0","category":"系统故障","reason":"影响全量用户"}'},
            {"role": "user", "content": '分类工单："我的头像上传失败"'},
            {"role": "assistant", "content": '{"priority":"P2","category":"功能异常","reason":"影响单用户非核心功能"}'},
            {"role": "user", "content": '分类工单："能不能加一个夜间模式"'},
            {"role": "assistant", "content": '{"priority":"P3","category":"需求建议","reason":"新功能请求不影响使用"}'},
            {"role": "user", "content": f'分类工单："{text}"'},
        ]
    )
    return parse_json(response.content[0].text.strip())

# 测试同一批工单
tickets = [
    "支付功能报错，用户无法完成购买",
    "页面字体能不能改大一点",
    "数据全部丢失了！！！",
]

print("=== 无 few-shot ===")
for t in tickets:
    r = classify_ticket_no_example(t)
    print(f"{r['priority']} | {r['category']} | {t[:15]}...")

print("\n=== 有 few-shot ===")
for t in tickets:
    r = classify_ticket_with_example(t)
    print(f"{r['priority']} | {r['category']} | {t[:15]}...")