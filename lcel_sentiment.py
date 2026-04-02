from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

model = ChatAnthropic(model="claude-haiku-4-5")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你只返回纯 JSON，不要 markdown 格式。"),
    ("human", """分析以下文本的情感：

文本："{text}"

返回格式：
{{"sentiment": "positive/negative/neutral", "confidence": 0.0-1.0, "reason": "原因"}}"""),
])

chain = prompt | model | JsonOutputParser()

# 测试
texts = [
    "今天天气真好，心情棒极了！",
    "这个产品质量太差了。",
    "明天会议在三点开始。",
]

for text in texts:
    result = chain.invoke({"text": text})
    print(f"文本：{text}")
    print(f"结果：{result}\n")