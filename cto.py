from anthropic import Anthropic
import json
import re

client = Anthropic()

applicant = {
    "姓名": "李四",
    "月收入": 15000,
    "月支出": 8000,
    "信用评分": 680,
    "申请贷款金额": 200000,
    "贷款期限": 24,
    "现有负债": 20000,
}

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
# 版本一：直接要结论
def approve_direct(data):
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": f"""
审核以下贷款申请，返回JSON：
{{"approved": true/false, "reason": "原因"}}

申请信息：{json.dumps(data, ensure_ascii=False)}
"""}]
    )
    return parse_json(response.content[0].text.strip())

# 版本二：让 AI 先推理再结论
def approve_with_cot(data):
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"""
审核以下贷款申请。

请按步骤分析：
1. 计算每月还款额（贷款金额/期限）
2. 计算债务收入比（月还款+现有负债月供）/月收入
3. 评估信用评分（低于650为风险）
4. 综合判断是否批准

审核规则（必须严格遵守）：
- 信用评分 >= 650 才可批准
- 债务收入比 < 60% 才可批准  
- 月还款额不超过可支配收入（月收入-月支出）的 80%

最后返回JSON：
{{"approved": true/false, "reason": "一句话结论"}}

申请信息：{json.dumps(data, ensure_ascii=False)}
"""}]
    )
    raw = response.content[0].text.strip()
    print(f"AI推理过程：\n{raw}\n")
    # 从推理过程中提取最后的JSON
    match = re.search(r'\{[^{}]*"approved"[^{}]*\}', raw)
    return parse_json(match.group()) if match else None

print("=== 直接结论 ===")
print(approve_direct(applicant))

print("\n=== CoT 推理 ===")
print(approve_with_cot(applicant))