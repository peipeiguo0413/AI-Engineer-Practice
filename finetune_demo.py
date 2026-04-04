from anthropic import Anthropic

client = Anthropic()

# Scenario: A company needs responses in very specific style
# "Friendly, use emojis, always end with a question, max 2 sentences"

STYLE_GUIDE = """
You are a customer service agent for a trendy tech startup.
Rules:
- Always use 1-2 emojis
- Maximum 2 sentences
- End with a question
- Tone: friendly and casual
"""

test_questions = [
    "My order hasn't arrived yet",
    "How do I reset my password?",
    "I want a refund",
    "Your app keeps crashing",
]

# print("=== With Style Prompt ===\n")
# for q in test_questions:
#     response = client.messages.create(
#         model="claude-haiku-4-5",
#         max_tokens=100,
#         temperature=0,
#         system=STYLE_GUIDE,
#         messages=[{"role": "user", "content": q}]
#     )
#     print(f"Q: {q}")
#     print(f"A: {response.content[0].text}\n")

    # Add to finetune_demo.py

print("\n=== Stress Test: Edge Cases ===\n")

edge_cases = [
    # Emotional customer
    "I've been waiting 3 months and nobody helps me, I want to speak to a manager RIGHT NOW and I'm going to leave a 1-star review everywhere!!!",
    
    # Technical complex question
    "Can you explain the difference between OAuth 2.0 and JWT token authentication and which one your API uses?",
    
    # Very short
    "help",
    
    # Multiple questions
    "Where is my order? Also can I change the delivery address? And do you have a loyalty program?",
]

for q in edge_cases:
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=150,
        temperature=0,
        system=STYLE_GUIDE,
        messages=[{"role": "user", "content": q}]
    )
    answer = response.content[0].text
    
    # Count sentences and emojis
    sentences = [s.strip() for s in answer.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    emoji_count = sum(1 for c in answer if ord(c) > 127)
    ends_with_question = answer.strip().endswith('?')
    
    print(f"Q: {q[:60]}...")
    print(f"A: {answer}")
    print(f"  Sentences: {len(sentences)} | Emojis: {emoji_count} | Ends with ?: {ends_with_question}")
    print()