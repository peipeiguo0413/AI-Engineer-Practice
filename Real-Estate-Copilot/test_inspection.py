import sys
sys.path.insert(0, ".")

from app.rag.inspection_rag import analyze_inspection_report
from app.reports.inspection_report_pdf import generate_inspection_pdf

result = analyze_inspection_report(
    "/Users/peipeiguo/Desktop/AI Agent Learning/user_data/Inspection_Report.pdf"
)

print("\n" + "="*60)
print("INSPECTION ANALYSIS RESULT")
print("="*60)

print(f"\nRecommendation: {result.get('recommendation')}")
print(f"Confidence:     {result.get('confidence')}")
print(f"Summary:        {result.get('summary')}")
print(f"\nTotal estimated repair cost: {result.get('total_estimated_repair_cost')}")
print(f"Critical issues: {result.get('critical_issues_count')}")
print(f"Major issues:    {result.get('major_issues_count')}")

print(f"\nAll Findings ({len(result.get('findings', []))}):")
for i, f in enumerate(result.get('findings', []), 1):
    severity_emoji = {
        "Critical": "🚨",
        "Major": "⚠️",
        "Minor": "🔧",
        "Informational": "ℹ️"
    }.get(f['severity'], "•")
    print(f"  {i:2}. [{f['severity']:13}] {f['issue'][:60]}")
    print(f"       Cost: ${f['estimated_repair_cost_usd']['low']:,}–${f['estimated_repair_cost_usd']['high']:,}")
    print(f"       Action: {f['recommendation'][:60]}")
    print()

print(f"\nKey Concerns:")
for concern in result.get('key_concerns', []):
    print(f"  • {concern}")

# Add at the bottom of test_inspection.
pdf_path = generate_inspection_pdf(
    result=result,
    output_path="./outputs/inspection_analysis.pdf",
    property_address="11409 107th place NE, kirkland, wa 98033",
    agent_name="Peipei Guo"  # your name!
)
print(f"\nPDF report generated: {pdf_path}")