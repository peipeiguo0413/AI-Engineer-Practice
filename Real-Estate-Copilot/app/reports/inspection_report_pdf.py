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

# ── Brand colors ───────────────────────────────────────
BLUE       = HexColor("#1B4F8A")
ORANGE     = HexColor("#E07A2F")
GREEN      = HexColor("#2E7D32")
RED        = HexColor("#C62828")
YELLOW     = HexColor("#F9A825")
LIGHT_BLUE = HexColor("#EBF3FB")
LIGHT_GRAY = HexColor("#F5F5F5")
MID_GRAY   = HexColor("#CCCCCC")
DARK_GRAY  = HexColor("#444444")

SEVERITY_COLORS = {
    "Critical":      RED,
    "Major":         ORANGE,
    "Minor":         YELLOW,
    "Informational": HexColor("#1565C0"),
}

SEVERITY_BG = {
    "Critical":      HexColor("#FFEBEE"),
    "Major":         HexColor("#FFF3E0"),
    "Minor":         HexColor("#FFFDE7"),
    "Informational": HexColor("#E3F2FD"),
}

RECOMMENDATION_COLORS = {
    "BUY":       GREEN,
    "NEGOTIATE": ORANGE,
    "AVOID":     RED,
}

W = letter[0] - 1.4 * inch

# ── Styles ─────────────────────────────────────────────
def S(name, **kwargs):
    return ParagraphStyle(name, **kwargs)

ST = {
    "cover_title": S("ct", fontName="Helvetica-Bold", fontSize=28,
                     textColor=white, alignment=TA_CENTER, leading=34),
    "cover_sub":   S("cs", fontName="Helvetica", fontSize=13,
                     textColor=HexColor("#B8D4F0"), alignment=TA_CENTER, leading=18),
    "cover_date":  S("cd", fontName="Helvetica-Oblique", fontSize=10,
                     textColor=HexColor("#7BAFD4"), alignment=TA_CENTER),
    "h2":          S("h2", fontName="Helvetica-Bold", fontSize=13,
                     textColor=BLUE, leading=16, spaceBefore=14, spaceAfter=6),
    "h3":          S("h3", fontName="Helvetica-Bold", fontSize=11,
                     textColor=ORANGE, leading=14, spaceBefore=10, spaceAfter=4),
    "body":        S("body", fontName="Helvetica", fontSize=10,
                     textColor=DARK_GRAY, leading=15, spaceAfter=4,
                     alignment=TA_JUSTIFY),
    "bullet":      S("bullet", fontName="Helvetica", fontSize=10,
                     textColor=DARK_GRAY, leading=14, leftIndent=14,
                     spaceAfter=3, bulletText="\u2022", bulletIndent=4),
    "label":       S("label", fontName="Helvetica-Bold", fontSize=9,
                     textColor=BLUE, leading=12),
    "value":       S("value", fontName="Helvetica", fontSize=9,
                     textColor=DARK_GRAY, leading=12),
    "footer":      S("footer", fontName="Helvetica-Oblique", fontSize=8,
                     textColor=MID_GRAY, alignment=TA_CENTER),
    "tag":         S("tag", fontName="Helvetica-Bold", fontSize=9,
                     textColor=white, alignment=TA_CENTER, leading=11),
}

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(MID_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(0.7*inch, 0.55*inch, letter[0]-0.7*inch, 0.55*inch)
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawCentredString(
        letter[0]/2, 0.38*inch,
        "Real Estate Copilot  |  Inspection Analysis Report  |  Confidential"
    )
    if doc.page > 1:
        canvas.drawRightString(letter[0]-0.7*inch, 0.38*inch, str(doc.page))
    canvas.restoreState()

def severity_badge(severity: str) -> Table:
    color = SEVERITY_COLORS.get(severity, DARK_GRAY)
    bg    = SEVERITY_BG.get(severity, LIGHT_GRAY)
    t = Table(
        [[Paragraph(severity, ParagraphStyle("sb",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=color, alignment=TA_CENTER, leading=10))]],
        colWidths=[0.9*inch]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("BOX",           (0,0), (-1,-1), 0.8, color),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]))
    return t

def recommendation_box(rec: str, confidence: float, summary: str) -> Table:
    color = RECOMMENDATION_COLORS.get(rec, DARK_GRAY)
    inner = [
        Paragraph(rec, ParagraphStyle("rb",
            fontName="Helvetica-Bold", fontSize=32,
            textColor=color, alignment=TA_CENTER, leading=38)),
        Spacer(1, 4),
        Paragraph(
            f"Confidence: {int(confidence * 100)}%",
            ParagraphStyle("rc", fontName="Helvetica", fontSize=11,
                           textColor=DARK_GRAY, alignment=TA_CENTER, leading=14)
        ),
        Spacer(1, 8),
        Paragraph(summary, ParagraphStyle("rs",
            fontName="Helvetica", fontSize=10,
            textColor=DARK_GRAY, alignment=TA_CENTER,
            leading=14, leftIndent=10, rightIndent=10)),
    ]
    t = Table([[inner]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT_BLUE),
        ("BOX",           (0,0), (-1,-1), 2, color),
        ("TOPPADDING",    (0,0), (-1,-1), 16),
        ("BOTTOMPADDING", (0,0), (-1,-1), 16),
        ("LEFTPADDING",   (0,0), (-1,-1), 20),
        ("RIGHTPADDING",  (0,0), (-1,-1), 20),
    ]))
    return t

def cost_summary_table(result: dict) -> Table:
    cost     = result.get("total_estimated_repair_cost", {})
    low      = cost.get("low", 0)
    high     = cost.get("high", 0)
    critical = result.get("critical_issues_count", 0)
    major    = result.get("major_issues_count", 0)
    findings = result.get("findings", [])
    minor    = sum(1 for f in findings if f.get("severity") == "Minor")
    info     = sum(1 for f in findings if f.get("severity") == "Informational")

    rows = [
        [Paragraph("Metric", ST["label"]),
         Paragraph("Value", ST["label"])],
        [Paragraph("Estimated Repair Cost", ST["value"]),
         Paragraph(f"${low:,} – ${high:,}", ParagraphStyle("cost",
             fontName="Helvetica-Bold", fontSize=10,
             textColor=RED if critical > 0 else ORANGE if major > 0 else GREEN,
             leading=13))],
        [Paragraph("Critical Issues", ST["value"]),
         Paragraph(str(critical), ParagraphStyle("crit",
             fontName="Helvetica-Bold", fontSize=10,
             textColor=RED if critical > 0 else GREEN, leading=13))],
        [Paragraph("Major Issues", ST["value"]),
         Paragraph(str(major), ParagraphStyle("maj",
             fontName="Helvetica-Bold", fontSize=10,
             textColor=ORANGE if major > 0 else GREEN, leading=13))],
        [Paragraph("Minor Issues", ST["value"]),
         Paragraph(str(minor), ST["value"])],
        [Paragraph("Informational", ST["value"]),
         Paragraph(str(info), ST["value"])],
    ]

    t = Table(rows, colWidths=[W*0.6, W*0.4])
    ts = [
        ("BACKGROUND",    (0,0), (-1,0), BLUE),
        ("TEXTCOLOR",     (0,0), (-1,0), white),
        ("GRID",          (0,0), (-1,-1), 0.5, MID_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("TEXTCOLOR",     (0,0), (-1,0), white),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0,i), (-1,i), LIGHT_GRAY))
    t.setStyle(TableStyle(ts))
    return t

def findings_table(findings: list) -> Table:
    header = [
        Paragraph("#",           ST["label"]),
        Paragraph("Severity",    ST["label"]),
        Paragraph("Issue",       ST["label"]),
        Paragraph("Est. Cost",   ST["label"]),
        Paragraph("Action",      ST["label"]),
    ]
    rows = [header]
    for i, f in enumerate(findings, 1):
        cost  = f.get("estimated_repair_cost_usd", {})
        low   = cost.get("low", 0)
        high  = cost.get("high", 0)
        sev   = f.get("severity", "Informational")
        color = SEVERITY_COLORS.get(sev, DARK_GRAY)
        rows.append([
            Paragraph(str(i), ST["value"]),
            Paragraph(sev, ParagraphStyle("sv",
                fontName="Helvetica-Bold", fontSize=9,
                textColor=color, leading=12)),
            Paragraph(f.get("issue", "")[:80],
                      ST["value"]),
            Paragraph(
                f"${low:,}–${high:,}" if high > 0 else "N/A",
                ST["value"]
            ),
            Paragraph(f.get("recommendation", "")[:60],
                      ST["value"]),
        ])

    t = Table(rows, colWidths=[
        0.25*inch, 0.85*inch, W*0.38, 0.85*inch, W*0.28
    ])
    ts = [
        ("BACKGROUND",    (0,0), (-1,0), BLUE),
        ("TEXTCOLOR",     (0,0), (-1,0), white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID",          (0,0), (-1,-1), 0.5, MID_GRAY),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0,i), (-1,i), LIGHT_GRAY))
    t.setStyle(TableStyle(ts))
    return t

def generate_inspection_pdf(result: dict, output_path: str,
                             property_address: str = "Property Address",
                             agent_name: str = None) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    story = []

    # ── Cover ──────────────────────────────────────────
    cover_content = [
        Spacer(1, 0.5*inch),
        Paragraph("Inspection Analysis Report", ST["cover_title"]),
        Spacer(1, 0.1*inch),
        Paragraph("Powered by Real Estate Copilot", ST["cover_sub"]),
        Spacer(1, 0.08*inch),
        Paragraph(
            f"{property_address}  \u2022  {datetime.now().strftime('%B %d, %Y')}",
            ST["cover_date"]
        ),
    ]
    if agent_name:
        cover_content += [
            Spacer(1, 0.06*inch),
            Paragraph(f"Prepared by {agent_name}", ST["cover_date"]),
        ]
    cover_content.append(Spacer(1, 0.5*inch))

    cover = Table([[cover_content]], colWidths=[W + 1.4*inch])
    cover.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), BLUE),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(cover)
    story.append(Spacer(1, 0.3*inch))

    # ── Recommendation ─────────────────────────────────
    story.append(Paragraph("Purchase Recommendation", ST["h2"]))
    story.append(recommendation_box(
        result.get("recommendation", "N/A"),
        result.get("confidence", 0),
        result.get("summary", "")
    ))
    story.append(Spacer(1, 0.2*inch))

    # ── Cost Summary ───────────────────────────────────
    story.append(Paragraph("Cost & Issue Summary", ST["h2"]))
    story.append(cost_summary_table(result))
    story.append(Spacer(1, 0.2*inch))

    # ── Key Concerns ───────────────────────────────────
    concerns = result.get("key_concerns", [])
    if concerns:
        story.append(Paragraph("Key Concerns", ST["h2"]))
        for concern in concerns:
            story.append(Paragraph(concern, ST["bullet"]))
        story.append(Spacer(1, 0.2*inch))

    story.append(PageBreak())

    # ── Full Findings ──────────────────────────────────
    story.append(Paragraph("Full Findings", ST["h2"]))
    story.append(Paragraph(
        f"The inspection identified {len(result.get('findings', []))} items. "
        "Review each item below and consult with your agent and contractor "
        "before making a purchase decision.",
        ST["body"]
    ))
    story.append(Spacer(1, 0.1*inch))
    story.append(findings_table(result.get("findings", [])))
    story.append(Spacer(1, 0.3*inch))

    # ── Disclaimer ─────────────────────────────────────
    story.append(HRFlowable(width=W, color=MID_GRAY, thickness=0.5))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "Disclaimer: This report is generated by AI and is intended for informational "
        "purposes only. All cost estimates are approximate ranges and may vary. "
        "This report does not replace a professional home inspection or legal advice. "
        "Always consult qualified professionals before making real estate decisions.",
        ParagraphStyle("disc", fontName="Helvetica-Oblique", fontSize=8,
                       textColor=MID_GRAY, leading=11, alignment=TA_JUSTIFY)
    ))

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.7*inch, rightMargin=0.7*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch,
    )
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"  PDF saved: {output_path}")
    return output_path