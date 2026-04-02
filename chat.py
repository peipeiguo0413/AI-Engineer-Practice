from anthropic import Anthropic

client = Anthropic()
history = []
MAX_TURNS = 3

def chat(user_input):
    history.append({"role": "user", "content": user_input})
    
    recent = history[-(MAX_TURNS * 2):]
    if recent and recent[0]["role"] == "assistant":
        recent = recent[1:]
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system="你是一个友好的助手。",
        messages=recent
    )
    
    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    
    # 打印 token 使用情况
    u = response.usage
    total_cost = (u.input_tokens * 0.000003) + (u.output_tokens * 0.000015)
    print(f"  [输入 {u.input_tokens} | 输出 {u.output_tokens} | 本次约 ${total_cost:.5f}]")
    
    return reply

if __name__ == "__main__":
    print("开始对话（quit 退出 / clear 清空历史）\n")
    while True:
        user_input = input("你: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "clear":
            history.clear()
            print("历史已清空\n")
            continue
        reply = chat(user_input)
        print(f"AI: {reply}\n")