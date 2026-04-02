from fastapi import FastAPI
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from fastapi.responses import StreamingResponse

app = FastAPI()
model = ChatAnthropic(model="claude-haiku-4-5")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | model | StrOutputParser()

# 简单的内存存储（生产里要用 Redis）
sessions = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    # 获取或创建会话历史
    if req.session_id not in sessions:
        sessions[req.session_id] = []
    
    history = sessions[req.session_id]
    
    response = chain.invoke({
        "history": history,
        "input": req.message,
    })
    
    # 更新历史
    history.append(HumanMessage(content=req.message))
    history.append(AIMessage(content=response))
    
    return {
        "reply": response,
        "session_id": req.session_id,
        "turns": len(history) // 2,
    }

@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"message": "会话已清空"}

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    if req.session_id not in sessions:
        sessions[req.session_id] = []
    
    history = sessions[req.session_id]
    
    # 收集完整回复用于存历史
    full_reply = []
    
    async def generate():
        async for chunk in chain.astream({
            "history": history,
            "input": req.message,
        }):
            full_reply.append(chunk)
            yield chunk  # 每生成一个 chunk 就立刻发出去
        
        # 流结束后更新历史
        history.append(HumanMessage(content=req.message))
        history.append(AIMessage(content="".join(full_reply)))
    
    return StreamingResponse(generate(), media_type="text/plain")