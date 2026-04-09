import sys
sys.path.insert(0, ".")

from app.agents.preference_agent import chat

session_id = "test-session-001"

# Start conversation
print("=== PREFERENCE COLLECTION AGENT ===\n")
result = chat(session_id)
print(f"Agent: {result['message']}\n")

# Simulate conversation
responses = [
    "buy",
    "Seattle, WA - Capitol Hill area",
    "$650k to $800k",
    "3 bedrooms",
    "yes",
    "Amazon HQ, Seattle WA",
    "need a garage, no HOA",
    "yes",
]

for user_input in responses:
    print(f"User:  {user_input}")
    result = chat(session_id, user_input)
    print(f"Agent: {result['message']}\n")
    if result["done"]:
        print("=== PROFILE SAVED ===")
        print(result["profile"])
        break