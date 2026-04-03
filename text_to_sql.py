import sqlite3
import pandas as pd
from anthropic import Anthropic

client = Anthropic()

# ── 创建示例数据库 ─────────────────────────────────────
conn = sqlite3.connect(":memory:")  # 内存数据库，不需要文件

# 创建表
conn.executescript("""
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT,
    city TEXT,
    age INTEGER,
    joined_date TEXT
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product TEXT,
    amount FLOAT,
    order_date TEXT,
    status TEXT
);

INSERT INTO customers VALUES
(1, 'Alice', 'New York', 28, '2022-03-15'),
(2, 'Bob', 'London', 35, '2021-07-22'),
(3, 'Carol', 'New York', 42, '2023-01-10'),
(4, 'David', 'Paris', 31, '2022-11-05'),
(5, 'Eve', 'London', 26, '2023-06-18');

INSERT INTO orders VALUES
(1, 1, 'Laptop', 1200.00, '2024-01-15', 'completed'),
(2, 1, 'Mouse', 45.00, '2024-02-20', 'completed'),
(3, 2, 'Keyboard', 89.00, '2024-01-08', 'completed'),
(4, 3, 'Monitor', 350.00, '2024-03-01', 'pending'),
(5, 3, 'Laptop', 1200.00, '2024-02-14', 'completed'),
(6, 4, 'Headphones', 199.00, '2024-01-25', 'completed'),
(7, 5, 'Mouse', 45.00, '2024-03-10', 'shipped'),
(8, 2, 'Monitor', 350.00, '2024-02-28', 'completed');
""")

# ── Schema 描述（告诉 LLM 数据库结构）────────────────────
SCHEMA = """
Tables:
1. customers(id, name, city, age, joined_date)
2. orders(id, customer_id, product, amount, order_date, status)
   - status: 'completed', 'pending', 'shipped'
   - customer_id references customers.id
"""

def text_to_sql(question: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        temperature=0,
        messages=[{"role": "user", "content": f"""
Given this database schema:
{SCHEMA}

Convert this question to SQL. Return only the SQL query, no explanation.

Question: {question}
"""}]
    )
    sql = response.content[0].text.strip()
    
    # Clean markdown wrapper
    if sql.startswith("```"):
        sql = sql.split("```")[1]
        if sql.startswith("sql"):
            sql = sql[3:]
    
    return sql.strip()

def ask_database(question: str):
    print(f"Q: {question}")
    
    # Step 1: Generate SQL
    sql = text_to_sql(question)
    print(f"SQL: {sql}")
    
    # Step 2: Execute SQL
    try:
        df = pd.read_sql_query(sql, conn)
        print(f"Result:\n{df.to_string()}\n")
        return df
    except Exception as e:
        print(f"Error: {e}\n")
        return None

# Test questions
ask_database("Which city has the most customers?")
ask_database("What is the total revenue by product?")
ask_database("Who are the top 3 customers by total spending?")
ask_database("How many orders are pending or shipped?")

def ask_database_with_answer(question: str):
    print(f"Q: {question}")
    
    # Step 1: Generate SQL
    sql = text_to_sql(question)
    
    # Step 2: Execute SQL
    try:
        df = pd.read_sql_query(sql, conn)
        
        # Step 3: Generate natural language answer
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            temperature=0,
            messages=[{"role": "user", "content": f"""
Answer this question in one clear sentence based on the data.

Question: {question}
Data: {df.to_string()}
"""}]
        )
        print(f"A: {response.content[0].text.strip()}\n")
        
    except Exception as e:
        print(f"Error: {e}\n")

# Test
ask_database_with_answer("Which city has the most customers?")
ask_database_with_answer("What is the total revenue by product?")
ask_database_with_answer("Who are the top 3 customers by total spending?")

# 在 text_to_sql.py 末尾加上

print("\n\n=== Auto Analysis Report ===\n")

# 收集关键数据
queries = {
    "total_revenue": "SELECT SUM(amount) as total FROM orders WHERE status='completed'",
    "top_product": "SELECT product, SUM(amount) as revenue FROM orders GROUP BY product ORDER BY revenue DESC LIMIT 1",
    "top_city": "SELECT city, COUNT(*) as count FROM customers GROUP BY city ORDER BY count DESC LIMIT 1",
    "pending_orders": "SELECT COUNT(*) as count FROM orders WHERE status != 'completed'",
}

data_summary = {}
for key, sql in queries.items():
    df = pd.read_sql_query(sql, conn)
    data_summary[key] = df.to_dict(orient="records")[0]

print("Raw data collected:")
for k, v in data_summary.items():
    print(f"  {k}: {v}")

# LLM 生成分析报告
response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=400,
    temperature=0,
    messages=[{"role": "user", "content": f"""
You are a business analyst. Write a concise executive summary (3-4 sentences) 
based on this e-commerce data. Highlight key insights and one recommendation.

Data:
{data_summary}
"""}]
)

print(f"\nExecutive Summary:\n{response.content[0].text}")