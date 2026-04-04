from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
import operator
from langgraph.graph import StateGraph, END
from typing import Literal


llm = ChatAnthropic(model="claude-haiku-4-5")

# ── State definition ───────────────────────────────────
# State is shared across all nodes in the graph
class ResearchState(TypedDict):
    topic: str                    # research topic
    research: str                 # raw research notes
    summary: str                  # final summary
    messages: Annotated[list, operator.add]  # conversation history

# ── Node 1: Researcher ─────────────────────────────────
def researcher(state: ResearchState) -> ResearchState:
    print("  [Researcher] Gathering information...")
    
    response = llm.invoke([
        HumanMessage(content=f"""
You are a researcher. Generate detailed research notes about: {state['topic']}
Include key facts, statistics, and important points.
Write 3-4 paragraphs.
""")
    ])
    
    return {
        "research": response.content,
        "messages": [AIMessage(content=f"Research completed: {response.content[:100]}...")]
    }

# ── Node 2: Summarizer ─────────────────────────────────
def summarizer(state: ResearchState) -> ResearchState:
    print("  [Summarizer] Creating summary...")
    
    response = llm.invoke([
        HumanMessage(content=f"""
You are an editor. Create a concise 3-bullet summary from these research notes:

{state['research']}

Format:
- Key point 1
- Key point 2  
- Key point 3
""")
    ])
    
    return {
        "summary": response.content,
        "messages": [AIMessage(content=f"Summary completed")]
    }

# ── Build graph ────────────────────────────────────────
workflow = StateGraph(ResearchState)

# Add nodes
workflow.add_node("researcher", researcher)
workflow.add_node("summarizer", summarizer)

# Add edges (define flow)
workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "summarizer")
workflow.add_edge("summarizer", END)

# Compile
graph = workflow.compile()

# ── Run ────────────────────────────────────────────────
print("=== LangGraph: Research Pipeline ===\n")

result = graph.invoke({
    "topic": "The impact of LLMs on software engineering jobs",
    "research": "",
    "summary": "",
    "messages": [],
})

print(f"Topic: {result['topic']}\n")
print(f"Research Preview: {result['research'][:200]}...\n")
print(f"Summary:\n{result['summary']}")


# ── New State ──────────────────────────────────────────
class QAState(TypedDict):
    topic: str
    draft: str
    feedback: str
    approved: bool
    revision_count: int
    messages: Annotated[list, operator.add]

# ── Node: Writer ───────────────────────────────────────
def writer(state: QAState) -> QAState:
    print(f"  [Writer] Writing draft (revision {state['revision_count'] + 1})...")
    
    # Include feedback if revising
    feedback_prompt = ""
    if state.get("feedback"):
        feedback_prompt = f"\nPrevious feedback to address: {state['feedback']}"
    
    response = llm.invoke([HumanMessage(content=f"""
Write a short 2-paragraph article about: {state['topic']}
Be concise and informative.{feedback_prompt}
""")])
    
    return {
        "draft": response.content,
        "revision_count": state["revision_count"] + 1,
        "messages": [AIMessage(content=f"Draft {state['revision_count'] + 1} completed")]
    }

# ── Node: Reviewer ─────────────────────────────────────
def reviewer(state: QAState) -> QAState:
    print(f"  [Reviewer] Reviewing draft...")
    
    response = llm.invoke([HumanMessage(content=f"""
Review this article and decide if it's good enough to publish.
Be strict - only approve if it's clear, informative, and well-structured.

Article:
{state['draft']}

Return JSON only:
{{"approved": true/false, "feedback": "specific feedback if not approved"}}
""")])
    
    import json, re
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw.strip())
    
    return {
        "approved": result["approved"],
        "feedback": result.get("feedback", ""),
        "messages": [AIMessage(content=f"Review: {'approved' if result['approved'] else 'needs revision'}")]
    }

# ── Conditional edge function ──────────────────────────
def should_continue(state: QAState) -> Literal["writer", END]:
    # Max 3 revisions to avoid infinite loop
    if state["approved"] or state["revision_count"] >= 3:
        return END
    return "writer"

# ── Build graph with conditional edge ─────────────────
qa_workflow = StateGraph(QAState)

qa_workflow.add_node("writer", writer)
qa_workflow.add_node("reviewer", reviewer)

qa_workflow.set_entry_point("writer")
qa_workflow.add_edge("writer", "reviewer")
qa_workflow.add_conditional_edges("reviewer", should_continue)

qa_graph = qa_workflow.compile()

# ── Run ────────────────────────────────────────────────
print("\n\n=== LangGraph: Writer + Reviewer with Feedback Loop ===\n")

qa_result = qa_graph.invoke({
    "topic": "Why Python is great for AI development",
    "draft": "",
    "feedback": "",
    "approved": False,
    "revision_count": 0,
    "messages": [],
})

print(f"Total revisions: {qa_result['revision_count']}")
print(f"Approved: {qa_result['approved']}")
print(f"\nFinal Draft:\n{qa_result['draft']}")

# Force at least one revision by making reviewer stricter
def strict_reviewer(state: QAState) -> QAState:
    print(f"  [Strict Reviewer] Reviewing draft...")
    
    response = llm.invoke([HumanMessage(content=f"""
You are a very strict editor. Review this article harshly.
Only approve if it has: specific examples, statistics, and actionable insights.
Reject the first draft almost always.

Article:
{state['draft']}

Return JSON only:
{{"approved": true/false, "feedback": "specific detailed feedback"}}
""")])
    
    import json, re
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw.strip())
    
    print(f"  Decision: {'approved' if result['approved'] else 'needs revision - ' + result['feedback'][:80]}")
    
    return {
        "approved": result["approved"],
        "feedback": result.get("feedback", ""),
        "messages": [AIMessage(content=f"Review: {'approved' if result['approved'] else 'needs revision'}")]
    }

# Rebuild with strict reviewer
strict_workflow = StateGraph(QAState)
strict_workflow.add_node("writer", writer)
strict_workflow.add_node("reviewer", strict_reviewer)
strict_workflow.set_entry_point("writer")
strict_workflow.add_edge("writer", "reviewer")
strict_workflow.add_conditional_edges("reviewer", should_continue)
strict_graph = strict_workflow.compile()

print("\n\n=== Strict Reviewer: Forces Multiple Revisions ===\n")

strict_result = strict_graph.invoke({
    "topic": "Best practices for deploying LLMs in production",
    "draft": "",
    "feedback": "",
    "approved": False,
    "revision_count": 0,
    "messages": [],
})

print(f"\nTotal revisions: {strict_result['revision_count']}")
print(f"Approved: {strict_result['approved']}")
print(f"\nMessage history:")
for msg in strict_result['messages']:
    print(f"  - {msg.content}")