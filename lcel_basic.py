from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

model = ChatAnthropic(model="claude-haiku-4-5")

# 第一步：定义 prompt 模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，回答要简洁，不要使用 markdown 格式，纯文字回答。"),
    ("human", "{question}"),
])

# 第二步：用 | 把三个组件串起来
chain = prompt | model | JsonOutputParser()

# 第三步：调用
result = chain.invoke({
    "role": "军事教官",
    "question": "睡不好觉怎么办？"
})

print(result)