from app.agents.property_agent import analyze_property
from app.models.property_form import InteriorConditionForm
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import json

def run_single_analysis(property_input: dict) -> dict:
    """Run analyze_property for one property. Used in parallel execution."""
    try:
        form = InteriorConditionForm(**property_input)
        result = analyze_property(form)
        result["input"] = property_input
        return result
    except Exception as e:
        return {
            "error": str(e),
            "address": property_input.get("address", "Unknown"),
            "input": property_input,
        }

def run_comparison(properties: List[dict], report_type: str = "buyer") -> dict:
    """
    Run parallel analysis on up to 5 properties and return comparison result.
    
    Each property dict should contain the same fields as InteriorConditionForm.
    Returns structured comparison with scoring matrix and recommendation.
    """
    if len(properties) < 2:
        return {"error": "Need at least 2 properties to compare"}
    if len(properties) > 5:
        return {"error": "Maximum 5 properties allowed"}

    print(f"\nComparing {len(properties)} properties in parallel...")

    # Run analyses in parallel
    results = [None] * len(properties)
    with ThreadPoolExecutor(max_workers=len(properties)) as executor:
        future_to_idx = {
            executor.submit(run_single_analysis, prop): i
            for i, prop in enumerate(properties)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()
            addr = properties[idx].get("address", f"Property {idx+1}")
            print(f"  Done: {addr}")

    # Build scoring matrix
    scored = []
    for i, result in enumerate(results):
        if result.get("error"):
            scored.append({
                "rank":     i + 1,
                "address":  result.get("address", f"Property {i+1}"),
                "error":    result["error"],
            })
            continue

        rec   = result.get("recommendation", {})
        pred  = result.get("price_prediction", {})
        cond  = result.get("condition", {})
        mort  = result.get("mortgage", {})
        insp  = result.get("inspection") or {}
        comp  = result.get("comps") or {}
        comp_analysis = comp.get("analysis") or {}

        asking = result.get("asking_price", 0)
        est    = pred.get("estimated_value", 0)
        delta_pct = ((est - asking) / asking * 100) if asking else 0

        has_inspection = bool(insp)
        scored.append({
            "address":          result.get("address", f"Property {i+1}"),
            "asking_price":     asking,
            "estimated_value":  est,
            "delta_pct":        round(delta_pct, 1),
            "condition_score":  cond.get("condition_score", 0),
            "condition_grade":  cond.get("grade", ""),
            "verdict":          rec.get("verdict", "N/A"),
            "confidence":       rec.get("confidence", 0),
            "monthly_payment":  mort.get("monthly_payment", 0),
            "comp_median":      comp_analysis.get("comp_median_price", 0),
            "price_vs_comp":    comp_analysis.get("target_vs_median_pct", 0),
            "fair_value_low":   comp_analysis.get("fair_value_range", {}).get("low", 0),
            "fair_value_high":  comp_analysis.get("fair_value_range", {}).get("high", 0),
            "has_inspection":   has_inspection,
            "critical_issues":  insp.get("critical_issues_count", None) if has_inspection else None,
            "major_issues":     insp.get("major_issues_count", None) if has_inspection else None,
            "repair_low":       (insp.get("total_estimated_repair_cost") or {}).get("low", None) if has_inspection else None,
            "repair_high":      (insp.get("total_estimated_repair_cost") or {}).get("high", None) if has_inspection else None,
            "summary":          rec.get("summary", ""),
            "key_strengths":    rec.get("key_strengths", []),
            "key_risks":        rec.get("key_risks", []),
            "negotiation":      rec.get("negotiation_leverage", ""),
            "full_result":      result,
        })

    # Score each property (0-100 composite)
    valid = [s for s in scored if not s.get("error")]
    if valid:
        _add_composite_scores(valid)
        valid.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
        for i, s in enumerate(valid):
            s["rank"] = i + 1

    return {
        "properties":    scored,
        "total":         len(properties),
        "valid":         len(valid),
        "report_type":   report_type,
        "top_pick":      valid[0]["address"] if valid else None,
        "top_pick_reason": _top_pick_reason(valid[0]) if valid else "",
    }


def _add_composite_scores(properties: List[dict]):
    """
    Score each property 0-100 across 5 dimensions.
    Modifies list in place.
    """
    # Normalize each dimension across all properties
    def normalize(values, higher_is_better=True):
        mn, mx = min(values), max(values)
        if mx == mn:
            return [50.0] * len(values)
        if higher_is_better:
            return [100 * (v - mn) / (mx - mn) for v in values]
        else:
            return [100 * (mx - v) / (mx - mn) for v in values]

    n = len(properties)
    if n == 0:
        return

    # Dimension scores (weights sum to 100)
    # Check if any property has inspection data
    has_any_inspection = any(p.get("has_inspection") for p in properties)

    if has_any_inspection:
        weights = {
            "price_value":   25,
            "condition":     20,
            "repair_cost":   20,
            "comp_position": 20,
            "confidence":    15,
        }
    else:
        weights = {
            "price_value":   30,
            "condition":     25,
            "repair_cost":    0,  # skip — no inspection data
            "comp_position": 25,
            "confidence":    20,
        }

    delta_scores     = normalize([p["delta_pct"]       for p in properties], True)
    condition_scores = normalize([p["condition_score"] for p in properties], True)
    comp_scores      = normalize([p["price_vs_comp"]   for p in properties], False)
    conf_scores      = normalize([p["confidence"]      for p in properties], True)

    if has_any_inspection:
        # Use 0 repair cost for properties without inspection (neutral score)
        repair_vals  = [p["repair_high"] if p.get("has_inspection") and p["repair_high"] is not None
                        else 0 for p in properties]
        repair_scores = normalize(repair_vals, False)
    else:
        repair_scores = [0.0] * len(properties)

    for i, prop in enumerate(properties):
        composite = (
            delta_scores[i]     * weights["price_value"]   / 100 +
            condition_scores[i] * weights["condition"]     / 100 +
            repair_scores[i]    * weights["repair_cost"]   / 100 +
            comp_scores[i]      * weights["comp_position"] / 100 +
            conf_scores[i]      * weights["confidence"]    / 100
        )
        prop["composite_score"] = round(composite, 1)
        prop["has_inspection_data"] = has_any_inspection
        prop["dim_scores"] = {
            "price_value":   round(delta_scores[i],     1),
            "condition":     round(condition_scores[i], 1),
            "repair_cost":   round(repair_scores[i],    1) if has_any_inspection else "N/A",
            "comp_position": round(comp_scores[i],      1),
            "confidence":    round(conf_scores[i],      1),
        }


def _top_pick_reason(prop: dict) -> str:
    reasons = []
    if prop.get("delta_pct", 0) > 0:
        reasons.append(f"priced {prop['delta_pct']:.1f}% below estimated value")
    if prop.get("condition_score", 0) >= 80:
        reasons.append(f"strong condition score ({prop['condition_score']}/100)")
    if prop.get("critical_issues", 0) == 0:
        reasons.append("zero critical inspection issues")
    repair = prop.get("repair_high", 0)
    if repair and repair < 5000:
        reasons.append(f"low repair costs (under ${repair:,})")
    if not reasons:
        reasons.append("best overall composite score across all dimensions")
    return "Top pick because: " + ", ".join(reasons) + "."
