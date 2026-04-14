from langchain_anthropic import ChatAnthropic
from app.config import MODEL_FAST
import json, re

llm = ChatAnthropic(model=MODEL_FAST, temperature=0.3, max_tokens=512)

_sessions: dict = {}

QUESTIONS = {
    "intent":   "Hi! I am your Real Estate Copilot!<br>Are you looking to <b>buy</b> or <b>rent</b>?",
    "location": "What city or neighborhood are you targeting?",
    "budget":   "What is your budget range? (e.g. $600k-$800k for buying, or $3,000-$4,500/month for renting)",
    "bedrooms": "How many bedrooms do you need?",
    "school":   "Is school district quality a priority? (yes / no)",
    "commute":  "Do you have a work address for commute time estimates? (or type skip)",
    "extras":   "Any must-haves or dealbreakers? (e.g. need garage, no HOA, pet friendly) — or type none",
}

def _llm_validate(step: str, user_msg: str, profile: dict) -> dict:
    """Use LLM to validate user input and extract structured value."""

    if step == "intent":
        prompt = (           "User was asked: Are you looking to buy or rent?\n"
            "User replied: " + user_msg + "\n\n"
            "Task: determine if the user clearly indicated buy or rent.\n"
            "Rules:\n"
            "- valid=true only if user clearly said buy, rent, or synonyms (purchase, lease, etc.)\n"
            "- valid=false if user said something unrelated, gibberish, or unclear\n"
            "- If valid=false, reply should politely ask again\n"
            "Return JSON only: {\"valid\": true/false, \"value\": \"buy\" or \"rent\" or null, \"reply\": \"natural follow-up\"}"
        )

    elif step == "location":
        prompt = (
            "User was asked: What city or neighborhood are you targeting?\n"
            "User replied: " + user_msg + "\n\n"
            "Task: determine if this is a real place name (city, neighborhood, zip code, region).\n"
            "Rules:\n"
            "- valid=true if it looks like a real location\n"
            "- valid=false if it is gibberish, a question, or clearly not a location\n"
            "- If valid=true, reply should acknowledge the location naturally and ask about budget\n"
            "- If valid=false, reply should politely ask for a location again\n"
            "Return JSON only: {\"valid\": true/false, \"value\": \"cleaned location\" or null, \"reply\": \"response text\"}"
        )

    elif step == "budget":
        prompt = (
            "User was asked: What is your budget range?\n"
            "User replied: " + user_msg + "\n\n"
            "Task: extract min and max budget numbers.\n"
            "Rules:\n"
            "- valid=true if user gave any number or range\n"
            "- valid=false if no numbers found or response is gibberish\n"
            "- k means thousand (500k = 500000), m means million\n"
            "- If only one number given, use it as max, set min=0\n"
            "- If valid=true, reply should acknowledge and ask how many bedrooms\n"
            "- If valid=false, reply should ask for budget again with example\n"
            "Return JSON only: {\"valid\": true/false, \"min\": 0, \"max\": 0, \"reply\": \"response text\"}"
        )

    elif step == "bedrooms":
        prompt = (
            "User was asked: How many bedrooms do you need?\n"
            "User replied: " + user_msg + "\n\n"
            "Task: extract bedroom count.\n"
            "Rules:\n"
            "- valid=true if user gave a number between 1-10\n"
            "- valid=false if no number found or number is unrealistic\n"
            "- If valid=true, reply should acknowledge and ask about school district\n"
            "- If valid=false, reply should ask again\n"
            "Return JSON only: {\"valid\": true/false, \"value\": number or null, \"reply\": \"response text\"}"
        )

    elif step == "school":
        prompt = (
            "User was asked: Is school district quality a priority?\n"
            "User replied: " + user_msg + "\n\n"
            "Task: determine yes or no.\n"
            "Rules:\n"
            "- valid=true for any clear yes/no answer\n"
            "- valid=false if completely unclear\n"
            "- If valid=true, reply should acknowledge and ask for commute address\n"
            "Return JSON only: {\"valid\": true/false, \"value\": true or false, \"reply\": \"response text\"}"
        )

    elif step == "commute":
        prompt = (
            "User was asked: Do you have a work address for commute estimates?\n"
            "User replied: " + user_msg + "\n\n"
            "Task: accept any address or skip/none.\n"
            "Rules:\n"
            "- valid=true always (any answer is acceptable here)\n"
            "- value=null if user said skip, none, no, or similar\n"
            "- value=address string if user gave an address\n"
            "- reply should acknowledge and ask about must-haves or dealbreakers\n"
            "Return JSON only: {\"valid\": true, \"value\": \"address\" or null, \"reply\": \"response text\"}"
        )

    elif step == "extras":
        prompt = (
            "User was asked: Any must-haves or dealbreakers?\n"
            "User replied: " + user_msg + "\n\n"
            "Task: accept any preferences or none.\n"
            "Rules:\n"
            "- valid=true always\n"
            "- value=null if user said none, no, or similar\n"
            "- value=preference string if user gave preferences\n"
            "- reply should show a summary of the full profile collected so far\n"
            "Profile so far: " + json.dumps(profile) + "\n"
            "Return JSON only: {\"valid\": true, \"value\": \"preferences\" or null, \"reply\": \"response text\"}"
        )
    else:
        return {"valid": True, "value": user_msg, "reply": ""}

    try:
        raw = llm.invoke(prompt).content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return {"valid": False, "reply": "I did not quite catch that. Could you try again?"}


def _build_summary(profile: dict) -> str:
    bmin = profile.get("budget_min") or 0
    bmax = profile.get("budget_max") or 0
    if bmin and bmax:
        budget_str = "${:,.0f} - ${:,.0f}".format(bmin, bmax)
    elif bmax:
        budget_str = "up to ${:,.0f}".format(bmax)
    else:
        budget_str = "Not specified"

    return (
        "Here is your preference profile:<br><br>"
        "- <b>Intent:</b> {}<br>"
        "- <b>Location:</b> {}<br>"
        "- <b>Budget:</b> {}<br>"
        "- <b>Bedrooms:</b> {}<br>"
        "- <b>School priority:</b> {}<br>"
        "- <b>Commute address:</b> {}<br>"
        "- <b>Must-haves/Dealbreakers:</b> {}<br><br>"
        "Does this look right? Type <b>yes</b> to save, or <b>no</b> to start over."
    ).format(
        (profile.get("intent") or "buy").capitalize(),
        profile.get("location") or "Not specified",
        budget_str,
        profile.get("bedrooms") or "Not specified",
        "Yes" if profile.get("school_priority") else "No",
        profile.get("commute_address") or "Not specified",
        profile.get("extras") or "None",
    )


def freeform_chat(session_id: str, user_message: str) -> dict:
    """Free-form real estate Q&A after profile is saved."""
    profile = get_profile(session_id)

    context = ""
    if profile:
        context = (
            "User profile: looking to {intent} in {location}, "
            "budget ${budget_min:,.0f}-${budget_max:,.0f}, "
            "{bedrooms} bedrooms, school priority: {school}.".format(
                intent=profile.get("intent", "buy"),
                location=profile.get("location", "Seattle"),
                budget_min=profile.get("budget_min") or 0,
                budget_max=profile.get("budget_max") or 0,
                bedrooms=profile.get("bedrooms", 3),
                school="yes" if profile.get("school_priority") else "no",
            )
        )

    prompt = (
        "You are a knowledgeable, friendly real estate advisor. "
        "Give practical, specific advice. Be concise but helpful. "
        + ("User context: " + context + "\n\n" if context else "")
        + "User question: " + user_message
    )

    response = llm.invoke(prompt)
    return {
        "message":      response.content,
        "profile":      profile,
        "done":         True,
        "current_step": "freeform",
    }


def chat(session_id: str, user_message: str = None) -> dict:
    """Multi-turn preference collection with LLM validation."""

    # Start new session
    if user_message is None:
        _sessions[session_id] = {"step": "intent", "profile": {}}
        return {
            "message":      QUESTIONS["intent"],
            "profile":      {},
            "done":         False,
            "current_step": "intent",
        }

    session = _sessions.get(session_id)
    if not session:
        _sessions[session_id] = {"step": "intent", "profile": {}}
        return chat(session_id, user_message)

    step    = session["step"]
    profile = session["profile"]
    msg     = user_message.strip()

    # Freeform after profile saved
    if step == "done":
        return freeform_chat(session_id, msg)

    # Confirm step
    if step == "confirm":
        if "yes" in msg.lower() or msg.lower() == "y":
            profile["confirmed"] = True
            session["step"] = "done"
            return {
                "message":      "Profile saved! You can now ask me anything about real estate.",
                "profile":      profile,
                "done":         True,
                "current_step": "done",
            }
        else:
            session["step"]    = "intent"
            session["profile"] = {}
            return {
                "message":      "No problem, let us start over.<br>" + QUESTIONS["intent"],
                "profile":      {},
                "done":         False,
                "current_step": "intent",
            }

    # Validate with LLM
    result = _llm_validate(step, msg, profile)

    if not result.get("valid", False):
        return {
            "message":      result.get("reply", "I did not quite catch that. Could you try again?"),
            "profile":      profile,
            "done":         False,
            "current_step": step,
        }

    # Update profile
    if step == "intent":
        profile["intent"] = result.get("value", "buy")
        session["step"]   = "location"
    elif step == "location":
        profile["location"] = result.get("value", msg)
        session["step"]     = "budget"
    elif step == "budget":
        profile["budget_min"] = result.get("min", 0)
        profile["budget_max"] = result.get("max", 0)
        session["step"]       = "bedrooms"
    elif step == "bedrooms":
        profile["bedrooms"] = result.get("value", 3)
        session["step"]     = "school"
    elif step == "school":
        profile["school_priority"] = result.get("value", False)
        session["step"]            = "commute"
    elif step == "commute":
        val = result.get("value")
        profile["commute_address"] = None if not val else val
        session["step"]            = "extras"
    elif step == "extras":
        val = result.get("value")
        profile["extras"] = None if not val else val
        session["step"]   = "confirm"

    reply = result.get("reply", "")
    if session["step"] == "confirm":
        reply = _build_summary(profile)

    session["profile"] = profile
    return {
        "message":      reply,
        "profile":      profile,
        "done":         False,
        "current_step": session["step"],
    }


def get_profile(session_id: str) -> dict:
    session = _sessions.get(session_id, {})
    return session.get("profile", {})
