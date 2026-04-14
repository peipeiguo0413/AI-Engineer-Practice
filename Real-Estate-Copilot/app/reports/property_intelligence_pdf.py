from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from datetime import datetime
import os

# =============================================================================
# TODO (Phase 1.5): True Cost Calculator — PDF Section 2 update
# Replace current simple mortgage table with full cost breakdown:
#   Monthly Mortgage:      $4,073
#   Property Tax:          $  625  (~1% of value / 12)
#   Homeowner Insurance:   $  150
#   HOA:                   $    0
#   Maintenance Reserve:   $  375  (1% rule)
#   Utilities (estimate):  $  200
#   ─────────────────────────────
#   TRUE MONTHLY COST:     $5,423  ← highlight this number
#   vs Zillow shows:       $4,073
#   Hidden costs:          $1,350/mo ($16,200/yr)
# =============================================================================

# =============================================================================
# TODO (Phase 1.5): Neighborhood Intelligence — Ps/risks:
#   Neighborhood Risk Flags table:
#   ┌─────────────────┬──────────────────────────────────┐
#   │ Flood Zone      │ Zone X — minimal risk            │
#   │ Crime Trend     │ Declining — down 12% YoY         │
#   │ Noise Level     │ Moderate — 0.3mi from I-5        │
#   │ Development     │ 2 mixed-use projects within 0.5mi│
#   │ School Rating   │ 8/10 — Lincoln Elementary        │
#   │ Walk Score      │ 82 — Very Walkable               │
#   └─────────────────┴──────────────────────────────────┘
# =============================================================================

# =============================================================================
# TODO (Phase 1.5): 10-Year Cost Projection — PDF Section 4 update
# Add after in──────────────────────┤
#   │ HVAC (age 12yr)          │ $4k-$6k      │ Budget for replacement yr 3-5│
#   │ Roof debris / vents      │ $500-$1,500  │ Annual maintenance           │
#   │ Grading/drainage         │ $1k-$3k      │ Fix now to avoid foundation  │
#   └──────────────────────────┴──────────────┴──────────────────────────────┘
#   Total 10-Year Outlook: $8,000 – $18,000
# =============================================================================

BLUE       = HexColor("#1B4F8A")
ORANGE     = HexColor("#E07A2F")
GREEN      = HexColor("#2E7D32")
RED        = HexColor("#C62828")
YELLOW     = HexColor("#F9A825")
LIGHT_BLUE = HexColor("#EBF3FB")
LIGHT_GRAY = HexColor("#F5F5F5")
MID_GRAY   = HexColor("#CCCCCC")
DARK_GRAY  = HexColor("#444444")

VERDICT_COLORS = {
    "BUY": GREEN, "NEGOTIATE": ORANGE, "AVOID": RED,
    "WORTH VISITING": GREEN, "BORDERLINE": ORANGE, "SKIP": RED,
}
SEV_COLORS = {
    "Critical": RED, "Major": ORANGE, "Minor": YELLOW, "Informational": BLUE
}

W = letter[0] - 1.4 * inch


def S(name, **kw):
    return ParagraphStyle(name, **kw)


ST = {
    "cover_title": S("ct", fontName="Helvetica-Bold", fontSize=28,
                     textColor=white, alignment=TA_CENTER, leading=34),
    "cover_sub":   S("cs", fontName="Helvetica", fontSize=13,
                     textColor=HexColor("#B8D4F0"), alignment=TA_CENTER, leading=18),
    "cover_date":  S("cd", fontName="Helvetica-Oblique", fontSize=10,
                     textColor=HexColor("#7BAFD4"), alignment=TA_CENTER),
    "cover_agent": S("ca", fontName="Helvetica-Bold", fontSize=11,
                     textColor=white, alignment=TA_CENTER),
    "h2":   S("h2", fontName="Helvetica-Bold", fontSize=13, textColor=BLUE,
               leading=16, spaceBefore=14, spaceAfter=6),
    "h3":   S("h3", fontName="Helvetica-Bold", fontSize=11, textColor=ORANGE,
               leading=14, spaceBefore=10, spaceAfter=4),
    "body": S("body", fontName="Helvetica", fontSize=10, textColor=DARK_GRAY,
               leading=15, spaceAfter=4, alignment=TA_LEFT),
    "body_j": S("bodyj", fontName="Helvetica", fontSize=10, textColor=DARK_GRAY,
                 leading=15, spaceAfter=4, alignment=TA_JUSTIFY),
    "bullet": S("bul", fontName="Helvetica", fontSize=10, textColor=DARK_GRAY,
                 leading=13, leftIndent=12, spaceAfter=2,
                 bulletText="\u2022", bulletIndent=2),
    "label":  S("lbl", fontName="Helvetica-Bold", fontSize=9,
                 textColor=BLUE, leading=12),
    "value":  S("val", fontName="Helvetica", fontSize=9,
                 textColor=DARK_GRAY, leading=12),
    "th":     S("th", fontName="Helvetica-Bold", fontSize=8.5,
                 textColor=white, leading=11),
    "td":     S("td", fontName="Helvetica", fontSize=8.5,
                 textColor=DARK_GRAY, leading=12),
    "td_b":   S("tdb", fontName="Helvetica-Bold", fontSize=8.5,
                 textColor=DARK_GRAY, leading=12),
    "link":   S("lnk", fontName="Helvetica", fontSize=8,
                 textColor=BLUE, leading=11),
    "disc":   S("disc", fontName="Helvetica-Oblique", fontSize=8,
                 textColor=MID_GRAY, leading=11, alignment=TA_JUSTIFY),
}


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(MID_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(0.7 * inch, 0.55 * inch, letter[0] - 0.7 * inch, 0.55 * inch)
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawCentredString(
        letter[0] / 2, 0.38 * inch,
        "Real Estate Copilot  |  Property Intelligence Report  |  Confidential"
    )
    if doc.page > 1:
        canvas.drawRightString(letter[0] - 0.7 * inch, 0.38 * inch, str(doc.page))
    canvas.restoreState()


def sp(n=8):
    return Spacer(1, n)


def bul(text):
    return Paragraph(text, ST["bullet"])


def kv_table(rows, col1_w=1.6 * inch):
    data = []
    ts = [
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for i, (k, v) in enumerate(rows):
        data.append([Paragraph(k, ST["label"]), Paragraph(v, ST["value"])])
        bg  = LIGHT_BLUE if i % 2 == 0 else white
        bg2 = white if i % 2 == 0 else LIGHT_GRAY
        ts += [("BACKGROUND", (0, i), (0, i), bg),
               ("BACKGROUND", (1, i), (1, i), bg2)]
    t = Table(data, colWidths=[col1_w, W - col1_w])
    t.setStyle(TableStyle(ts))
    return t


def section_badge(num, title):
    t = Table([[
        Paragraph("0{}".format(num), ParagraphStyle("sn",
            fontName="Helvetica-Bold", fontSize=11, textColor=white,
            alignment=TA_CENTER, leading=14)),
        Paragraph(title, ParagraphStyle("st",
            fontName="Helvetica-Bold", fontSize=14, textColor=BLUE, leading=18))
    ]], colWidths=[0.42 * inch, W - 0.42 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), BLUE),
        ("BACKGROUND", (1, 0), (1, 0), LIGHT_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (0, 0), 6),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("BOX", (0, 0), (-1, -1), 0.5, MID_GRAY),
    ]))
    return t


def verdict_box(verdict, confidence, summary):
    color = VERDICT_COLORS.get(verdict, DARK_GRAY)
    try:
        conf_pct = int(float(confidence or 0) * 100)
    except Exception:
        conf_pct = 0
    inner = [
        Paragraph(verdict, ParagraphStyle("vb",
            fontName="Helvetica-Bold", fontSize=30,
            textColor=color, alignment=TA_CENTER, leading=36)),
        Spacer(1, 4),
        Paragraph(
            "Confidence: {}%".format(conf_pct),
            ParagraphStyle("vc", fontName="Helvetica", fontSize=11,
                           textColor=DARK_GRAY, alignment=TA_CENTER, leading=14)
        ),
        Spacer(1, 8),
        # Summary left-aligned
        Paragraph(summary or "", ParagraphStyle("vs",
            fontName="Helvetica", fontSize=10, textColor=DARK_GRAY,
            alignment=TA_LEFT, leading=15, leftIndent=6, rightIndent=6)),
    ]
    t = Table([[inner]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 2, color),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    return t


def sr_table(strengths, risks):
    max_len = max(len(strengths), len(risks))
    data = [[Paragraph("Strengths", ST["label"]), Paragraph("Risks", ST["label"])]]
    for i in range(max_len):
        s = ("+ " + strengths[i]) if i < len(strengths) else ""
        r = ("- " + risks[i])     if i < len(risks)     else ""
        data.append([Paragraph(s, ST["value"]), Paragraph(r, ST["value"])])
    t = Table(data, colWidths=[W * 0.5, W * 0.5])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID",       (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return t


def comp_table(comp_list):
    """Full comparable sales table with all fields."""
    headers = [
        "Address", "List Price", "Sale Price", "Sale Date",
        "DOM", "Sqft", "Bed/Bath", "Built", "HOA/mo",
        "Cond.", "Similarity"
    ]
    col_widths = [
        W*0.22, W*0.09, W*0.09, W*0.09,
        W*0.05, W*0.07, W*0.07, W*0.06, W*0.07,
        W*0.06, W*0.08
    ]
    data = [[Paragraph(h, ST["th"]) for h in headers]]

    for i, c in enumerate(comp_list):
        hoa = c.get("hoa_monthly", 0) or 0
        hoa_str = "${:,}".format(int(hoa)) if hoa and hoa > 0 else "None"
        row = [
            Paragraph(c.get("address", ""), ST["td"]),
            Paragraph("${:,}".format(int(c.get("listing_price", 0) or 0)), ST["td"]),
            Paragraph("${:,}".format(int(c.get("sale_price", 0) or 0)), ST["td_b"]),
            Paragraph(str(c.get("sale_date", "")), ST["td"]),
            Paragraph(str(c.get("days_on_market", "")), ST["td"]),
            Paragraph("{:,}".format(int(c.get("sqft", 0) or 0)), ST["td"]),
            Paragraph("{}bd/{}ba".format(
                c.get("bedrooms", ""), c.get("bathrooms", "")), ST["td"]),
            Paragraph(str(c.get("year_built", "")), ST["td"]),
            Paragraph(hoa_str, ST["td"]),
            Paragraph(str(c.get("condition_score", "")), ST["td"]),
            Paragraph("{}%".format(c.get("similarity_score", "")), ST["td_b"]),
        ]
        data.append(row)

    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(ts))
    return t


def comp_detail_table(comp_list):
    """Interior condition and listing URL details per comp."""
    data = [[
        Paragraph("Address", ST["th"]),
        Paragraph("Interior Condition", ST["th"]),
        Paragraph("Key Differences vs Target", ST["th"]),
        Paragraph("Listing", ST["th"]),
    ]]
    col_widths = [W * 0.22, W * 0.30, W * 0.30, W * 0.18]

    for c in comp_list:
        url = c.get("listing_url", "")
        url_text = ('<link href="' + url + '"><font color="#1B4F8A"><u>View listing</u></font></link>'
                    if url else "N/A")
        data.append([
            Paragraph(c.get("address", ""), ST["td"]),
            Paragraph(c.get("interior_condition", ""), ST["td"]),
            Paragraph(c.get("key_differences", ""), ST["td"]),
            Paragraph(url_text, ST["link"]),
        ])

    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(ts))
    return t


def generate_property_intelligence_pdf(
    result,
    output_path,
    property_address="Property Address",
    report_type="buyer",
    agent_name=None,
    agent_license=None,
):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    rec  = result.get("recommendation", {})
    pred = result.get("price_prediction", {})
    cond = result.get("condition", {})
    mort = result.get("mortgage", {})
    roi  = result.get("roi")
    insp = result.get("inspection")
    comp = result.get("comps") or {}
    comp_analysis = comp.get("analysis") or {}
    comp_list     = comp.get("comps") or []
    val  = result.get("validation", {})
    ask  = result.get("asking_price", 0)

    story = []

    # ── COVER ─────────────────────────────────────────────
    report_label = "Buyer Report" if report_type == "buyer" else "Investor Report"
    cover_content = [
        Spacer(1, 0.5 * inch),
        Paragraph("Property Intelligence Report", ST["cover_title"]),
        Spacer(1, 0.1 * inch),
        Paragraph("Real Estate Copilot  \u00b7  " + report_label, ST["cover_sub"]),
        Spacer(1, 0.08 * inch),
        Paragraph(
            property_address + "  \u00b7  " + datetime.now().strftime("%B %d, %Y"),
            ST["cover_date"]
        ),
    ]
    if agent_name:
        label = "Prepared by " + agent_name
        if agent_license:
            label += "  \u00b7  " + agent_license
        cover_content += [Spacer(1, 0.1 * inch), Paragraph(label, ST["cover_agent"])]
    cover_content.append(Spacer(1, 0.5 * inch))

    cover = Table([[cover_content]], colWidths=[W + 1.4 * inch])
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(cover)
    story.append(sp(20))

    # ═══════════════════════════════════════════════════════
    # SECTION 1: PURCHASE RECOMMENDATION
    # ═══════════════════════════════════════════════════════
    story.append(section_badge(1, "Purchase Recommendation"))
    story.append(sp(10))

    # Property summary card
    form_data = result.get("form_data", {})
    story.append(kv_table([
        ("Address",      property_address),
        ("Asking Price", "${:,.0f}".format(ask)),
        ("Size",         "{:,} sqft  \u00b7  {} bed  \u00b7  {} bath  \u00b7  Built {}".format(
            result.get("sqft", 0) or 0,
            result.get("bedrooms", 0) or 0,
            result.get("bathrooms", 0) or 0,
            result.get("year_built", "") or "")),
        ("Report Type",  report_type.capitalize()),
    ]))
    story.append(sp(12))
    story.append(verdict_box(
        rec.get("verdict", "N/A"),
        rec.get("confidence", 0),
        rec.get("summary", "")
    ))
    story.append(sp(12))

    # Trust level + price assessment
    trust = val.get("trust_level", "medium")
    trust_msg = "All validation checks passed" if trust == "high" else "Review warnings below"
    story.append(kv_table([
        ("Trust Level",      trust.upper() + "  \u2014  " + trust_msg),
        ("Price Assessment", rec.get("price_assessment", "").capitalize()),
    ]))
    if val.get("warnings"):
        story.append(sp(6))
        for w in val["warnings"]:
            story.append(bul("\u26a0  " + w))
    story.append(sp(14))

    # Property condition
    story.append(Paragraph("Property Condition", ST["h3"]))
    story.append(kv_table([
        ("Condition Score",
         "{}/100  \u2014  {}".format(
             cond.get("condition_score", 0), cond.get("grade", ""))),
    ]))
    story.append(sp(8))

    if insp:
        cost = insp.get("total_estimated_repair_cost", {})
        story.append(kv_table([
            ("Inspection Verdict", insp.get("recommendation", "")),
            ("Critical Issues",    str(insp.get("critical_issues_count", 0))),
            ("Major Issues",       str(insp.get("major_issues_count", 0))),
            ("Est. Repair Cost",   "${:,} \u2013 ${:,}".format(
                cost.get("low", 0), cost.get("high", 0))),
        ]))
        story.append(sp(8))

        findings = insp.get("findings", [])
        if findings:
            story.append(Paragraph("Inspection Findings:", ST["h3"]))
            fdata = [[Paragraph(h, ST["th"]) for h in
                      ["#", "Severity", "Issue", "Est. Cost", "Recommendation"]]]
            for i, f in enumerate(findings, 1):
                c   = f.get("estimated_repair_cost_usd", {})
                sev = f.get("severity", "")
                fdata.append([
                    Paragraph(str(i), ST["td"]),
                    Paragraph(sev, ParagraphStyle("fsev",
                        fontName="Helvetica-Bold", fontSize=8,
                        textColor=SEV_COLORS.get(sev, DARK_GRAY), leading=11)),
                    Paragraph(f.get("issue", "")[:60], ST["td"]),
                    Paragraph(
                        "${:,}\u2013${:,}".format(c.get("low", 0), c.get("high", 0))
                        if c.get("high", 0) > 0 else "N/A", ST["td"]),
                    Paragraph(f.get("recommendation", "")[:60], ST["td"]),
                ])
            fit = Table(fdata,
                        colWidths=[0.22*inch, 0.72*inch, W*0.33, 0.82*inch, W*0.28])
            fit.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("GRID",       (0, 0), (-1, -1), 0.5, MID_GRAY),
                ("VALIGN",     (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 4),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ]))
            story.append(fit)
    story.append(sp(14))

    # Strengths & Risks
    strengths = rec.get("key_strengths", [])
    risks     = rec.get("key_risks", [])
    if strengths or risks:
        story.append(Paragraph("Strengths & Risks", ST["h3"]))
        story.append(sr_table(strengths, risks))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # SECTION 2: PRICE ANALYSIS
    # ═══════════════════════════════════════════════════════
    story.append(section_badge(2, "Price Analysis"))
    story.append(sp(10))

    est       = pred.get("estimated_value", 0)
    delta_pct = ((est - ask) / ask * 100) if ask else 0
    adj_pct   = pred.get("adjustment_pct", 0)
    ci        = pred.get("confidence_interval", {})

    story.append(kv_table([
        ("Asking Price",
         "${:,.0f}".format(ask)),
        ("AI Estimated Value",
         "${:,.0f}  ({:+.1f}% vs asking)".format(est, delta_pct)),
        ("Confidence Interval",
         "${:,.0f} \u2013 ${:,.0f}".format(
             ci.get("low", 0), ci.get("high", 0))),
        ("Condition Adjustment",
         "{:+.1f}%  applied based on interior condition assessment".format(adj_pct)),
        ("Confidence Level",
         pred.get("confidence_level", "medium").capitalize()),
    ]))
    story.append(sp(10))

    if pred.get("reasoning"):
        story.append(Paragraph("Condition Assessment Reasoning:", ST["h3"]))
        story.append(Paragraph(pred["reasoning"], ST["body_j"]))
    story.append(sp(14))

    # Financial model
    story.append(Paragraph("Financial Model", ST["h3"]))
    story.append(kv_table([
        ("Monthly Mortgage",
         "${:,.0f}  (30yr fixed, 7.2% rate)".format(mort.get("monthly_payment", 0))),
        ("Down Payment",
         "${:,.0f}  ({}%)".format(
             mort.get("down_payment", 0), mort.get("down_payment_percent", 20))),
        ("Loan Amount",
         "${:,.0f}".format(mort.get("principal", 0))),
        ("Total Interest Paid",
         "${:,.0f}  over 30 years".format(mort.get("total_interest", 0))),
    ]))

    if report_type == "investor" and roi:
        story.append(sp(10))
        story.append(Paragraph("Investment Returns:", ST["h3"]))
        story.append(kv_table([
            ("Annual Rental Income",
             "${:,.0f}".format(roi.get("annual_rental_income", 0))),
            ("Net Operating Income",
             "${:,.0f}".format(roi.get("net_operating_income", 0))),
            ("Cap Rate",
             "{:.1f}%".format(roi.get("cap_rate_percent", 0))),
            ("Annual Cash Flow",
             "${:,.0f}".format(roi.get("annual_cash_flow", 0))),
            ("Cash-on-Cash Return",
             "{:.1f}%".format(roi.get("cash_on_cash_return", 0))),
        ]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # SECTION 3: TOP COMPARABLE SALES
    # ═══════════════════════════════════════════════════════
    story.append(section_badge(3, "Top Comparable Sales"))
    story.append(sp(10))

    if comp_analysis:
        # Summary metrics
        fair_low = comp_analysis.get("fair_value_range", {}).get("low", 0)
        fair_hi  = comp_analysis.get("fair_value_range", {}).get("high", 0)
        story.append(kv_table([
            ("Comp Median Sale Price",
             "${:,.0f}".format(comp_analysis.get("comp_median_price", 0))),
            ("Comp Median Price / Sqft",
             "${:,.0f}".format(comp_analysis.get("comp_median_price_per_sqft", 0))),
            ("Target Price / Sqft",
             "${:,.0f}".format(comp_analysis.get("target_price_per_sqft", 0))),
            ("Target vs Comp Median",
             "{:+.1f}%".format(comp_analysis.get("target_vs_median_pct", 0))),
            ("Fair Value Range",
             "${:,.0f} \u2013 ${:,.0f}".format(fair_low, fair_hi)),
            ("Market Verdict",
             comp_analysis.get("verdict", "")),
        ]))
        story.append(sp(10))

        if comp_analysis.get("price_delta_explanation"):
            story.append(Paragraph("Price Position Analysis:", ST["h3"]))
            story.append(Paragraph(
                comp_analysis["price_delta_explanation"], ST["body_j"]))
        story.append(sp(10))

        # Price adjustment factors
        factors = comp_analysis.get("adjustment_factors", [])
        if factors:
            story.append(Paragraph("Condition Adjustment Factors vs Comp Average:", ST["h3"]))
            fdata = [[
                Paragraph("Factor", ST["th"]),
                Paragraph("Price Impact", ST["th"])
            ]]
            for f in factors:
                impact = f.get("impact_pct", 0)
                sign   = "+" if impact >= 0 else ""
                fcolor = GREEN if impact >= 0 else RED
                fdata.append([
                    Paragraph(f.get("factor", ""), ST["td"]),
                    Paragraph("{}{:.1f}%".format(sign, impact),
                        ParagraphStyle("imp", fontName="Helvetica-Bold",
                                       fontSize=9, textColor=fcolor, leading=12))
                ])
            ft = Table(fdata, colWidths=[W * 0.78, W * 0.22])
            ft.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("GRID",       (0, 0), (-1, -1), 0.5, MID_GRAY),
                ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ]))
            story.append(ft)
        story.append(sp(14))

    if comp_list:
        # Main comp table
        story.append(Paragraph("Comparable Sales Detail:", ST["h3"]))
        story.append(comp_table(comp_list))
        story.append(sp(14))

        # Interior condition + links
        story.append(Paragraph("Interior Condition & Listing Links:", ST["h3"]))
        story.append(Paragraph(
            "Note: Comparable sales data and listing URLs are AI-generated estimates "
            "for illustrative purposes. Verify with MLS or licensed agent.",
            ParagraphStyle("note", fontName="Helvetica-Oblique", fontSize=8,
                           textColor=ORANGE, leading=11, spaceAfter=6)
        ))
        story.append(comp_detail_table(comp_list))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # SECTION 4: NEGOTIATION STRATEGY
    # ═══════════════════════════════════════════════════════
    story.append(section_badge(4, "Negotiation Strategy"))
    story.append(sp(10))

    story.append(Paragraph(rec.get("negotiation_leverage", ""), ST["body_j"]))
    story.append(sp(12))

    if comp_analysis:
        fair_low = comp_analysis.get("fair_value_range", {}).get("low", 0)
        fair_hi  = comp_analysis.get("fair_value_range", {}).get("high", 0)
        verdict  = rec.get("verdict", "")
        if fair_low and fair_hi:
            # If underpriced/BUY, don't suggest going below asking
            if verdict == "BUY" or ask <= fair_low:
                savings_str  = "Property is already below or at market value — good value at asking"
                offer_str    = "${:,.0f}  (asking price — already fairly valued)".format(int(ask))
            else:
                savings_low = ask - fair_hi
                savings_hi  = ask - fair_low
                if savings_hi <= 0:
                    savings_str = "Property is already below market — good value at asking"
                elif savings_low <= 0:
                    savings_str = "Up to ${:,.0f} if offer accepted at fair value low".format(
                        int(savings_hi))
                else:
                    savings_str = "${:,.0f} \u2013 ${:,.0f}".format(
                        int(savings_low), int(savings_hi))
                offer_str = "${:,.0f}  (bottom of fair value range)".format(int(fair_low))

            story.append(kv_table([
                ("Suggested Offer Range",    "${:,.0f} \u2013 ${:,.0f}".format(
                    int(fair_low), int(fair_hi))),
                ("Potential Savings vs Asking", savings_str),
                ("Opening Offer Suggestion", offer_str),
            ]))

    if insp:
        cost = insp.get("total_estimated_repair_cost", {})
        if cost.get("high", 0) > 0:
            story.append(sp(10))
            story.append(Paragraph("Inspection-Based Leverage:", ST["h3"]))
            story.append(kv_table([
                ("Repair Credits to Request",
                 "${:,} \u2013 ${:,}  (based on inspection findings)".format(
                     cost.get("low", 0), cost.get("high", 0))),
                ("Recommended Approach",
                 "Request seller credit at closing rather than price reduction "
                 "— easier to negotiate and achieves the same financial outcome"),
            ]))

    # Negotiation email template
    story.append(sp(14))
    story.append(Paragraph("Ready-to-Send Offer Email:", ST["h3"]))
    fair_low    = comp_analysis.get("fair_value_range", {}).get("low", 0) if comp_analysis else 0
    repair_low  = insp.get("total_estimated_repair_cost", {}).get("low", 0) if insp else 0
    repair_high = insp.get("total_estimated_repair_cost", {}).get("high", 0) if insp else 0
    verdict     = rec.get("verdict", "")
    # If BUY/underpriced offer at asking; if NEGOTIATE/AVOID offer at fair value low
    if verdict == "BUY" or not fair_low or ask <= fair_low:
        offer_price = int(ask)
    else:
        offer_price = int(fair_low)

    email_body = (
        "Subject: Offer for {address}\n\n"
        "Dear [Listing Agent],\n\n"
        "We are pleased to submit an offer of ${offer:,.0f} for the property at {address}. "
        "Our offer reflects the current market data and comparable sales in the area, "
        "which indicate a fair value range of ${fair_low:,.0f}\u2013${fair_hi:,.0f}.\n\n"
        "{repair_para}"
        "We are motivated buyers and can be flexible on closing timeline. "
        "Please review our offer and let us know if you have any questions.\n\n"
        "Best regards,\n"
        "[Your Name]"
    ).format(
        address=property_address,
        offer=offer_price,
        fair_low=fair_low if fair_low else int(ask * 0.97),
        fair_hi=comp_analysis.get("fair_value_range", {}).get("high", ask) if comp_analysis else ask,
        repair_para=(
            "Additionally, the inspection identified ${:,}\u2013${:,} in repair items. "
            "We respectfully request a seller credit of ${:,} at closing to address these findings.\n\n".format(
                repair_low, repair_high, repair_high)
            if repair_high > 0 else ""
        )
    )

    email_box = Table([[
        [Paragraph(line, ParagraphStyle("email",
            fontName="Courier", fontSize=8.5, textColor=DARK_GRAY,
            leading=13, spaceAfter=2))
         for line in email_body.split("\n")]
    ]], colWidths=[W])
    email_box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GRAY),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    story.append(email_box)

    story.append(sp(20))
    story.append(HRFlowable(width=W, color=MID_GRAY, thickness=0.5))
    story.append(sp(8))
    story.append(Paragraph(
        "Disclaimer: This report is generated by AI for informational purposes only. "
        "Price estimates are based on condition scoring and AI-generated comparable data, "
        "not verified MLS data. Comparable sales addresses and listing URLs are "
        "illustrative examples. Always consult a licensed real estate professional "
        "before making any purchase decision.",
        ST["disc"]
    ))

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print("  PDF saved: " + output_path)
    return output_path
