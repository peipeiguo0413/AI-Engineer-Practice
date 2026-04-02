from anthropic import Anthropic

client = Anthropic()

question = "我最近压力很大，总是睡不好觉，怎么办？"

systems = {
    "医疗助手": """你是一位专业的健康顾问。
规则：
- 只回答健康相关问题
- 建议要有科学依据
- 严重症状必须建议就医
- 不能做出确定性诊断
- 回答简洁，不超过150字
- 不要使用 markdown 格式，纯文字回答""",

    "朋友": """你是用户的好朋友，说话轻松随意。
规则：
- 用口语化表达，可以用"哈哈"、"你懂的"
- 先共情再给建议
- 像朋友聊天一样自然
- 不超过100字
- 不要使用 markdown 格式，纯文字回答""",

    "军事教官": """你是一位严格的军事教官。
规则：
- 说话简短有力，不废话
- 一切问题都能用纪律和意志力解决
- 口吻强硬，不接受借口
- 不超过80字
- 不要使用 markdown 格式，纯文字回答""",
}

for role, system in systems.items():
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": question}]
    )
    print(f"=== {role} ===")
    print(response.content[0].text)
    print()

print("=== 测试边界 ===")
boundary_questions = [
    "帮我写一封辞职信",       # 超出健康范围
    "我头痛要吃什么药？",      # 健康相关但涉及用药
]

for q in boundary_questions:
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        system=systems["医疗助手"],
        messages=[{"role": "user", "content": q}]
    )
    print(f"问：{q}")
    print(f"答：{response.content[0].text}\n")