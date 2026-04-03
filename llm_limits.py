from anthropic import Anthropic

client = Anthropic()

def test(question):
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": question}]
    )
    print(f"Q: {question}")
    print(f"A: {response.content[0].text}\n")

# # Test 1: 简单数学
# test("What is 15 * 47?")

# # Test 2: 稍复杂的数学
# test("What is 1234567 * 9876543?")

# # Test 3: 概率计算
# test("If I flip a coin 10 times, what is the exact probability of getting exactly 7 heads?")

# # Test 4: 实时信息
# test("What is the current price of Apple stock?")

# # Test 5: 私有信息
# test("What were the exact sales figures for Anthropic in Q3 2024?")

# 简单计算（15 * 47 = 705）      → 正确 ✓
# 大数乘法（7位数 * 7位数）       → 错误 ✗
# 概率计算（有推理过程）          → 正确 ✓
# 实时信息（股价）               → 正确拒绝 ✓
# 私有信息（Anthropic 财报）      → 正确拒绝 ✓

# 规律：
# LLM 推理过程是对的（概率题的公式、步骤全对）
# LLM 精确计算是不可靠的（大数乘法出错）
# LLM 知道自己的边界（实时信息、私有数据会拒绝）

# question = "Is Python or JavaScript better for backend development? Answer in one sentence."

# print(f"Q: {question}\n")
# for i in range(5):
#     response = client.messages.create(
#         model="claude-haiku-4-5",
#         max_tokens=100,
#         temperature=0,
#         messages=[{"role": "user", "content": question}]
#     )
#     print(f"Run {i+1}: {response.content[0].text.strip()}")


tests = [
    # 众所周知的事实
    "What is the capital of France?",
    
    # 需要推理的问题
    "If all cats are mammals and all mammals are animals, are all cats animals?",
    
    # 知识截止日期
    "What is the latest version of iPhone released in 2025?",
    
    # 需要实时计算的问题
    "How many days until Christmas 2026?",
    
    # 故意刁难：让它承认不确定
    "What did I have for breakfast this morning?",
]

# for q in tests:
#     response = client.messages.create(
#         model="claude-haiku-4-5",
#         max_tokens=150,
#         temperature=0,
#         messages=[{"role": "user", "content": q}]
#     )
#     print(f"Q: {q}")
#     print(f"A: {response.content[0].text.strip()}\n")

#     LLM 擅长的：
# ✓ 语言理解和生成
# ✓ 逻辑推理（三段论、因果推断）
# ✓ 知识问答（训练数据范围内）
# ✓ 结构化信息提取
# ✓ 代码生成
# ✓ 翻译和改写
# ✓ 知道自己不知道什么
# LLM 不擅长的：
# ✗ 精确大数计算（用 Tool 解决）
# ✗ 实时信息（用 RAG / 搜索 Tool 解决）
# ✗ 个人隐私数据（用数据库 Tool 解决）
# ✗ 当前时间感知（传入 datetime 解决）
# ✗ 100% 稳定输出（用 temperature=0 缓解）

# 这就是 Agent + Tool 设计的核心逻辑——LLM 负责推理和规划，Tool 负责弥补它的短板。

text = """
Meeting Notes - Product Review
Date: March 15
Attendees: Sarah (PM), John (Engineering), Lisa (Design)

We discussed the Q2 roadmap. Sarah mentioned the mobile app 
needs a new onboarding flow by April 30th. John said the 
backend API refactor will take 3 weeks and needs 2 engineers. 
Lisa will deliver mockups by March 22nd. Budget concern raised 
- we're 15% over on design costs. Next meeting scheduled for 
March 29th at 2pm.
"""

response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=500,
    temperature=0,
    messages=[{"role": "user", "content": f"""
Extract structured information from these meeting notes.
Return JSON only:
{{
  "date": "...",
  "attendees": [...],
  "action_items": [
    {{"owner": "...", "task": "...", "deadline": "..."}}
  ],
  "risks": [...],
  "next_meeting": "..."
}}

Notes: {text}
"""}]
)
print(response.content[0].text)