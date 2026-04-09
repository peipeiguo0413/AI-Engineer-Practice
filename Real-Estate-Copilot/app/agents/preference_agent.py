from langchain_anthropic import ChatAnthropic
from app.config import MODEL_FAST
import json, re

llm = ChatAnthropic(model=MODEL_FAST, temperature=0, max_tokens=256)

# In-memory session store
_sessions: dict = {}

STEPS = [
    "intent",
    "location",
    "budget",
    "bedrooms",
    "school",
    "commute",
    "extras",
    "confirm",
]

QUESTIONS = {
    "intent":   "Hi! I'm your Real Estate Copilot 🏠\nAre you looking to **buy** or **rent**?",
    "location": "What city or neighborhood are you targeting?",
    "budget":   "What's your budget range? (e.g. $600k-$800k for buying, or $3,000-$4,500/month for renting)",
    "bedrooms": "How many bedrooms do you need?",
    "school":   "Is school district quality a priority? (yes / no)",
    "commute":  "Do you have a work address for commute time estimates? (or type 'skip')",
    "extras":   "Any must-haves or dealbreakers? (e.g. 'need garage', 'no HOA', 'pet friendly') — or type 'none'",
    "confirm":  None,  # dynamically generated
}

def _extract_budget(text: str) -> dict:
    response = llm.invoke(
        "Extract min and max budget from this text. "
        "Return JSON only, numbers only no symbols: "
        '{"min": 0, "max": 0}\n'
        f"Text: {text}"
    )
    try:
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1].strip("json").strip()
        return json.loads(raw)
    except Exception:
        nums = re.findall(r'\d[\d,]*', text.replace("k", "000").replace("K", "000"))
        nums = [int(n.replace(",", "")) for n in nums]
        if len(nums) >= 2:
            return {"min": min(nums), "max": max(nums)}
        elif len(nums) == 1:
            return {"min": 0, "max": nums[0]}
        return {"min": 0, "max": 0}

def _build_summary(profile: dict) -> str:
    budget_str = ""
    bmin = profile.get("budget_min", 0)
    bmax = profile.get("budget_max", 0)
    if bmin and bmax:
        budget_str = "${:,.0f} – ${:,.0f}".format(bmin, bmax)
    elif bmax:
        budget_str = "up to ${:,.0f}".format(bmax)

    return (
        "Here's your preference profile:\n\n"
        "- **Intent:** {}\n"
        "- **Location:** {}\n"
        "- **Budget:** {}\n"
        "- **Bedrooms:** {}\n"
        "- **School priority:** {}\n"
        "- **Commute address:** {}\n"
        "- **Must-haves/Dealbreakers:** {}\n\n"
        "Does this look right? Type **yes** to save, or **no** to start over."
    ).format(
        (profile.get("intent") or "buy").capitalize(),
        profile.get("location") or "Not specified",
        budget_str or "Not specified",
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
        "You are a helpful real estate advisor. "
        + ("Context about this user: " + context + " " if context else "")
        + "Answer the following question concisely and helpfully.\n\n"
        + "Question: " + user_message
    )

    response = llm.invoke(prompt)
    return {
        "message":      response.content,
        "profile":      profile,
        "done":         True,
        "current_step": "freeform",
    }


def chat(session_id: str, user_message: str = None) -> dict:
    """
    Multi-turn preference collection conversation.
    Call with user_message=None to start a new conversation.
    Returns: {message, profile, done, current_step}
    """
    # Start new or reset session
    if user_message is None:
        _sessions[session_id] = {
            "step":    "intent",
            "profile": {},
        }
        return {
            "message":      QUESTIONS["intent"],
            "profile":      {},
            "done":         False,
            "current_step": "intent",
        }
    # Start new session
    if user_message is None:
        _sessions[session_id] = {
            "step":    "intent",
            "profile": {},
        }
        return {
            "message":      QUESTIONS["intent"],
            "profile":      {},
            "done":         False,
            "current_step": "intent",
        }

    session = _sessions[session_id]
    step    = session["step"]
    profile = session["profile"]
    msg     = user_message.strip()

    # Process user input for current step
    if step == "intent":
        intent = "rent" if "rent" in msg.lower() else "buy"
        profile["intent"] = intent
        session["step"]   = "location"
        reply = "Got it, looking to **{}**! {}".format(
            intent, QUESTIONS["location"])

    elif step == "location":
        profile["location"] = msg
        session["step"]     = "budget"
        reply = QUESTIONS["budget"]

    elif step == "budget":
        budget = _extract_budget(msg)
        profile["budget_min"] = budget.get("min", 0)
        profile["budget_max"] = budget.get("max", 0)
        session["step"]       = "bedrooms"
        reply = QUESTIONS["bedrooms"]

    elif step == "bedrooms":
        nums  = re.findall(r'\d+', msg)
        beds  = int(nums[0]) if nums else 3
        profile["bedrooms"] = beds
        session["step"]     = "school"
        reply = QUESTIONS["school"]

    elif step == "school":
        profile["school_priority"] = "yes" in msg.lower() or msg.lower() == "y"
        session["step"]            = "commute"
        reply = QUESTIONS["commute"]

    elif step == "commute":
        profile["commute_address"] = None if "skip" in msg.lower() else msg
        session["step"]            = "extras"
        reply = QUESTIONS["extras"]

    elif step == "extras":
        profile["extras"] = None if msg.lower() in ("none", "no", "n/a") else msg
        session["step"]   = "confirm"
        reply = _build_summary(profile)

    elif step == "confirm":
        if "yes" in msg.lower() or msg.lower() == "y":
            profile["confirmed"] = True
            session["step"]      = "done"
            reply = (
                "✅ Profile saved! You can now use Quick Fit Check "
                "to screen properties against your preferences."
            )
        else:
            # Start over
            session["step"]    = "intent"
            session["profile"] = {}
            profile = {}
            reply = "No problem, let's start over.\n\n" + QUESTIONS["intent"]

    else:
        return freeform_chat(session_id, msg)

    session["profile"] = profile
    done = session["step"] == "done"

    return {
        "message":      reply,
        "profile":      profile,
        "done":         done,
        "current_step": session["step"],
    }

def get_profile(session_id: str) -> dict:
    """Retrieve saved profile for a session."""
    session = _sessions.get(session_id, {})
    return session.get("profile", {})

def _extract_budget(text: str) -> dict:
    response = llm.invoke(
        "Extract min and max budget from this text. "
        "Return JSON only, numbers only no symbols: "
        '{"min": 0, "max": 0}\n'
        f"Text: {text}"
    )
    try:
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1].strip("json").strip()
        return json.loads(raw)
    except Exception:
        nums = re.findall(r'\d[\d,]*', text.replace("k", "000").replace("K", "000"))
        nums = [int(n.replace(",", "")) for n in nums]
        if len(nums) >= 2:
            return {"min": min(nums), "max": max(nums)}
        elif len(nums) == 1:
            return {"min": 0, "max": nums[0]}
        return {"min": 0, "max": 0}

def _build_summary(profile: dict) -> str:
    budget_str = ""
    bmin = profile.get("budget_min", 0)
    bmax = profile.get("budget_max", 0)
    if bmin and bmax:
        budget_str = "${:,.0f} – ${:,.0f}".format(bmin, bmax)
    elif bmax:
        budget_str = "up to ${:,.0f}".format(bmax)

    return (
        "Here's your preference profile:\n\n"
        "- **Intent:** {}\n"
        "- **Location:** {}\n"
        "- **Budget:** {}\n"
        "- **Bedrooms:** {}\n"
        "- **School priority:** {}\n"
        "- **Commute address:** {}\n"
        "- **Must-haves/Dealbreakers:** {}\n\n"
        "Does this look right? Type **yes** to save, or **no** to start over."
    ).format(
        (profile.get("intent") or "buy").capitalize(),
        profile.get("location") or "Not specified",
        budget_str or "Not specified",
        profile.get("bedrooms") or "Not specified",
        "Yes" if profile.get("school_priority") else "No",
        profile.get("commute_address") or "Not specified",
        profile.get("extras") or "None",
    )

def chat(session_id: str, user_message: str = None) -> dict:
    """
    Multi-turn preference collection conversation.
    Call with user_message=None to start a new conversation.
    Returns: {message, profile, done, current_step}
    """
    # Start new or reset session
    if user_message is None:
        _sessions[session_id] = {
            "step":    "intent",
            "profile": {},
        }
        return {
            "message":      QUESTIONS["intent"],
            "profile":      {},
            "done":         False,
            "current_step": "intent",
        }
    # Start new session
    if user_message is None:
        _sessions[session_id] = {
            "step":    "intent",
            "profile": {},
        }
        return {
            "message":      QUESTIONS["intent"],
            "profile":      {},
            "done":         False,
            "current_step": "intent",
        }

    session = _sessions[session_id]
    step    = session["step"]
    profile = session["profile"]
    msg     = user_message.strip()

    # Process user input for current step
    if step == "intent":
        intent = "rent" if "rent" in msg.lower() else "buy"
        profile["intent"] = intent
        session["step"]   = "location"
        reply = "Got it, looking to **{}**! {}".format(
            intent, QUESTIONS["location"])

    elif step == "location":
        profile["location"] = msg
        session["step"]     = "budget"
        reply = QUESTIONS["budget"]

    elif step == "budget":
        budget = _extract_budget(msg)
        profile["budget_min"] = budget.get("min", 0)
        profile["budget_max"] = budget.get("max", 0)
        session["step"]       = "bedrooms"
        reply = QUESTIONS["bedrooms"]

    elif step == "bedrooms":
        nums  = re.findall(r'\d+', msg)
        beds  = int(nums[0]) if nums else 3
        profile["bedrooms"] = beds
        session["step"]     = "school"
        reply = QUESTIONS["school"]

    elif step == "school":
        profile["school_priority"] = "yes" in msg.lower() or msg.lower() == "y"
        session["step"]            = "commute"
        reply = QUESTIONS["commute"]

    elif step == "commute":
        profile["commute_address"] = None if "skip" in msg.lower() else msg
        session["step"]            = "extras"
        reply = QUESTIONS["extras"]

    elif step == "extras":
        profile["extras"] = None if msg.lower() in ("none", "no", "n/a") else msg
        session["step"]   = "confirm"
        reply = _build_summary(profile)

    elif step == "confirm":
        if "yes" in msg.lower() or msg.lower() == "y":
            profile["confirmed"] = True
            session["step"]      = "done"
            reply = (
                "✅ Profile saved! You can now use Quick Fit Check "
                "to screen properties against your preferences."
            )
        else:
            # Start over
            session["step"]    = "intent"
            session["profile"] = {}
            profile = {}
            reply = "No problem, let's start over.\n\n" + QUESTIONS["intent"]

    else:
        return freeform_chat(session_id, msg)

    session["profile"] = profile
    done = session["step"] == "done"

    return {
        "message":      reply,
        "profile":      profile,
        "done":         done,
        "current_step": session["step"],
    }

def get_profile(session_id: str) -> dict:
    """Retrieve saved profile for a session."""
    session = _sessions.get(session_id, {})
    return session.get("profile", {})