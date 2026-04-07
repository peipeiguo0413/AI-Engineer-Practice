import sys
sys.path.insert(0, ".")

from app.models.property_form import InteriorConditionForm, Condition, FlooringType
from app.agents.property_agent import analyze_property

# Test with a sample property
form = InteriorConditionForm(
    address="1234 Maple Street, Seattle, WA 98101",
    asking_price=750000,
    sqft=1800,
    bedrooms=3,
    bathrooms=2.0,
    year_built=1998,
    report_type="buyer",
    kitchen_renovated=True,
    kitchen_reno_year=2020,
    kitchen_condition=Condition.excellent,
    master_bath_renovated=False,
    other_baths_condition=Condition.fair,
    flooring_type=FlooringType.hardwood,
    flooring_age_years=26,
    flooring_condition=Condition.good,
    roof_age_years=8,
    roof_condition=Condition.good,
    furnace_age_years=12,
    ac_age_years=8,
    water_heater_age=10,
    recent_upgrades="New kitchen in 2020, roof replaced 2016",
    known_issues="Minor grading issue around foundation",
)

result = analyze_property(form)

print("\n" + "="*60)
print("PROPERTY ANALYSIS RESULT")
print("="*60)
print(f"\nAddress:     {result['address']}")
print(f"Asking:      ${result['asking_price']:,.0f}")
print(f"Condition:   {result['condition']['condition_score']}/100 ({result['condition']['grade']})")

pred = result['price_prediction']
print(f"\nAI Price Estimate: ${pred.get('estimated_value', 0):,.0f}")
print(f"Confidence Interval: ${pred.get('confidence_interval', {}).get('low', 0):,.0f} – ${pred.get('confidence_interval', {}).get('high', 0):,.0f}")
print(f"Reasoning: {pred.get('reasoning', '')}")

rec = result['recommendation']
print(f"\nVerdict:     {rec.get('verdict')} (confidence: {rec.get('confidence')})")
print(f"Summary:     {rec.get('summary')}")
print(f"Assessment:  {rec.get('price_assessment')}")
print(f"\nStrengths:")
for s in rec.get('key_strengths', []):
    print(f"  + {s}")
print(f"Risks:")
for r in rec.get('key_risks', []):
    print(f"  - {r}")
print(f"\nNegotiation leverage: {rec.get('negotiation_leverage')}")

mort = result['mortgage']
print(f"\nMonthly Payment: ${mort.get('monthly_payment', 0):,.0f}")
print(f"Total Interest:  ${mort.get('total_interest', 0):,.0f}")

print("\n\n=== COMBINED: Inspection + Interior Form ===")
from app.rag.inspection_rag import analyze_inspection_report

inspection = analyze_inspection_report(
    "/Users/peipeiguo/Desktop/AI Agent Learning/user_data/Inspection_Report.pdf"
)

result_combined = analyze_property(form, inspection_result=inspection)
rec  = result_combined["recommendation"]
pred = result_combined["price_prediction"]
cost = inspection.get("total_estimated_repair_cost", {})

print(f"\nVerdict:         {rec.get('verdict')}")
print(f"Price Estimate:  ${pred.get('estimated_value', 0):,.0f}")
print(f"Repair Cost:     ${cost.get('low', 0):,} – ${cost.get('high', 0):,}")
print(f"Summary:         {rec.get('summary')}")
print(f"Negotiation:     {rec.get('negotiation_leverage', '')[:150]}")