from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from app.config import MODEL_FAST
import json

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
    """Predict property value based on features and condition."""
    prompt = (
        "You are a real estate appraiser. Based on this property data, "
        "provide a price estimate with confidence interval.\n"
        "Property data: " + property_data + "\n\n"
        "Return JSON only:\n"
        '{"estimated_value": 0, "confidence_interval": {"low": 0, "high": 0}, '
        '"confidence_level": "low/medium/high", '
        '"key_factors": ["factor 1"], '
        '"condition_adjustment_pct": 0, '
        '"reasoning": "2-3 sentence explanation"}'
    )
    response = llm.invoke(prompt)
    return response.content
