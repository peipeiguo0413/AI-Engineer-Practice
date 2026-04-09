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
    except Exception:
        return []


COMP_SCHEMA = '''{
  "address": "123 Example St, Seattle WA 98103",
  "listing_price": 750000,
  "sale_price": 738000,
  "sale_date": "2025-10-15",
  "days_on_market": 18,
  "sqft": 1750,
  "bedrooms": 3,
  "bathrooms": 2.0,
  "year_built": 1998,
  "hoa_monthly": 0,
  "hoa_exists": false,
  "condition_score": 78,
  "interior_condition": "Good — original kitchen, updated bathrooms, hardwood floors",
  "similarity_score": 92,
  "key_differences": "Slightly smaller sqft, no kitchen renovation",
  "listing_url": "https://www.zillow.com/homes/123-example-st"
}'''

COMP_PROMPT = """You are a professional real estate appraiser generating realistic comparable sales data.

TASK: Generate exactly 5 comparable sales for the target property below.

RULES:
1. Each comp MUST be a realistic property in the same city/ZIP area as the target
2. Sale prices should vary naturally — some higher, some lower than target asking price
3. listing_price should be 1-4% ABOVE sale_price (properties rarely sell at exact list price)
4. days_on_market: REQUIRED — must be a realistic integer between 8 and 45
5. HOA: hoa_monthly=0 and hoa_exists=false for single-family homes; condos may have HOA
6. condition_score: REQUIRED — must be an integer between 65 and 95, vary across comps
7. interior_condition: REQUIRED — 1 sentence describing kitchen, bathrooms, flooring, condition
8. key_differences: REQUIRED — how this comp differs FROM the target property (not same text)
9. listing_url: REQUIRED — format: https://www.zillow.com/homes/[street-address]-[city]-[state]
10. Sale dates should be within the last 9 months
11. Similarity scores: highest comp gets 90-96, lowest gets 78-85

CRITICAL: days_on_market and condition_score MUST be non-zero integers.
CRITICAL: interior_condition and key_differences MUST be different text from each other.

TARGET PROPERTY:
{property_info}

Return a JSON array of exactly 5 comparable sales. Each item must follow this schema exactly:
{schema}

Return the JSON array only. No markdown, no explanation."""


ANALYSIS_PROMPT = """You are a professional real estate appraiser analyzing price positioning.

TASK: Analyze how the target property's asking price compares to the provided comparable sales.

RULES:
1. Calculate the true median sale price from the comps (not listing price)
2. Calculate price per sqft for target and comp median
3. target_vs_median_pct = ((target_asking - comp_median_sale) / comp_median_sale) * 100
4. Each adjustment factor must cite a SPECIFIC condition difference vs comps
5. adjustment_pct values: renovated kitchen +2 to +4%, old roof -1 to -3%, etc.
6. fair_value_range should be comp_median +/- 3-5% based on condition
7. verdict options: "fairly priced" / "slightly overpriced" / "significantly overpriced" / "underpriced"

TARGET PROPERTY:
{target}

COMPARABLE SALES:
{comps}

Return JSON only — no markdown, no explanation:
{{
  "comp_median_price": 0,
  "comp_median_price_per_sqft": 0,
  "target_price_per_sqft": 0,
  "target_vs_median_pct": 0.0,
  "price_delta_explanation": "This property is X% above/below the comp median of $X because...",
  "adjustment_factors": [
    {{"factor": "Kitchen renovated 2020 vs comp average", "impact_pct": 2.5}},
    {{"factor": "Roof age 8 years vs comp average 12 years", "impact_pct": -1.0}}
  ],
  "fair_value_range": {{"low": 0, "high": 0}},
  "verdict": "fairly priced"
}}"""


@tool
def find_comparable_sales(property_info: str) -> str:
    """
    Find the most similar recently sold properties for a given property.
    Input: JSON string with address, sqft, bedrooms, bathrooms, year_built, asking_price.
    Returns 5 comparable sales with full details.
    """
    prompt = COMP_PROMPT.format(
        property_info=property_info,
        schema=COMP_SCHEMA
    )
    response = llm.invoke(prompt)
    return response.content


@tool
def analyze_price_vs_comps(target_and_comps: str) -> str:
    """
    Analyze how a target property's price compares to comparable sales.
    Input: JSON string with target property and list of comps.
    """
    try:
        data   = json.loads(target_and_comps)
        target = json.dumps(data.get("target", {}), indent=2)
        comps  = json.dumps(data.get("comps", []), indent=2)
    except Exception:
        target = target_and_comps
        comps  = "[]"

    prompt = ANALYSIS_PROMPT.format(target=target, comps=comps)
    response = llm.invoke(prompt)
    return response.content


def run_comp_analysis(form, condition_score: int) -> dict:
    """
    Full comparable sales analysis pipeline.
    """
    print("  Finding comparable sales...")

    property_info = json.dumps({
        "address":         form.address,
        "asking_price":    form.asking_price,
        "sqft":            form.sqft,
        "bedrooms":        form.bedrooms,
        "bathrooms":       form.bathrooms,
        "year_built":      form.year_built,
        "condition_score": condition_score,
        "kitchen_renovated": form.kitchen_renovated,
        "roof_age_years":    form.roof_age_years,
        "recent_upgrades":   form.recent_upgrades,
    })

    comps_raw  = find_comparable_sales.invoke(property_info)
    comps_list = parse_json(comps_raw)

    if not comps_list or not isinstance(comps_list, list):
        print("  Warning: Could not parse comparable sales")
        return {"error": "Could not find comparable sales", "comps": [], "analysis": {}}

    print("  Found {} comparable sales".format(len(comps_list)))

    # Analyze price vs comps
    target_and_comps = json.dumps({
        "target": {
            "address":           form.address,
            "asking_price":      form.asking_price,
            "sqft":              form.sqft,
            "bedrooms":          form.bedrooms,
            "bathrooms":         form.bathrooms,
            "year_built":        form.year_built,
            "condition_score":   condition_score,
            "kitchen_renovated": form.kitchen_renovated,
            "roof_age_years":    form.roof_age_years,
        },
        "comps": comps_list
    })

    analysis_raw = analyze_price_vs_comps.invoke(target_and_comps)
    analysis     = parse_json(analysis_raw)

    if isinstance(analysis, list):
        analysis = analysis[0] if analysis else {}

    return {
        "comps":    comps_list,
        "analysis": analysis,
    }
