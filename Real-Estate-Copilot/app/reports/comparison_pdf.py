from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os

BLUE       = HexColor("#1B4F8A")
ORANGE     = HexColor("#E07A2F")
GREEN      = HexColor("#2E7D32")
RED        = HexColor("#C62828")
LIGHT_BLUE = HexColor("#EBF3FB")
LIGHT_GRAY = HexColor("#F5F5F5")
MID_GRAY   = HexColor("#CCCCCC")
DARK_GRAY  = HexColor("#444444")

VERDICT_COLORS = {"BUY": GREEN, "NEGOTIATE": ORANGE, "AVOID": RED}
W = letter[0] - 1.4 * inch
BORDER = {"style": "SINGLE", "size": 1, "color": "#CCCCCC"}


def S(name, **kw):
    return ParagraphStyle(name, **kw)


ST = {
    "cover_title": S("ct", fontName="Helvetica-Bold", fontSize=26, textColor=white,
                     alignment=TA_CENTER, leading=32),
    "cover_sub":   S("cs", fontName="Helvetica", fontSize=12,
                     textColor=HexColor("#B8D4F0"), alignment=TA_CENTER, leading=16),
    "cover_date":  S("cd", fontName="Helvetica-Oblique", fontSize=10,
                     textColor=HexColor("#7BAFD4"), alignment=TA_CENTER),
    "h2":    S("h2", fontName="Helvetica-Bold", fontSize=11, textColor=ORANGE,
               leading=14, spaceBefore=10, spaceAfter=4),
    "body":  S("body", fontName="Helvetica", fontSize=10, textColor=DARK_GRAY,
               leading=15, spaceAfter=4),
    "body_j":S("bodyj", fontName="Helvetica", fontSize=10, textColor=DARK_GRAY,
               leading=15, spaceAfter=4, alignment=TA_JUSTIFY),
    "th":    S("th", fontName="Helvetica-Bold", fontSize=8.5, textColor=white, leading=11),
    "td":    S("td", fontName="Helvetica", fontSize=9, textColor=DARK_GRAY, leading=12),
    "td_b":  S("tdb", fontName="Helvetica-Bold", fontSize=9, textColor=DARK_GRAY, leading=12),
    "label": S("lbl", fontName="Helvetica-Bold", fontSize=9, textColor=BLUE, leading=12),
    "value": S("val", fontName="Helvetica", fontSize=9, textColor=DARK_GRAY, leading=12),
    "disc":  S("disc", fontName="Helvetica-Oblique", fontSize=8,
               textColor=MID_GRAY, leading=11, alignment=TA_JUSTIFY),
}

grid_style = [
    ("GRID", (0, 0), (-1, -1), 0.4, MID_GRAY),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
]


def sp(n=8):
    return Spacer(1, n)


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(MID_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(0.7 * inch, 0.55 * inch, letter[0] - 0.7 * inch, 0.55 * inch)
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawCentredString(
        letter[0] / 2, 0.38 * inch,
        "Real Estate Copilot  |  Multi-Property Comparison  |  Confidential"
    )
    if doc.page > 1:
        canvas.drawRightString(letter[0] - 0.7 * inch, 0.38 * inch, str(doc.page))
    canvas.restoreState()


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


def score_bar(score):
    filled = max(0.01, min(1.0, score / 100))
    empty  = max(0.01, 1.0 - filled)
    bar_w  = 1.4 * inch
    color  = GREEN if score >= 70 else ORANGE if score >= 45 else RED

    filled_cell = Table([[Paragraph("", ST["td"])]],
                        colWidths=[bar_w * filled])
    filled_cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    empty_cell = Table([[Paragraph("", ST["td"])]],
                       colWidths=[bar_w * empty])
    empty_cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    label = Paragraph(
        "{:.0f}".format(score),
        ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=9,
                       textColor=color, leading=12)
    )

    t = Table([[filled_cell, empty_cell, label]],
              colWidths=[bar_w * filled, bar_w * empty, 0.35 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def kv_table(rows, col1_w=1.6 * inch):
    data = []
    ts = list(grid_style) + [("VALIGN", (0, 0), (-1, -1), "TOP")]
    for i, (k, v) in enumerate(rows):
        data.append([Paragraph(k, ST["label"]), Paragraph(v, ST["value"])])
        ts += [
            ("BACKGROUND", (0, i), (0, i), LIGHT_BLUE if i % 2 == 0 else white),
            ("BACKGROUND", (1, i), (1, i), white if i % 2 == 0 else LIGHT_GRAY),
        ]
    t = Table(data, colWidths=[col1_w, W - col1_w])
    t.setStyle(TableStyle(ts))
    return t


def generate_comparison_pdf(
    comparison_result,
    output_path,
    agent_name=None,
    agent_license=None,
):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    props       = comparison_result.get("properties", [])
    valid_props = [p for p in props if not p.get("error")]
    top_pick    = comparison_result.get("top_pick", "")
    top_reason  = comparison_result.get("top_pick_reason", "")
    n           = len(valid_props)

    story = []

    # ── COVER ─────────────────────────────────────────
    cover_items = [
        Spacer(1, 0.4 * inch),
        Paragraph("Multi-Property Comparison", ST["cover_title"]),
        Spacer(1, 0.08 * inch),
        Paragraph(
            "Real Estate Copilot  \u00b7  {} Properties Analyzed".format(n),
            ST["cover_sub"]
        ),
        Spacer(1, 0.06 * inch),
        Paragraph(datetime.now().strftime("%B %d, %Y"), ST["cover_date"]),
        Spacer(1, 0.12 * inch),
    ]

    for p in valid_props:
        is_top = p["address"] == top_pick
        cover_items.append(Paragraph(
            ("\u2605 " if is_top else "\u2022 ") + p["address"],
            ParagraphStyle("addr",
                fontName="Helvetica-Bold" if is_top else "Helvetica",
                fontSize=10,
                textColor=HexColor("#FFD700") if is_top else HexColor("#B8D4F0"),
                alignment=TA_CENTER, leading=15)
        ))

    if agent_name:
        label = "Prepared by " + agent_name
        if agent_license:
            label += "  \u00b7  " + agent_license
        cover_items += [
            Spacer(1, 0.1 * inch),
            Paragraph(label, ParagraphStyle("ca", fontName="Helvetica-Bold",
                fontSize=10, textColor=white, alignment=TA_CENTER)),
        ]
    cover_items.append(Spacer(1, 0.4 * inch))

    cover = Table([[cover_items]], colWidths=[W + 1.4 * inch])
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(cover)
    story.append(sp(20))

    # ── SECTION 1: OVERVIEW TABLE ──────────────────────
    story.append(section_badge(1, "Side-by-Side Comparison"))
    story.append(sp(10))

    label_w = 1.6 * inch
    prop_w  = (W - label_w) / n

    # Header row
    header = [Paragraph("", ST["th"])]
    for p in valid_props:
        is_top     = p["address"] == top_pick
        rank_color = GREEN if is_top else BLUE
        short_addr = p["address"].split(",")[0]
        rank_label = "#{} {}".format(p["rank"], "\u2605 TOP PICK" if is_top else "")

        inner = Table(
            [[Paragraph(rank_label, ParagraphStyle("rh",
                 fontName="Helvetica-Bold", fontSize=8,
                 textColor=HexColor("#FFD700") if is_top else white,
                 alignment=TA_CENTER, leading=10))],
             [Paragraph(short_addr, ParagraphStyle("ah",
                 fontName="Helvetica-Bold", fontSize=9,
                 textColor=white, alignment=TA_CENTER, leading=12))]],
            colWidths=[prop_w - 4]
        )
        inner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), rank_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]))
        header.append(inner)

    # Data rows
    def drow(label, values, bold=False):
        row = [Paragraph(label, ST["label"])]
        for v in values:
            row.append(Paragraph(str(v), ST["td_b"] if bold else ST["td"]))
        return row

    rows = [
        drow("Asking Price",
             ["${:,.0f}".format(p["asking_price"]) for p in valid_props]),
        drow("AI Est. Value",
             ["${:,.0f} ({:+.1f}%)".format(p["estimated_value"], p["delta_pct"])
              for p in valid_props]),
        drow("Verdict",
             [p["verdict"] for p in valid_props], bold=True),
        drow("Condition Score",
             ["{}/100 ({})".format(p["condition_score"], p["condition_grade"])
              for p in valid_props]),
        drow("Comp Median",
             ["${:,.0f}".format(p["comp_median"]) if p["comp_median"] else "N/A"
              for p in valid_props]),
        drow("vs Comp Median",
             ["{:+.1f}%".format(p["price_vs_comp"]) if p["price_vs_comp"] else "N/A"
              for p in valid_props]),
        drow("Monthly Payment",
             ["${:,.0f}".format(p["monthly_payment"]) for p in valid_props]),
        drow("Critical Issues",
             [str(p["critical_issues"]) if p["critical_issues"] is not None else "N/A"
              for p in valid_props]),
        drow("Repair Cost",
             ["${:,}-${:,}".format(p["repair_low"], p["repair_high"])
              if p.get("repair_low") is not None else "No inspection data"
              for p in valid_props]),
        drow("Composite Score",
             ["{:.0f}/100".format(p["composite_score"]) for p in valid_props], bold=True),
    ]

    col_widths = [label_w] + [prop_w] * n
    ts = list(grid_style) + [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
    ]
    for i in range(1, len(rows) + 1):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))

    # Highlight top pick column
    for i, p in enumerate(valid_props):
        if p["address"] == top_pick:
            ts.append(("BACKGROUND", (i + 1, 0), (i + 1, 0), GREEN))

    overview_t = Table([header] + rows, colWidths=col_widths)
    overview_t.setStyle(TableStyle(ts))
    story.append(overview_t)
    story.append(sp(12))

    # Score bars
    story.append(Paragraph("Composite Score", ST["h2"]))
    story.append(sp(6))
    score_rows = []
    for p in valid_props:
        short = p["address"].split(",")[0]
        score_rows.append([Paragraph(short, ST["label"]), score_bar(p["composite_score"])])
    score_t = Table(score_rows, colWidths=[2.2 * inch, W - 2.2 * inch])
    score_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, MID_GRAY),
    ]))
    story.append(score_t)
    story.append(PageBreak())

    # ── SECTION 2: RECOMMENDATION ─────────────────────
    story.append(section_badge(2, "Our Recommendation"))
    story.append(sp(10))

    if valid_props:
        top = next((p for p in valid_props if p["address"] == top_pick), valid_props[0])
        rec_color = VERDICT_COLORS.get(top["verdict"], DARK_GRAY)

        rec_inner = [
            Paragraph("\u2605  TOP PICK", ParagraphStyle("tp",
                fontName="Helvetica-Bold", fontSize=11, textColor=rec_color,
                leading=14, alignment=TA_CENTER)),
            Spacer(1, 4),
            Paragraph(top["address"], ParagraphStyle("ta",
                fontName="Helvetica-Bold", fontSize=14, textColor=DARK_GRAY,
                leading=18, alignment=TA_CENTER)),
            Spacer(1, 6),
            Paragraph(top_reason, ParagraphStyle("tr",
                fontName="Helvetica-Oblique", fontSize=10, textColor=DARK_GRAY,
                leading=15, alignment=TA_CENTER)),
            Spacer(1, 8),
            Paragraph(top.get("summary", ""), ParagraphStyle("ts",
                fontName="Helvetica", fontSize=10, textColor=DARK_GRAY,
                leading=15, alignment=TA_LEFT)),
        ]
        rec_box = Table([[rec_inner]], colWidths=[W])
        rec_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
            ("BOX", (0, 0), (-1, -1), 2, rec_color),
            ("TOPPADDING", (0, 0), (-1, -1), 16),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ("LEFTPADDING", (0, 0), (-1, -1), 20),
            ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ]))
        story.append(rec_box)
        story.append(sp(14))

        # Strengths & Risks of top pick
        story.append(Paragraph("Top Pick \u2014 Strengths & Risks", ST["h2"]))
        strengths = top.get("key_strengths", [])
        risks     = top.get("key_risks", [])
        max_len   = max(len(strengths), len(risks), 1)
        sr_data   = [[Paragraph("Strengths", ST["label"]),
                      Paragraph("Risks", ST["label"])]]
        for i in range(max_len):
            s = ("+ " + strengths[i]) if i < len(strengths) else ""
            r = ("- " + risks[i])     if i < len(risks)     else ""
            sr_data.append([Paragraph(s, ST["value"]), Paragraph(r, ST["value"])])
        sr_t = Table(sr_data, colWidths=[W * 0.5, W * 0.5])
        sr_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR",  (0, 0), (-1, 0), white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID",       (0, 0), (-1, -1), 0.4, MID_GRAY),
            ("VALIGN",     (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        story.append(sr_t)
    story.append(PageBreak())

    # ── SECTION 3: PER-PROPERTY DETAIL ────────────────
    story.append(section_badge(3, "Property-by-Property Analysis"))
    story.append(sp(10))

    for idx, p in enumerate(valid_props):
        is_top     = p["address"] == top_pick
        rank_color = GREEN if is_top else BLUE

        prop_header = Table([[
            Paragraph("#{} {}".format(p["rank"], "\u2605 TOP PICK" if is_top else ""),
                ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=11,
                    textColor=HexColor("#FFD700") if is_top else white,
                    alignment=TA_CENTER, leading=14)),
            Paragraph(p["address"], ParagraphStyle("pa",
                fontName="Helvetica-Bold", fontSize=12, textColor=white, leading=16)),
        ]], colWidths=[1.2 * inch, W - 1.2 * inch])
        prop_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), rank_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(prop_header)
        story.append(sp(8))

        kv_rows = [
            ("Asking Price",
             "${:,.0f}".format(p["asking_price"])),
            ("AI Est. Value",
             "${:,.0f}  ({:+.1f}% vs asking)".format(p["estimated_value"], p["delta_pct"])),
            ("Verdict",
             "{} (confidence: {:.0%})".format(p["verdict"], p["confidence"])),
            ("Condition Score",
             "{}/100  \u2014  {}".format(p["condition_score"], p["condition_grade"])),
            ("Monthly Payment",
             "${:,.0f}".format(p["monthly_payment"])),
            ("Comp Median",
             "${:,.0f}  ({:+.1f}% vs asking)".format(p["comp_median"], p["price_vs_comp"])
             if p["comp_median"] else "N/A"),
            ("Repair Cost",
             "${:,} \u2013 ${:,}".format(p["repair_low"], p["repair_high"])
             if p.get("repair_low") is not None else "No inspection data available"),
            ("Composite Score",
             "{:.0f}/100".format(p["composite_score"])),
        ]
        story.append(kv_table(kv_rows))
        story.append(sp(10))

        if p.get("summary"):
            story.append(Paragraph(p["summary"], ST["body_j"]))
            story.append(sp(8))

        if p.get("negotiation"):
            story.append(Paragraph("Negotiation Strategy", ST["h2"]))
            story.append(Paragraph(p["negotiation"], ST["body_j"]))

        if idx < len(valid_props) - 1:
            story.append(sp(16))
            story.append(HRFlowable(width=W, color=MID_GRAY, thickness=0.5))
            story.append(sp(16))

    story.append(sp(20))
    story.append(HRFlowable(width=W, color=MID_GRAY, thickness=0.4))
    story.append(sp(8))
    story.append(Paragraph(
        "Disclaimer: This report is generated by AI for informational purposes only. "
        "Price estimates are based on condition scoring and AI-generated comparable data. "
        "Always consult a licensed real estate professional before making any purchase decision.",
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
