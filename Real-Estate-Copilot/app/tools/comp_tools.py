from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from app.config import MODEL_SMART
import json

llm = ChatAnthropic(model=MODEL_SMART, temperature=0, max_tokens=2048)

def parse_json(raw: str):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned.strip())
    except:
        return []

@tool
def find_comparable_sales(property_info: str) -> str:
    """
    Find the most similar recently sold properties for a given property.
    Input: JSON string with address, sqft, bedrooms, bathrooms, year_built, asking_price.
    Returns top 5 comparable sales with similarity scores.
    """
    response = llm.invoke(
        "You are a real estate appraiser. Generate 5 realistic comparable sales "
        "for this property. Make them similar but with natural variation.\n\n"
        "Target property: " + property_info + "\n\n"
        "Return JSON array only:\n"
        '[{"address": "123 Example St, Seattle WA", '
        '"sold_price": 720000, '
        '"sold_date": "2025-10-15", '
        '"sqft": 1750, '
        '"bedrooms": 3, '
        '"bathrooms": 2, '
        '"year_built": 1998, '
        '"similarity_score": 92, '
        '"key_differences": "Slightly smaller, no kitchen renovation"}, ...]'
    )
    return response.content

@tool
def analyze_price_vs_comps(target_and_comps: str) -> str:
    """
    Analyze how a target property's price compares to its comparable sales.
    Produces explainable price delta with per-factor attribution.
    Input: JSON with target property details and list of comps.
    """
    response = llm.invoke(
        "You are a real estate appraiser. Analyze how the target property's "
        "asking price compares to the comparable sales provided.\n\n"
        "Data: " + target_and_comps + "\n\n"
        "Return JSON only:\n"
        '{"comp_median_price": 0, '
        '"comp_price_per_sqft": 0, '
        '"target_vs_median_pct": 0, '
        '"price_delta_explanation": "This property is X% above/below comp median because...", '
        '"adjustment_factors": ['
        '{"factor": "Kitchen renovation 2020", "impact_pct": 2.5}, '
        '{"factor": "Roof age 18 years", "impact_pct": -1.5}], '
        '"fair_value_range": {"low": 0, "high": 0}, '
        '"verdict": "fairly priced / slightly overpriced / significantly overpriced / underpriced"}'
    )
    return response.content

def run_comp_analysis(form, condition_score: int) -> dict:
    """
    Full comparable sales analysis pipeline.
    1. Find similar sold properties
    2. Analyze price vs comps
    3. Return structured result
    """
    print("  Finding comparable sales...")

    # Step 1: Find comps
    property_info = json.dumps({
        "address":       form.address,
        "asking_price":  form.asking_price,
        "sqft":          form.sqft,
        "bedrooms":      form.bedrooms,
        "bathrooms":     form.bathrooms,
        "year_built":    form.year_built,
        "condition_score": condition_score,
    })

    comps_raw  = find_comparable_sales.invoke(property_info)
    comps_list = parse_json(comps_raw)

    if not comps_list:
        return {"error": "Could not find comparable sales"}

    print(f"  Found {len(comps_list)} comparable sales")

    # Step 2: Analyze price vs comps
    target_and_comps = json.dumps({
        "target": {
            "address":       form.address,
            "asking_price":  form.asking_price,
            "sqft":          form.sqft,
            "bedrooms":      form.bedrooms,
            "year_built":    form.year_built,
            "condition_score": condition_score,
            "kitchen_renovated": form.kitchen_renovated,
            "roof_age_years":    form.roof_age_years,
        },
        "comps": comps_list
    })

    analysis_raw = analyze_price_vs_comps.invoke(target_and_comps)
    analysis     = parse_json(analysis_raw)

    return {
        "comps":    comps_list,
        "analysis": analysis,
    }
