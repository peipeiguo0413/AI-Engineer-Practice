from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from app.config import MODEL_FAST
import json

# =============================================================================
# TODO (Phase 1.5): True Cost Calculator
# Location: add as new @tool function below existing mortgage/ROI tools
# Purpose: show real monthly cost beyond just mortgage payment
# Implementation:
#   Input: asking_price, sqft, hoa_monthly, year_built, location
#   Output: {
#     mortgage_payment: 4073,
#     property_tax_monthly: 625,      # ~1% of value / 12
#     insurance_monthly: 150,          # ~$1,800/yr typical
#     hoa_monthly: 0,
#     maintenance_monthly: 375,        # 1% of value / 12 (rule of thumb)
#     utilities_estimate: 200,
#     total_true_monthly_cost: 5423,   # the number Zillow never shows
#     vs_rent_equivalent: "Renting equivalent would cost ~$4,200/mo"
#   }
# Key insight: "Your true monthly cost is $5,423 — not the $4,073 Zillow shows"
# ===========================================================================

# =============================================================================
# TODO (Phase 1.5): Neighborhood Intelligence Tool
# Location: add as new @tool function, called from property_agent.py
# Purpose: surface risks Zillow doesn't show
# Implementation:
#   Input: address, zip_code
#   Output: {
#     crime_trend: "declining / stable / increasing",
#     flood_zone: "Zone X (minimal) / Zone AE (high risk)",
#     noise_level: "low / moderate / high (near highway/airport)",
#     development_pipeline: "3 new condo projects approved within 0.5mi",
#     school_rating: 8,               # GreatSchools API (Phase 2: real data)
#     walk_score: 82,
#     appreciation_trend: "+3.2% YoY over last 5 years",
#     risk_flags: ["flood zone AE", "highway noise"]
#   }
# Phase 1: LLM-estimated based on address/neighborhood knowledge
# Phase 2: integrate real APIs (GreatSchools, WalkScore, FEMA flood maps)
# =============================================================================

llm = ChatAnthropic(model=MODEL_FAST, temperature=0, max_tokens=512)

def parse_json(raw):
    cleaned = raw.strip()
    if cleaned.startswith("\`\`\`"):
        cleaned = cleaned.split("\`\`\`")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned.strip())
    except:
        return {"error": "parse failed"}

@tool
def search_property_market(address: str) -> str:
    """Get market data and price estimates for a property address."""
    response = llm.invoke(
        "Provide realistic current market data for real estate in this area: " + address +
        ". Include median home price per sqft, recent sales trends, average days on market, "
        "and whether it is a buyer or seller market. Be specific with numbers. 150 words max."
    )
    return response.content

@tool
def search_school_ratings(address: str) -> str:
    """Get school district ratings for a given address."""
    response = llm.invoke(
        "Provide realistic school district information near: " + address +
        ". Include elementary, middle, and high school quality ratings (1-10), "
        "district name, and notable characteristics. 100 words max."
    )
    return response.content

@tool
def search_neighborhood(address: str) -> str:
    """Get neighborhood walkability, safety, and amenities info."""
    response = llm.invoke(
        "Describe the neighborhood near: " + address +
        ". Include walkability score (1-100), safety rating, nearby amenities, "
        "and commute options. Be realistic and specific. 100 words max."
    )
    return response.content

@tool
def calculate_mortgage(price_and_params: str) -> str:
    """Calculate monthly mortgage. Input: price=500000 down_payment=100000 rate=7.0 years=30"""
    try:
        params       = dict(p.split("=") for p in price_and_params.split())
        price        = float(params.get("price", 500000))
        down_payment = float(params.get("down_payment", price * 0.2))
        rate         = float(params.get("rate", 7.0)) / 100 / 12
        years        = int(params.get("years", 30))
        n            = years * 12
        principal    = price - down_payment
        if rate > 0:
            monthly = principal * (rate * (1 + rate)**n) / ((1 + rate)**n - 1)
        else:
            monthly = principal / n
        return json.dumps({
            "monthly_payment":      round(monthly, 2),
            "principal":            round(principal, 2),
            "down_payment":         round(down_payment, 2),
            "total_interest":       round((monthly * n) - principal, 2),
            "down_payment_percent": round(down_payment / price * 100, 1),
        })
    except Exception as e:
        return "Error: " + str(e)

@tool
def calculate_roi(investment_params: str) -> str:
    """Calculate ROI for rental property. Input: price=500000 monthly_rent=2500 expenses=500"""
    try:
        params       = dict(p.split("=") for p in investment_params.split())
        price        = float(params.get("price", 500000))
        monthly_rent = float(params.get("monthly_rent", 2000))
        monthly_exp  = float(params.get("expenses", 400))
        down_payment = float(params.get("down_payment", price * 0.2))
        annual_rent  = monthly_rent * 12
        annual_exp   = monthly_exp * 12
        noi          = annual_rent - annual_exp
        cap_rate     = (noi / price) * 100
        rate         = 0.07 / 12
        n            = 360
        principal    = price - down_payment
        monthly_mort = principal * (rate * (1+rate)**n) / ((1+rate)**n - 1)
        annual_cf    = noi - (monthly_mort * 12)
        coc_return   = (annual_cf / down_payment) * 100
        return json.dumps({
            "annual_rental_income": round(annual_rent, 2),
            "net_operating_income": round(noi, 2),
            "cap_rate_percent":     round(cap_rate, 2),
            "monthly_mortgage":     round(monthly_mort, 2),
            "annual_cash_flow":     round(annual_cf, 2),
            "cash_on_cash_return":  round(coc_return, 2),
        })
    except Exception as e:
        return "Error: " + str(e)

@tool
def predict_property_price(property_data: str) -> str:
    """Predict condition-based price adjustment for a property."""
    rules = (
        "Apply these rules based on the property data:\n"
        "- Kitchen renovated within 5 years: +2% to +4%\n"
        "- Kitchen renovated 5-10 years ago: +1% to +2%\n"
        "- No kitchen renovation: -1% to -3%\n"
        "- Roof under 5 years: +1% to +2%\n"
        "- Roof 15-25 years: -1% to -3%\n"
        "- Roof over 25 years: -3% to -6%\n"
        "- Foundation issues: -5% to -15%\n"
        "- HVAC over 15 years: -1% to -2%\n"
        "- Condition score 85-100: +2% to +4%\n"
        "- Condition score 70-84: 0% to +2%\n"
        "- Condition score 55-69: -2% to -4%\n"
        "- Condition score below 55: -5% to -10%\n"
        "IMPORTANT: Only return adjustment_pct=0 if property is perfectly average."
    )
    prompt = (
        "You are a real estate appraiser.\n\n"
        + rules + "\n\n"
        + "Property data: " + property_data + "\n\n"
        + "Return JSON only (no markdown):\n"
        + '{"adjustment_pct": -3.5, '
        + '"confidence_level": "medium", '
        + '"key_factors": ["factor: impact%"], '
        + '"reasoning": "2-3 sentence explanation"}'
    )
    response = llm.invoke(prompt)
    return response.content
