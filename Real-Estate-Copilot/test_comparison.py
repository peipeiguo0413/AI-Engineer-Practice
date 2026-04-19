import sys
sys.path.insert(0, ".")

from app.agents.comparison_agent import run_comparison

properties = [
    {
        "address":        "1234 Maple Street, Seattle, WA 98101",
        "asking_price":   750000,
        "sqft":           1800,
        "bedrooms":       3,
        "bathrooms":      2.0,
        "year_built":     1998,
        "report_type":    "buyer",
        "kitchen_renovated":   True,
        "kitchen_reno_year":   2020,
        "roof_age_years":      8,
        "roof_condition":      "good",
        "furnace_age_years":   12,
    },
    {
        "address":        "567 Pine Avenue, Seattle, WA 98103",
        "asking_price":   820000,
        "sqft":           2100,
        "bedrooms":       4,
        "bathrooms":      2.5,
        "year_built":     2005,
        "report_type":    "buyer",
        "kitchen_renovated":   False,
        "roof_age_years":      5,
        "roof_condition":      "excellent",
        "furnace_age_years":   8,
    },
]

print("=== MULTI-PROPERTY COMPARISON TEST ===\n")
result = run_comparison(properties, report_type="buyer")

print(f"Total properties: {result['total']}")
print(f"Top pick: {result['top_pick']}")
print(f"Reason: {result['top_pick_reason']}")
print()

for p in result["properties"]:
    if p.get("error"):
        print(f"ERROR: {p['address']} - {p['error']}")
        continue
    print(f"Rank #{p['rank']}: {p['address']}")
    print(f"  Composite Score:  {p.get('composite_score', 0):.1f}/100")
    print(f"  Verdict:          {p['verdict']}")
    print(f"  Asking Price:     ${p['asking_price']:,.0f}")
    print(f"  Estimated Value:  ${p['estimated_value']:,.0f} ({p['delta_pct']:+.1f}%)")
    print(f"  Condition Score:  {p['condition_score']}/100")
    repair_str = (f"${p['repair_low']:,} - ${p['repair_high']:,}"
                  if p.get('repair_low') is not None
                  else "N/A (no inspection data)")
    print(f"  Repair Cost:      {repair_str}")
    print(f"  Dim Scores:       {p.get('dim_scores', {})}")
    print()

# Generate Comparison PDF
print("\n=== GENERATING COMPARISON PDF ===")
from app.reports.comparison_pdf import generate_comparison_pdf
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
pdf_path = generate_comparison_pdf(
    comparison_result=result,
    output_path=f"./outputs/comparison_{timestamp}.pdf",
    agent_name="Peipei Guo",
    agent_license="WA#12345",
)
print(f"Report saved: {pdf_path}")
