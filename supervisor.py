from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langgraph.types import Command
import operator
import json


llm = ChatAnthropic(model="claude-haiku-4-5")

# ── State ──────────────────────────────────────────────
class TeamState(TypedDict):
    task: str
    research: str
    code: str
    report: str
    next_agent: str
    messages: Annotated[list, operator.add]

# ── Worker Agent 1: Researcher ─────────────────────────
def researcher_agent(state: TeamState) -> TeamState:
    print("  [Researcher] Working...")
    
    response = llm.invoke([HumanMessage(content=f"""
Research this topic and provide key facts and insights:
{state['task']}

Be concise, 2-3 paragraphs.
""")])
    
    return {
        "research": response.content,
        "messages": [AIMessage(content=f"Researcher: completed research")]
    }

# ── Worker Agent 2: Coder ──────────────────────────────
def coder_agent(state: TeamState) -> TeamState:
    print("  [Coder] Working...")
    
    response = llm.invoke([HumanMessage(content=f"""
Based on this context, write a simple Python code example:
Task: {state['task']}
Research: {state['research']}

Write clean, commented code with a brief explanation.
""")])
    
    return {
        "code": response.content,
        "messages": [AIMessage(content=f"Coder: completed code example")]
    }

# ── Worker Agent 3: Report Writer ─────────────────────
def writer_agent(state: TeamState) -> TeamState:
    print("  [Writer] Working...")
    
    response = llm.invoke([HumanMessage(content=f"""
Write a concise technical report combining:
Task: {state['task']}
Research: {state['research']}
Code Example: {state['code']}

Structure: Brief intro, key findings, code walkthrough, conclusion.
Keep it under 300 words.
""")])
    
    return {
        "report": response.content,
        "messages": [AIMessage(content=f"Writer: completed report")]
    }

# ── Supervisor ─────────────────────────────────────────
def supervisor(state: TeamState) -> TeamState:
    print("  [Supervisor] Deciding next step...")
    
    # Build context of what's been done
    done = []
    if state.get("research"): done.append("research")
    if state.get("code"): done.append("code")
    if state.get("report"): done.append("report")
    
    response = llm.invoke([HumanMessage(content=f"""
You are a supervisor managing a team to complete this task:
"{state['task']}"

Work completed so far: {done if done else "nothing yet"}

Available agents:
- "researcher": gathers information and facts
- "coder": writes Python code examples
- "writer": creates final report (only after research AND code are done)
- "FINISH": when the report is complete

What should be the next step? Return JSON only:
{{"next": "researcher" or "coder" or "writer" or "FINISH",
  "reason": "brief reason"}}
""")])
    
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw.strip())
    
    print(f"  [Supervisor] → {result['next']} ({result['reason']})")
    
    return {
        "next_agent": result["next"],
        "messages": [AIMessage(content=f"Supervisor: routing to {result['next']}")]
    }

# ── Routing function ───────────────────────────────────
def route(state: TeamState) -> Literal["researcher", "coder", "writer", END]:
    next_agent = state.get("next_agent", "")
    if next_agent == "FINISH":
        return END
    return next_agent

# ── Build graph ────────────────────────────────────────
workflow = StateGraph(TeamState)

workflow.add_node("supervisor", supervisor)
workflow.add_node("researcher", researcher_agent)
workflow.add_node("coder", coder_agent)
workflow.add_node("writer", writer_agent)

# Supervisor decides where to go
workflow.set_entry_point("supervisor")
workflow.add_conditional_edges("supervisor", route)

# All workers report back to supervisor
workflow.add_edge("researcher", "supervisor")
workflow.add_edge("coder", "supervisor")
workflow.add_edge("writer", "supervisor")

graph = workflow.compile()

# ── Run ────────────────────────────────────────────────
print("=== Supervisor Pattern: AI Team ===\n")

result = graph.invoke({
    "task": "Explain how to use LangChain LCEL to build a simple RAG pipeline",
    "research": "",
    "code": "",
    "report": "",
    "next_agent": "",
    "messages": [],
})

print(f"\n{'='*60}")
print("FINAL REPORT:")
print('='*60)
print(result['report'])
print(f"\nTotal steps: {len(result['messages'])}")
print("Execution path:")
for msg in result['messages']:
    print(f"  → {msg.content}")

# ── State with approval ────────────────────────────────
class ApprovalState(TypedDict):
    task: str
    draft: str
    human_approved: bool
    messages: Annotated[list, operator.add]

# ── Writer node ────────────────────────────────────────
def draft_writer(state: ApprovalState) -> ApprovalState:
    print("  [Writer] Creating draft...")
    
    response = llm.invoke([HumanMessage(content=f"""
Write a professional email about: {state['task']}
Keep it concise and professional.
""")])
    
    return {
        "draft": response.content,
        "messages": [AIMessage(content="Writer: draft completed")]
    }
    
# ── Human approval node ────────────────────────────────
def human_approval(state: ApprovalState) -> ApprovalState:
    # This pauses execution and waits for human input
    user_input = interrupt({
        "draft": state["draft"],
        "message": "Please review and approve/reject this draft"
    })
    
    approved = user_input.lower() in ["yes", "y", "approve", "approved"]
    
    return {
        "human_approved": approved,
        "messages": [AIMessage(content=f"Human: {'approved' if approved else 'rejected'}")]
    }

# ── Send node ──────────────────────────────────────────
def send_email(state: ApprovalState) -> ApprovalState:
    if state["human_approved"]:
        print("\n  [System] Email sent successfully!")
    else:
        print("\n  [System] Email cancelled by human.")
    
    return {
        "messages": [AIMessage(content="System: process completed")]
    }

# ── Routing ────────────────────────────────────────────
def after_approval(state: ApprovalState) -> Literal["send_email", END]:
    return "send_email"

# ── Build graph with checkpointer ─────────────────────
# MemorySaver enables graph to pause and resume
checkpointer = MemorySaver()

approval_workflow = StateGraph(ApprovalState)
approval_workflow.add_node("writer", draft_writer)
approval_workflow.add_node("human_approval", human_approval)
approval_workflow.add_node("send_email", send_email)

approval_workflow.set_entry_point("writer")
approval_workflow.add_edge("writer", "human_approval")
approval_workflow.add_conditional_edges("human_approval", after_approval)
approval_workflow.add_edge("send_email", END)

# Compile with checkpointer for pause/resume
approval_graph = approval_workflow.compile(checkpointer=checkpointer)

# ── Run with human in the loop ─────────────────────────
print("\n\n=== Human-in-the-Loop: Email Approval ===\n")

config = {"configurable": {"thread_id": "email_001"}}

initial_state = {
    "task": "Inform the team about next week's LLM workshop",
    "draft": "",
    "human_approved": False,
    "messages": [],
}

# Production pattern: print BEFORE invoking, not inside the node
result = approval_graph.invoke(initial_state, config=config)

# Check if interrupted
if "__interrupt__" in result:
    # Show draft OUTSIDE the graph
    interrupt_data = result["__interrupt__"][0].value
    print("=" * 50)
    print("HUMAN REVIEW REQUIRED")
    print("=" * 50)
    print(f"\nDraft:\n{interrupt_data['draft']}")
    print("\n" + "=" * 50)
    
    # Get human input
    human_input = input("\nApprove? (yes/no): ")
    
    # Resume graph
    final_result = approval_graph.invoke(
        Command(resume=human_input),
        config=config
    )
    
    print("\nExecution path:")
    for msg in final_result['messages']:
        print(f"  → {msg.content}")