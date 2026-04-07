from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.tools.property_tools import (
    search_property_market, search_school_ratings,
    search_neighborhood, calculate_mortgage,
    calculate_roi, predict_property_price
)
from app.models.property_form import InteriorConditionForm
from app.config import MODEL_SMART
import json

llm = ChatAnthropic(model=MODEL_SMART, temperature=0, max_tokens=2048)

def parse_json(raw):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned.strip())
    except:
        return {"error": "parse failed", "raw": raw[:300]}

def compute_condition_score(form):
    score = 70
    if form.kitchen_renovated:
        age = 2026 - (form.kitchen_reno_year or 2010)
        score += max(0, 10 - age)
    if form.master_bath_renovated:
        age = 2026 - (form.master_bath_reno_year or 2010)
        score += max(0, 6 - age)
    cond_map = {"excellent": 5, "good": 3, "fair": 0, "poor": -5, "unknown": 0}
    score += cond_map.get(form.flooring_condition.value, 0)
    if form.roof_age_years:
        if form.roof_age_years < 5:    score += 8
        elif form.roof_age_years < 10: score += 4
        elif form.roof_age_years > 20: score -= 8
    score += cond_map.get(form.roof_condition.value, 0)
    if form.foundation_issues:
        score -= 15
    for age in [form.furnace_age_years, form.ac_age_years, form.water_heater_age]:
        if age and age > 15:
            score -= 3
    final = max(0, min(100, score))
    grade = "Excellent" if final >= 85 else "Good" if final >= 70 else "Fair" if final >= 55 else "Poor"
    return {"condition_score": final, "grade": grade}

def analyze_property(form, inspection_result=None):
    print("Analyzing property: " + form.address)

    condition = compute_condition_score(form)
    cs = condition["condition_score"]
    cg = condition["grade"]
    print("  Condition score: " + str(cs) + "/100 (" + cg + ")")

    print("  Searching market data...")
    market_data = search_property_market.invoke(form.address)
    search_school_ratings.invoke(form.address)

    print("  Running financial calculations...")
    mortgage_result = calculate_mortgage.invoke(
        "price=" + str(form.asking_price) + " rate=7.2 years=30"
    )

    roi_result = None
    if form.report_type == "investor" and form.expected_monthly_rent:
        roi_result = calculate_roi.invoke(
            "price=" + str(form.asking_price) +
            " monthly_rent=" + str(form.expected_monthly_rent) +
            " expenses=" + str(form.monthly_expenses or 500)
        )

    print("  Generating price prediction...")
    property_data = json.dumps({
        "address": form.address,
        "asking_price": form.asking_price,
        "sqft": form.sqft,
        "bedrooms": form.bedrooms,
        "bathrooms": form.bathrooms,
        "year_built": form.year_built,
        "condition_score": condition["condition_score"],
        "condition_grade": condition["grade"],
        "kitchen_renovated": form.kitchen_renovated,
        "roof_age_years": form.roof_age_years,
        "market_context": market_data[:500],
        "inspection_repair_cost": (
            inspection_result.get("total_estimated_repair_cost", {})
            if inspection_result else None
        ),
    })
    price_prediction = parse_json(predict_property_price.invoke(property_data))

    print("  Generating recommendation...")
    mortgage = json.loads(mortgage_result)

    inspection_summary = ""
    if inspection_result:
        cost = inspection_result.get("total_estimated_repair_cost", {})
        low  = cost.get("low", 0)
        high = cost.get("high", 0)
        crit = inspection_result.get("critical_issues_count", 0)
        inspection_summary = "Inspection: " + str(crit) + " critical issues. Repair cost: $" + str(low) + "-$" + str(high)

    roi_summary = ""
    if roi_result:
        roi = json.loads(roi_result)
        cap  = roi.get("cap_rate_percent")
        cf   = roi.get("annual_cash_flow")
        roi_summary = "Cap Rate: " + str(cap) + "%, Annual Cash Flow: $" + str(cf)

    rec_prompt = ChatPromptTemplate.from_template(
        "You are a real estate advisor. Generate a purchase recommendation.\n"
        "Property: {address}\n"
        "Asking Price: ${asking_price}\n"
        "Condition Score: {condition_score}/100 ({condition_grade})\n"
        "Estimated Value: ${estimated_value}\n"
        "Monthly Mortgage: ${monthly_payment}\n"
        "{inspection_summary}\n"
        "{roi_summary}\n"
        "Market Context: {market_context}\n\n"
        "Return JSON only:\n"
        '{{"verdict": "BUY/NEGOTIATE/AVOID", "confidence": 0.0, '
        '"summary": "2-3 sentence summary", '
        '"price_assessment": "fair/overpriced/underpriced", '
        '"key_strengths": ["strength 1"], '
        '"key_risks": ["risk 1"], '
        '"negotiation_leverage": "what to use"}}'
    )

    rec_raw = (rec_prompt | llm | StrOutputParser()).invoke({
        "address":           form.address,
        "asking_price":      form.asking_price,
        "condition_score":   condition["condition_score"],
        "condition_grade":   condition["grade"],
        "estimated_value":   price_prediction.get("estimated_value", 0),
        "monthly_payment":   mortgage.get("monthly_payment", 0),
        "inspection_summary": inspection_summary,
        "roi_summary":       roi_summary,
        "market_context":    market_data[:400],
    })

    return {
        "address":          form.address,
        "asking_price":     form.asking_price,
        "report_type":      form.report_type,
        "condition":        condition,
        "price_prediction": price_prediction,
        "mortgage":         mortgage,
        "roi":              json.loads(roi_result) if roi_result else None,
        "recommendation":   parse_json(rec_raw),
        "inspection":       inspection_result,
    }
