from anthropic import Anthropic

client = Anthropic()

review = """
I've been using this laptop for 3 months. The battery life is 
disappointing, only lasting 4 hours. The keyboard feels cheap. 
However, the display is absolutely stunning and the performance 
is blazing fast. Customer service was helpful when I had questions.
"""

# Version A：模糊 prompt
def version_a(text):
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        temperature=0,
        messages=[{"role": "user", "content": f"Analyze this review: {text}"}]
    )
    return response.content[0].text

# Version B：结构化 prompt
def version_b(text):
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        temperature=0,
        messages=[{"role": "user", "content": f"""
Analyze this product review and return JSON only:
{{
  "overall_sentiment": "positive/negative/mixed",
  "score": 1-10,
  "pros": ["..."],
  "cons": ["..."],
  "would_recommend": true/false
}}

Review: {text}
"""}]
    )
    return response.content[0].text

# Version C：加上 few-shot + 规则
def version_c(text):
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        temperature=0,
        messages=[
            {"role": "user", "content": """
Analyze this review and return JSON only.
Rules:
- score 1-10 based on overall sentiment
- pros/cons must be specific, not generic
- would_recommend is true only if score >= 7

Review: "Perfect laptop, battery lasts 12 hours, super fast!"
"""},
            {"role": "assistant", "content": '{"overall_sentiment":"positive","score":9,"pros":["12-hour battery","fast performance"],"cons":[],"would_recommend":true}'},
            {"role": "user", "content": f"""
Analyze this review and return JSON only.
Rules:
- score 1-10 based on overall sentiment
- pros/cons must be specific, not generic  
- would_recommend is true only if score >= 7

Review: {text}
"""}
        ]
    )
    return response.content[0].text

print("=== Version A (vague) ===")
print(version_a(review))

print("\n=== Version B (structured) ===")
print(version_b(review))

print("\n=== Version C (few-shot + rules) ===")
print(version_c(review))