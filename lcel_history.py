from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

model = ChatAnthropic(model="claude-haiku-4-5")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的助手。"),
    MessagesPlaceholder(variable_name="history"),  # 历史记录占位符
    ("human", "{input}"),
])

chain = prompt | model | StrOutputParser()

# 手动维护历史（原理和 Week 1 完全一样）
history = []

def chat(user_input):
    response = chain.invoke({
        "history": history,
        "input": user_input,
    })
    
    # 更新历史
    history.append(HumanMessage(content=user_input))
    history.append(AIMessage(content=response))
    
    print(f"  [历史 {len(history)} 条]")
    return response

# 测试
print(chat("我叫小明"))
print(chat("我叫什么名字？"))