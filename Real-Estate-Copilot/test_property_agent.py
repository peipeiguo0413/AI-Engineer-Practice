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

# Validation
val = result.get("validation", {})
print(f"\n{'='*60}")
print(f"VALIDATION")
print(f"{'='*60}")
print(f"Passed:      {val.get('passed')}")
print(f"Trust Level: {val.get('trust_level')}")
if val.get('errors'):
    print(f"Errors:")
    for e in val['errors']:
        print(f"  ✗ {e}")
if val.get('warnings'):
    print(f"Warnings:")
    for w in val['warnings']:
        print(f"  ⚠ {w}")

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

print("\n\n=== VALIDATION TEST: Overpriced Property ===")
from app.models.property_form import InteriorConditionForm, Condition, FlooringType

bad_form = InteriorConditionForm(
    address="999 Problem Street, Seattle, WA 98101",
    asking_price=1500000,  # 要价极高
    sqft=1800,
    bedrooms=3,
    bathrooms=2.0,
    year_built=1965,
    report_type="buyer",
    kitchen_renovated=False,
    kitchen_condition=Condition.poor,
    master_bath_renovated=False,
    other_baths_condition=Condition.poor,
    flooring_type=FlooringType.carpet,
    flooring_age_years=30,
    flooring_condition=Condition.poor,
    roof_age_years=25,
    roof_condition=Condition.poor,
    foundation_issues=True,   # 有基础问题
    furnace_age_years=20,
    ac_age_years=20,
    water_heater_age=18,
)

bad_result = analyze_property(bad_form)
bad_val = bad_result.get("validation", {})
print(f"Verdict:     {bad_result['recommendation'].get('verdict')}")
print(f"Price Estimate: ${bad_result['price_prediction'].get('estimated_value', 0):,.0f}")
print(f"Asking:         ${bad_form.asking_price:,.0f}")
print(f"Passed:      {bad_val.get('passed')}")
print(f"Trust Level: {bad_val.get('trust_level')}")
if bad_val.get('warnings'):
    print("Warnings:")
    for w in bad_val['warnings']:
        print(f"  ⚠ {w}")
# Comparable Sales
print("\n\n=== COMPARABLE SALES (standalone) ===")
comp = result.get("comps", {})
analysis = comp.get("analysis", {})
comps_list = comp.get("comps", [])

if analysis:
    print(f"Comp Median Price:   ${analysis.get('comp_median_price', 0):,.0f}")
    print(f"Target vs Median:    {analysis.get('target_vs_median_pct', 0):+.1f}%")
    low = analysis.get('fair_value_range', {}).get('low', 0)
    high = analysis.get('fair_value_range', {}).get('high', 0)
    print(f"Fair Value Range:    ${low:,.0f} – ${high:,.0f}")
    print(f"Verdict:             {analysis.get('verdict', '')}")
    print(f"\nPrice Delta Explanation:")
    print(f"  {analysis.get('price_delta_explanation', '')}")
    print(f"\nAdjustment Factors:")
    for factor in analysis.get('adjustment_factors', []):
        impact = factor.get('impact_pct', 0)
        sign = "+" if impact > 0 else ""
        print(f"  {sign}{impact}%  {factor.get('factor', '')}")
    print(f"\nTop Comparableales:")
    for i, c in enumerate(comps_list[:3], 1):
        print(f"  {i}. {c.get('address', '')} — ${c.get('sold_price', 0):,.0f} ({c.get('sqft', 0):,} sqft, similarity: {c.get('similarity_score', 0)})")
else:
    print("No comp analysis available")
