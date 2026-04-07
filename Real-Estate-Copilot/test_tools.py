import sys
sys.path.insert(0, ".")

from app.tools.property_tools import calculate_mortgage, calculate_roi

print("=== Mortgage Calculator ===")
result = calculate_mortgage.invoke(
    "price=650000 down_payment=130000 rate=7.2 years=30"
)
print(result)

print("\n=== ROI Calculator ===")
result = calculate_roi.invoke(
    "price=650000 monthly_rent=3200 expenses=600 down_payment=130000"
)
print(result)
