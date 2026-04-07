from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun

llm = ChatAnthropic(model="claude-haiku-4-5")

# ── Tool 1: Calculator ─────────────────────────────────
@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    Use this for any arithmetic calculation.
    Input should be a valid Python math expression like '15 * 47' or '100 / 4'.
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# ── Tool 2: Word counter ───────────────────────────────
@tool
def word_counter(text: str) -> str:
    """
    Count the number of words in a text.
    Use this when asked about word count or text length.
    """
    count = len(text.split())
    return f"{count} words"

# ── Tool 3: Currency converter ─────────────────────────
@tool
def currency_converter(amount_and_currencies: str) -> str:
    """
    Convert between currencies using fixed rates.
    Input format: "100 USD to EUR"
    Supported: USD, EUR, GBP, JPY, CNY
    """
    rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 149.5,
        "CNY": 7.24,
    }
    
    try:
        parts = amount_and_currencies.upper().split()
        amount = float(parts[0])
        from_currency = parts[1]
        to_currency = parts[3]
        
        usd = amount / rates[from_currency]
        result = usd * rates[to_currency]
        return f"{amount} {from_currency} = {result:.2f} {to_currency}"
    except Exception as e:
        return f"Error: {e}"

# Add search tool
search = DuckDuckGoSearchRun()

@tool
def web_search(query: str) -> str:
    """
    Search the web for current information.
    Use this for recent events, current prices, news, 
    or any information that might have changed recently.
    """
    try:
        return search.run(query)
    except Exception as e:
        return f"Search failed: {e}"

# ── Build Agent ────────────────────────────────────────
tools = [calculator, word_counter, currency_converter, web_search]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with access to tools. Use tools when needed."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # 显示推理过程
    max_iterations=5,
)

# ── Test ───────────────────────────────────────────────
questions = [
    "What is 1234567 * 9876543?",  # 上周 LLM 算错的那道题！
    "How many words are in this sentence: The quick brown fox jumps over the lazy dog?",
    "I have 500 EUR, how much is that in JPY?",
    "If I have 1000 USD and convert to EUR, then convert all of it to GBP, how much do I get?",  # 多步推理
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    result = agent_executor.invoke({"input": q})
    # Parse output properly
    output = result['output']
    if isinstance(output, list):
        output = " ".join([o['text'] for o in output if o.get('type') == 'text'])

    print(f"\nFinal Answer: {output}")

# Test with questions requiring real-time info
print("\n\n=== Agent with Web Search ===\n")

realtime_questions = [
    "What is the latest version of Python?",
    "What is 15% tip on a $47.50 restaurant bill?",  # calculator + math
    "Who won the most recent FIFA World Cup?",
]

for q in realtime_questions:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    result = agent_executor.invoke({"input": q})
    output = result['output']
    if isinstance(output, list):
        output = " ".join([o['text'] for o in output if o.get('type') == 'text'])
    print(f"\nFinal Answer: {output}")

print("\n\n=== Complex Multi-Tool Task ===\n")

complex_question = """
I'm planning a trip. I have 2000 GBP budget.
1. How much is that in USD?
2. Search for the current average hotel price in Tokyo per night
3. If hotels cost $150/night, how many nights can I stay with my USD budget?
"""

print(f"Q: {complex_question}")
result = agent_executor.invoke({"input": complex_question})
output = result['output']
if isinstance(output, list):
    output = " ".join([o['text'] for o in output if o.get('type') == 'text'])
print(f"\nFinal Answer: {output}")